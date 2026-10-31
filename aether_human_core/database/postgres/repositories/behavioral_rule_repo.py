"""
Repository for Behavioral Constraints and Social Influence Directives.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aether_human_core.database.postgres.models import BehavioralRuleModel

logger = logging.getLogger("Aether.Repo.BehavioralRule")


class BehavioralRuleRepository:
    """
    Data access layer for compiling, storing, and evaluating social directives.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_rule(
        self,
        commander_id: int,
        rule_type: str,
        instruction_text: str,
        target_user_id: Optional[int] = None,
        target_gender: Optional[str] = None,
        target_keywords: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> BehavioralRuleModel:
        rule = BehavioralRuleModel(
            user_id=commander_id,
            rule_type=rule_type,
            instruction_text=instruction_text,
            target_user_id=target_user_id,
            target_gender=target_gender,
            target_keywords=target_keywords or [],
            is_active=True,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        self.session.add(rule)
        await self.session.flush()
        logger.info(
            f"Created Active Behavioral Rule #{rule.id} [Type={rule_type}] commanded by User [{commander_id}]: {instruction_text}"
        )
        return rule

    async def get_active_rules(self) -> List[BehavioralRuleModel]:
        now = datetime.utcnow()
        stmt = (
            select(BehavioralRuleModel)
            .where(
                BehavioralRuleModel.is_active == True,
                (BehavioralRuleModel.expires_at.is_(None)) | (BehavioralRuleModel.expires_at > now),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_matching_interceptors(
        self,
        sender_id: int,
        sender_gender: str,
        message_text: str,
    ) -> List[BehavioralRuleModel]:
        """
        Pre-Cognitive Interceptor match: queries active rules that apply to the incoming sender.
        """
        active_rules = await self.get_active_rules()
        matched: List[BehavioralRuleModel] = []

        for rule in active_rules:
            # Skip if sender is the commander themselves
            if sender_id == rule.user_id:
                continue

            if rule.rule_type == "RESTRICT_FEMALE_TALK" and sender_gender == "female":
                matched.append(rule)
            elif rule.rule_type in ("IGNORE_USER", "COLD_MODE") and rule.target_user_id == sender_id:
                matched.append(rule)
            elif rule.target_keywords:
                for kw in rule.target_keywords:
                    if kw.lower() in message_text.lower():
                        matched.append(rule)
                        break

        return matched

    async def deactivate_rule(self, rule_id: int) -> bool:
        stmt = (
            update(BehavioralRuleModel)
            .where(BehavioralRuleModel.id == rule_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
