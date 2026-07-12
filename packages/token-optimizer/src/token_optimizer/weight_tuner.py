"""Auto-tuning of reranker weights from quality logs."""

from typing import Dict, List, Tuple
import statistics


class WeightTuner:
    """Auto-tune reranker intent boost weights."""

    @staticmethod
    def compute_correlation(values_x: List[float], values_y: List[float]) -> float:
        """
        Compute Pearson correlation coefficient.

        Args:
            values_x: First list of values
            values_y: Second list of values

        Returns:
            Correlation coefficient in [-1, 1]
        """
        if len(values_x) < 2 or len(values_y) < 2:
            return 0.0

        if len(values_x) != len(values_y):
            return 0.0

        mean_x = statistics.mean(values_x)
        mean_y = statistics.mean(values_y)

        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(values_x, values_y))
        denom_x = statistics.stdev(values_x) if len(values_x) > 1 else 1.0
        denom_y = statistics.stdev(values_y) if len(values_y) > 1 else 1.0

        if denom_x == 0 or denom_y == 0:
            return 0.0

        return numerator / (denom_x * denom_y * len(values_x))

    @staticmethod
    def auto_tune(
        logs: List[Dict],
        baseline_weights: Dict[str, Dict[str, float]],
        target_metric: str = "llm_output_tokens",
        correlation_threshold: float = 0.7,
    ) -> Dict[str, Dict[str, float]]:
        """
        Auto-tune reranker weights from logs.

        Strategy:
        - Group logs by intent_class
        - Compute correlation: rerank_factor vs target_metric
        - If correlation > threshold, increase weight by 10%
        - If correlation < -threshold, decrease weight by 10%
        - Bounded by [0.5, 2.0] to prevent wild swings

        Args:
            logs: Parsed quality logs
            baseline_weights: Current weights to tune
            target_metric: Metric to optimize (llm_output_tokens, etc.)
            correlation_threshold: Min |correlation| to trigger tune

        Returns:
            Updated weights dict
        """
        if not logs:
            return baseline_weights

        # Group by intent class
        logs_by_class = {}
        for log in logs:
            cls = log.get("intent_class", "unknown")
            if cls not in logs_by_class:
                logs_by_class[cls] = []
            logs_by_class[cls].append(log)

        # Tune weights per class
        tuned = {}
        for cls_name, cls_weights in baseline_weights.items():
            if cls_name not in logs_by_class:
                tuned[cls_name] = cls_weights
                continue

            cls_logs = logs_by_class[cls_name]
            rerank_factors = [log.get("rerank_factor", 1.0) for log in cls_logs]
            metrics = [log.get(target_metric, 0) for log in cls_logs]

            correlation = WeightTuner.compute_correlation(rerank_factors, metrics)

            tuned_class_weights = {}
            for keyword, weight in cls_weights.items():
                if abs(correlation) > correlation_threshold:
                    if correlation > 0:
                        # Positive correlation: increase weight
                        new_weight = weight * 1.1
                    else:
                        # Negative correlation: decrease weight
                        new_weight = weight * 0.9
                else:
                    # No significant correlation: keep weight
                    new_weight = weight

                # Bound weight to [0.5, 2.0]
                tuned_class_weights[keyword] = max(0.5, min(2.0, new_weight))

            tuned[cls_name] = tuned_class_weights

        return tuned

    @staticmethod
    def report_tuning_deltas(
        baseline_weights: Dict[str, Dict[str, float]],
        tuned_weights: Dict[str, Dict[str, float]],
    ) -> Dict[str, float]:
        """
        Report changes made during tuning.

        Args:
            baseline_weights: Original weights
            tuned_weights: Updated weights

        Returns:
            Dict of changes per weight
        """
        deltas = {}
        for cls_name in baseline_weights:
            if cls_name not in tuned_weights:
                continue

            for keyword in baseline_weights[cls_name]:
                key = f"{cls_name}:{keyword}"
                baseline = baseline_weights[cls_name][keyword]
                tuned = tuned_weights[cls_name].get(keyword, baseline)
                delta = tuned - baseline

                if delta != 0:
                    deltas[key] = round(delta, 3)

        return deltas
