"""
Multi-Dimensional Affinity Matrix and Dynamic Social Influence Protocol.
Calculates continuous social coordinates: Affinity, Trust, Romantic Attachment, and Dominance/Respect.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("Aether.Psychology.Affinity")


class RelationshipTier(str, Enum):
    ANTAGONIST = "ANTAGONIST"
    STRANGER = "STRANGER"
    ACQUAINTANCE = "ACQUAINTANCE"
    FRIEND = "FRIEND"
    CLOSE_FRIEND = "CLOSE_FRIEND"
    ROMANTIC_INTEREST = "ROMANTIC_INTEREST"
    EXCLUSIVE_PARTNER = "EXCLUSIVE_PARTNER"


class UserAffinityVector(BaseModel):
    """
    Mathematical state of human relation with a specific user.
    """
    user_id: int
    affinity_score: float = Field(default=0.0, ge=-100.0, le=100.0, description="Overall liking and affection")
    trust_score: float = Field(default=20.0, ge=0.0, le=100.0, description="Faithfulness and credibility")
    romantic_attachment: float = Field(default=0.0, ge=0.0, le=100.0, description="Romantic chemistry and possessiveness")
    respect_dominance: float = Field(default=0.0, ge=-50.0, le=50.0, description="Perceived authority and social dominance")
    tier: RelationshipTier = RelationshipTier.STRANGER

    def can_issue_behavioral_orders(self) -> bool:
        """
        Only exclusive romantic partners or deeply respected close friends can enforce behavioural constraints.
        """
        return self.tier == RelationshipTier.EXCLUSIVE_PARTNER or (
            self.romantic_attachment >= 75.0 and self.trust_score >= 60.0
        ) or (self.affinity_score >= 85.0 and self.respect_dominance >= 30.0)


class AffinityMatrixCalculator:
    """
    Engine for evaluating human conversational acts into coordinate shifts.
    """
    @classmethod
    def evaluate_interaction_delta(
        cls,
        current_vector: UserAffinityVector,
        action_type: str,
        emotional_intensity: float = 1.0,
    ) -> Tuple[float, float, float, float]:
        """
        Computes (d_affinity, d_trust, d_romantic, d_respect) deltas.
        """
        da = 0.0
        dt = 0.0
        dr = 0.0
        dp = 0.0
        intensity = max(0.2, min(3.0, emotional_intensity))

        if action_type == "KIND_SUPPORT":
            da = 4.0 * intensity
            dt = 5.0 * intensity
            dp = 1.0 * intensity

        elif action_type == "SHARED_HUMOR":
            da = 3.5 * intensity
            dt = 2.0 * intensity
            if current_vector.romantic_attachment > 20.0:
                dr = 2.0 * intensity

        elif action_type == "ROMANTIC_FLIRT":
            if current_vector.affinity_score >= 25.0:
                # Reciprocal flirtation
                da = 5.0 * intensity
                dr = 7.0 * intensity
                dt = 2.0 * intensity
            else:
                # Creepy unsolicited flirtation from stranger
                da = -4.0 * intensity
                dt = -3.0 * intensity
                dp = -5.0 * intensity

        elif action_type == "RUDE_ATTEMPT_TO_CONTROL":
            # Attempting to boss the bot around without high affinity
            if current_vector.can_issue_behavioral_orders():
                # Legitimate partner reprimand
                da = -1.0 * intensity
                dp = 2.0 * intensity
            else:
                # Arrogant stranger
                da = -12.0 * intensity
                dt = -10.0 * intensity
                dp = -15.0 * intensity

        elif action_type == "INSULT":
            da = -15.0 * intensity
            dt = -12.0 * intensity
            dr = -10.0 * intensity
            dp = -10.0 * intensity

        elif action_type == "KEPT_PROMISE_OR_LOYALTY":
            da = 6.0 * intensity
            dt = 10.0 * intensity
            dr = 4.0 * intensity

        elif action_type == "BETRAYED_SECRET":
            da = -45.0 * intensity
            dt = -60.0 * intensity
            dr = -35.0 * intensity

        return (da, dt, dr, dp)

    @classmethod
    def recompute_tier(cls, vector: UserAffinityVector) -> RelationshipTier:
        """
        Determines the qualitative social tier from continuous coordinates.
        """
        if vector.affinity_score <= -40.0:
            return RelationshipTier.ANTAGONIST

        if vector.romantic_attachment >= 75.0 and vector.trust_score >= 65.0:
            return RelationshipTier.EXCLUSIVE_PARTNER

        if vector.romantic_attachment >= 45.0 and vector.affinity_score >= 35.0:
            return RelationshipTier.ROMANTIC_INTEREST

        if vector.affinity_score >= 60.0 and vector.trust_score >= 50.0:
            return RelationshipTier.CLOSE_FRIEND

        if vector.affinity_score >= 20.0:
            return RelationshipTier.FRIEND

        if vector.affinity_score >= 0.0:
            return RelationshipTier.ACQUAINTANCE

        return RelationshipTier.STRANGER


affinity_calc = AffinityMatrixCalculator()
