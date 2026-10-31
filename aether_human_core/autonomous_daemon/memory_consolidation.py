"""
Nightly Memory Consolidation and 'Dreaming' Engine for Aether-Human.
Simulates REM dream consolidation during biological sleep hours.
Transfers working memory into long-term Qdrant vectors and Neo4j graph schemas,
and restores homeostatic neuro-chemical equilibrium.
"""

from __future__ import annotations

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

from aether_human_core.config.llm_router import llm_pool
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.models import MessageRecordModel, AuditLogModel
from aether_human_core.database.postgres.repositories.message_repo import MessageRepository
from aether_human_core.database.vector_store.qdrant_client import vector_memory
from aether_human_core.database.neo4j_graph.social_graph import social_graph
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine

logger = logging.getLogger("Aether.Daemon.MemoryConsolidation")


class MemoryConsolidationDaemon:
    """
    Simulates the biological consolidation of memories during night-time sleep.
    """
    def __init__(self, check_interval_seconds: int = 3600):  # Check hourly
        self.interval = check_interval_seconds
        self._is_running = False
        self._last_consolidation_date: Optional[str] = None
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._consolidation_loop())
            logger.info("Memory Consolidation Daemon started.")

    def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Memory Consolidation Daemon stopped.")

    async def _consolidation_loop(self) -> None:
        while self._is_running:
            try:
                await self.maybe_trigger_nightly_consolidation()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in consolidation daemon loop: {exc}")

            await asyncio.sleep(self.interval)

    async def maybe_trigger_nightly_consolidation(self) -> None:
        """
        Executes consolidation during the deep sleep window (04:00 AM - 05:30 AM Cairo time).
        """
        circadian = circadian_engine.evaluate_circadian_state()
        hour = circadian["hour_fraction"]
        today_str = circadian["cairo_time_str"].split()[0]

        # Check if deep night and not yet executed today
        if 4.0 <= hour <= 6.0 and self._last_consolidation_date != today_str:
            logger.info("🌙 Entering REM Dream State: Consolidating episodic memories of the past 24 hours...")
            await self._execute_consolidation_procedure(today_str)
            self._last_consolidation_date = today_str

    async def _execute_consolidation_procedure(self, today_str: str) -> None:
        """
        Consolidates messages into high-level episodic memories and resets hormones.
        """
        yesterday = datetime.utcnow() - timedelta(days=1)

        async with db_manager.session() as session:
            # Fetch recent active messages
            from sqlalchemy import select
            stmt = (
                select(MessageRecordModel)
                .where(MessageRecordModel.created_at >= yesterday)
                .order_by(MessageRecordModel.created_at)
                .limit(200)
            )
            result = await session.execute(stmt)
            recent_msgs = list(result.scalars().all())

            if not recent_msgs:
                logger.info("No conversational logs in past 24 hours to consolidate.")
                # Reset hormones to baseline anyway
                endocrine_engine.state.cortisol = endocrine_engine.state.BASE_CORTISOL
                endocrine_engine.state.energy = 1.0
                return

            conversation_text = "\n".join(
                f"{'عمر' if m.is_from_bot else f'مستخدم {m.sender_id}'}: {m.text}"
                for m in recent_msgs
                if m.text
            )

            prompt = (
                f"أنت العقل الباطن لـ 'عمر' أثناء النوم في مرحلة الحلم. "
                f"لخص أحداث اليوم والمواقف العاطفية المهمة في نقاط دلالية مكثفة باللهجة المصرية، "
                f"مع ذكر العلاقات التي تطورت، الوعود التي قطعت، أو الخلافات التي حدثت:\n\n"
                f"{conversation_text[:4000]}\n\n"
                f"أخرج ملخص الذكريات الدائمة في 3-5 نقاط:"
            )

            try:
                summary = await llm_pool.generate_content(
                    prompt=prompt,
                    temperature=0.4,
                )

                # Store consolidated memory in Qdrant Vector Store
                await vector_memory.store_memory(
                    text=f"[ذكريات مجمعة ليوم {today_str}]: {summary.strip()}",
                    user_id=0,
                    chat_id=0,
                    emotional_valence=0.2,
                    importance_weight=3.0,
                    metadata={"consolidation_date": today_str},
                )

                # Log audit record
                audit_log = AuditLogModel(
                    timestamp=datetime.utcnow(),
                    component="MemoryConsolidation",
                    action="NIGHTLY_DREAM_CONSOLIDATION",
                    details={"date": today_str, "summary": summary[:300]},
                )
                session.add(audit_log)
                await session.flush()

                # Restore endocrine homeostatic levels
                endocrine_engine.state.cortisol = endocrine_engine.state.BASE_CORTISOL
                endocrine_engine.state.dopamine = endocrine_engine.state.BASE_DOPAMINE
                endocrine_engine.state.energy = 1.0
                logger.info(f"✨ Nightly dream consolidation completed successfully for {today_str}.")

            except Exception as exc:
                logger.error(f"Failed to execute dream consolidation: {exc}")


memory_consolidation_daemon = MemoryConsolidationDaemon()
