"""Architecture suite: style/layer/subsystem accuracy vs ground truth, via
adapter.detect_architecture().
"""

import time

from core.ground_truth import load_ground_truth
from core.metrics.set_based import cluster_match, precision_recall_f1
from core.result_model import SuiteResult

SUITE_NAME = "architecture"


def _layer_edges_respected(layers_pred: dict[str, int], layer_edges_gt: list[list[str]]) -> float:
    """% of ground-truth-labeled layer edges (lower_file, higher_file) respected --
    i.e. predicted layer(lower_file) <= predicted layer(higher_file).
    Edges referencing a file with no predicted layer are skipped (can't judge).
    """
    if not layer_edges_gt:
        return 1.0
    judged = 0
    respected = 0
    for lower, higher in layer_edges_gt:
        if lower not in layers_pred or higher not in layers_pred:
            continue
        judged += 1
        if layers_pred[lower] <= layers_pred[higher]:
            respected += 1
    return round(respected / judged, 4) if judged else 1.0


def evaluate(adapter, dataset_item: dict, config) -> SuiteResult:
    name = dataset_item["name"]
    dataset_dir = dataset_item["dataset_dir"]
    repo_path = dataset_item["repo_path"]

    gt = load_ground_truth(dataset_dir, "architecture")
    style_gt = gt["style"]
    layers_gt: dict[str, int] = gt.get("layers", {})
    subsystems_gt = [set(cluster) for cluster in gt.get("subsystems", [])]
    layer_edges_gt = gt.get("layer_edges", [])

    t0 = time.perf_counter()
    arch = adapter.detect_architecture(repo_path)
    elapsed = time.perf_counter() - t0

    style_correct = 1.0 if arch.style == style_gt else 0.0

    layer_pred_set = {(f, n) for f, n in arch.layers.items() if f in layers_gt}
    layer_gt_set = {(f, n) for f, n in layers_gt.items()}
    layer_scores = precision_recall_f1(layer_pred_set, layer_gt_set)

    subsystem_scores = cluster_match(
        [set(c) for c in arch.subsystems], subsystems_gt)

    dependency_direction_accuracy = _layer_edges_respected(arch.layers, layer_edges_gt)

    metrics = {
        "architecture_style_accuracy": style_correct,
        "architecture_confidence": arch.confidence,
        "layer_precision": layer_scores["precision"],
        "layer_recall": layer_scores["recall"],
        "layer_f1": layer_scores["f1"],
        "subsystem_mean_jaccard": subsystem_scores["mean_jaccard"],
        "subsystem_matched": subsystem_scores["matched"],
        "subsystem_unmatched": subsystem_scores["unmatched"],
        "dependency_direction_accuracy": dependency_direction_accuracy,
    }
    detail = {
        "ground_truth_style": style_gt,
        "predicted_style": arch.style,
        "predicted_alternative": arch.alternative,
        "layer_scores": layer_scores,
        "subsystem_scores": subsystem_scores,
        "evidence": arch.evidence[:8],
    }

    return SuiteResult(
        suite=SUITE_NAME, dataset=name, metrics=metrics, detail=detail,
        timings={"detect_architecture": round(elapsed, 3)}, status="SUCCESS",
    )
