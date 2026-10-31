"""
Acoustic Voice Engine Package.
"""

from aether_human_core.multimodal_engine.acoustic_voice.emotion_detector import (
    acoustic_detector,
    AcousticEmotionDetector,
    AcousticPerceptionResult,
)
from aether_human_core.multimodal_engine.acoustic_voice.realistic_voice_generator import (
    voice_generator,
    RealisticVoiceGenerator,
)

__all__ = [
    "acoustic_detector",
    "AcousticEmotionDetector",
    "AcousticPerceptionResult",
    "voice_generator",
    "RealisticVoiceGenerator",
]
