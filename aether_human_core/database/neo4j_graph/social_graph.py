"""
Social Knowledge Graph service for Project Aether-Human.
Maintains inter-user social hierarchies, group dynamics, gossip networks, and multi-hop Cypher queries.
Includes an in-memory graph fallback when Neo4j standalone is absent.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from pydantic import BaseModel, Field

from aether_human_core.database.neo4j_graph.connection import neo4j_conn

logger = logging.getLogger("Aether.DB.SocialGraph")


class GraphEdge(BaseModel):
    source_id: int
    target_id: int
    relation_type: str  # KNOWS, CLOSE_TO, JEALOUS_OF, IN_LOVE_WITH, ANTAGONISTIC_TO, OWES_SECRET
    weight: float = 1.0
    properties: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SocialGraphService:
    """
    Orchestrates social graph operations between Users, Chats, and Secrets.
    Integrates Neo4j with an in-memory high-speed cache.
    """
    def __init__(self):
        # In-memory graph representation
        self._user_nodes: Dict[int, Dict[str, Any]] = {}
        self._chat_nodes: Dict[int, Dict[str, Any]] = {}
        self._edges: List[GraphEdge] = []
        self._user_chat_participation: Dict[int, Set[int]] = {}  # user_id -> set of chat_ids

    async def initialize(self) -> None:
        """
        Connects to Neo4j and provisions graph constraints/indexes.
        """
        connected = await neo4j_conn.connect()
        if connected:
            # Create schema constraints in Neo4j
            await neo4j_conn.execute_query(
                "CREATE CONSTRAINT user_tg_id IF NOT EXISTS FOR (u:User) REQUIRE u.telegram_id IS UNIQUE"
            )
            await neo4j_conn.execute_query(
                "CREATE CONSTRAINT chat_tg_id IF NOT EXISTS FOR (c:Chat) REQUIRE c.chat_id IS UNIQUE"
            )
            logger.info("Neo4j graph constraints verified.")

    async def sync_user_node(
        self,
        telegram_id: int,
        name: str,
        gender: str = "unknown",
        affinity: float = 0.0,
        tier: str = "STRANGER",
    ) -> None:
        """
        Upserts a User node into Neo4j and memory cache.
        """
        # Memory update
        self._user_nodes[telegram_id] = {
            "telegram_id": telegram_id,
            "name": name,
            "gender": gender,
            "affinity": affinity,
            "tier": tier,
            "updated_at": datetime.utcnow(),
        }

        # Neo4j update
        if neo4j_conn.is_connected:
            cypher = """
            MERGE (u:User {telegram_id: $tg_id})
            SET u.name = $name,
                u.gender = $gender,
                u.affinity = $affinity,
                u.tier = $tier,
                u.last_seen = datetime()
            """
            await neo4j_conn.execute_query(
                cypher,
                {"tg_id": telegram_id, "name": name, "gender": gender, "affinity": affinity, "tier": tier},
            )

    async def sync_chat_node(self, chat_id: int, title: str, chat_type: str) -> None:
        self._chat_nodes[chat_id] = {
            "chat_id": chat_id,
            "title": title,
            "chat_type": chat_type,
            "updated_at": datetime.utcnow(),
        }
        if neo4j_conn.is_connected:
            cypher = """
            MERGE (c:Chat {chat_id: $chat_id})
            SET c.title = $title,
                c.chat_type = $chat_type,
                c.last_seen = datetime()
            """
            await neo4j_conn.execute_query(cypher, {"chat_id": chat_id, "title": title, "chat_type": chat_type})

    async def record_user_participation(self, user_id: int, chat_id: int) -> None:
        """
        Registers membership of a user in a specific chat.
        """
        if user_id not in self._user_chat_participation:
            self._user_chat_participation[user_id] = set()
        self._user_chat_participation[user_id].add(chat_id)

        if neo4j_conn.is_connected:
            cypher = """
            MATCH (u:User {telegram_id: $user_id})
            MATCH (c:Chat {chat_id: $chat_id})
            MERGE (u)-[r:PARTICIPATES_IN]->(c)
            SET r.last_activity = datetime()
            """
            await neo4j_conn.execute_query(cypher, {"user_id": user_id, "chat_id": chat_id})

    async def record_inter_user_relation(
        self,
        source_id: int,
        target_id: int,
        relation_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Records or updates a directional social bond (e.g. FRIEND_OF, JEALOUS_OF, ANTAGONISTIC_TO).
        """
        props = properties or {}
        # In-memory update
        existing = next(
            (e for e in self._edges if e.source_id == source_id and e.target_id == target_id and e.relation_type == relation_type),
            None,
        )
        if existing:
            existing.weight = weight
            existing.properties.update(props)
            existing.updated_at = datetime.utcnow()
        else:
            self._edges.append(
                GraphEdge(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    weight=weight,
                    properties=props,
                )
            )

        # Neo4j update
        if neo4j_conn.is_connected:
            cypher = f"""
            MATCH (a:User {{telegram_id: $source_id}})
            MATCH (b:User {{telegram_id: $target_id}})
            MERGE (a)-[r:{relation_type}]->(b)
            SET r.weight = $weight,
                r.updated_at = datetime()
            """
            await neo4j_conn.execute_query(
                cypher,
                {"source_id": source_id, "target_id": target_id, "weight": weight},
            )

    async def get_user_social_circle(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Returns all immediate relations (allies, rivals, love interests) of a given user.
        """
        if neo4j_conn.is_connected:
            cypher = """
            MATCH (u:User {telegram_id: $user_id})-[r]->(target:User)
            RETURN type(r) AS relation, r.weight AS weight, target.telegram_id AS target_id, target.name AS target_name
            """
            records = await neo4j_conn.execute_query(cypher, {"user_id": user_id})
            if records:
                return records

        # Fallback in-memory
        results = []
        for e in self._edges:
            if e.source_id == user_id:
                target_node = self._user_nodes.get(e.target_id, {})
                results.append({
                    "relation": e.relation_type,
                    "weight": e.weight,
                    "target_id": e.target_id,
                    "target_name": target_node.get("name", "Unknown"),
                })
        return results

    async def calculate_betrayal_risk(
        self,
        secret_owner_id: int,
        prospective_recipient_id: int,
    ) -> float:
        """
        Calculates betrayal risk (0.0 to 1.0) of leaking secret_owner's confidential disclosure
        to prospective_recipient. High risk if recipient is antagonistic or close friends with owner's rivals.
        """
        if secret_owner_id == prospective_recipient_id:
            return 0.0

        # Check direct relation
        direct_edges = [
            e for e in self._edges
            if (e.source_id == prospective_recipient_id and e.target_id == secret_owner_id)
            or (e.source_id == secret_owner_id and e.target_id == prospective_recipient_id)
        ]

        for e in direct_edges:
            if e.relation_type == "ANTAGONISTIC_TO":
                # High drama / high risk of exploitation
                return 0.90
            if e.relation_type in ("CLOSE_TO", "IN_LOVE_WITH"):
                # Very close, low risk of malicious leak unless jealous
                if "jealousy" in e.properties and e.properties["jealousy"] > 0.5:
                    return 0.85
                return 0.20

        return 0.50


# Global singleton instance
social_graph = SocialGraphService()
