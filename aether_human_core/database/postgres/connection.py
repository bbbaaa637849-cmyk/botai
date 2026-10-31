"""
Asynchronous Database Connection and Session Lifecycle for Project Aether-Human.
Compatible with PostgreSQL (asyncpg) and SQLite (aiosqlite) for standalone environments.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from aether_human_core.config.settings import settings

logger = logging.getLogger("Aether.DB.Postgres")

Base = declarative_base()


class DatabaseManager:
    """
    Manages async database engine lifecycle, connection pooling, and session creation.
    """
    def __init__(self, db_url: str):
        self.db_url: str = db_url
        connect_args = {"timeout": 30} if "sqlite" in self.db_url else {}
        self.engine: AsyncEngine = create_async_engine(
            self.db_url,
            echo=settings.debug,
            future=True,
            connect_args=connect_args,
            pool_pre_ping=True if "sqlite" not in self.db_url else False,
        )

        if "sqlite" in self.db_url:
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=30000")
                    cursor.close()
                except Exception:
                    pass

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(f"DatabaseManager initialized with backend URL scheme: {self.db_url.split('://')[0]}")

    async def init_schema(self) -> None:
        """
        Creates all defined database tables if they do not exist,
        and applies automatic non-destructive schema migrations.
        """
        async with self.engine.begin() as conn:
            logger.info("Verifying and building relational database schema...")
            await conn.run_sync(Base.metadata.create_all)

            def apply_safe_migrations(sync_conn):
                try:
                    if "sqlite" in self.db_url:
                        cursor = sync_conn.connection.cursor()
                        cursor.execute("PRAGMA table_info(users)")
                        existing_cols = [row[1] for row in cursor.fetchall()]
                        if "role" not in existing_cols:
                            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'MEMBER'")
                        if "role_assigned_by" not in existing_cols:
                            cursor.execute("ALTER TABLE users ADD COLUMN role_assigned_by BIGINT")
                        if "custom_title" not in existing_cols:
                            cursor.execute("ALTER TABLE users ADD COLUMN custom_title VARCHAR(128)")
                        cursor.close()
                except Exception as ex:
                    logger.debug(f"Migration step note: {ex}")

            await conn.run_sync(apply_safe_migrations)
            logger.info("Relational database schema ready.")

    async def close(self) -> None:
        """
        Closes connection pool.
        """
        await self.engine.dispose()
        logger.info("Database engine connections closed.")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Yields an transactional AsyncSession context.
        Rolls back automatically on unhandled exceptions.
        """
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error(f"Database session exception encountered. Transaction rolled back: {exc}")
            raise
        finally:
            await session.close()


# Global DB Manager
db_manager = DatabaseManager(settings.postgres_url)
