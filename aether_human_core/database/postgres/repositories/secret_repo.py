"""
Repository for Confidential Disclosures, Secret Item tracking, and Betrayal mechanics.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aether_human_core.database.postgres.models import SecretItemModel

logger = logging.getLogger("Aether.Repo.Secret")


class SecretRepository:
    """
    Data access layer for human secrets, leak probabilities, and betrayal history.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_secret(
        self,
        owner_user_id: int,
        secret_content: str,
        confidentiality_score: int = 5,
    ) -> SecretItemModel:
        secret = SecretItemModel(
            owner_user_id=owner_user_id,
            secret_content=secret_content,
            confidentiality_score=max(1, min(10, confidentiality_score)),
            leaked_to_user_ids=[],
            is_betrayed=False,
            created_at=datetime.utcnow(),
        )
        self.session.add(secret)
        await self.session.flush()
        logger.info(
            f"Stored Confidential Secret #{secret.id} from User [{owner_user_id}] "
            f"(Confidentiality: {confidentiality_score}/10)"
        )
        return secret

    async def get_user_secrets(self, owner_user_id: int) -> List[SecretItemModel]:
        stmt = select(SecretItemModel).where(SecretItemModel.owner_user_id == owner_user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def record_leak(self, secret_id: int, recipient_user_id: int) -> bool:
        stmt = select(SecretItemModel).where(SecretItemModel.id == secret_id)
        result = await self.session.execute(stmt)
        secret = result.scalars().first()
        if not secret:
            return False

        leaked_list = list(secret.leaked_to_user_ids or [])
        if recipient_user_id not in leaked_list:
            leaked_list.append(recipient_user_id)
            secret.leaked_to_user_ids = leaked_list
            secret.is_betrayed = True
            await self.session.flush()
            logger.warning(
                f"Betrayal event: Secret #{secret_id} owned by [{secret.owner_user_id}] leaked to [{recipient_user_id}]."
            )
        return True
