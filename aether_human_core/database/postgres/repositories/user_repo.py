"""
Repository for User Profile operations, Affinity Matrix queries, and relationship tier transitions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from aether_human_core.database.postgres.models import UserModel

logger = logging.getLogger("Aether.Repo.User")


class UserRepository:
    """
    Data access layer for User Profiles and dynamic affinity scores.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str = "",
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        gender: str = "unknown",
    ) -> UserModel:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            user = UserModel(
                telegram_id=telegram_id,
                first_name=first_name or "",
                last_name=last_name or "",
                username=username,
                gender=gender,
                affinity_score=0.0,
                trust_score=20.0,
                romantic_attachment=0.0,
                respect_dominance=0.0,
                relationship_tier="STRANGER",
                created_at=datetime.utcnow(),
                last_interaction_at=datetime.utcnow(),
            )
            self.session.add(user)
            await self.session.flush()
            logger.info(f"Registered new User [tg_id={telegram_id}, name={first_name}] into Unified Profile.")
        else:
            # Refresh last active time and name metadata if changed
            updated = False
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if username and user.username != username:
                user.username = username
                updated = True
            user.last_interaction_at = datetime.utcnow()
            if updated:
                await self.session.flush()
        return user

    async def update_gender(self, telegram_id: int, gender: str) -> Optional[UserModel]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.gender = gender
            user.updated_at = datetime.utcnow()
            await self.session.flush()
            logger.info(f"Updated gender for user [{telegram_id}] to '{gender}'.")
        return user

    async def update_notes(self, telegram_id: int, notes: str) -> Optional[UserModel]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.notes = notes
            user.updated_at = datetime.utcnow()
            await self.session.flush()
            logger.info(f"Updated notes for user [{telegram_id}].")
        return user

    async def update_affinity_scores(
        self,
        telegram_id: int,
        delta_affinity: float = 0.0,
        delta_trust: float = 0.0,
        delta_romantic: float = 0.0,
        delta_respect: float = 0.0,
    ) -> UserModel:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            raise ValueError(f"User with telegram_id {telegram_id} does not exist.")

        # Clamp and update
        user.affinity_score = max(-100.0, min(100.0, user.affinity_score + delta_affinity))
        user.trust_score = max(0.0, min(100.0, user.trust_score + delta_trust))
        user.romantic_attachment = max(0.0, min(100.0, user.romantic_attachment + delta_romantic))
        user.respect_dominance = max(-50.0, min(50.0, user.respect_dominance + delta_respect))

        # Re-evaluate relationship tier
        user.relationship_tier = self._compute_relationship_tier(
            user.affinity_score, user.trust_score, user.romantic_attachment
        )
        user.updated_at = datetime.utcnow()
        await self.session.flush()

        logger.debug(
            f"Updated affinity for [{user.telegram_id}]: "
            f"Aff={user.affinity_score:.1f}, Trust={user.trust_score:.1f}, "
            f"Rom={user.romantic_attachment:.1f}, Tier={user.relationship_tier}"
        )
        return user

    @staticmethod
    def _compute_relationship_tier(affinity: float, trust: float, romantic: float) -> str:
        if affinity < -40.0:
            return "ANTAGONIST"
        if romantic >= 75.0 and trust >= 65.0:
            return "EXCLUSIVE_PARTNER"
        if romantic >= 45.0:
            return "ROMANTIC_INTEREST"
        if affinity >= 60.0 and trust >= 50.0:
            return "CLOSE_FRIEND"
        if affinity >= 20.0:
            return "FRIEND"
        if affinity >= 0.0:
            return "ACQUAINTANCE"
        return "STRANGER"

    async def get_top_affinity_users(self, limit: int = 10) -> List[UserModel]:
        stmt = select(UserModel).order_by(desc(UserModel.affinity_score)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_exclusive_partners(self) -> List[UserModel]:
        stmt = select(UserModel).where(UserModel.relationship_tier == "EXCLUSIVE_PARTNER")
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
