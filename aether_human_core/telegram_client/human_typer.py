"""
Human UX & Typing Simulation Engine for Project Aether-Human.
Implements Multi-Bubble message bursting, typing latency (WPM),
and realistic Arabic keyboard typo generation with automated *self-correction.
"""

from __future__ import annotations

import logging
import random
import re
import asyncio
from typing import List, Tuple, Optional
from pydantic import BaseModel

from aether_human_core.config.settings import settings
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine

logger = logging.getLogger("Aether.Telegram.HumanTyper")


class BurstMessage(BaseModel):
    text: str
    typing_delay_sec: float
    has_typo: bool = False
    correction_text: Optional[str] = None


class HumanTyperSimulator:
    """
    Transforms single text blocks into realistic human chat bursts with timing and typos.
    """
    # Common Arabic keyboard adjacent letter substitution map
    ARABIC_KEYBOARD_NEIGHBORS = {
        "ب": ["ي", "ل", "س"],
        "ي": ["ب", "س", "ش"],
        "ت": ["ن", "ا", "ك"],
        "ن": ["ت", "م", "ه"],
        "م": ["ن", "ك", "و"],
        "ك": ["م", "ت", "ط"],
        "ل": ["ب", "ا", "س"],
        "ا": ["ل", "ت", "أ"],
        "س": ["ي", "ب", "ش"],
        "ش": ["س", "ي"],
        "ر": ["ز", "د", "و"],
        "و": ["ر", "ز", "م"],
        "ه": ["ع", "خ", "ن"],
        "ع": ["ه", "غ"],
    }

    @classmethod
    def split_into_multi_bubble_bursts(cls, text: str) -> List[str]:
        """
        Splits text into 2 to 4 colloquial short message bubbles.
        Avoids sending monolithic paragraphs.
        """
        cleaned = text.strip()
        if not cleaned:
            return []

        # Split on common Arabic human conversational separators
        # E.g. newlines, full stops, or conjunctions
        raw_parts = re.split(r"[\n\r]+|\. +|(?<=[،,]) +", cleaned)
        bubbles: List[str] = []

        current_bubble = ""
        for part in raw_parts:
            part = part.strip()
            if not part:
                continue

            if len(current_bubble) + len(part) < 65 and current_bubble:
                current_bubble = f"{current_bubble} {part}"
            else:
                if current_bubble:
                    bubbles.append(current_bubble.strip())
                current_bubble = part

        if current_bubble:
            bubbles.append(current_bubble.strip())

        # If it's still a single long string, split by word count
        if len(bubbles) == 1 and len(bubbles[0].split()) > 14:
            words = bubbles[0].split()
            mid = len(words) // 2
            bubbles = [" ".join(words[:mid]), " ".join(words[mid:])]

        return bubbles if bubbles else [cleaned]

    @classmethod
    def calculate_typing_delay(
        cls,
        text: str,
        wpm_base: int = settings.typing_speed_wpm_base,
        is_shy: bool = False,
    ) -> float:
        """
        Calculates realistic typing duration in seconds based on word count, fatigue, and shyness.
        """
        circadian = circadian_engine.evaluate_circadian_state()
        effective_wpm = wpm_base * circadian["wpm_multiplier"]
        if is_shy:
            effective_wpm *= 0.75  # Typing slower due to nervousness

        word_count = max(1, len(text.split()))
        # Minutes to seconds
        base_seconds = (word_count / effective_wpm) * 60.0
        # Add human thinking latency jitter (0.8s - 2.5s)
        jitter = random.uniform(0.8, 2.5)
        total_delay = max(1.2, min(14.0, base_seconds + jitter))
        return round(total_delay, 2)

    @classmethod
    def maybe_inject_typo(
        cls,
        text: str,
        base_probability: float = settings.typo_base_probability,
    ) -> Tuple[str, Optional[str]]:
        """
        With a calculated probability, injects a single keyboard typo into a word,
        and provides the follow-up correction string (e.g. '*الكلمة').
        """
        circadian = circadian_engine.evaluate_circadian_state()
        prob = base_probability * circadian["typo_multiplier"]

        words = text.split()
        if len(words) < 3 or random.random() > prob:
            return text, None

        # Pick candidate word with length >= 4
        candidates = [i for i, w in enumerate(words) if len(w) >= 4 and not w.startswith("http")]
        if not candidates:
            return text, None

        target_idx = random.choice(candidates)
        target_word = words[target_idx]

        # Find a character that has keyboard neighbors
        char_indices = [
            i for i, ch in enumerate(target_word) if ch in cls.ARABIC_KEYBOARD_NEIGHBORS
        ]
        if not char_indices:
            return text, None

        char_idx = random.choice(char_indices)
        orig_char = target_word[char_idx]
        typo_char = random.choice(cls.ARABIC_KEYBOARD_NEIGHBORS[orig_char])

        typo_word = target_word[:char_idx] + typo_char + target_word[char_idx + 1 :]
        words[target_idx] = typo_word

        corrupted_text = " ".join(words)
        correction_text = f"*{target_word}"

        logger.debug(f"Injected typo: '{target_word}' -> '{typo_word}' | Correction: '{correction_text}'")
        return corrupted_text, correction_text

    @classmethod
    def prepare_message_bursts(
        cls,
        text: str,
        is_shy: bool = False,
    ) -> List[BurstMessage]:
        """
        Full pipeline: partitions text into bubbles, computes timing delays, and injects self-corrections.
        """
        bubbles = cls.split_into_multi_bubble_bursts(text)
        burst_items: List[BurstMessage] = []

        for i, bubble in enumerate(bubbles):
            corrupted, correction = cls.maybe_inject_typo(bubble)
            delay = cls.calculate_typing_delay(corrupted, is_shy=is_shy)

            burst_items.append(
                BurstMessage(
                    text=corrupted,
                    typing_delay_sec=delay,
                    has_typo=bool(correction),
                    correction_text=correction,
                )
            )

        return burst_items


human_typer = HumanTyperSimulator()
