"""Retrieval suite: Recall@k, Precision@k, MRR, NDCG@10 against a hand-authored
question set, via adapter.retrieve().
"""

import time

from core.ground_truth import load_ground_truth
from core.metrics.ranking import mrr, ndcg_at_k, precision_at_k, recall_at_k
from core.result_model import SuiteResult

SUITE_NAME = "retrieval"
NDCG_K = 10


def _expected_ids(question: dict) -> set:
    """A hit counts as relevant if its id matches an expected file or symbol."""
    return set(question.get("expected_files", [])) | set(question.get("expected_symbols", []))


def evaluate(adapter, dataset_item: dict, config) -> SuiteResult:
    name = dataset_item["name"]
    dataset_dir = dataset_item["dataset_dir"]
    repo_path = dataset_item["repo_path"]

    # Ortho's retrieve() searches ContextHub artifacts, which must be populated
    # first (mirrors what assemble_context()'s production path does via
    # _ingest_analysis_artifacts in pipeline.py). Optional hasattr guard keeps
    # this suite runnable against any adapter that doesn't need/have this step.
    if hasattr(adapter, "ingest_analysis_artifacts"):
        adapter.ingest_analysis_artifacts(repo_path)

    questions = load_ground_truth(dataset_dir, "retrieval")

    per_question = []
    total_time = 0.0
    max_k = max(max(config.retrieval_k), NDCG_K)

    for q in questions:
        expected = _expected_ids(q)

        t0 = time.perf_counter()
        hits = adapter.retrieve(repo_path, q["question"], max_k)
        total_time += time.perf_counter() - t0

        entry = {"question": q["question"]}
        for k in config.retrieval_k:
            entry[f"recall_at_{k}"] = recall_at_k(hits, expected, k)
            entry[f"precision_at_{k}"] = precision_at_k(hits, expected, k)
        entry["mrr"] = mrr(hits, expected)
        entry["ndcg_at_10"] = ndcg_at_k(hits, expected, NDCG_K)
        per_question.append(entry)

    def mean(key):
        vals = [e[key] for e in per_question if key in e]
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    metrics = {"questions_evaluated": len(per_question), "mrr": mean("mrr"),
               "ndcg_at_10": mean("ndcg_at_10")}
    for k in config.retrieval_k:
        metrics[f"recall_at_{k}"] = mean(f"recall_at_{k}")
        metrics[f"precision_at_{k}"] = mean(f"precision_at_{k}")

    detail = {"per_question": per_question}

    return SuiteResult(
        suite=SUITE_NAME, dataset=name, metrics=metrics, detail=detail,
        timings={"retrieve_total": round(total_time, 3)}, status="SUCCESS",
    )
