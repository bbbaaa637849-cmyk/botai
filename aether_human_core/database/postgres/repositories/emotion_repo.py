"""
Repository for Neuro-Hormone logs and Psychological State Histories.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from aether_human_core.database.postgres.models import NeuroHormoneHistoryModel

logger = logging.getLogger("Aether.Repo.Emotion")


class EmotionRepository:
    """
    Data access layer for psychological shocks, endocrine states, and circadian metrics.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_state(
        self,
        dopamine: float,
        oxytocin: float,
        cortisol: float,
        serotonin: float,
        energy: float,
        trigger_event: str,
        trigger_user_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> NeuroHormoneHistoryModel:
        record = NeuroHormoneHistoryModel(
            timestamp=datetime.utcnow(),
            dopamine=dopamine,
            oxytocin=oxytocin,
            cortisol=cortisol,
            serotonin=serotonin,
            energy=energy,
            trigger_event=trigger_event,
            trigger_user_id=trigger_user_id,
            notes=notes,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_latest_state(self) -> Optional[NeuroHormoneHistoryModel]:
        stmt = (
            select(NeuroHormoneHistoryModel)
            .order_by(desc(NeuroHormoneHistoryModel.timestamp))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_recent_history(self, limit: int = 50) -> List[NeuroHormoneHistoryModel]:
        stmt = (
            select(NeuroHormoneHistoryModel)
            .order_by(desc(NeuroHormoneHistoryModel.timestamp))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        records = list(result.scalars().all())
        records.reverse()
        return records
