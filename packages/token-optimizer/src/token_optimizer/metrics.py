"""Metrics collection and analysis for Phase 4 token reduction."""

from typing import Dict, List, Optional
import statistics


class MetricsCollector:
    """Compute token reduction metrics."""

    @staticmethod
    def compute_reduction(
        baseline_tokens: List[int],
        current_tokens: List[int],
    ) -> Dict[str, float]:
        """
        Compare Phase 3 vs Phase 4 token usage.

        Args:
            baseline_tokens: List of token counts from Phase 3
            current_tokens: List of token counts from Phase 4

        Returns:
            Metrics dict with reduction_pct, avg_phase3, avg_phase4, p50, p95
        """
        if not baseline_tokens or not current_tokens:
            return {
                "reduction_pct": 0.0,
                "avg_phase3": 0.0,
                "avg_phase4": 0.0,
                "p50_phase3": 0.0,
                "p50_phase4": 0.0,
                "p95_phase3": 0.0,
                "p95_phase4": 0.0,
                "baseline_count": len(baseline_tokens),
                "current_count": len(current_tokens),
            }

        avg_phase3 = statistics.mean(baseline_tokens)
        avg_phase4 = statistics.mean(current_tokens)

        # Calculate percentiles
        sorted_base = sorted(baseline_tokens)
        sorted_curr = sorted(current_tokens)

        p95_idx = int(len(sorted_base) * 0.95)

        # statistics.median interpolates on even-length inputs; the previous
        # sorted[n//2] indexing returned the upper-middle value, not the median.
        p50_phase3 = statistics.median(sorted_base)
        p50_phase4 = statistics.median(sorted_curr)

        p95_phase3 = sorted_base[min(p95_idx, len(sorted_base) - 1)]
        p95_phase4 = sorted_curr[min(p95_idx, len(sorted_curr) - 1)]

        # Calculate reduction percentage
        reduction_pct = 100.0 * (avg_phase3 - avg_phase4) / avg_phase3 if avg_phase3 > 0 else 0.0

        return {
            "reduction_pct": round(reduction_pct, 2),
            "avg_phase3": round(avg_phase3, 1),
            "avg_phase4": round(avg_phase4, 1),
            "p50_phase3": p50_phase3,
            "p50_phase4": p50_phase4,
            "p95_phase3": p95_phase3,
            "p95_phase4": p95_phase4,
            "baseline_count": len(baseline_tokens),
            "current_count": len(current_tokens),
        }

    @staticmethod
    def compute_by_intent_class(
        baseline_logs: List[Dict],
        current_logs: List[Dict],
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute reduction per intent class.

        Args:
            baseline_logs: Phase 3 log entries
            current_logs: Phase 4 log entries

        Returns:
            Dict mapping intent_class → metrics
        """
        # Group by intent class
        baseline_by_class = {}
        for entry in baseline_logs:
            cls = entry.get("intent_class", "unknown")
            if cls not in baseline_by_class:
                baseline_by_class[cls] = []
            baseline_by_class[cls].append(entry.get("tokens_used", 0))

        current_by_class = {}
        for entry in current_logs:
            cls = entry.get("intent_class", "unknown")
            if cls not in current_by_class:
                current_by_class[cls] = []
            current_by_class[cls].append(entry.get("tokens_used", 0))

        # Compute metrics per class
        results = {}
        for cls in set(list(baseline_by_class.keys()) + list(current_by_class.keys())):
            base = baseline_by_class.get(cls, [0])
            curr = current_by_class.get(cls, [0])
            results[cls] = MetricsCollector.compute_reduction(base, curr)

        return results
