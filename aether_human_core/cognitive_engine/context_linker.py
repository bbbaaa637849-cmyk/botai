"""
Cross-Context Omni-Memory and Group-to-DM Synapse Engine.
Bridges user activities, disputes, and sentiments between shared Telegram groups and private DMs.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.message_repo import MessageRepository

logger = logging.getLogger("Aether.Cognitive.ContextLinker")


class ContextLinkerService:
    """
    Synthesizes cross-chat behavioral synapses.
    Enables Omar to organically recall: 'I noticed you were stressed in the group earlier...'.
    """

    @classmethod
    async def get_cross_context_summary(
        cls,
        user_id: int,
        user_name: str,
        current_chat_id: int,
        is_dm: bool,
    ) -> Optional[str]:
        """
        Inspects user's recent messages in other contexts to create organic conversational bridges.
        """
        async with db_manager.session() as session:
            msg_repo = MessageRepository(session)
            recent_group_msgs = await msg_repo.get_user_recent_group_messages(
                user_id=user_id,
                current_chat_id=current_chat_id,
                limit=5,
            )

        if not recent_group_msgs:
            return None

        # Analyze tone and content of recent group messages
        snippets: List[str] = []
        for m in recent_group_msgs:
            if m.text and len(m.text.strip()) > 3:
                snippets.append(f'"{m.text.strip()}"')

        if not snippets:
            return None

        joined_snippets = " | ".join(snippets[:3])

        # Formulate contextual bridge observation
        if is_dm:
            bridge = (
                f"[سياق عابر من الجروبات المشتركة: المستخدم {user_name} كان بيتكلم في الجروب مؤخراً بالرسائل دي: "
                f"({joined_snippets}). لو حسيت إنه كان متضايق أو في مشكلة هناك، اربط الكلام ده عفوياً في الخاص زي أي إنسان طبيعي]."
            )
        else:
            bridge = (
                f"[سياق عابر: أنت تعرف {user_name} من الخاص، لكن المحادثة الحالية في جروب عام. "
                f"تذكر علاقتك بيه لكن متفضحش أسراركم الخاصة قدام الناس]."
            )

        logger.info(f"Generated Cross-Context Synapse bridge for user [{user_id}] ({user_name}).")
        return bridge


context_linker = ContextLinkerService()
