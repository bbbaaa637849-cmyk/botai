"""
Cognitive Maestro and Multi-Engine Orchestrator for Project Aether-Human.
Coordinates Perception, Social Constraints, Hormones, Episodic Memory, GraphRAG,
Inner Monologue, and Conversational Vernacular Generation.
"""

from __future__ import annotations

import logging
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from aether_human_core.config.settings import settings
from aether_human_core.config.llm_router import llm_pool
from aether_human_core.config.personality_profile import CharacterPromptTemplates, personality_baseline
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.database.postgres.repositories.message_repo import MessageRepository
from aether_human_core.database.postgres.repositories.behavioral_rule_repo import BehavioralRuleRepository
from aether_human_core.database.postgres.repositories.secret_repo import SecretRepository
from aether_human_core.database.vector_store.qdrant_client import vector_memory
from aether_human_core.database.neo4j_graph.social_graph import social_graph

from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.affinity_matrix import affinity_calc, UserAffinityVector, RelationshipTier
from aether_human_core.psychology_engine.social_influence import (
    SocialConstraintCompiler,
    PreCognitiveRuleInterceptor,
)
from aether_human_core.psychology_engine.micro_traits import micro_traits_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.psychology_engine.dialect_chameleon import dialect_chameleon
from aether_human_core.cognitive_engine.context_linker import context_linker
from aether_human_core.cognitive_engine.inner_monologue import inner_monologue_engine, MonologueDecision
from aether_human_core.cognitive_engine.cognitive_cache import cognitive_cache

logger = logging.getLogger("Aether.Cognitive.Orchestrator")


class OrchestratedResponse(BaseModel):
    decision_type: str = "REPLY"  # REPLY, GHOST_SEEN, REACT_ONLY, IGNORE
    raw_response_text: str = ""
    reaction_emoji: Optional[str] = None
    is_shy: bool = False
    is_cold_dismissal: bool = False
    should_send_voice: bool = False
    should_send_photo: bool = False
    loyalty_partner_id: Optional[int] = None
    loyalty_report_message: Optional[str] = None
    inner_monologue_text: str = ""
    detected_dialect: str = "egyptian"


class CognitiveOrchestrator:
    """
    Central cognitive pipeline orchestrating the entire psychological and linguistic entity.
    """

    @classmethod
    async def process_incoming_event(
        cls,
        telegram_message_id: int,
        chat_id: int,
        sender_id: int,
        sender_name: str,
        message_text: str,
        media_type: str = "text",
        sender_gender: str = "unknown",
        chat_type: str = "private",
        chat_title: Optional[str] = None,
    ) -> OrchestratedResponse:
        """
        Executes end-to-end cognitive reasoning on an incoming Telegram event.
        """
        is_dm = chat_type == "private"
        chat_title_effective = chat_title or ("محادثة خاصة" if is_dm else "جروب عام")
        logger.info(
            f"Orchestrating event: Sender [{sender_id} ({sender_name})] | "
            f"Chat [{chat_id} ({chat_title_effective})] | Text: '{message_text[:40]}...'"
        )

        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            msg_repo = MessageRepository(session)
            rule_repo = BehavioralRuleRepository(session)
            secret_repo = SecretRepository(session)

            # 1. Fetch or create Unified User Profile & Chat
            user_record = await user_repo.get_or_create(
                telegram_id=sender_id,
                first_name=sender_name,
                gender=sender_gender,
            )

            # Auto-detect and persist explicit gender declarations in message text
            text_lower = message_text.lower().strip()
            import re
            is_male_claim = any(
                re.search(pat, text_lower)
                for pat in [
                    r"\bأنا\s+(ولد|ذكر|راجل|شاب|شب)\b",
                    r"\b(أنا\s+أخوك|معاك\s+راجل|يا\s+بني\s+أنا\s+راجل|أنا\s+مش\s+بنت)\b",
                    r"\b(أنا\s+بكلمك\s+كراجل|أنا\s+ذكر)\b",
                ]
            )
            is_female_claim = any(
                re.search(pat, text_lower)
                for pat in [
                    r"\bأنا\s+(بنت|فتاة|أنثى|ست|صبية)\b",
                    r"\b(أنا\s+مش\s+ولد|أنا\s+مش\s+راجل)\b",
                ]
            )
            if is_male_claim and user_record.gender != "male":
                user_record = await user_repo.update_gender(sender_id, "male")
                logger.info(f"Persisted detected male gender for user [{sender_id} ({sender_name})].")
            elif is_female_claim and user_record.gender != "female":
                user_record = await user_repo.update_gender(sender_id, "female")
                logger.info(f"Persisted detected female gender for user [{sender_id} ({sender_name})].")

            # Format demographic descriptor for cognitive context
            if user_record.gender == "male":
                gender_desc = "ذكر / شاب (يُخاطب كأخ وصاحب وجدعنة بصيغة المذكر)"
            elif user_record.gender == "female":
                gender_desc = "أنثى / فتاة (تُخاطب بلطف وأدب واحترام)"
            else:
                gender_desc = "غير محدد بعد (افتراضاً شاب يتعامل معه بأخوة ولطف)"

            # 1.5 Dynamic Dialect & Regional Accent Detection
            prior_dialect = user_record.notes if (user_record.notes and user_record.notes in dialect_chameleon.DIALECTS) else None
            detected_profile = dialect_chameleon.detect_dialect(message_text, user_prior_dialect=prior_dialect)
            if user_record.notes != detected_profile.code:
                await user_repo.update_notes(sender_id, detected_profile.code)
                user_record.notes = detected_profile.code
            chat_record = await msg_repo.get_or_create_chat(
                chat_id=chat_id,
                title=chat_title_effective,
                chat_type=chat_type,
            )

            # 2. Log incoming message into historical ledger
            await msg_repo.log_message(
                telegram_message_id=telegram_message_id,
                chat_id=chat_id,
                sender_id=sender_id,
                text=message_text,
                media_type=media_type,
                is_from_bot=False,
            )

            # Sync node to Social Knowledge Graph
            await social_graph.sync_user_node(
                telegram_id=sender_id,
                name=sender_name,
                gender=user_record.gender,
                affinity=user_record.affinity_score,
                tier=user_record.relationship_tier,
            )
            await social_graph.record_user_participation(user_id=sender_id, chat_id=chat_id)

            # Construct affinity vector
            user_vector = UserAffinityVector(
                user_id=sender_id,
                affinity_score=user_record.affinity_score,
                trust_score=user_record.trust_score,
                romantic_attachment=user_record.romantic_attachment,
                respect_dominance=user_record.respect_dominance,
                tier=RelationshipTier(user_record.relationship_tier),
            )

            # 3. Dignity Check: Is sender demeaning or insulting?
            dignity_defense = micro_traits_engine.evaluate_dignity_defense(user_vector, message_text)
            if dignity_defense:
                endocrine_engine.apply_event_shock("INSULT_OR_DISRESPECT", intensity=1.5)
                await user_repo.update_affinity_scores(sender_id, delta_affinity=-15.0, delta_respect=-10.0)
                return OrchestratedResponse(
                    decision_type="REPLY",
                    raw_response_text=dignity_defense,
                    inner_monologue_text="شتمني ومش هقبل أي إهانة لكرامتي.",
                )

            # 4. Check for Social Constraint Directive (e.g. 'Don't talk to girls')
            directive_result = SocialConstraintCompiler.compile_directive(
                commander=user_vector,
                commander_name=sender_name,
                message_text=message_text,
            )
            if directive_result.is_accepted and directive_result.rule_type:
                # Save active constraint
                await rule_repo.create_rule(
                    commander_id=sender_id,
                    rule_type=directive_result.rule_type,
                    instruction_text=directive_result.instruction_text or "",
                    target_gender=directive_result.target_gender,
                    target_user_id=directive_result.target_user_id,
                )
                return OrchestratedResponse(
                    decision_type="REPLY",
                    raw_response_text=directive_result.response_to_commander,
                    inner_monologue_text="حبيبتي أصدرت أمر عاطفي ووافقت عليه عشان ولائي ليها.",
                )
            elif not directive_result.is_accepted and directive_result.rejection_reason == "INSUFFICIENT_AFFINITY_AUTHORITY":
                return OrchestratedResponse(
                    decision_type="REPLY",
                    raw_response_text=directive_result.response_to_commander,
                    inner_monologue_text="شخص عادي حاول يملي عليا أوامر ورفضت بكرامة.",
                )

            # 5. Pre-Cognitive Interceptor: Active behavioral constraints filtering
            active_rules = await rule_repo.get_active_rules()
            interception = PreCognitiveRuleInterceptor.intercept_incoming_message(
                sender_id=sender_id,
                sender_name=sender_name,
                sender_gender=user_record.gender,
                message_text=message_text,
                active_rules=active_rules,
            )
            if interception.is_intercepted:
                if interception.behavior_mode == "COLD_DISMISS":
                    return OrchestratedResponse(
                        decision_type="REPLY",
                        raw_response_text=interception.curt_response_text or "تمام.",
                        is_cold_dismissal=True,
                        loyalty_partner_id=interception.loyalty_partner_id,
                        loyalty_report_message=interception.loyalty_report_message,
                        inner_monologue_text="بنت داخلة تكلمني وقاعدتي بتلزمني أرد بجفاف وأبلغ شريكتي.",
                    )
                elif interception.behavior_mode == "IGNORE_GHOST":
                    return OrchestratedResponse(
                        decision_type="GHOST_SEEN",
                        inner_monologue_text="ممنوع أرد عليه.. هعمل سين وأطنش.",
                    )

            # 6. Circadian Rhythm check: Is Omar asleep?
            circadian = circadian_engine.evaluate_circadian_state()
            if settings.enable_sleep_ghosting and circadian["is_sleeping"]:
                # If sleeping, only wake up if exclusive partner messages repeatedly
                if user_vector.tier != RelationshipTier.EXCLUSIVE_PARTNER:
                    logger.info("Omar is sleeping. Ghosting non-partner message.")
                    return OrchestratedResponse(
                        decision_type="IGNORE",
                        inner_monologue_text="أنا نايم دلوقتي ومش هصحى أرد.",
                        detected_dialect=detected_profile.code,
                    )

            # 6.5 Zero-Cost Cognitive Cache Check (Preserves quota for 1,000+ users)
            if not active_rules:
                cached_match = cognitive_cache.evaluate_heuristic_match(message_text)
                if cached_match:
                    c_reply, c_mono, c_emoji = cached_match
                    logger.info(f"Zero-Cost Cognitive Cache intercepted greeting/reaction: '{message_text[:30]}'")
                    return OrchestratedResponse(
                        decision_type="REPLY",
                        raw_response_text=c_reply,
                        reaction_emoji=c_emoji,
                        inner_monologue_text=c_mono,
                    )

            # 7. Cross-Context Synapse (Group-to-DM memory bridge)
            cross_context_info = await context_linker.get_cross_context_summary(
                user_id=sender_id,
                user_name=sender_name,
                current_chat_id=chat_id,
                is_dm=is_dm,
            )

            # 8. Episodic Long-Term Memory recall
            recalled_memories = await vector_memory.recall_relevant_memories(
                query_text=message_text,
                user_id=sender_id,
                top_k=3,
            )
            memories_str = "\n".join(f"- {m['text']}" for m in recalled_memories) if recalled_memories else ""

            # 9. Shyness evaluation
            hormones = endocrine_engine.get_current_state()
            is_shy, shy_prefix, shy_emoji = micro_traits_engine.evaluate_shyness(
                user_vector, message_text, hormones.oxytocin
            )

            # 10. Fetch recent conversation history (Critical for continuous context & memory)
            recent_history = await msg_repo.get_recent_chat_history(chat_id=chat_id, limit=8)
            history_lines = []
            for h in recent_history:
                sender_label = "عمر" if h.is_from_bot else sender_name
                history_lines.append(f"{sender_label}: {h.text}")
            history_text = "\n".join(history_lines)

            # 11. Inner Monologue simulation with full dialogue context
            rules_summary = "\n".join(r.instruction_text for r in active_rules) if active_rules else ""
            context_block = f"{cross_context_info or ''}\n{memories_str}"

            monologue = await inner_monologue_engine.simulate_introspection(
                user_vector=user_vector,
                user_display_name=sender_name,
                chat_title=chat_title_effective,
                is_dm=is_dm,
                message_text=message_text,
                hormones=hormones,
                active_rules_summary=rules_summary,
                context_secrets_and_memories=context_block,
                recent_history=history_text,
                user_gender_desc=gender_desc,
                user_notes=f"اللهجة والبلد المفضلة للمستخدم: {detected_profile.name_ar}",
                dialect_instruction=detected_profile.mirroring_instruction,
            )

            if monologue.decision == "GHOST_SEEN":
                return OrchestratedResponse(
                    decision_type="GHOST_SEEN",
                    inner_monologue_text=monologue.internal_thought_raw,
                )
            elif monologue.decision == "REACT_ONLY":
                return OrchestratedResponse(
                    decision_type="REACT_ONLY",
                    reaction_emoji=monologue.recommended_reaction_emoji or "👍",
                    inner_monologue_text=monologue.internal_thought_raw,
                )

            # 11. LLM Conversational Generation (Single-Pass Fusion Optimization)
            if monologue.reply_text and len(monologue.reply_text.strip()) > 2:
                # 100% savings: Re-use unified single-pass generated speech, zero extra LLM tokens
                raw_reply = monologue.reply_text.strip()
                logger.debug(f"Single-Pass inference utilized (saved 2nd LLM call): '{raw_reply[:35]}...'")
            else:
                # Fallback to secondary call only if single-pass JSON omitted reply_text
                dynamic_system_prompt = (
                    f"{CharacterPromptTemplates.SYSTEM_CONSTITUTION}\n\n"
                    f"حالتك النفسية الحالية:\n"
                    f"- الدوبامين: {hormones.dopamine:.2f} | الأوكسيتوسين: {hormones.oxytocin:.2f} | "
                    f"الكورتيزول: {hormones.cortisol:.2f} | السيروتونين: {hormones.serotonin:.2f}\n"
                    f"- علاقتك بالشخص ({sender_name}): {user_vector.tier.value} (معزة: {user_vector.affinity_score:.1f}/100)\n"
                    f"- تفكيرك الداخلي السري قبل ما ترد: \"{monologue.internal_thought_raw}\"\n"
                )

                if is_shy:
                    dynamic_system_prompt += (
                        "\n[ملحوظة خاصة: أنت خجلان ومحرج جداً ومبسوط من كلام الشخص. "
                        "اكتب بتلعثم خفيف ونقاط ... واستخدم تعبيرات خجل عفوية]."
                    )

                if cross_context_info:
                    dynamic_system_prompt += f"\n{cross_context_info}"

                if not is_dm:
                    dynamic_system_prompt += (
                        "\n[توجيه الجروبات والمحادثات العامة الإجباري]:\n"
                        "- أنت تتكلم الآن في جروب عام وسط ناس كتير، فمن غير اللائق أن ترغي أو تكتب كلاماً كثيراً.\n"
                        "- اجعل ردك في قمة الإيجاز والسرعة (جملة واحدة فقط أو من 5 إلى 15 كلمة كحد أقصى، كعادة الشباب في الجروبات الكبيرة).\n"
                        "- ارمِ كلمتك في الجون وخليك مختصر وطبيعي، وتجنب الشرح المطول تماماً."
                    )
                    chat_prompt = (
                        f"سجل المحادثة الأخيرة في الجروب:\n{history_text}\n\n"
                        f"المطلوب: اكتب ردك البشري التلقائي والمختصر جداً كـ 'عمر' في الجروب الآن (باللهجة المصرية، جملة واحدة سريعة فقط):"
                    )
                else:
                    chat_prompt = (
                        f"سجل المحادثة الأخيرة:\n{history_text}\n\n"
                        f"المطلوب: اكتب ردك البشري التلقائي كـ 'عمر' الآن (باللهجة المصرية القاهرية فقط). "
                        f"لا تكتب اسمك ولا تضع مقدمات، اكتب نص الرسالة فوراً:"
                    )

                raw_reply = await llm_pool.generate_content(
                    prompt=chat_prompt,
                    system_instruction=dynamic_system_prompt,
                    temperature=settings.gemini_temperature,
                )
                raw_reply = raw_reply.strip()

            # Prepend shyness prefix if triggered
            if is_shy and shy_prefix and not raw_reply.startswith("احم"):
                raw_reply = f"{shy_prefix}{raw_reply}"
            if is_shy and shy_emoji and shy_emoji not in raw_reply:
                raw_reply = f"{raw_reply} {shy_emoji}"

            # 12. Evaluate affinity modulation & store memory
            da, dt, dr, dp = affinity_calc.evaluate_interaction_delta(
                user_vector, action_type="KIND_SUPPORT" if hormones.oxytocin > 0.6 else "SHARED_HUMOR"
            )
            await user_repo.update_affinity_scores(
                sender_id, delta_affinity=da, delta_trust=dt, delta_romantic=dr, delta_respect=dp
            )

            # Store memory in vector store
            await vector_memory.store_memory(
                text=f"{sender_name}: {message_text} -> عمر: {raw_reply}",
                user_id=sender_id,
                chat_id=chat_id,
                emotional_valence=hormones.oxytocin - hormones.cortisol,
                importance_weight=1.5 if user_vector.tier == RelationshipTier.EXCLUSIVE_PARTNER else 1.0,
            )

            # Log bot's outgoing message
            await msg_repo.log_message(
                telegram_message_id=telegram_message_id + 1,
                chat_id=chat_id,
                sender_id=0,  # 0 indicates Bot itself
                text=raw_reply,
                is_from_bot=True,
            )

            return OrchestratedResponse(
                decision_type="REPLY",
                raw_response_text=raw_reply,
                reaction_emoji=monologue.recommended_reaction_emoji,
                is_shy=is_shy,
                inner_monologue_text=monologue.internal_thought_raw,
                detected_dialect=detected_profile.code,
                loyalty_partner_id=user_vector.user_id if (monologue.should_report_to_partner and user_vector.tier == RelationshipTier.EXCLUSIVE_PARTNER) else None,
                loyalty_report_message=monologue.partner_report_message if monologue.should_report_to_partner else None,
            )


cognitive_orchestrator = CognitiveOrchestrator()
