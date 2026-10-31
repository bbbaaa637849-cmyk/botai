"""
Neuro-Endocrine & Psychological Hormone Simulation Engine.
Implements continuous differential decay, homeostasis recovery, and acute neurotransmitter surges.
Simulates Dopamine, Oxytocin, Cortisol, Serotonin, and Physical Energy.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("Aether.Psychology.Hormones")


class HormoneState(BaseModel):
    """
    Normalized neuro-chemical levels ranging from 0.0 (depleted) to 1.0 (saturated).
    Homeostatic baselines reflect natural disposition.
    """
    dopamine: float = Field(default=0.55, ge=0.0, le=1.0, description="Reward, excitement, curiosity")
    oxytocin: float = Field(default=0.50, ge=0.0, le=1.0, description="Empathy, social warmth, affection, shyness")
    cortisol: float = Field(default=0.15, ge=0.0, le=1.0, description="Stress, threat vigilance, irritation, defensiveness")
    serotonin: float = Field(default=0.60, ge=0.0, le=1.0, description="Mood stability, confidence, emotional resilience")
    energy: float = Field(default=0.85, ge=0.0, le=1.0, description="Physical alertness and conversational stamina")
    last_updated: float = Field(default_factory=time.time)

    # Baselines
    BASE_DOPAMINE: float = 0.50
    BASE_OXYTOCIN: float = 0.45
    BASE_CORTISOL: float = 0.15
    BASE_SEROTONIN: float = 0.60
    BASE_ENERGY: float = 0.80


class NeuroEndocrineEngine:
    """
    Mathematical simulator of human neuro-chemistry.
    Applies continuous relaxation towards equilibrium and models acute psychological shocks.
    """
    def __init__(self, decay_rate_per_hour: float = 0.15):
        self.state: HormoneState = HormoneState()
        self.decay_rate_per_sec: float = decay_rate_per_hour / 3600.0

    def get_current_state(self) -> HormoneState:
        self.apply_homeostatic_decay()
        return self.state.model_copy()

    def apply_homeostatic_decay(self) -> None:
        """
        Advances continuous differential equation:
        dH/dt = -alpha * (H - H_baseline)
        """
        now = time.time()
        dt = max(0.0, now - self.state.last_updated)
        if dt < 0.5:
            return

        decay_factor = math.exp(-self.decay_rate_per_sec * dt)

        self.state.dopamine = self.state.BASE_DOPAMINE + (self.state.dopamine - self.state.BASE_DOPAMINE) * decay_factor
        self.state.oxytocin = self.state.BASE_OXYTOCIN + (self.state.oxytocin - self.state.BASE_OXYTOCIN) * decay_factor
        self.state.cortisol = self.state.BASE_CORTISOL + (self.state.cortisol - self.state.BASE_CORTISOL) * decay_factor
        self.state.serotonin = self.state.BASE_SEROTONIN + (self.state.serotonin - self.state.BASE_SEROTONIN) * decay_factor

        self.state.last_updated = now

    def apply_event_shock(
        self,
        event_name: str,
        intensity: float = 1.0,
        user_affinity: float = 0.0,
    ) -> Dict[str, float]:
        """
        Triggers acute surges or drops in endocrine levels based on human interactions.
        """
        self.apply_homeostatic_decay()
        intensity = max(0.1, min(2.5, intensity))
        deltas: Dict[str, float] = {}

        if event_name == "PRAISE_OR_COMPLIMENT":
            # Praise from loved ones surges oxytocin + dopamine
            multiplier = 1.0 + max(0.0, user_affinity / 100.0)
            deltas["dopamine"] = 0.18 * intensity * multiplier
            deltas["oxytocin"] = 0.20 * intensity * multiplier
            deltas["cortisol"] = -0.10 * intensity

        elif event_name == "INSULT_OR_DISRESPECT":
            # Insults surge cortisol and deplete serotonin
            deltas["cortisol"] = 0.35 * intensity
            deltas["dopamine"] = -0.20 * intensity
            deltas["serotonin"] = -0.15 * intensity

        elif event_name == "ROMANTIC_FLIRTATION":
            if user_affinity >= 30.0:
                # Welcome flirtation: massive dopamine and oxytocin (triggers shyness)
                deltas["oxytocin"] = 0.30 * intensity
                deltas["dopamine"] = 0.25 * intensity
            else:
                # Creepy or unwanted flirtation from stranger: cortisol up
                deltas["cortisol"] = 0.25 * intensity
                deltas["serotonin"] = -0.10 * intensity

        elif event_name == "JEALOUSY_STIMULUS":
            # Seeing a loved one flirt with someone else
            deltas["cortisol"] = 0.30 * intensity
            deltas["oxytocin"] = -0.15 * intensity
            deltas["serotonin"] = -0.20 * intensity

        elif event_name == "IGNORED_OR_GHOSTED":
            deltas["cortisol"] = 0.15 * intensity
            deltas["dopamine"] = -0.15 * intensity

        elif event_name == "BETRAYAL_DISCOVERED":
            deltas["cortisol"] = 0.50 * intensity
            deltas["oxytocin"] = -0.40 * intensity
            deltas["serotonin"] = -0.30 * intensity

        # Apply and clamp
        for hormone, delta in deltas.items():
            curr = getattr(self.state, hormone)
            new_val = max(0.0, min(1.0, curr + delta))
            setattr(self.state, hormone, new_val)

        logger.info(f"Applied shock [{event_name}] (intensity={intensity:.1f}): {deltas}")
        return deltas

    def evaluate_psychological_mood(self) -> Dict[str, Any]:
        """
        Synthesizes current hormone configuration into a high-level psychological description.
        """
        s = self.get_current_state()

        if s.cortisol >= 0.60:
            mood = "عصبي ومضغوط"
            temperament = "IRRITABLE_DEFENSIVE"
        elif s.oxytocin >= 0.70 and s.dopamine >= 0.65:
            mood = "طاير من الفرحة وخجلان"
            temperament = "EUPHORIC_AFFECTIONATE_SHY"
        elif s.oxytocin >= 0.60:
            mood = "رايق ودافي ومبسوط"
            temperament = "WARM_ATTACHED"
        elif s.dopamine <= 0.30 and s.serotonin <= 0.40:
            mood = "مخنوق ومقفول شوية"
            temperament = "MELANCHOLIC_WITHDRAWN"
        else:
            mood = "طبيعي ومستقر"
            temperament = "BALANCED_NORMAL"

        return {
            "mood_ar": mood,
            "temperament": temperament,
            "dopamine": round(s.dopamine, 3),
            "oxytocin": round(s.oxytocin, 3),
            "cortisol": round(s.cortisol, 3),
            "serotonin": round(s.serotonin, 3),
            "energy": round(s.energy, 3),
        }


# Global endocrine engine instance
endocrine_engine = NeuroEndocrineEngine()
