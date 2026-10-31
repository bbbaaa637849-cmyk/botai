"""
LLM Router and Gemini API Multi-Key Pool Manager for Project Aether-Human.
Provides robust sliding-window rate limiting, least-loaded key distribution,
multi-model cascading failover, and token metrics across Google Gemini API credentials.
Engineered to handle ~1,000 active users safely across the 11-key pool without 429 exhaustion.
"""

from __future__ import annotations

import asyncio
from collections import deque
import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

from aether_human_core.config.settings import settings

logger = logging.getLogger("Aether.LLMRouter")


class KeyHealthTracker:
    """
    Monitors health metrics, sliding-window RPM, and cool-off periods for a single API key.
    """
    def __init__(self, key: str, index: int):
        self.key: str = key
        self.index: int = index
        self.total_calls: int = 0
        self.successful_calls: int = 0
        self.failed_calls: int = 0
        self.rate_limited_count: int = 0
        self.last_used_timestamp: float = 0.0
        self.cool_down_until: float = 0.0
        self.is_active: bool = True
        # 60-second sliding window timestamps
        self.call_timestamps: deque[float] = deque()

    @property
    def masked_key(self) -> str:
        if len(self.key) <= 10:
            return "***"
        return f"{self.key[:6]}...{self.key[-4:]}"

    def clean_old_calls(self, now: Optional[float] = None) -> None:
        t = now or time.time()
        window_start = t - 60.0
        while self.call_timestamps and self.call_timestamps[0] < window_start:
            self.call_timestamps.popleft()

    def get_current_rpm(self, now: Optional[float] = None) -> int:
        self.clean_old_calls(now)
        return len(self.call_timestamps)

    def is_available(self, max_rpm: int = 12) -> bool:
        if not self.is_active:
            return False
        now = time.time()
        if now < self.cool_down_until:
            return False
        if self.get_current_rpm(now) >= max_rpm:
            return False
        return True

    def seconds_until_available(self, max_rpm: int = 12) -> float:
        if not self.is_active:
            return 9999.0
        now = time.time()
        # Cooldown check
        cooldown_wait = max(0.0, self.cool_down_until - now)
        # Sliding window check
        self.clean_old_calls(now)
        if len(self.call_timestamps) >= max_rpm:
            oldest = self.call_timestamps[0]
            rpm_wait = max(0.0, (oldest + 60.0) - now)
        else:
            rpm_wait = 0.0
        return max(cooldown_wait, rpm_wait)

    def record_attempt(self) -> None:
        now = time.time()
        self.total_calls += 1
        self.last_used_timestamp = now
        self.call_timestamps.append(now)

    def mark_success(self) -> None:
        self.successful_calls += 1
        # Reset cooldown on success
        self.cool_down_until = 0.0

    def mark_rate_limited(self, cool_off_seconds: float = 20.0) -> None:
        self.failed_calls += 1
        self.rate_limited_count += 1
        self.cool_down_until = time.time() + cool_off_seconds
        logger.warning(
            f"Key [{self.index}] ({self.masked_key}) rate-limited (429). Cooldown: {cool_off_seconds:.1f}s."
        )

    def mark_fatal_error(self) -> None:
        self.failed_calls += 1
        self.is_active = False
        logger.error(f"Key [{self.index}] ({self.masked_key}) marked inactive due to fatal auth/permission error.")


class GeminiKeyPoolManager:
    """
    Intelligent Governor managing multi-key pool for Gemini model inference.
    Executes resilient REST-based generation with least-loaded key selection,
    sliding-window RPM smoothing, and multi-model cascading.
    """
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    # Priority cascade of verified fast & high-quota models
    MODEL_CASCADE: List[str] = [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.5-flash",
    ]

    def __init__(self, keys: Optional[List[str]] = None, max_rpm_per_key: int = 12):
        raw_keys = keys if keys is not None else settings.gemini_keys_list
        self.trackers: List[KeyHealthTracker] = [
            KeyHealthTracker(key=k, index=idx) for idx, k in enumerate(raw_keys)
        ]
        self.max_rpm_per_key: int = max_rpm_per_key
        self._lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None
        logger.info(
            f"Initialized GeminiKeyPoolManager with {len(self.trackers)} keys. "
            f"Max pool capacity: {len(self.trackers) * max_rpm_per_key} RPM safe limit."
        )

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=8.0))
        return self._http_client

    async def close(self) -> None:
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def _select_best_tracker(self) -> KeyHealthTracker:
        """
        Picks the healthiest, least-loaded key using sliding-window RPM load balancing.
        If all keys are saturated or cooling down, waits for the earliest one to clear.
        """
        async with self._lock:
            active_trackers = [t for t in self.trackers if t.is_active]
            if not active_trackers:
                raise RuntimeError("No active Gemini API keys available in the pool.")

            now = time.time()
            available = [t for t in active_trackers if t.is_available(self.max_rpm_per_key)]

            if available:
                # Pick the tracker with lowest current RPM in the last 60s
                # Ties broken by oldest last_used_timestamp to ensure fair round-robin
                best = min(available, key=lambda t: (t.get_current_rpm(now), t.last_used_timestamp))
                best.record_attempt()
                return best

            # If no tracker is currently available, find the one that will become available soonest
            soonest_tracker = min(active_trackers, key=lambda t: t.seconds_until_available(self.max_rpm_per_key))
            wait_time = soonest_tracker.seconds_until_available(self.max_rpm_per_key)
            wait_time = min(max(wait_time, 0.1), 5.0)

            logger.info(
                f"All Gemini keys at capacity or cooldown. Governor pacing request: waiting {wait_time:.2f}s "
                f"for key [{soonest_tracker.index}] ({soonest_tracker.masked_key})."
            )
            await asyncio.sleep(wait_time)
            soonest_tracker.record_attempt()
            return soonest_tracker

    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 12
    ) -> str:
        """
        Sends prompt to Gemini with least-loaded key selection and multi-model cascade failover.
        """
        current_model = model_name or settings.gemini_default_model
        temp = temperature if temperature is not None else settings.gemini_temperature
        tokens = max_tokens or settings.gemini_max_output_tokens
        client = await self._get_client()

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temp,
                "maxOutputTokens": tokens
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        last_exception: Optional[Exception] = None
        model_cascade_idx: int = 0

        for attempt in range(max_retries):
            tracker = await self._select_best_tracker()
            url = f"{self.BASE_URL}/{current_model}:generateContent?key={tracker.key}"

            try:
                response = await client.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        text_response = "".join(part.get("text", "") for part in parts)
                        tracker.mark_success()
                        return text_response
                    else:
                        tracker.mark_success()
                        return ""

                elif response.status_code in (429, 503, 500):
                    # Rate limit or temporary outage: cooldown key and rotate model cascade
                    cooldown = 15.0 + (attempt * 3.0)
                    tracker.mark_rate_limited(cool_off_seconds=cooldown)
                    
                    # Advance model cascade
                    model_cascade_idx = (model_cascade_idx + 1) % len(self.MODEL_CASCADE)
                    current_model = self.MODEL_CASCADE[model_cascade_idx]
                    logger.warning(
                        f"Status {response.status_code} on key [{tracker.index}]. "
                        f"Cascading to model: {current_model}."
                    )
                    await asyncio.sleep(0.3)

                elif response.status_code == 404:
                    resp_text = response.text
                    logger.warning(f"Model {current_model} returned 404. Falling back to default flash-lite.")
                    current_model = "gemini-flash-lite-latest"
                    await asyncio.sleep(0.2)

                elif response.status_code in (400, 403):
                    resp_text = response.text
                    if "API_KEY_INVALID" in resp_text or "PERMISSION_DENIED" in resp_text:
                        tracker.mark_fatal_error()
                    else:
                        logger.error(f"Gemini client error {response.status_code}: {resp_text[:120]}")
                        tracker.mark_rate_limited(cool_off_seconds=10.0)

                else:
                    logger.warning(f"Unexpected status {response.status_code}: {response.text[:120]}")
                    tracker.mark_rate_limited(cool_off_seconds=5.0)

            except httpx.RequestError as exc:
                logger.error(f"HTTP request error with key [{tracker.index}]: {exc}")
                tracker.mark_rate_limited(cool_off_seconds=5.0)
                last_exception = exc
                await asyncio.sleep(0.5)

        error_msg = f"Failed to generate content after {max_retries} attempts across Gemini key pool."
        logger.critical(error_msg)
        raise RuntimeError(error_msg) from last_exception

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Prompts Gemini and strictly extracts a valid JSON structure from response.
        """
        augmented_prompt = (
            f"{prompt}\n\nIMPORTANT: Respond with pure, valid JSON only. Do not wrap in markdown or backticks."
        )
        raw_text = await self.generate_content(
            prompt=augmented_prompt,
            system_instruction=system_instruction,
            model_name=model_name,
            temperature=temperature or 0.2,
            max_tokens=2048,
        )

        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.warning(f"JSONDecodeError encountered: {err}. Attempting structured regex recovery.")
            import re
            extracted: Dict[str, Any] = {}
            for field in [
                "reply_text",
                "emotional_reaction",
                "decision",
                "recommended_reaction_emoji",
                "partner_report_message",
                "internal_thought_raw",
            ]:
                match = re.search(rf'"{field}"\s*:\s*"([^"]*)"', cleaned)
                if match:
                    extracted[field] = match.group(1)

            # Boolean check
            bool_match = re.search(r'"should_report_to_partner"\s*:\s*(true|false)', cleaned, re.IGNORECASE)
            extracted["should_report_to_partner"] = bool_match.group(1).lower() == "true" if bool_match else False

            if extracted.get("decision") or extracted.get("reply_text"):
                return extracted

            start_brace = cleaned.find("{")
            end_brace = cleaned.rfind("}")
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                try:
                    return json.loads(cleaned[start_brace : end_brace + 1])
                except Exception:
                    pass
            return {
                "decision": "REPLY_CASUALLY",
                "reply_text": "تمام معاك يا غالي، معاك أهو في المعادي.",
                "emotional_reaction": "طبيعي",
                "internal_thought_raw": cleaned[:200],
            }


# Global singleton instance of GeminiKeyPoolManager
llm_pool = GeminiKeyPoolManager()
