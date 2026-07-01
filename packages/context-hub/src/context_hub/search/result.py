"""Unified SearchResult contract for all search methods."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    """Unified result contract for all search methods (BM25, semantic, hybrid)."""

    artifact_id: str
    title: str
    type: str
    content: str
    relevance_scope: str
    relevance_score: float  # 0.0-1.0 (normalized across all search types)
    source: str
    created_at: str

    # Method-specific metadata (optional, populated by specific search implementations)
    bm25_rank: Optional[int] = None  # rank in BM25 result set
    semantic_distance: Optional[float] = None  # distance in vector space
    rrf_score: Optional[float] = None  # RRF merged score (hybrid search only)
    snippet: Optional[str] = None  # highlighted excerpt (BM25 only)
