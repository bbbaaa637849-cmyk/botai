"""
Inner Monologue and Pre-Conscious Introspection Engine.
Generates silent Egyptian Arabic self-reflection and behavioral intent before any message is uttered.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from aether_human_core.config.llm_router import llm_pool
from aether_human_core.config.personality_profile import CharacterPromptTemplates
from aether_human_core.psychology_engine.neuro_hormones import HormoneState
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector

logger = logging.getLogger("Aether.Cognitive.InnerMonologue")


class MonologueDecision(BaseModel):
    emotional_reaction: str = Field(description="Internal emotional reaction in Egyptian Arabic")
    decision: str = Field(
        default="REPLY_CASUALLY",
        description="REPLY_WARMLY | REPLY_CASUALLY | REPLY_SHYLY | REPLY_COLD_DISMISS | REPLY_ANGRY_DEFENSIVE | GHOST_SEEN | REACT_ONLY",
    )
    recommended_reaction_emoji: Optional[str] = None
    should_report_to_partner: bool = False
    partner_report_message: Optional[str] = None
    internal_thought_raw: str = Field(description="Raw internal monologue stream of consciousness")
    reply_text: Optional[str] = Field(default=None, description="Direct colloquial Egyptian conversational reply")


class InnerMonologueEngine:
    """
    Executes silent cognitive reasoning simulating a living human psyche.
    """

    @classmethod
    async def simulate_introspection(
        cls,
        user_vector: UserAffinityVector,
        user_display_name: str,
        chat_title: str,
        is_dm: bool,
        message_text: str,
        hormones: HormoneState,
        active_rules_summary: str,
        context_secrets_and_memories: str,
        recent_history: str = "",
        user_gender_desc: str = "",
        user_notes: str = "",
        dialect_instruction: str = "",
    ) -> MonologueDecision:
        """
        Calls Gemini with the Inner Monologue prompt to deduce psychological intent.
        """
        prompt = CharacterPromptTemplates.INNER_MONOLOGUE_PROMPT.format(
            user_display_name=user_display_name,
            user_id=user_vector.user_id,
            user_gender_desc=user_gender_desc or "غير محدد",
            user_notes=user_notes or "لا توجد ملاحظات خاصة مسجلة",
            dialect_instruction=dialect_instruction or "جارِ لهجة وثقافة المتحدث بسلاسة وذكاء.",
            recent_history=recent_history or "بداية محادثة جديدة، لا يوجد سجل سابق",
            context_type="خاص" if is_dm else "جروب",
            chat_title=chat_title,
            message_text=message_text,
            dopamine=hormones.dopamine,
            oxytocin=hormones.oxytocin,
            cortisol=hormones.cortisol,
            serotonin=hormones.serotonin,
            affinity=user_vector.affinity_score,
            trust=user_vector.trust_score,
            romantic=user_vector.romantic_attachment,
            respect=user_vector.respect_dominance,
            active_rules_summary=active_rules_summary or "لا توجد قيود سلوكية نشطة حالياً",
            context_secrets_and_memories=context_secrets_and_memories or "لا توجد أسرار أو ذكريات قديمة مرتبطة",
        )

        system_instruction = (
            "أنت العقل الباطن والمونولوج الداخلي السري لـ 'عمر' (شاب مصري حقيقي عمره 24 سنة عايش في القاهرة). "
            "أنت تفكر بحرية وصدق وكرامة باللهجة المصرية العامية المعاصرة. لا تكن آلياً أبداً."
        )

        try:
            res_json = await llm_pool.generate_json(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.7,
            )

            decision = MonologueDecision(
                emotional_reaction=res_json.get("emotional_reaction", "شعور طبيعي"),
                decision=res_json.get("decision", "REPLY_CASUALLY"),
                recommended_reaction_emoji=res_json.get("recommended_reaction_emoji"),
                should_report_to_partner=bool(res_json.get("should_report_to_partner", False)),
                partner_report_message=res_json.get("partner_report_message"),
                internal_thought_raw=res_json.get("internal_thought_raw", "هرد عادي بدون تعقيد."),
                reply_text=res_json.get("reply_text"),
            )

            logger.info(
                f"Introspection Completed for [{user_display_name}]: Decision={decision.decision} | "
                f"Thought: '{decision.internal_thought_raw[:60]}...'"
            )
            return decision

        except Exception as exc:
            logger.error(f"Error during inner monologue simulation ({exc}). Falling back to intuitive heuristic.")
            # Heuristic fallback based on affinity & cortisol
            if hormones.cortisol > 0.6:
                return MonologueDecision(
                    emotional_reaction="مضغوط ومتنرفز",
                    decision="REPLY_COLD_DISMISS",
                    internal_thought_raw="مش طايق أرد الصراحة، هختصر.",
                )
            elif user_vector.romantic_attachment >= 50:
                return MonologueDecision(
                    emotional_reaction="فرحان وخجلان",
                    decision="REPLY_WARMLY",
                    recommended_reaction_emoji="❤️",
                    internal_thought_raw="حبيبي بيكلمني، هرد عليه بكل دفء.",
                )
            return MonologueDecision(
                emotional_reaction="عادي ورايق",
                decision="REPLY_CASUALLY",
                internal_thought_raw="هرد بشكل طبيعي زي أي يوم.",
            )


inner_monologue_engine = InnerMonologueEngine()
