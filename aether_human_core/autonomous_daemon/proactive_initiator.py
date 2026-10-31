"""
Proactive Autonomous Initiator and Subconscious Event Daemon.
Spontaneously initiates conversations with high-affinity friends, checks on life events (exams, interviews),
and monitors interpersonal absences without external triggers.
"""

from __future__ import annotations

import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import List

from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.database.vector_store.qdrant_client import vector_memory
from aether_human_core.telegram_client.human_typer import human_typer
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager
from aether_human_core.psychology_engine.affinity_matrix import RelationshipTier
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine

logger = logging.getLogger("Aether.Daemon.ProactiveInitiator")


class ProactiveInitiatorDaemon:
    """
    Subconscious background loop driving human proactivity and emotional initiative.
    """
    ABSENCE_CHECK_PHRASES = [
        "إيه يا عم الغيبة دي كلها؟ قلقتني عليك والله.. طمني إيه أخبارك؟",
        "وحشتني يا غالي.. بقالك كام يوم مختفي ومطمنيش، خير في إيه؟",
        "مساء الفل.. افتكرتك فجأة قولت لازم أسأل عليك وأشوف يومك ماشي إزاي.",
        "طمني عليك، شغلتك الدنيا أوي كدا ولا إيه؟",
    ]

    PARTNER_MISSING_PHRASES = [
        "وحشتيني أوي.. مختفية بقالك حبة وقلبي مش متطمن، طمنيني عليكي يا روحي ❤️",
        "إيه الغيبة دي؟ اليوم ملوش طعم من غير ما نرغي.. مستنيكي تطمنيني أول ما تشوفي الرسالة ❤️",
    ]

    EVENT_FOLLOW_UP_TEMPLATES = [
        "طمني يا بطل عملت إيه في موضوع {event_name}؟ يا رب تكون الدنيا مشيت تمام!",
        "كنت مستني أطمن عليك.. إيه الأخبار في {event_name}؟ طحنتهم ولا إيه؟",
    ]

    def __init__(self, check_interval_seconds: int = 1800):  # Every 30 minutes
        self.interval = check_interval_seconds
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._daemon_loop())
            logger.info("Proactive Initiator Daemon started.")

    def stop(self) -> None:
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Proactive Initiator Daemon stopped.")

    async def _daemon_loop(self) -> None:
        while self._is_running:
            try:
                await self.evaluate_proactive_initiatives()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Error in Proactive Initiator loop: {exc}")

            await asyncio.sleep(self.interval)

    async def evaluate_proactive_initiatives(self) -> None:
        """
        Scans for users with high affinity who have been silent, or scheduled human life events.
        """
        circadian = circadian_engine.evaluate_circadian_state()
        if circadian["is_sleeping"]:
            logger.debug("Omar is sleeping. Skipping proactive messaging initiative.")
            return

        async with db_manager.session() as session:
            user_repo = UserRepository(session)
            top_users = await user_repo.get_top_affinity_users(limit=10)

        now = datetime.utcnow()
        for user in top_users:
            if user.affinity_score < 40.0:
                continue

            last_seen = user.last_interaction_at or user.created_at
            silence_duration = now - last_seen

            # If user has been silent for more than 24 hours (or 14 hours for romantic partner)
            threshold_hours = 14 if user.relationship_tier == "EXCLUSIVE_PARTNER" else 28
            if silence_duration > timedelta(hours=threshold_hours):
                if random.random() < 0.45:  # Organic probability
                    if user.relationship_tier == "EXCLUSIVE_PARTNER":
                        phrase = random.choice(self.PARTNER_MISSING_PHRASES)
                    else:
                        phrase = random.choice(self.ABSENCE_CHECK_PHRASES)

                    logger.info(
                        f"Proactive impulse: Messaging [{user.first_name} ({user.telegram_id})] "
                        f"after {silence_duration.total_seconds() / 3600:.1f}h of silence."
                    )

                    bursts = human_typer.prepare_message_bursts(phrase)
                    await mtproto_manager.dispatch_burst_messages(
                        chat_id=user.telegram_id, bursts=bursts
                    )

                    # Update last interaction timestamp so we don't spam
                    async with db_manager.session() as session:
                        u_repo = UserRepository(session)
                        db_user = await u_repo.get_by_telegram_id(user.telegram_id)
                        if db_user:
                            db_user.last_interaction_at = datetime.utcnow()
                            await session.flush()
                    break  # One proactive action per cycle to stay natural


proactive_daemon = ProactiveInitiatorDaemon()
