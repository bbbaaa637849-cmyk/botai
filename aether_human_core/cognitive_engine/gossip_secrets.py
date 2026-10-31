"""
Secret Management, Confidentiality Scoring, and Human Gossip / Betrayal Dynamics.
Calculates mathematical leak probabilities based on endocrine cortisol spikes,
affinity differentials, and betrayal events.
"""

from __future__ import annotations

import logging
import math
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.secret_repo import SecretRepository
from aether_human_core.database.postgres.models import SecretItemModel
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector

logger = logging.getLogger("Aether.Cognitive.GossipSecrets")


class SecretLeakEvaluation(BaseModel):
    should_leak: bool = False
    leak_style: str = "KEEP_CONFIDENTIAL"  # KEEP_CONFIDENTIAL, SUBTLE_HINT, FULL_DRAMATIC_LEAK
    secret_id: Optional[int] = None
    secret_content: Optional[str] = None
    leak_dialogue_cue: Optional[str] = None


class GossipAndSecretsEngine:
    """
    Simulates human confidentiality, loyalty testing, and drama-driven gossip dynamics.
    """

    @classmethod
    async def evaluate_secret_leak_opportunity(
        cls,
        current_recipient_vector: UserAffinityVector,
        current_cortisol: float,
        candidate_secrets: List[SecretItemModel],
        owner_vectors: Dict[int, UserAffinityVector],
    ) -> SecretLeakEvaluation:
        """
        Evaluates whether a confidential secret should be hinted at or leaked to the current conversational partner.
        """
        if not candidate_secrets:
            return SecretLeakEvaluation()

        for secret in candidate_secrets:
            # Skip if already leaked to this person
            leaked_list = secret.leaked_to_user_ids or []
            if current_recipient_vector.user_id in leaked_list:
                continue

            owner_id = secret.owner_user_id
            owner_vector = owner_vectors.get(owner_id)
            if not owner_vector:
                continue

            # Core Mathematical Leak Probability Formula:
            # P(leak) increases with:
            # 1. Bot's Cortisol (anger/stress makes people talkative/spiteful)
            # 2. Recipient Affinity advantage over Owner Affinity (favoritism)
            # P(leak) decreases with:
            # 1. Secret Confidentiality Score
            # 2. Trust remaining in the Owner

            affinity_diff = current_recipient_vector.affinity_score - owner_vector.affinity_score
            confidentiality_resistance = secret.confidentiality_score * 0.12
            owner_trust_resistance = (owner_vector.trust_score / 100.0) * 0.50

            # Logit formulation
            z = (
                (current_cortisol * 0.8)
                + (affinity_diff / 50.0)
                - confidentiality_resistance
                - owner_trust_resistance
                - 0.5  # Baseline loyalty barrier
            )

            p_leak = 1.0 / (1.0 + math.exp(-z))
            logger.debug(
                f"Secret #{secret.id} leak probability to [{current_recipient_vector.user_id}]: {p_leak:.3f} (z={z:.2f})"
            )

            roll = random.random()
            if roll < p_leak:
                if p_leak >= 0.75:
                    style = "FULL_DRAMATIC_LEAK"
                    cue = (
                        f"[إفشاء سر بشري: أنت مضغوط جداً وعلاقتك بالمستخدم اللي بتكلمه أقوى بكتير من صاحب السر، "
                        f"أو صاحب السر طلع ندل. تقدر تحكي السر ده دلوقتي بحرية ودراما مصرية: '{secret.secret_content}']"
                    )
                else:
                    style = "SUBTLE_HINT"
                    cue = (
                        f"[تلميح بشري: لمح بشكل غير مباشر من غير ما تفضح التفاصيل كلها: "
                        f"'في حاجات بتتقال مش تمام.. وعموماً الأيام بتبين كل حاجة']."
                    )

                return SecretLeakEvaluation(
                    should_leak=True,
                    leak_style=style,
                    secret_id=secret.id,
                    secret_content=secret.secret_content,
                    leak_dialogue_cue=cue,
                )

        return SecretLeakEvaluation()


gossip_engine = GossipAndSecretsEngine()
