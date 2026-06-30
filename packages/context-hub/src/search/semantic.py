"""Semantic search via sqlite-vec (KNN embedding similarity)."""

import sqlite3
import struct
from typing import Optional

from .result import SearchResult


class SemanticSearch:
    """KNN search using sqlite-vec extension."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.available = self._check_available()

    def _check_available(self) -> bool:
        """Check if sqlite-vec extension is available."""
        try:
            self.db.execute("SELECT COUNT(*) FROM artifact_embeddings LIMIT 1")
            return True
        except sqlite3.OperationalError:
            return False

    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        type_filter: Optional[list[str]] = None,
        scope_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search artifacts via KNN embedding similarity.

        Returns results ranked by embedding distance (nearest first).
        Requires embeddings to be pre-computed.
        """
        if not self.available:
            return []

        where_clauses = ["1=1"]
        params = []

        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            where_clauses.append(f"a.type IN ({placeholders})")
            params.extend(type_filter)

        if scope_filter:
            where_clauses.append("a.relevance_scope = ?")
            params.append(scope_filter)

        where_sql = " AND ".join(where_clauses)

        # Pack embedding as binary for sqlite-vec
        embedding_bytes = struct.pack(f"{len(query_embedding)}f", *query_embedding)

        sql = f"""
            SELECT
                ae.artifact_id,
                a.title,
                a.type,
                a.content,
                a.relevance_scope,
                a.source,
                a.created_at,
                ae.distance
            FROM artifact_embeddings ae
            JOIN artifacts a ON ae.artifact_id = a.id
            WHERE ae.embedding MATCH ?
                AND {where_sql}
            ORDER BY ae.distance ASC
            LIMIT ?
        """
        params = [embedding_bytes] + params + [k]

        try:
            rows = self.db.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return []

        results = []
        for i, row in enumerate(rows):
            # Convert distance to similarity (0.0-1.0)
            relevance_score = 1.0 / (1.0 + row[7])

            results.append(
                SearchResult(
                    artifact_id=row[0],
                    title=row[1],
                    type=row[2],
                    content=row[3],
                    relevance_scope=row[4],
                    relevance_score=relevance_score,
                    source=row[5],
                    created_at=row[6],
                    semantic_distance=row[7],
                )
            )

        return results
