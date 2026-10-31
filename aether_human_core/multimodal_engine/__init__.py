"""
Multimodal Engine Master Package.
"""

from aether_human_core.multimodal_engine.visual_identity.life_simulator import life_sim
from aether_human_core.multimodal_engine.visual_identity.face_lock_pipeline import face_lock_pipeline
from aether_human_core.multimodal_engine.acoustic_voice.emotion_detector import acoustic_detector
from aether_human_core.multimodal_engine.acoustic_voice.realistic_voice_generator import voice_generator

__all__ = [
    "life_sim",
    "face_lock_pipeline",
    "acoustic_detector",
    "voice_generator",
]
