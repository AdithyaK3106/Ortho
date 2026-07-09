"""Repository Intelligence suite: precision/recall/F1 for symbols, imports,
call graph vs ground truth, via adapter.scan_repository().
"""

import time

from core.ground_truth import load_ground_truth
from core.metrics.set_based import precision_recall_f1
from core.result_model import SuiteResult

SUITE_NAME = "repository"


def evaluate(adapter, dataset_item: dict, config) -> SuiteResult:
    name = dataset_item["name"]
    dataset_dir = dataset_item["dataset_dir"]
    repo_path = dataset_item["repo_path"]

    symbols_gt = set(load_ground_truth(dataset_dir, "symbols", suite="repository"))
    imports_gt = {tuple(pair)
                  for pair in load_ground_truth(dataset_dir, "imports", suite="repository")}
    callgraph_gt = {tuple(pair)
                    for pair in load_ground_truth(dataset_dir, "callgraph", suite="repository")}

    t0 = time.perf_counter()
    index = adapter.scan_repository(repo_path)
    elapsed = time.perf_counter() - t0

    symbols_pred = set(index.symbols)
    imports_pred = {tuple(pair) for pair in index.imports}
    calls_pred = {tuple(pair) for pair in index.calls}

    symbols_scores = precision_recall_f1(symbols_pred, symbols_gt)
    imports_scores = precision_recall_f1(imports_pred, imports_gt)
    calls_scores = precision_recall_f1(calls_pred, callgraph_gt)

    parse_success_rate = (index.files_scanned / index.files_total
                           if index.files_total else 0.0)
    repo_coverage = (index.files_scanned / index.files_total
                      if index.files_total else 0.0)

    metrics = {
        "symbols_precision": symbols_scores["precision"],
        "symbols_recall": symbols_scores["recall"],
        "symbols_f1": symbols_scores["f1"],
        "imports_precision": imports_scores["precision"],
        "imports_recall": imports_scores["recall"],
        "imports_f1": imports_scores["f1"],
        "callgraph_precision": calls_scores["precision"],
        "callgraph_recall": calls_scores["recall"],
        "callgraph_f1": calls_scores["f1"],
        "parse_success_rate": round(parse_success_rate, 4),
        "repository_coverage": round(repo_coverage, 4),
    }
    detail = {
        "symbols": symbols_scores,
        "imports": imports_scores,
        "callgraph": calls_scores,
        "parse_errors": index.parse_errors[:10],
    }

    return SuiteResult(
        suite=SUITE_NAME, dataset=name, metrics=metrics, detail=detail,
        timings={"scan_repository": round(elapsed, 3)}, status="SUCCESS",
    )
