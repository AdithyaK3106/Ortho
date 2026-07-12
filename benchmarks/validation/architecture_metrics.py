"""Architecture detection metrics for 8-repository benchmark.

Measures style accuracy, confidence calibration, layer detection,
and subsystem clustering independently of detector implementation.
"""

from dataclasses import dataclass
from typing import Optional, Any
from collections import defaultdict


@dataclass
class ArchitectureMetrics:
    """Comprehensive metrics for architecture detection on one repository."""

    # Style prediction
    style_correct: bool
    predicted_style: str
    ground_truth_style: str
    predicted_confidence: float

    # Calibration: how honest is the confidence?
    # If correct: expected_accuracy = 1.0
    # If wrong: expected_accuracy = 0.0
    calibration_error: float

    # Layer detection (if applicable)
    layer_precision: Optional[float] = None
    layer_recall: Optional[float] = None
    layer_f1: Optional[float] = None

    # Subsystem detection
    subsystem_mean_jaccard: float = 0.0
    subsystem_matched: int = 0
    subsystem_unmatched: int = 0

    # Raw evidence from detector
    evidence: list = None


def compute_style_accuracy(predictions: list[str], ground_truth: list[str]) -> float:
    """Proportion of correct style predictions.

    Args:
        predictions: List of predicted styles (one per repo)
        ground_truth: List of ground truth styles

    Returns:
        Accuracy in range [0.0, 1.0]
    """
    if not predictions:
        return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    return correct / len(predictions)


def compute_confusion_matrix(
    predictions: list[str],
    ground_truth: list[str],
    styles: list[str]
) -> dict[str, dict[str, int]]:
    """Build N×N confusion matrix for style prediction.

    Args:
        predictions: Predicted styles
        ground_truth: Ground truth styles
        styles: All possible style labels

    Returns:
        Dict mapping {ground_truth: {predicted: count}}
    """
    matrix = {gt: {p: 0 for p in styles} for gt in styles}
    for pred, true in zip(predictions, ground_truth):
        matrix[true][pred] += 1
    return matrix


def compute_calibration_error(
    predictions: list[dict],
    bin_edges: list[float] = None
) -> tuple[float, dict]:
    """Expected Calibration Error (ECE) across all repositories.

    Bins predictions by confidence and compares predicted confidence
    to actual accuracy within each bin.

    Args:
        predictions: List of {confidence, is_correct} dicts
        bin_edges: Bin boundaries (default: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    Returns:
        (ece: float, analysis: dict with per-bin breakdown)
    """
    if not predictions:
        return 0.0, {}

    if bin_edges is None:
        bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    bins = defaultdict(lambda: {"confidences": [], "correct": []})

    for pred in predictions:
        conf = pred["confidence"]
        is_correct = pred["is_correct"]

        # Find bin for this confidence
        for i in range(len(bin_edges) - 1):
            if bin_edges[i] <= conf < bin_edges[i + 1]:
                bin_label = f"[{bin_edges[i]:.1f}, {bin_edges[i+1]:.1f})"
                bins[bin_label]["confidences"].append(conf)
                bins[bin_label]["correct"].append(is_correct)
                break
        else:
            # conf == 1.0, goes in last bin
            bin_label = f"[{bin_edges[-2]:.1f}, {bin_edges[-1]:.1f}]"
            bins[bin_label]["confidences"].append(conf)
            bins[bin_label]["correct"].append(is_correct)

    # Compute ECE
    total_samples = len(predictions)
    ece = 0.0
    analysis = {}

    for bin_label in sorted(bins.keys()):
        bin_data = bins[bin_label]
        if not bin_data["confidences"]:
            continue

        bin_size = len(bin_data["confidences"])
        bin_confidence = sum(bin_data["confidences"]) / bin_size
        bin_accuracy = sum(bin_data["correct"]) / bin_size

        bin_error = abs(bin_confidence - bin_accuracy)
        bin_weight = bin_size / total_samples

        ece += bin_weight * bin_error

        analysis[bin_label] = {
            "size": bin_size,
            "avg_confidence": round(bin_confidence, 3),
            "accuracy": round(bin_accuracy, 3),
            "error": round(bin_error, 3),
            "weight": round(bin_weight, 3),
        }

    return round(ece, 3), analysis


def compute_layer_metrics(
    predicted_files_by_layer: dict[int, set[str]],
    ground_truth_files_by_layer: dict[int, set[str]],
) -> dict[str, float]:
    """Compute precision, recall, F1 for layer detection.

    For layered architectures, check if detector correctly partitions
    files into layers.

    Args:
        predicted_files_by_layer: {layer_num: set(file_ids)}
        ground_truth_files_by_layer: {layer_num: set(file_ids)}

    Returns:
        {precision, recall, f1}
    """
    # Flatten to sets of all files
    all_pred_files = set().union(*predicted_files_by_layer.values())
    all_true_files = set().union(*ground_truth_files_by_layer.values())

    if not all_true_files:
        # No ground truth layers → metrics undefined
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    # Precision: % of predicted layer assignments that are correct
    # Correct = file assigned to same layer in both
    correct = 0
    for layer_num, pred_files in predicted_files_by_layer.items():
        for true_layer, true_files in ground_truth_files_by_layer.items():
            if layer_num == true_layer:
                correct += len(pred_files & true_files)

    precision = correct / len(all_pred_files) if all_pred_files else 0.0

    # Recall: % of ground truth layer assignments matched by predictions
    recall = correct / len(all_true_files) if all_true_files else 0.0

    # F1
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def compute_subsystem_jaccard(
    predicted_subsystems: list[set[str]],
    ground_truth_subsystems: list[set[str]],
) -> tuple[float, int, int]:
    """Compute mean Jaccard similarity between predicted and ground truth subsystems.

    Uses greedy matching: for each ground truth subsystem, find best-matching
    predicted subsystem and compute Jaccard.

    Args:
        predicted_subsystems: List of sets (files in each predicted subsystem)
        ground_truth_subsystems: List of sets (files in each ground truth subsystem)

    Returns:
        (mean_jaccard, matched_count, unmatched_count)
    """
    if not ground_truth_subsystems:
        return 0.0, 0, 0

    matched = 0
    total_jaccard = 0.0

    for gt_subsystem in ground_truth_subsystems:
        # Find best-matching predicted subsystem
        best_jaccard = 0.0
        best_idx = -1

        for pred_idx, pred_subsystem in enumerate(predicted_subsystems):
            if len(pred_subsystem) == 0 or len(gt_subsystem) == 0:
                jaccard = 0.0
            else:
                intersection = len(pred_subsystem & gt_subsystem)
                union = len(pred_subsystem | gt_subsystem)
                jaccard = intersection / union if union > 0 else 0.0

            if jaccard > best_jaccard:
                best_jaccard = jaccard
                best_idx = pred_idx

        total_jaccard += best_jaccard
        if best_jaccard > 0.0:
            matched += 1

    mean_jaccard = total_jaccard / len(ground_truth_subsystems)
    unmatched = len(ground_truth_subsystems) - matched

    return round(mean_jaccard, 4), matched, unmatched


def build_per_repo_report(
    repo_name: str,
    ground_truth: dict,
    detector_result: dict,
    metrics: ArchitectureMetrics,
) -> dict[str, Any]:
    """Generate comprehensive per-repository report.

    Args:
        repo_name: Repository identifier
        ground_truth: Ground truth metadata (from ground-truth.json)
        detector_result: Raw detector output
        metrics: Computed metrics

    Returns:
        Report dict with all details
    """
    return {
        "repository": repo_name,
        "ground_truth": {
            "style": ground_truth.get("style"),
            "confidence": ground_truth.get("confidence"),
            "rationale": ground_truth.get("rationale"),
            "subsystem_count": len(ground_truth.get("subsystems", [])),
        },
        "detector_results": {
            "predicted_style": metrics.predicted_style,
            "confidence": metrics.predicted_confidence,
            "evidence": metrics.evidence or [],
        },
        "accuracy": {
            "style_correct": metrics.style_correct,
            "calibration_error": metrics.calibration_error,
        },
        "layer_detection": {
            "precision": metrics.layer_precision,
            "recall": metrics.layer_recall,
            "f1": metrics.layer_f1,
        } if metrics.layer_precision is not None else None,
        "subsystem_detection": {
            "mean_jaccard": metrics.subsystem_mean_jaccard,
            "matched": metrics.subsystem_matched,
            "unmatched": metrics.subsystem_unmatched,
        },
    }


def build_aggregate_report(per_repo_reports: list[dict]) -> dict[str, Any]:
    """Generate aggregate report across all repositories.

    Args:
        per_repo_reports: List of per-repository report dicts

    Returns:
        Summary report with metrics and analysis
    """
    if not per_repo_reports:
        return {}

    # Extract metrics
    style_correct = [r["accuracy"]["style_correct"] for r in per_repo_reports]
    calibration_errors = [r["accuracy"]["calibration_error"] for r in per_repo_reports]
    subsystem_jaccards = [
        r["subsystem_detection"]["mean_jaccard"]
        for r in per_repo_reports
        if r["subsystem_detection"]["mean_jaccard"] is not None
    ]
    layer_f1s = [
        r["layer_detection"]["f1"]
        for r in per_repo_reports
        if r["layer_detection"] is not None and r["layer_detection"]["f1"] is not None
    ]

    # Aggregate
    return {
        "summary": {
            "total_repositories": len(per_repo_reports),
            "style_accuracy": round(sum(style_correct) / len(style_correct), 3)
            if style_correct else 0.0,
            "mean_calibration_error": round(
                sum(calibration_errors) / len(calibration_errors), 3
            ) if calibration_errors else 0.0,
            "mean_subsystem_jaccard": round(
                sum(subsystem_jaccards) / len(subsystem_jaccards), 3
            ) if subsystem_jaccards else 0.0,
            "mean_layer_f1": round(
                sum(layer_f1s) / len(layer_f1s), 3
            ) if layer_f1s else 0.0,
        },
        "per_repository": per_repo_reports,
    }
