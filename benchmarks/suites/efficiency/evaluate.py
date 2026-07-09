"""Efficiency suite (Token + Performance): reuses existing timing/memory/context
metrics from the task-015 pipeline, via adapter.assemble_context() and
adapter.scan_repository()'s own timing. Measurement, not correctness -- no
ground truth required (Context Recall/Precision is covered by the retrieval
suite on the same corpus, not duplicated here).
"""

import time
import tracemalloc

from core.result_model import SuiteResult

SUITE_NAME = "efficiency"

DEFAULT_QUERY = "architecture overview subsystems dependency health technical debt"


def evaluate(adapter, dataset_item: dict, config) -> SuiteResult:
    name = dataset_item["name"]
    repo_path = dataset_item["repo_path"]
    query = dataset_item.get("manifest", {}).get("efficiency_query", DEFAULT_QUERY)

    timings = {}
    tracemalloc.start()
    try:
        t0 = time.perf_counter()
        adapter.scan_repository(repo_path)
        timings["scan_repository"] = round(time.perf_counter() - t0, 3)

        t0 = time.perf_counter()
        adapter.detect_architecture(repo_path)
        timings["detect_architecture"] = round(time.perf_counter() - t0, 3)

        if hasattr(adapter, "ingest_analysis_artifacts"):
            t0 = time.perf_counter()
            adapter.ingest_analysis_artifacts(repo_path)
            timings["ingest_analysis_artifacts"] = round(time.perf_counter() - t0, 3)

        t0 = time.perf_counter()
        ctx = adapter.assemble_context(repo_path, query, config.token_budget)
        timings["assemble_context"] = round(time.perf_counter() - t0, 3)

        _, peak = tracemalloc.get_traced_memory()
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()

    timings["total"] = round(sum(timings.values()), 3)

    raw_searched_tokens = ctx.chars_included / 4 if ctx.chars_included else 0.0
    compression_ratio = (round(raw_searched_tokens / ctx.tokens_used, 4)
                          if ctx.tokens_used else 0.0)

    metrics = {
        "context_tokens_used": ctx.tokens_used,
        "context_budget_fill_pct": ctx.budget_fill_pct,
        "context_compression_ratio": compression_ratio,
        "context_latency_ms": ctx.latency_ms,
        "context_chunks_total": ctx.chunks_total,
        "context_chunks_included": ctx.chunks_included,
        "peak_memory_mb": round(peak / (1024 * 1024), 2),
        "time_scan_repository_s": timings["scan_repository"],
        "time_detect_architecture_s": timings["detect_architecture"],
        "time_assemble_context_s": timings["assemble_context"],
        "time_total_s": timings["total"],
    }
    detail = {"budget_total": ctx.budget_total, "query": query}

    return SuiteResult(
        suite=SUITE_NAME, dataset=name, metrics=metrics, detail=detail,
        timings=timings, status="SUCCESS",
    )
