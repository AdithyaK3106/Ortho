"""Semantic duplicate detection and removal for context chunks."""

from dataclasses import dataclass
from typing import List, Dict, Set
import hashlib
from .types import ContextChunk


@dataclass
class DeduplicationResult:
    """Result of deduplication operation."""
    deduplicated_chunks: List[ContextChunk]
    removed_count: int
    cluster_count: int


def _compute_token_overlap(text1: str, text2: str) -> float:
    """Compute Jaccard similarity based on token overlap."""
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())

    if not tokens1 or not tokens2:
        return 0.0

    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    return intersection / union if union > 0 else 0.0


def _cluster_chunks(
    chunks: List[ContextChunk],
    similarity_threshold: float,
) -> Dict[int, List[ContextChunk]]:
    """
    Cluster chunks by similarity using greedy clustering.

    Returns a dict mapping cluster_id → list of chunks in that cluster.
    ponytail: simple greedy clustering, not optimal but deterministic and fast.
    """
    if not chunks:
        return {}

    clusters: Dict[int, List[ContextChunk]] = {}
    chunk_to_cluster: Dict[str, int] = {}
    next_cluster_id = 0

    # Sort chunks by ID for determinism
    sorted_chunks = sorted(chunks, key=lambda c: c.id)

    for chunk in sorted_chunks:
        # Check if chunk is similar to any existing cluster representative
        assigned = False
        for cluster_id, cluster_chunks in clusters.items():
            # Use first chunk in cluster as representative
            representative = cluster_chunks[0]
            similarity = _compute_token_overlap(chunk.content, representative.content)

            if similarity >= similarity_threshold:
                cluster_chunks.append(chunk)
                chunk_to_cluster[chunk.id] = cluster_id
                assigned = True
                break

        if not assigned:
            # Create new cluster
            clusters[next_cluster_id] = [chunk]
            chunk_to_cluster[chunk.id] = next_cluster_id
            next_cluster_id += 1

    return clusters


def detect_and_remove_duplicates(
    chunks: List[ContextChunk],
    similarity_threshold: float = 0.85,
) -> DeduplicationResult:
    """
    Remove semantically duplicate chunks from list.

    Strategy:
    - Compute pairwise similarity (token-based Jaccard)
    - Cluster chunks with similarity >= threshold
    - Keep highest-relevance chunk per cluster; discard others
    - Return deduplicated list preserving original order

    Args:
        chunks: List of ContextChunk objects
        similarity_threshold: Similarity cutoff for deduplication (0.0–1.0)

    Returns:
        DeduplicationResult with deduplicated chunks, removed count, and cluster count
    """
    if not chunks:
        return DeduplicationResult(
            deduplicated_chunks=[],
            removed_count=0,
            cluster_count=0,
        )

    # Cluster chunks
    clusters = _cluster_chunks(chunks, similarity_threshold)

    # Select best chunk per cluster
    best_per_cluster: Dict[int, ContextChunk] = {}
    for cluster_id, cluster_chunks in clusters.items():
        # Sort by relevance_score (descending), break ties by chunk.id (deterministic)
        best = max(cluster_chunks, key=lambda c: (c.relevance_score, c.id))
        best_per_cluster[cluster_id] = best

    # Build deduplicated list preserving original order
    deduplicated = []
    original_order = {chunk.id: i for i, chunk in enumerate(chunks)}

    for chunk in chunks:
        # Recompute cluster to maintain order
        cluster_id = None
        for cid, cluster_chunks in clusters.items():
            if any(c.id == chunk.id for c in cluster_chunks):
                cluster_id = cid
                break

        if cluster_id is not None and best_per_cluster[cluster_id].id == chunk.id:
            deduplicated.append(chunk)

    removed_count = len(chunks) - len(deduplicated)

    return DeduplicationResult(
        deduplicated_chunks=deduplicated,
        removed_count=removed_count,
        cluster_count=len(clusters),
    )
