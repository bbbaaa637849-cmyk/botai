"""
Visual Identity Package.
"""

from aether_human_core.multimodal_engine.visual_identity.life_simulator import (
    life_sim,
    VirtualLifeSimulator,
    PhysicalLifeState,
)
from aether_human_core.multimodal_engine.visual_identity.face_lock_pipeline import (
    face_lock_pipeline,
    FaceLockIdentityPipeline,
)

__all__ = [
    "life_sim",
    "VirtualLifeSimulator",
    "PhysicalLifeState",
    "face_lock_pipeline",
    "FaceLockIdentityPipeline",
]
