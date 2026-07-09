"""Precision/recall/F1 and cluster-matching metrics over sets."""


def precision_recall_f1(predicted: set, expected: set) -> dict:
    """Standard set-based precision/recall/F1.

    Edge cases: both empty -> precision=recall=f1=1.0 (nothing to find, found
    nothing -- vacuously correct). predicted empty, expected non-empty ->
    precision=1.0 (no false positives), recall=0.0, f1=0.0. expected empty,
    predicted non-empty -> precision=0.0, recall=1.0 (nothing to miss), f1=0.0.
    """
    predicted = set(predicted)
    expected = set(expected)

    if not predicted and not expected:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0,
                "correct": 0, "missed": 0, "extra": 0}

    correct = predicted & expected
    missed = expected - predicted
    extra = predicted - expected

    precision = len(correct) / len(predicted) if predicted else 1.0
    recall = len(correct) / len(expected) if expected else 1.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "correct": len(correct),
        "missed": len(missed),
        "extra": len(extra),
    }


def cluster_match(predicted_clusters: list[set], expected_clusters: list[set]) -> dict:
    """Best-overlap pairing between predicted and expected clusters (e.g. subsystems).

    Each expected cluster is greedily paired with the predicted cluster that
    maximizes Jaccard overlap (deterministic: ties broken by predicted cluster's
    sorted-member tuple). Reports mean best-Jaccard across expected clusters,
    plus how many expected clusters found no predicted match at all (overlap 0).
    """
    predicted_clusters = [set(c) for c in predicted_clusters]
    expected_clusters = [set(c) for c in expected_clusters]

    if not expected_clusters:
        return {"mean_jaccard": 1.0 if not predicted_clusters else 0.0,
                "matched": 0, "unmatched": 0, "pairs": []}

    def jaccard(a: set, b: set) -> float:
        if not a and not b:
            return 1.0
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    pairs = []
    unmatched = 0
    total = 0.0
    for exp in expected_clusters:
        best_score = -1.0
        best_idx = None
        for idx, pred in enumerate(predicted_clusters):
            score = jaccard(pred, exp)
            key = (score, tuple(sorted(pred)))
            best_key = (best_score, tuple(sorted(predicted_clusters[best_idx]))) if best_idx is not None else (-1.0, ())
            if best_idx is None or key > best_key:
                best_score, best_idx = score, idx
        total += max(best_score, 0.0)
        if best_score <= 0.0:
            unmatched += 1
        pairs.append({"expected_size": len(exp),
                       "predicted_index": best_idx,
                       "jaccard": round(max(best_score, 0.0), 4)})

    return {
        "mean_jaccard": round(total / len(expected_clusters), 4),
        "matched": len(expected_clusters) - unmatched,
        "unmatched": unmatched,
        "pairs": pairs,
    }
