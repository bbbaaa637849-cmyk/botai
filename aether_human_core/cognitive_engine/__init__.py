"""
Cognitive Engine package initialization.
"""

from aether_human_core.cognitive_engine.context_linker import (
    context_linker,
    ContextLinkerService,
)
from aether_human_core.cognitive_engine.gossip_secrets import (
    gossip_engine,
    GossipAndSecretsEngine,
    SecretLeakEvaluation,
)
from aether_human_core.cognitive_engine.inner_monologue import (
    inner_monologue_engine,
    InnerMonologueEngine,
    MonologueDecision,
)
from aether_human_core.cognitive_engine.orchestrator import (
    cognitive_orchestrator,
    CognitiveOrchestrator,
    OrchestratedResponse,
)

__all__ = [
    "context_linker",
    "ContextLinkerService",
    "gossip_engine",
    "GossipAndSecretsEngine",
    "SecretLeakEvaluation",
    "inner_monologue_engine",
    "InnerMonologueEngine",
    "MonologueDecision",
    "cognitive_orchestrator",
    "CognitiveOrchestrator",
    "OrchestratedResponse",
]
