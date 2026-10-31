"""
Configuration, Settings, Personality Profiles, and LLM Routing.
"""

from aether_human_core.config.settings import settings
from aether_human_core.config.personality_profile import (
    personality_baseline,
    linguistic_vocab,
    CharacterPromptTemplates,
)
from aether_human_core.config.llm_router import llm_pool, GeminiKeyPoolManager

__all__ = [
    "settings",
    "personality_baseline",
    "linguistic_vocab",
    "CharacterPromptTemplates",
    "llm_pool",
    "GeminiKeyPoolManager",
]
