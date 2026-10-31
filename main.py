"""
PROJECT "AETHER-HUMAN"
Autonomous Sentient-Like Telegram Entity (Monorepo Master Entrypoint)

Orchestrates:
1. Relational Database Layer (PostgreSQL / SQLite)
2. Social Knowledge Graph (Neo4j / GraphRAG)
3. Episodic & Semantic Vector Store (Qdrant)
4. Neuro-Endocrine & Psychological Hormone Engine
5. Cognitive Maestro & Pre-Conscious Inner Monologue (Gemini Key Pool)
6. Multimodal Visual Identity & Acoustic Voice Synthesis
7. Telegram MTProto Userbot Client (Telethon)
8. Autonomous Proactive Daemons & Nightly REM Dreaming
9. Admin Observatory FastAPI Web & WebSockets Telemetry Server
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import uvicorn

# Configure UTF-8 for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from aether_human_core.config.settings import settings
from aether_human_core.config.llm_router import llm_pool
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.neo4j_graph.social_graph import social_graph
from aether_human_core.database.vector_store.qdrant_client import vector_memory
from aether_human_core.telegram_client.mtproto_manager import mtproto_manager
from aether_human_core.autonomous_daemon.proactive_initiator import proactive_daemon
from aether_human_core.autonomous_daemon.memory_consolidation import memory_consolidation_daemon
from aether_human_core.admin_observatory.server import app

# Configure enterprise-grade logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)-24s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("Aether.Core.Main")


class AetherSystemMaster:
    """
    Main Application Supervisor lifecycle manager.
    """
    def __init__(self):
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        logger.info("=" * 70)
        logger.info("🌟 INITIATING PROJECT AETHER-HUMAN CORE ENGINE 🌟")
        logger.info(f"Identity: Omar (عمر) | Age: 24 | Cairo, Egypt")
        logger.info(f"Gemini API Key Pool: {len(settings.gemini_keys_list)} active rotation keys")
        logger.info("=" * 70)

        # 1. Initialize Relational Storage Schema
        logger.info("[1/7] Initializing Relational PostgreSQL/SQLite Data Access Layer...")
        await db_manager.init_schema()

        # 2. Initialize Neo4j Social Knowledge Graph
        logger.info("[2/7] Connecting to Neo4j Social Knowledge Graph...")
        await social_graph.initialize()

        # 3. Initialize Long-Term Episodic Vector Store
        logger.info("[3/7] Initializing Qdrant Episodic Long-Term Memory...")
        await vector_memory.initialize()

        # 4. Initialize Telegram MTProto Userbot Client
        logger.info("[4/7] Launching Telegram MTProto Userbot Client...")
        await mtproto_manager.initialize()

        # 5. Launch Autonomous Subconscious Daemons
        logger.info("[5/7] Activating Proactive Initiator & Nightly Dream Daemons...")
        proactive_daemon.start()
        memory_consolidation_daemon.start()

        # 6. Launch Admin Observatory Server
        server_task = None
        server = None
        async def _safe_serve(srv):
            try:
                await srv.serve()
            except Exception as e:
                logger.warning(f"Admin Observatory UI notice: {e}")

        try:
            config = uvicorn.Config(
                app=app,
                host=settings.admin_host,
                port=settings.admin_port,
                log_level="warning",
                loop="asyncio",
            )
            server = uvicorn.Server(config)
            server_task = asyncio.create_task(_safe_serve(server))
            logger.info(f"[6/7] Starting Admin Observatory on http://localhost:{settings.admin_port} ...")
        except Exception as exc:
            logger.warning(f"Could not bind Admin Observatory on port {settings.admin_port}: {exc}")

        logger.info("[7/7] ✨ All micro-engines successfully synchronized and alive.")

        # Keep running until termination signal
        try:
            await self._shutdown_event.wait()
        finally:
            logger.info("Graceful shutdown initiated...")
            proactive_daemon.stop()
            memory_consolidation_daemon.stop()
            await mtproto_manager.close()
            await llm_pool.close()
            await db_manager.close()
            server.should_exit = True
            await server_task
            logger.info("Aether-Human Core shutdown complete.")

    def request_shutdown(self) -> None:
        self._shutdown_event.set()


async def main():
    master = AetherSystemMaster()

    # Register OS signal handlers if supported on the current platform
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, master.request_shutdown)
        except NotImplementedError:
            pass  # Windows signals handled through loop exceptions

    try:
        await master.start()
    except (KeyboardInterrupt, asyncio.CancelledError):
        master.request_shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
