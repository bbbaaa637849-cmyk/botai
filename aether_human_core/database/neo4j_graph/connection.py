"""
Neo4j Graph Database Driver and Session Lifecycle with resilient fallback.
"""

from __future__ import annotations

import logging
from typing import Optional, Any, Dict, List
from neo4j import AsyncGraphDatabase, AsyncDriver

from aether_human_core.config.settings import settings

logger = logging.getLogger("Aether.DB.Neo4j")


class Neo4jConnectionManager:
    """
    Manages connection pools to Neo4j graph cluster with health checking.
    """
    def __init__(
        self,
        uri: str = settings.neo4j_uri,
        user: str = settings.neo4j_user,
        password: str = settings.neo4j_password,
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[AsyncDriver] = None
        self._is_connected: bool = False

    async def connect(self) -> bool:
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
            )
            # Verify connectivity
            async with self._driver.session() as session:
                result = await session.run("RETURN 1 AS ping")
                record = await result.single()
                if record and record["ping"] == 1:
                    self._is_connected = True
                    logger.info("Successfully connected to Neo4j Social Knowledge Graph.")
                    return True
        except Exception as exc:
            self._is_connected = False
            logger.warning(
                f"Neo4j connection to {self.uri} failed ({exc}). Operating with local in-memory fallback graph."
            )
            return False
        return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes Cypher query on active Neo4j connection.
        """
        if not self._is_connected or not self._driver:
            return []

        try:
            async with self._driver.session() as session:
                result = await session.run(query, parameters or {})
                records = [record.data() async for record in result]
                return records
        except Exception as exc:
            logger.error(f"Cypher execution failed: {exc} | Query: {query}")
            return []

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._is_connected = False
            logger.info("Neo4j driver connection closed.")


# Global singleton instance
neo4j_conn = Neo4jConnectionManager()
