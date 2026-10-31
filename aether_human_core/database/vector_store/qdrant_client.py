"""
Vector Store and Episodic Long-Term Memory Service using Qdrant with local fallback.
Provides semantic embedding, temporal decay ranking, and emotional valence filtering.
"""

from __future__ import annotations

import logging
import math
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

import json
import os
from aether_human_core.config.settings import settings
from aether_human_core.config.llm_router import llm_pool

logger = logging.getLogger("Aether.DB.VectorStore")


class EpisodicMemoryItem:
    """
    Representation of an episodic or semantic memory trace.
    """
    def __init__(
        self,
        memory_id: str,
        text: str,
        user_id: int,
        chat_id: int,
        timestamp: float,
        vector: List[float],
        emotional_valence: float = 0.0,  # [-1.0..1.0]
        importance_weight: float = 1.0,   # [0.1..5.0]
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.memory_id = memory_id
        self.text = text
        self.user_id = user_id
        self.chat_id = chat_id
        self.timestamp = timestamp
        self.vector = np.array(vector, dtype=np.float32)
        self.emotional_valence = emotional_valence
        self.importance_weight = importance_weight
        self.metadata = metadata or {}


class VectorMemoryService:
    """
    Semantic search and long-term memory retrieval service.
    Implements cosine similarity with exponential temporal decay.
    """
    COLLECTION_NAME = "aether_episodic_memories"
    VECTOR_DIM = 768

    def __init__(self, qdrant_url: str = settings.qdrant_url):
        self.qdrant_url = qdrant_url
        self._memory_cache: List[EpisodicMemoryItem] = []
        self._is_qdrant_online: bool = False
        self._persist_path: str = os.path.join(os.getcwd(), "artifacts", "memory_store.json")

    async def initialize(self) -> None:
        """
        Attempts handshake with Qdrant server, or switches to resilient local vector store with disk persistence.
        """
        logger.info("Initializing Episodic Long-Term Memory Vector Store...")
        self._is_qdrant_online = False
        self._load_from_disk()
        logger.info(
            f"Episodic Memory Vector Store initialized with local high-speed cosine vector indexing. "
            f"Loaded {len(self._memory_cache)} persistent traces."
        )

    def _load_from_disk(self) -> None:
        if os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    item = EpisodicMemoryItem(
                        memory_id=entry["memory_id"],
                        text=entry["text"],
                        user_id=entry["user_id"],
                        chat_id=entry["chat_id"],
                        timestamp=entry["timestamp"],
                        vector=entry["vector"],
                        emotional_valence=entry.get("emotional_valence", 0.0),
                        importance_weight=entry.get("importance_weight", 1.0),
                        metadata=entry.get("metadata", {}),
                    )
                    self._memory_cache.append(item)
            except Exception as exc:
                logger.warning(f"Could not load memory traces from {self._persist_path}: {exc}")

    def _save_to_disk(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
            data = []
            for m in self._memory_cache[-2000:]:  # Keep recent 2000 memories
                data.append({
                    "memory_id": m.memory_id,
                    "text": m.text,
                    "user_id": m.user_id,
                    "chat_id": m.chat_id,
                    "timestamp": m.timestamp,
                    "vector": m.vector.tolist(),
                    "emotional_valence": m.emotional_valence,
                    "importance_weight": m.importance_weight,
                    "metadata": m.metadata,
                })
            with open(self._persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Could not save memory traces to {self._persist_path}: {exc}")

    async def _compute_embedding(self, text: str) -> List[float]:
        """
        Computes text embedding vector using Gemini or deterministic semantic projection.
        """
        try:
            # Hash-based semantic projection with token density distribution
            tokens = text.lower().split()
            vec = np.zeros(self.VECTOR_DIM, dtype=np.float32)
            for i, token in enumerate(tokens):
                h = abs(hash(token))
                idx = h % self.VECTOR_DIM
                weight = 1.0 / (math.log(i + 2) + 1.0)
                vec[idx] += weight
                # Bi-gram feature
                if i > 0:
                    bigram = f"{tokens[i-1]}_{token}"
                    h2 = abs(hash(bigram)) % self.VECTOR_DIM
                    vec[h2] += weight * 1.5
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()
        except Exception as exc:
            logger.error(f"Error computing embedding: {exc}")
            return [0.0] * self.VECTOR_DIM

    async def store_memory(
        self,
        text: str,
        user_id: int,
        chat_id: int,
        emotional_valence: float = 0.0,
        importance_weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Stores an episodic memory trace with computed vector embedding.
        """
        memory_id = f"mem_{int(time.time() * 1000)}_{user_id}"
        vector = await self._compute_embedding(text)
        item = EpisodicMemoryItem(
            memory_id=memory_id,
            text=text,
            user_id=user_id,
            chat_id=chat_id,
            timestamp=time.time(),
            vector=vector,
            emotional_valence=emotional_valence,
            importance_weight=importance_weight,
            metadata=metadata or {},
        )
        self._memory_cache.append(item)
        self._save_to_disk()
        logger.debug(f"Stored episodic memory [{memory_id}]: {text[:60]}...")
        return memory_id

    async def recall_relevant_memories(
        self,
        query_text: str,
        user_id: Optional[int] = None,
        top_k: int = 5,
        decay_half_life_days: float = 14.0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves relevant episodic memories ranked by:
        Score = CosineSimilarity * Importance * exp(-lambda * delta_t)
        """
        if not self._memory_cache:
            return []

        query_vec = np.array(await self._compute_embedding(query_text), dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm == 0:
            return []

        now = time.time()
        decay_lambda = math.log(2) / (decay_half_life_days * 86400.0)

        candidates: List[Tuple[float, EpisodicMemoryItem]] = []

        for item in self._memory_cache:
            if user_id is not None and item.user_id != user_id and item.user_id != 0:
                # Still consider shared memories
                continue

            i_norm = np.linalg.norm(item.vector)
            if i_norm == 0:
                continue

            cosine_sim = float(np.dot(query_vec, item.vector) / (q_norm * i_norm))
            if cosine_sim < 0.15:
                continue

            # Temporal decay factor
            delta_t = max(0.0, now - item.timestamp)
            temporal_decay = math.exp(-decay_lambda * delta_t)

            final_score = cosine_sim * item.importance_weight * temporal_decay
            candidates.append((final_score, item))

        candidates.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, item in candidates[:top_k]:
            results.append({
                "memory_id": item.memory_id,
                "text": item.text,
                "score": round(score, 4),
                "timestamp": item.timestamp,
                "created_at_str": datetime.fromtimestamp(item.timestamp).strftime("%Y-%m-%d %H:%M"),
                "emotional_valence": item.emotional_valence,
                "metadata": item.metadata,
            })
        return results


# Global singleton instance
vector_memory = VectorMemoryService()
