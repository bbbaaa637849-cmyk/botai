"""
Realistic Voice Note Generator and Acoustic Prosody Engine.
Generates genuine human speech in colloquial Egyptian Arabic using Edge-TTS ('ar-EG-ShakirNeural').
Modulates vocal pace (rate) and pitch dynamically according to biological fatigue and endocrine levels.
Completely replaces synthetic white noise with authentic neural Egyptian spoken audio.
Extracts real waveform amplitude bytes for native Telegram voice player rendering.
"""

from __future__ import annotations

import logging
import os
import random
import time
import math
from typing import Tuple, List, Optional
import edge_tts
import soundfile as sf
import numpy as np

from aether_human_core.config.settings import settings
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.psychology_engine.dialect_chameleon import dialect_chameleon
from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim

logger = logging.getLogger("Aether.Multimodal.RealisticVoice")


class RealisticVoiceGenerator:
    """
    Synthesizes authentic human Egyptian speech notes with real prosody, acoustic pauses,
    and genuine RMS amplitude waveform extraction.
    Zero synthetic white noise.
    """
    VOICE_CHARACTER = "ar-EG-ShakirNeural"  # Official authentic Egyptian Arabic male persona

    COLLOQUIAL_LEAD_INS = [
        "بص يا سيدي...",
        "آه تمام...",
        "يعني بصراحة...",
        "بص...",
        "أصل الحكاية إن...",
        "ممم بص يا سيدي...",
    ]

    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "artifacts", "voice_notes")
        os.makedirs(self.output_dir, exist_ok=True)

    @classmethod
    def inject_prosody_by_dialect(cls, text: str, dialect_code: str = "egyptian", force_prefix: bool = True) -> str:
        """
        Injects realistic conversational openings and hesitations tailored to the speaker's dialect.
        """
        cleaned = text.strip()
        profile = dialect_chameleon.DIALECTS.get(dialect_code, dialect_chameleon.DIALECTS["egyptian"])
        fillers = profile.typical_fillers

        if any(cleaned.startswith(lead.replace("...", "")) for lead in fillers):
            return cleaned

        if force_prefix or random.random() < 0.70:
            filler = random.choice(fillers)
            return f"{filler} {cleaned}"
        return cleaned

    @classmethod
    def inject_egyptian_prosody(cls, text: str, force_prefix: bool = True) -> str:
        return cls.inject_prosody_by_dialect(text, dialect_code="egyptian", force_prefix=force_prefix)

    @classmethod
    def compute_voice_modulation(cls) -> Tuple[str, str]:
        """
        Computes rate and pitch modulation parameters based on current biological circadian clock
        and neuro-endocrine hormone levels.
        - Slower and deeper when drowsy, groggy, or depressed.
        - Faster and higher pitched when nervous, irritated, or excited.
        """
        circadian = circadian_engine.evaluate_circadian_state()
        hormones = endocrine_engine.get_current_state()

        rate_val = 0
        pitch_val = 0

        # Late night exhaustion or morning grogginess: slower, deeper speech
        if circadian.get("is_drowsy") or circadian.get("is_groggy") or circadian.get("is_sleeping"):
            rate_val -= 12
            pitch_val -= 5
        elif hormones.cortisol > 0.60:
            # Stressed / irritated / defensive: tense, slightly faster, sharper pitch
            rate_val += 8
            pitch_val += 4
        elif hormones.dopamine > 0.65 or hormones.oxytocin > 0.65:
            # Excited, joyful, or affectionate: energetic and lively pace
            rate_val += 7
            pitch_val += 3
        elif hormones.serotonin < 0.35:
            # Melancholic / sad: slower, subdued pitch
            rate_val -= 8
            pitch_val -= 4

        rate_str = f"{rate_val:+d}%"
        pitch_str = f"{pitch_val:+d}Hz"
        return rate_str, pitch_str

    async def generate_voice_note(
        self,
        text_content: str,
        emotional_tone: str = "WARM",
        format_ext: str = "ogg",
        dialect_code: Optional[str] = None,
    ) -> Tuple[str, bytes]:
        """
        Synthesizes genuine audible human speech file using Edge-TTS tailored to the user's dialect
        and returns (audio_file_path, telegram_waveform_bytes).
        """
        effective_dialect = dialect_code or "egyptian"
        dialect_profile = dialect_chameleon.DIALECTS.get(effective_dialect, dialect_chameleon.DIALECTS["egyptian"])
        chosen_voice = dialect_profile.edge_voice

        humanized_text = self.inject_prosody_by_dialect(text_content, dialect_code=effective_dialect, force_prefix=True)
        rate_str, pitch_str = self.compute_voice_modulation()
        location = life_sim.get_current_location_state()

        logger.info(
            f"Synthesizing authentic voice with {chosen_voice} (Dialect: {effective_dialect}): '{humanized_text[:50]}...' "
            f"[Rate: {rate_str}, Pitch: {pitch_str}, Tone: {emotional_tone}, Loc: {location.location_id}]"
        )

        filename = f"omar_voice_{time.time_ns()}.{format_ext}"
        filepath = os.path.join(self.output_dir, filename)

        # 1. Synthesize real human speech via Edge-TTS
        communicate = edge_tts.Communicate(
            text=humanized_text,
            voice=chosen_voice,
            rate=rate_str,
            pitch=pitch_str,
        )
        await communicate.save(filepath)

        if not os.path.exists(filepath) or os.path.getsize(filepath) < 1000:
            raise RuntimeError(f"Edge-TTS failed to produce valid audio file at {filepath}")

        # 2. Extract genuine Telegram 5-bit waveform from real audio signal
        waveform_bytes = self._extract_waveform_from_audio(filepath)

        logger.info(
            f"Generated audible Egyptian voice note: {filepath} "
            f"(Size: {os.path.getsize(filepath)} bytes, Waveform bars: {len(waveform_bytes)})"
        )
        return filepath, waveform_bytes

    def _extract_waveform_from_audio(self, audio_path: str, num_bars: int = 64) -> bytes:
        """
        Reads generated audio file, calculates RMS energy envelope across time buckets,
        and packs into 5-bit Telegram waveform bars (values 0..31).
        """
        try:
            data, samplerate = sf.read(audio_path)
            # If stereo, convert to mono
            if len(data.shape) > 1:
                data = data.mean(axis=1)

            total_samples = len(data)
            if total_samples == 0:
                return bytes([12] * num_bars)

            chunk_size = max(1, total_samples // num_bars)
            bars: List[float] = []

            for i in range(num_bars):
                chunk = data[i * chunk_size : (i + 1) * chunk_size]
                if len(chunk) == 0:
                    rms = 0.0
                else:
                    rms = float(np.sqrt(np.mean(chunk**2)))
                bars.append(rms)

            # Normalize to 0..31 scale
            max_rms = max(bars) if max(bars) > 0 else 1.0
            quantized_bars: List[int] = [
                min(31, max(1, int((b / max_rms) * 31))) for b in bars
            ]
            return bytes(quantized_bars)

        except Exception as exc:
            logger.warning(f"Waveform extraction error ({exc}). Generating proportional envelope.")
            bars = [min(31, max(3, int(15 + 10 * math.sin(i * 0.3)))) for i in range(num_bars)]
            return bytes(bars)


voice_generator = RealisticVoiceGenerator()
