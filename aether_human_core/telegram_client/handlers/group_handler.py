"""
Group Chat Event Handler and Social Dynamics Observer for Project Aether-Human.
Strictly regulates Omar's public group engagements:
- Only intervenes if explicitly tagged (@mention), replied to, or named.
- Selectively chimes in if group opinion/advice is genuinely sought on an engaging topic.
- Deliberately keeps responses ultra-concise to prevent cluttering busy group chats.
"""

from __future__ import annotations

import logging
import random
import re
from typing import Optional, Dict, Any, List

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.database.neo4j_graph.social_graph import social_graph
from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator
from aether_human_core.telegram_client.human_typer import human_typer
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector, RelationshipTier
from aether_human_core.psychology_engine.micro_traits import micro_traits_engine

logger = logging.getLogger("Aether.Telegram.GroupHandler")


class GroupEventHandler:
    """
    Monitors group dynamics with disciplined, realistic human participation.
    """
    NAME_PATTERNS = ["عمر", "عمور", "عمورة", "يا عمر", "omar"]

    OPINION_TRIGGERS = [
        "إيه رأيكم", "ايه رايكم", "شايفين إيه", "شايفين ايه",
        "حد عنده رأي", "حد عنده راي", "تنصحوني بإيه", "تنصحوني بايه",
        "حد جرب", "حد يفيدنا", "أعمل إيه", "اعمل ايه", "إيه العمل",
        "ايه العمل", "إيه الحل", "ايه الحل", "مين يعرف", "رأيكم", "رايكم"
    ]

    ENGAGING_TOPICS = [
        "برمجة", "كود", "بايثون", "ذكاء اصطناعي", "ai", "لابتوب",
        "شغل", "شركة", "ماتش", "كورة", "أهلي", "زمالك", "كافيه",
        "قهوة", "خروجة", "سفر", "جيم", "تمرين", "سعر", "موبايل"
    ]

    @classmethod
    async def handle_group_message(
        cls,
        message_id: int,
        chat_id: int,
        sender_id: int,
        sender_name: str,
        sender_gender: str,
        message_text: str,
        chat_title: str,
        is_reply_to_bot: bool = False,
        is_bot_mentioned: bool = False,
    ) -> None:
        """
        Processes group communication event with strict selectivity.
        """
        text_lower = message_text.lower().strip()
        logger.info(
            f"Group Event in [{chat_title} ({chat_id})]: Sender [{sender_id} ({sender_name})]: '{message_text[:35]}...'"
        )

        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            user_record = await user_repo.get_or_create(
                telegram_id=sender_id,
                first_name=sender_name,
                gender=sender_gender,
            )

        # 1. Check Group Jealousy Trigger: Is this a high-attachment partner flirting publicly?
        partner_vector = UserAffinityVector(
            user_id=sender_id,
            affinity_score=user_record.affinity_score,
            trust_score=user_record.trust_score,
            romantic_attachment=user_record.romantic_attachment,
            respect_dominance=user_record.respect_dominance,
            tier=RelationshipTier(user_record.relationship_tier),
        )

        jealousy_reproach = micro_traits_engine.evaluate_group_jealousy(
            partner_vector=partner_vector,
            partner_name=sender_name,
            message_in_group=message_text,
            target_person_name="الأعضاء في الجروب",
        )

        if jealousy_reproach:
            logger.warning(
                f"Partner [{sender_name}] triggered jealousy! Scheduling private reproach DM: '{jealousy_reproach}'"
            )
            bursts = human_typer.prepare_message_bursts(jealousy_reproach)
            await mtproto_manager.dispatch_burst_messages(chat_id=sender_id, bursts=bursts)

        # 2. Strict Group Intervention Filter:
        # A) Explicit direct address:
        has_direct_name = any(re.search(rf"\b{re.escape(p)}\b", text_lower) or p in text_lower for p in cls.NAME_PATTERNS)
        is_direct_target = is_reply_to_bot or is_bot_mentioned or has_direct_name

        # B) Genuinely asking for group opinion / advice on a topic Omar cares about:
        is_asking_opinion = any(trig in text_lower for trig in cls.OPINION_TRIGGERS)
        is_relevant_topic = any(topic in text_lower for topic in cls.ENGAGING_TOPICS)
        has_question_mark = "?" in message_text or "؟" in message_text

        is_opinion_sought = is_asking_opinion and (is_relevant_topic or has_question_mark)

        # Decision: Intervene if directly addressed, or selectively (35% chance) if an open opinion is asked
        should_intervene = is_direct_target or (is_opinion_sought and random.random() < 0.35)

        if not should_intervene:
            logger.info(
                f"Silently observing in [{chat_title}]. Not addressed directly, avoiding group chat spam."
            )
            return

        reason = "DIRECT_MENTION" if is_direct_target else "OPINION_INVITATION"
        logger.info(f"Intervening in group [{chat_title}] due to [{reason}].")

        # 3. Cognitive orchestration
        resp = await cognitive_orchestrator.process_incoming_event(
            telegram_message_id=message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=message_text,
            media_type="text",
            sender_gender=sender_gender,
            chat_type="supergroup",
            chat_title=chat_title,
        )

        # 4. Ultra-concise group reply delivery:
        # Prevent long multi-bubble spamming in group chats
        if resp.decision_type == "REPLY" and resp.raw_response_text:
            bursts = human_typer.prepare_message_bursts(resp.raw_response_text, is_shy=resp.is_shy)
            # In groups, limit to 1 punchy bubble, or 2 if both are very short
            group_bursts = bursts[:1] if len(bursts) > 1 and len(bursts[0].text) > 30 else bursts[:2]

            await mtproto_manager.dispatch_burst_messages(
                chat_id=chat_id,
                bursts=group_bursts,
                reply_to_msg_id=message_id,
            )

        if resp.reaction_emoji:
            await mtproto_manager.send_reaction(
                chat_id=chat_id,
                message_id=message_id,
                emoji=resp.reaction_emoji,
            )


group_handler = GroupEventHandler()
