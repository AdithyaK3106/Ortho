"""Ranking metrics: Recall@k, Precision@k, MRR, NDCG@k, over ranked hit lists.

`hits` is any ordered sequence of items where each item has an `.id` (or is a
plain string id) usable to test membership in `expected_ids`. Suites pass in
`list[RetrievalHit]`-like objects or bare id strings.
"""

import math


def _hit_id(hit):
    return hit.id if hasattr(hit, "id") else hit


def recall_at_k(hits: list, expected_ids: set, k: int) -> float:
    """Fraction of expected_ids present in the top-k hits."""
    expected_ids = set(expected_ids)
    if not expected_ids:
        return 1.0
    top_k_ids = {_hit_id(h) for h in hits[:k]}
    return round(len(top_k_ids & expected_ids) / len(expected_ids), 4)


def precision_at_k(hits: list, expected_ids: set, k: int) -> float:
    """Fraction of the top-k hits that are relevant (in expected_ids)."""
    if k <= 0:
        return 0.0
    expected_ids = set(expected_ids)
    top_k = hits[:k]
    if not top_k:
        return 0.0
    relevant = sum(1 for h in top_k if _hit_id(h) in expected_ids)
    return round(relevant / len(top_k), 4)


def mrr(hits: list, expected_ids: set) -> float:
    """Mean Reciprocal Rank: 1/rank of the first relevant hit, 0 if none found."""
    expected_ids = set(expected_ids)
    for rank, h in enumerate(hits, start=1):
        if _hit_id(h) in expected_ids:
            return round(1.0 / rank, 4)
    return 0.0


def ndcg_at_k(hits: list, expected_ids: set, k: int) -> float:
    """Normalized Discounted Cumulative Gain at k with binary relevance.

    DCG = sum(rel_i / log2(i+1)) for i=1..k (1-indexed rank).
    IDCG = DCG of the ideal ranking (all relevant items first).
    Returns 0.0 if there is nothing relevant to find (empty expected_ids) and
    the hit list is also empty; 1.0 if expected_ids is empty (nothing to rank,
    vacuously perfect) matching the precision_recall_f1 convention.
    """
    expected_ids = set(expected_ids)
    if not expected_ids:
        return 1.0

    top_k = hits[:k]
    dcg = sum(
        (1.0 if _hit_id(h) in expected_ids else 0.0) / math.log2(i + 1)
        for i, h in enumerate(top_k, start=1)
    )
    ideal_relevant_count = min(len(expected_ids), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_relevant_count + 1))
    if idcg == 0.0:
        return 0.0
    return round(dcg / idcg, 4)
