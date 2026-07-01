"""BM25 full-text search via SQLite FTS5."""

import sqlite3
from typing import Optional

from .result import SearchResult


class BM25Search:
    """Full-text search using SQLite FTS5 (BM25 algorithm)."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def search(
        self,
        query: str,
        limit: int = 10,
        type_filter: Optional[list[str]] = None,
        scope_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search artifacts via FTS5 (BM25).

        Returns results ranked by FTS5 relevance (highest first).
        """
        # ponytail: empty query returns empty results (FTS5 can't handle empty MATCH)
        if not query or not query.strip():
            return []

        where_clauses = []
        params = [query]

        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            where_clauses.append(f"a.type IN ({placeholders})")
            params.extend(type_filter)

        if scope_filter:
            where_clauses.append("a.relevance_scope = ?")
            params.append(scope_filter)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        sql = f"""
            SELECT
                a.id,
                a.title,
                a.type,
                a.content,
                a.relevance_scope,
                a.source,
                a.created_at,
                rank,
                highlight(artifacts_fts, 1, '<match>', '</match>') as snippet
            FROM artifacts_fts
            JOIN artifacts a ON artifacts_fts.rowid = a.rowid
            WHERE artifacts_fts MATCH ?
                AND {where_sql}
            ORDER BY rank
            LIMIT ?
        """
        params.append(limit)

        rows = self.db.execute(sql, params).fetchall()

        results = []
        for i, row in enumerate(rows):
            # Normalize rank to relevance_score (0.0-1.0)
            relevance_score = 1.0 / (1.0 + abs(row[7]))

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
                    bm25_rank=len(rows) - i,
                    snippet=row[8],
                )
            )

        return results
