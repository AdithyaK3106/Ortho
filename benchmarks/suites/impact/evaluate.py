"""Impact suite: precision/recall/F1 of predicted-impacted files vs cached
git-history ground truth, Blast Radius relative error, and Risk Score
Correlation, via adapter.analyze_impact().
"""

import time

from core.ground_truth import load_ground_truth
from core.metrics.correlation import spearman
from core.metrics.set_based import precision_recall_f1
from core.result_model import SuiteResult

SUITE_NAME = "impact"


def evaluate(adapter, dataset_item: dict, config) -> SuiteResult:
    name = dataset_item["name"]
    dataset_dir = dataset_item["dataset_dir"]
    repo_path = dataset_item["repo_path"]

    entries = load_ground_truth(dataset_dir, "impact")

    per_entry = []
    risk_scores = []
    actual_counts = []
    total_time = 0.0

    for entry in entries:
        changed_file = entry["changed_file"]
        actually_impacted = set(entry["actually_impacted"])

        t0 = time.perf_counter()
        result = adapter.analyze_impact(repo_path, changed_file)
        total_time += time.perf_counter() - t0

        predicted = set(result.impacted_files)
        scores = precision_recall_f1(predicted, actually_impacted)
        actual_count = len(actually_impacted)
        blast_radius_rel_error = (
            abs(result.blast_radius - actual_count) / actual_count
            if actual_count else (0.0 if result.blast_radius == 0 else 1.0)
        )

        per_entry.append({
            "changed_file": changed_file,
            "precision": scores["precision"], "recall": scores["recall"],
            "f1": scores["f1"],
            "predicted_blast_radius": result.blast_radius,
            "actual_blast_radius": actual_count,
            "blast_radius_rel_error": round(blast_radius_rel_error, 4),
            "risk_score": result.risk_score,
        })
        risk_scores.append(result.risk_score)
        actual_counts.append(float(actual_count))

    if per_entry:
        mean_precision = sum(e["precision"] for e in per_entry) / len(per_entry)
        mean_recall = sum(e["recall"] for e in per_entry) / len(per_entry)
        mean_f1 = sum(e["f1"] for e in per_entry) / len(per_entry)
        mean_blast_error = sum(e["blast_radius_rel_error"] for e in per_entry) / len(per_entry)
    else:
        mean_precision = mean_recall = mean_f1 = mean_blast_error = 0.0

    risk_correlation = spearman(risk_scores, actual_counts)

    metrics = {
        "impact_precision": round(mean_precision, 4),
        "impact_recall": round(mean_recall, 4),
        "impact_f1": round(mean_f1, 4),
        "blast_radius_mean_relative_error": round(mean_blast_error, 4),
        "risk_score_correlation": risk_correlation,
        "entries_evaluated": len(per_entry),
    }
    detail = {"per_entry": per_entry}

    return SuiteResult(
        suite=SUITE_NAME, dataset=name, metrics=metrics, detail=detail,
        timings={"analyze_impact_total": round(total_time, 3)}, status="SUCCESS",
    )
