"""Hybrid search: merge BM25 + semantic via Reciprocal Rank Fusion (RRF)."""

import sqlite3
from typing import Optional

from .bm25 import BM25Search
from .result import SearchResult
from .semantic import SemanticSearch


class HybridSearch:
    """Merge BM25 + semantic results via RRF."""

    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.bm25 = BM25Search(db)
        self.semantic = SemanticSearch(db)

    def search(
        self,
        query: str,
        query_embedding: Optional[list[float]] = None,
        limit: int = 10,
        type_filter: Optional[list[str]] = None,
        scope_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Merge BM25 + semantic results via Reciprocal Rank Fusion (RRF).

        Scoring formula: score(doc) = sum(1 / (k + rank)) for each result set
        where k = 60 (standard RRF constant)

        Falls back to BM25 only if semantic search unavailable.
        """
        k_rrf = 60

        # BM25 results (always available)
        bm25_results = self.bm25.search(
            query, limit * 2, type_filter, scope_filter
        )
        bm25_ranked = {
            r.artifact_id: 1.0 / (k_rrf + i)
            for i, r in enumerate(bm25_results)
        }

        # Semantic results (if embedding provided)
        semantic_ranked = {}
        if query_embedding:
            try:
                semantic_results = self.semantic.search(
                    query_embedding, k=limit * 2, type_filter=type_filter, scope_filter=scope_filter
                )
                semantic_ranked = {
                    r.artifact_id: 1.0 / (k_rrf + i)
                    for i, r in enumerate(semantic_results)
                }
            except Exception:
                # Graceful degradation to BM25 only
                pass

        # Merge: sum RRF scores
        merged = {}
        all_results = {r.artifact_id: r for r in bm25_results}

        for artifact_id, score in bm25_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score

        for artifact_id, score in semantic_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score

        # Rank by merged RRF score (descending)
        ranked_ids = sorted(merged.items(), key=lambda x: -x[1])[:limit]

        # Return with RRF score
        results = []
        for artifact_id, rrf_score in ranked_ids:
            result = all_results.get(artifact_id)
            if result:
                result.rrf_score = rrf_score
                results.append(result)

        return results
