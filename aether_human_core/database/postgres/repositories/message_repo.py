"""
Repository for Chat containers and Message transactions across DMs and Supergroups.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from aether_human_core.database.postgres.models import ChatModel, MessageRecordModel

logger = logging.getLogger("Aether.Repo.Message")


class MessageRepository:
    """
    Data access layer for conversation traces, media logs, and cross-context message queries.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_chat(
        self,
        chat_id: int,
        title: Optional[str] = None,
        chat_type: str = "private",
    ) -> ChatModel:
        stmt = select(ChatModel).where(ChatModel.chat_id == chat_id)
        result = await self.session.execute(stmt)
        chat = result.scalars().first()
        if not chat:
            chat = ChatModel(
                chat_id=chat_id,
                title=title or ("Private Chat" if chat_type == "private" else "Group"),
                chat_type=chat_type,
                created_at=datetime.utcnow(),
                last_message_at=datetime.utcnow(),
            )
            self.session.add(chat)
            await self.session.flush()
        else:
            if title and chat.title != title:
                chat.title = title
            chat.last_message_at = datetime.utcnow()
            await self.session.flush()
        return chat

    async def log_message(
        self,
        telegram_message_id: int,
        chat_id: int,
        sender_id: int,
        text: Optional[str] = None,
        media_type: str = "text",
        sentiment: Optional[str] = None,
        perceived_emotion: Optional[str] = None,
        is_from_bot: bool = False,
        reply_to_msg_id: Optional[int] = None,
    ) -> MessageRecordModel:
        record = MessageRecordModel(
            telegram_message_id=telegram_message_id,
            chat_id=chat_id,
            sender_id=sender_id,
            text=text or "",
            media_type=media_type,
            sentiment=sentiment,
            perceived_emotion=perceived_emotion,
            is_from_bot=is_from_bot,
            reply_to_msg_id=reply_to_msg_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_recent_chat_history(
        self,
        chat_id: int,
        limit: int = 15,
    ) -> List[MessageRecordModel]:
        stmt = (
            select(MessageRecordModel)
            .where(MessageRecordModel.chat_id == chat_id)
            .order_by(desc(MessageRecordModel.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        records = list(result.scalars().all())
        records.reverse()  # Return in chronological order
        return records

    async def get_user_recent_group_messages(
        self,
        user_id: int,
        current_chat_id: int,
        limit: int = 10,
    ) -> List[MessageRecordModel]:
        """
        Cross-Context Synapse query: retrieves recent messages authored by user in other groups.
        """
        stmt = (
            select(MessageRecordModel)
            .join(ChatModel, MessageRecordModel.chat_id == ChatModel.chat_id)
            .where(
                MessageRecordModel.sender_id == user_id,
                MessageRecordModel.chat_id != current_chat_id,
                ChatModel.chat_type.in_(["group", "supergroup"]),
            )
            .order_by(desc(MessageRecordModel.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
