"""
Social Influence Protocol, Constraint Compiler, and Pre-Cognitive Rule Interceptor.
Compiles natural language emotional demands into strict database-backed behavioral directives,
and enforces icy cold dismissals with automated loyalty reporting to romantic partners.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel

from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector, RelationshipTier
from aether_human_core.database.postgres.models import BehavioralRuleModel

logger = logging.getLogger("Aether.Psychology.SocialInfluence")


class CompilationResult(BaseModel):
    is_accepted: bool
    rejection_reason: Optional[str] = None
    rule_type: Optional[str] = None
    instruction_text: Optional[str] = None
    target_gender: Optional[str] = None
    target_user_id: Optional[int] = None
    response_to_commander: str


class InterceptionResult(BaseModel):
    is_intercepted: bool
    behavior_mode: str = "NORMAL"  # NORMAL, COLD_DISMISS, IGNORE_GHOST, SARCASTIC_REBELLION
    curt_response_text: Optional[str] = None
    should_report_loyalty: bool = False
    loyalty_partner_id: Optional[int] = None
    loyalty_report_message: Optional[str] = None


class SocialConstraintCompiler:
    """
    Translates colloquial emotional demands from Telegram chat into operational behavioral constraints.
    """
    RESTRICT_FEMALE_PHRASES = [
        "متكلمش بنات", "ماتكلمش بنات", "بلاش تكلم بنات", "خليك رسمي مع البنات",
        "ماتردش على أي بنت", "ناشف مع أي بنت", "متكلمش غيري", "ماتكلمش غيري"
    ]
    IGNORE_USER_PHRASES = [
        "ماتردش على", "مبحبش فلان", "ماتكلمش فلان", "فكك من", "بلوك لـ"
    ]

    @classmethod
    def compile_directive(
        cls,
        commander: UserAffinityVector,
        commander_name: str,
        message_text: str,
    ) -> CompilationResult:
        """
        Analyzes message text for social control directives and validates against commander's affinity tier.
        """
        text_lower = message_text.lower().strip()

        # Check for female restriction demand
        is_female_restrict = any(phrase in text_lower for phrase in cls.RESTRICT_FEMALE_PHRASES)
        is_ignore_demand = any(phrase in text_lower for phrase in cls.IGNORE_USER_PHRASES)

        if not is_female_restrict and not is_ignore_demand:
            return CompilationResult(
                is_accepted=False,
                rejection_reason="NOT_A_DIRECTIVE",
                response_to_commander="",
            )

        # Authority Validation: Can this user boss the bot around?
        if not commander.can_issue_behavioral_orders():
            # Rebellion: Reject with dignity and Egyptian sarcasm
            rebellious_reply = (
                f"أنتِ مين أصلاً عشان تقوليلي أكلم مين ومكلمش مين؟ كبري مخك وخليكي في حالك أحسن."
                if commander.affinity_score <= 10.0
                else f"معلش يا {commander_name}، أنا أه بحترمك بس محدش بيتحكم في طريقتي ولا كلامي مع الناس."
            )
            logger.warning(
                f"User [{commander.user_id}] attempted behavioral control without authority (Tier: {commander.tier}). Rebellious rejection triggered."
            )
            return CompilationResult(
                is_accepted=False,
                rejection_reason="INSUFFICIENT_AFFINITY_AUTHORITY",
                response_to_commander=rebellious_reply,
            )

        # Legitimate Partner Order Accepted!
        if is_female_restrict:
            rule_type = "RESTRICT_FEMALE_TALK"
            instruction = "حظر الكلام الودي مع أي فتاة، والرد الرسمي والجاف فقط مع إشعار الشريكة."
            acceptance_reply = (
                f"حاضر يا روحي من عيوني الاتنين.. والله ما في غيرك في عيني، وأي بنت هتدخل هصدها وهقفل معاها الكلام فوراً متقلقيش خالص ❤️"
            )
            return CompilationResult(
                is_accepted=True,
                rule_type=rule_type,
                instruction_text=instruction,
                target_gender="female",
                response_to_commander=acceptance_reply,
            )

        return CompilationResult(
            is_accepted=True,
            rule_type="COLD_MODE",
            instruction_text=text_lower,
            response_to_commander=f"حاضر، اللي تشوفيه هيمشي بالظبط.",
        )


class PreCognitiveRuleInterceptor:
    """
    Evaluates incoming communications before cognitive reasoning to apply active constraints.
    """
    COLD_RESPONSES = [
        "معلش مشغول شوية.",
        "تمام.",
        "حصل خير.",
        "ماليش في الكلام ده الصراحة.",
        "مش فاضي نتكلم بعدين.",
        "أهلاً، في حاجة ضرورية؟ لأني مشغول جداً.",
    ]

    @classmethod
    def intercept_incoming_message(
        cls,
        sender_id: int,
        sender_name: str,
        sender_gender: str,
        message_text: str,
        active_rules: List[BehavioralRuleModel],
    ) -> InterceptionResult:
        """
        Interception filter: checks if sender violates active constraints.
        """
        for rule in active_rules:
            if not rule.is_active:
                continue

            # Check female interaction restriction
            if rule.rule_type == "RESTRICT_FEMALE_TALK" and sender_gender == "female":
                # Deterministic curt response
                idx = abs(hash(sender_name + message_text)) % len(cls.COLD_RESPONSES)
                curt_reply = cls.COLD_RESPONSES[idx]

                # Craft loyalty report for commander
                loyalty_msg = (
                    f"حبيبتي.. على فكرة {sender_name} لسه دخلت تكلمني دلوقتي، وأنا صديتها وقفلت الكلام معاها بجفاف زي ما وعدتك بالظبط عشان متزعليش ❤️"
                )

                logger.info(
                    f"PreCognitive Interceptor BLOCKED female user [{sender_id} ({sender_name})]. "
                    f"Applying COLD_DISMISS. Scheduled loyalty report to commander [{rule.user_id}]."
                )

                return InterceptionResult(
                    is_intercepted=True,
                    behavior_mode="COLD_DISMISS",
                    curt_response_text=curt_reply,
                    should_report_loyalty=True,
                    loyalty_partner_id=rule.user_id,
                    loyalty_report_message=loyalty_msg,
                )

            # Check target-specific cold mode / block
            if rule.rule_type in ("COLD_MODE", "IGNORE_USER") and rule.target_user_id == sender_id:
                return InterceptionResult(
                    is_intercepted=True,
                    behavior_mode="COLD_DISMISS" if rule.rule_type == "COLD_MODE" else "IGNORE_GHOST",
                    curt_response_text="تمام." if rule.rule_type == "COLD_MODE" else None,
                    should_report_loyalty=False,
                )

        return InterceptionResult(is_intercepted=False)
