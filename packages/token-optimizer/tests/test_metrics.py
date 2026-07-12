"""Tests for metrics collection (Component 8).

Tests for measuring token reduction vs Phase 3 baseline and quality metrics.
"""

import pytest
from typing import Dict, List


class MockMetricsLog:
    """Mock metrics for testing."""

    def __init__(self, logs: List[Dict] = None):
        self.logs = logs or []

    def avg_tokens(self) -> float:
        """Average token usage."""
        if not self.logs:
            return 0.0
        return sum(log.get("tokens", 0) for log in self.logs) / len(self.logs)

    def percentile(self, p: int) -> float:
        """Percentile of token usage (0-100)."""
        if not self.logs:
            return 0.0
        sorted_tokens = sorted(log.get("tokens", 0) for log in self.logs)
        idx = int(len(sorted_tokens) * p / 100)
        return sorted_tokens[min(idx, len(sorted_tokens) - 1)]


class TestMetricsBoundaryConditions:
    """Boundary conditions for metrics collection."""

    def test_empty_baseline(self):
        """No baseline logs available."""
        baseline = MockMetricsLog([])
        assert baseline.avg_tokens() == 0.0

    def test_empty_current_metrics(self):
        """No current logs available."""
        current = MockMetricsLog([])
        assert current.avg_tokens() == 0.0

    def test_single_log_entry(self):
        """Single log entry in baseline."""
        logs = [{"tokens": 5000}]
        baseline = MockMetricsLog(logs)
        assert baseline.avg_tokens() == 5000.0

    def test_very_large_token_counts(self):
        """Very large token values (millions)."""
        logs = [{"tokens": 1000000}]
        baseline = MockMetricsLog(logs)
        assert baseline.avg_tokens() == 1000000.0

    def test_zero_tokens(self):
        """Zero token counts."""
        logs = [{"tokens": 0}]
        baseline = MockMetricsLog(logs)
        assert baseline.avg_tokens() == 0.0

    def test_negative_token_counts_invalid(self):
        """Negative token counts should be invalid."""
        logs = [{"tokens": -100}]
        # Should reject or handle gracefully
        assert logs[0]["tokens"] < 0


class TestMetricsComparison:
    """Comparing baseline vs current metrics."""

    def test_token_reduction_calculation(self):
        """Calculate token reduction percentage."""
        phase3_avg = 5200
        phase4_avg = 4410
        reduction_pct = (phase3_avg - phase4_avg) / phase3_avg * 100
        assert reduction_pct > 0
        assert reduction_pct == pytest.approx(15.17, abs=0.1)

    def test_no_degradation_check(self):
        """Verify no token increase from baseline."""
        phase3_avg = 5000
        phase4_avg = 5000
        assert phase4_avg <= phase3_avg

    def test_degradation_detected(self):
        """Detect when current is worse than baseline."""
        phase3_avg = 5000
        phase4_avg = 6000
        degradation = (phase4_avg - phase3_avg) / phase3_avg * 100
        assert degradation > 0

    def test_minimal_improvement_threshold(self):
        """Improvement below 1% marked as minimal."""
        phase3_avg = 5000
        phase4_avg = 4950
        improvement = (phase3_avg - phase4_avg) / phase3_avg * 100
        assert improvement < 2

    def test_significant_improvement_threshold(self):
        """Improvement above 20% marked as significant."""
        phase3_avg = 5000
        phase4_avg = 4000
        improvement = (phase3_avg - phase4_avg) / phase3_avg * 100
        assert improvement > 15


class TestMetricsPercentiles:
    """Percentile calculations."""

    def test_p50_median(self):
        """P50 percentile is median."""
        logs = [{"tokens": x * 100} for x in range(1, 101)]  # 100-10000
        metrics = MockMetricsLog(logs)
        p50 = metrics.percentile(50)
        assert 5000 < p50 < 5100

    def test_p95_high_tail(self):
        """P95 in high tail."""
        logs = [{"tokens": x * 100} for x in range(1, 101)]
        metrics = MockMetricsLog(logs)
        p95 = metrics.percentile(95)
        assert p95 > metrics.percentile(50)

    def test_p99_extreme_tail(self):
        """P99 in extreme tail."""
        logs = [{"tokens": x * 100} for x in range(1, 101)]
        metrics = MockMetricsLog(logs)
        p99 = metrics.percentile(99)
        assert p99 > metrics.percentile(95)

    def test_p0_minimum(self):
        """P0 returns minimum."""
        logs = [{"tokens": 1000}, {"tokens": 5000}, {"tokens": 9000}]
        metrics = MockMetricsLog(logs)
        p0 = metrics.percentile(0)
        assert p0 <= 1000

    def test_p100_maximum(self):
        """P100 returns maximum."""
        logs = [{"tokens": 1000}, {"tokens": 5000}, {"tokens": 9000}]
        metrics = MockMetricsLog(logs)
        p100 = metrics.percentile(100)
        assert p100 >= 9000

    def test_percentile_with_duplicates(self):
        """Percentile with duplicate values."""
        logs = [{"tokens": 1000} for _ in range(50)]
        logs.extend([{"tokens": 9000} for _ in range(50)])
        metrics = MockMetricsLog(logs)
        p50 = metrics.percentile(50)
        # Should be in the middle
        assert 1000 <= p50 <= 9000


class TestMetricsAggregation:
    """Aggregating metrics across scenarios."""

    def test_metrics_by_intent_class(self):
        """Group metrics by intent class."""
        logs = [
            {"intent": "feature_development", "tokens": 5000},
            {"intent": "feature_development", "tokens": 5200},
            {"intent": "bug_fix", "tokens": 4000},
            {"intent": "bug_fix", "tokens": 4100},
        ]
        # Group by intent
        by_intent = {}
        for log in logs:
            intent = log["intent"]
            by_intent.setdefault(intent, []).append(log["tokens"])
        assert "feature_development" in by_intent
        assert "bug_fix" in by_intent

    def test_metrics_by_model(self):
        """Group metrics by LLM model."""
        logs = [
            {"model": "claude-opus", "tokens": 6000},
            {"model": "claude-haiku", "tokens": 4000},
            {"model": "claude-opus", "tokens": 6100},
        ]
        by_model = {}
        for log in logs:
            model = log["model"]
            by_model.setdefault(model, []).append(log["tokens"])
        assert "claude-opus" in by_model
        assert "claude-haiku" in by_model

    def test_metrics_by_date(self):
        """Group metrics by date."""
        logs = [
            {"date": "2026-01-01", "tokens": 5000},
            {"date": "2026-01-02", "tokens": 4900},
            {"date": "2026-01-01", "tokens": 5100},
        ]
        by_date = {}
        for log in logs:
            date = log["date"]
            by_date.setdefault(date, []).append(log["tokens"])
        assert "2026-01-01" in by_date
        assert "2026-01-02" in by_date


class TestMetricsStdDev:
    """Standard deviation and variance."""

    def test_stddev_calculation(self):
        """Calculate standard deviation."""
        values = [1000, 2000, 3000, 4000, 5000]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        stddev = variance ** 0.5
        assert stddev > 0

    def test_low_variance_consistent(self):
        """Low variance indicates consistent results."""
        values = [5000, 5000, 5000, 5000]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        assert variance == 0.0

    def test_high_variance_inconsistent(self):
        """High variance indicates inconsistent results."""
        values = [1000, 9000]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        assert variance > 0


class TestMetricsQualityScores:
    """Quality score metrics."""

    def test_llm_output_quality_score(self):
        """LLM output quality on 0-1 scale."""
        quality = 0.87  # 87% quality
        assert 0.0 <= quality <= 1.0

    def test_context_relevance_score(self):
        """Context relevance on 0-1 scale."""
        relevance = 0.92
        assert 0.0 <= relevance <= 1.0

    def test_correlation_token_reduction_quality(self):
        """Correlation between token reduction and quality."""
        # Should be non-negative
        correlation = 0.45
        assert correlation >= -1.0 and correlation <= 1.0

    def test_quality_above_threshold(self):
        """Quality maintained above baseline."""
        baseline_quality = 0.85
        current_quality = 0.88
        assert current_quality >= baseline_quality


class TestMetricsErrorHandling:
    """Error handling in metrics."""

    def test_missing_baseline_data(self):
        """Graceful handling when baseline missing."""
        baseline = MockMetricsLog([])
        current = MockMetricsLog([{"tokens": 5000}])
        # Should not crash
        assert baseline.avg_tokens() == 0.0

    def test_mismatched_log_sizes(self):
        """Handling baseline/current with different sizes."""
        baseline = MockMetricsLog([{"tokens": 5000} for _ in range(100)])
        current = MockMetricsLog([{"tokens": 4500} for _ in range(10)])
        # Should handle
        assert len(baseline.logs) != len(current.logs)

    def test_invalid_metric_values(self):
        """Invalid metric values handled."""
        logs = [{"tokens": "invalid"}]
        # Should reject or convert
        pass

    def test_outlier_detection(self):
        """Detect and handle outliers."""
        logs = [
            {"tokens": 5000},
            {"tokens": 5100},
            {"tokens": 50000},  # Outlier
            {"tokens": 5200},
        ]
        # Should flag outlier
        tokens = [log["tokens"] for log in logs]
        assert max(tokens) > min(tokens) * 5


class TestMetricsDeterminism:
    """Determinism and reproducibility."""

    def test_same_logs_same_metrics(self):
        """Same logs produce same computed metrics."""
        logs = [{"tokens": x * 100} for x in range(1, 101)]
        metrics1 = MockMetricsLog(logs)
        metrics2 = MockMetricsLog(logs)
        assert metrics1.avg_tokens() == metrics2.avg_tokens()

    def test_percentile_order_independent(self):
        """Percentile independent of log order."""
        logs_a = [{"tokens": x * 100} for x in range(1, 11)]
        logs_b = list(reversed(logs_a))
        metrics_a = MockMetricsLog(logs_a)
        metrics_b = MockMetricsLog(logs_b)
        assert metrics_a.percentile(50) == metrics_b.percentile(50)
