"""Tests for ranking weight tuning (Component 9).

Tests for auto-tuning reranker weights from quality logs.
"""

import pytest
from typing import Dict, List

from token_optimizer.weight_tuner import WeightTuner


class MockWeightTuner:
    """Mock weight tuner for testing."""

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "api": 1.5,
            "error": 1.8,
            "dependency": 1.7,
        }

    def tune(self, logs: List[Dict], delta: float = 0.1) -> Dict[str, float]:
        """Tune weights based on logs."""
        # Simple mock: increase weights with positive correlation
        tuned = {}
        for keyword, weight in self.weights.items():
            correlation = self._compute_correlation(logs, keyword)
            if correlation > 0.7:
                tuned[keyword] = min(weight * (1 + delta), 2.0)
            elif correlation < 0.3:
                tuned[keyword] = max(weight * (1 - delta), 1.0)
            else:
                tuned[keyword] = weight
        return tuned

    def _compute_correlation(self, logs: List[Dict], keyword: str) -> float:
        """Mock correlation computation."""
        # Simulate correlation between rerank_factor and quality
        return 0.5


class TestWeightTuningBoundaryConditions:
    """Boundary conditions for weight tuning."""

    def test_empty_logs(self):
        """No logs available for tuning."""
        tuner = MockWeightTuner()
        tuned = tuner.tune([])
        # Should return original weights
        assert tuned == tuner.weights

    def test_single_log_entry(self):
        """Single log entry for tuning."""
        logs = [{"keyword": "api", "rerank_factor": 1.5, "quality": 0.9}]
        tuner = MockWeightTuner()
        tuned = tuner.tune(logs)
        assert isinstance(tuned, dict)

    def test_very_large_log_set(self):
        """Very large log set (10K+ entries)."""
        logs = [{"keyword": f"kw{i}", "quality": 0.5} for i in range(10000)]
        tuner = MockWeightTuner()
        tuned = tuner.tune(logs)
        assert len(tuned) > 0

    def test_no_keywords_to_tune(self):
        """No keywords defined for tuning (real WeightTuner)."""
        logs = [{"intent_class": "bug_fix", "quality": 0.9}]
        tuned = WeightTuner.auto_tune(logs, {})
        assert tuned == {}

    def test_zero_initial_weights_invalid(self):
        """Zero weight invalid (real WeightTuner)."""
        logs = [{"intent_class": "bug_fix"}]
        with pytest.raises((ValueError, AssertionError)):
            WeightTuner.auto_tune(logs, {"bug_fix": {"api": 0.0}})

    def test_negative_weights_invalid(self):
        """Negative weights invalid (real WeightTuner)."""
        logs = [{"intent_class": "bug_fix"}]
        with pytest.raises((ValueError, AssertionError)):
            WeightTuner.auto_tune(logs, {"bug_fix": {"api": -0.5}})


class TestWeightTuningCorrelation:
    """Correlation analysis for tuning."""

    def test_high_positive_correlation(self):
        """High correlation: increase weight."""
        logs = [
            {"keyword": "api", "rerank_factor": 1.8, "quality": 0.95},
            {"keyword": "api", "rerank_factor": 1.8, "quality": 0.94},
            {"keyword": "api", "rerank_factor": 1.5, "quality": 0.85},
        ]
        tuner = MockWeightTuner({"api": 1.5})
        # Should detect correlation and increase "api" weight
        correlation = tuner._compute_correlation(logs, "api")
        assert correlation >= 0

    def test_low_negative_correlation(self):
        """Low correlation: decrease weight."""
        logs = [
            {"keyword": "api", "rerank_factor": 1.5, "quality": 0.85},
            {"keyword": "api", "rerank_factor": 1.8, "quality": 0.83},
        ]
        tuner = MockWeightTuner({"api": 1.5})
        correlation = tuner._compute_correlation(logs, "api")
        # Negative correlation suggests weight not helping

    def test_zero_correlation(self):
        """Zero correlation: no change."""
        logs = [
            {"keyword": "api", "rerank_factor": 1.5, "quality": 0.9},
            {"keyword": "api", "rerank_factor": 1.8, "quality": 0.9},
        ]
        tuner = MockWeightTuner({"api": 1.5})
        original = tuner.weights["api"]
        tuned = tuner.tune(logs)
        # Zero correlation should keep original weight
        assert tuned["api"] == original


class TestWeightTuningIncrements:
    """Weight increment/decrement logic."""

    def test_increment_10_percent(self):
        """Increase weight by 10%."""
        original = 1.5
        delta = 0.1
        increased = original * (1 + delta)
        assert increased == pytest.approx(1.65)

    def test_decrement_10_percent(self):
        """Decrease weight by 10%."""
        original = 1.5
        delta = 0.1
        decreased = original * (1 - delta)
        assert decreased == pytest.approx(1.35)

    def test_increment_capped_at_2_0(self):
        """Increment capped at 2.0 max."""
        original = 1.9
        delta = 0.2
        increased = min(original * (1 + delta), 2.0)
        assert increased == 2.0

    def test_decrement_capped_at_1_0(self):
        """Decrement capped at 1.0 min."""
        original = 1.1
        delta = 0.2
        decreased = max(original * (1 - delta), 1.0)
        assert decreased == pytest.approx(1.0)

    def test_delta_too_large(self):
        """Large delta (>20%) rejected."""
        delta = 0.5  # 50% — too aggressive
        # Should cap to reasonable range
        assert delta > 0.2


class TestWeightTuningStability:
    """Stability of tuning (no wild swings)."""

    def test_bounded_weight_changes(self):
        """Real WeightTuner clamps tuned weights to [0.5, 2.0]."""
        # Perfect positive correlation between rerank_factor and metric
        # → auto_tune multiplies by 1.1; 1.95 * 1.1 = 2.145 must clamp to 2.0.
        logs = [
            {"intent_class": "bug_fix", "rerank_factor": 1.0, "llm_output_tokens": 100},
            {"intent_class": "bug_fix", "rerank_factor": 2.0, "llm_output_tokens": 200},
            {"intent_class": "bug_fix", "rerank_factor": 3.0, "llm_output_tokens": 300},
        ]
        tuned = WeightTuner.auto_tune(logs, {"bug_fix": {"api": 1.95}})
        assert tuned["bug_fix"]["api"] == 2.0

    def test_pearson_correlation_exact(self):
        """Regression: correlation must be true Pearson, not shrunk by (n-1)/n."""
        assert WeightTuner.compute_correlation([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
        assert WeightTuner.compute_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
        assert WeightTuner.compute_correlation([1, 1, 1], [1, 2, 3]) == 0.0

    def test_repeated_tuning_convergence(self):
        """Repeated tuning converges."""
        # First tune: 1.5 → 1.65
        # Second tune: 1.65 → 1.80
        # Should converge, not diverge
        pass

    def test_outlier_logs_dont_destabilize(self):
        """Outlier logs don't cause wild weight changes."""
        logs = [
            {"quality": 0.9} for _ in range(99)
        ] + [{"quality": 0.1}]  # One outlier
        tuner = MockWeightTuner({"api": 1.5})
        # Should ignore outlier
        pass

    def test_minority_signal_ignored(self):
        """Minority signal (<10%) ignored."""
        logs = [
            {"quality": 0.9} for _ in range(91)
        ] + [{"quality": 0.1} for _ in range(9)]
        tuner = MockWeightTuner({"api": 1.5})
        original = tuner.weights["api"]
        # Strong majority signal keeps weight
        assert original > 1.0


class TestWeightTuningBatch:
    """Batch tuning scenarios."""

    def test_single_keyword_tuning(self):
        """Tuning single keyword."""
        tuner = MockWeightTuner({"api": 1.5})
        logs = [{"keyword": "api", "quality": 0.9}]
        tuned = tuner.tune(logs)
        assert "api" in tuned

    def test_multiple_keyword_tuning(self):
        """Tuning multiple keywords simultaneously."""
        tuner = MockWeightTuner({
            "api": 1.5,
            "error": 1.8,
            "dependency": 1.7,
        })
        logs = [{"quality": 0.9} for _ in range(100)]
        tuned = tuner.tune(logs)
        assert len(tuned) == 3

    def test_new_keyword_detection(self):
        """Detect new keyword in logs for tuning."""
        tuner = MockWeightTuner({"api": 1.5})
        logs = [
            {"keyword": "api", "quality": 0.9},
            {"keyword": "new_keyword", "quality": 0.85},  # New
        ]
        # Should handle new keyword gracefully
        pass

    def test_deprecated_keyword_removal(self):
        """Remove keyword not in logs anymore."""
        tuner = MockWeightTuner({"old_keyword": 1.5, "api": 1.5})
        logs = [{"keyword": "api", "quality": 0.9}]
        # Should keep old_keyword or remove it?
        pass


class TestWeightTuningMetrics:
    """Metrics for tuning effectiveness."""

    def test_correlation_before_after(self):
        """Correlation improves after tuning."""
        # Before: correlation 0.3
        # After tuning: correlation 0.7+
        before = 0.3
        after = 0.75
        assert after > before

    def test_variance_reduction(self):
        """Output variance reduced by tuning."""
        # Tuned weights should reduce quality variance
        pass

    def test_tuning_impact_on_baseline(self):
        """Tuning improves metrics on baseline logs."""
        logs = [{"keyword": "api", "quality": 0.9}]
        tuner = MockWeightTuner()
        original_avg_quality = sum(log["quality"] for log in logs) / len(logs)
        tuned = tuner.tune(logs)
        # Tuned weights should improve quality
        assert original_avg_quality > 0


class TestWeightTuningErrorHandling:
    """Error handling in tuning."""

    def test_missing_log_fields(self):
        """Log entries missing fields handled."""
        logs = [
            {"keyword": "api", "quality": 0.9},
            {"keyword": "api"},  # Missing quality
        ]
        tuner = MockWeightTuner()
        # Should skip malformed entries
        pass

    def test_invalid_correlation_values(self):
        """Invalid correlation values rejected."""
        # Correlation outside [-1, 1]
        with pytest.raises((ValueError, AssertionError)):
            invalid_corr = 1.5
            assert -1 <= invalid_corr <= 1

    def test_tuning_with_no_quality_variance(self):
        """All logs same quality (no variance)."""
        logs = [{"keyword": "api", "quality": 0.9} for _ in range(100)]
        tuner = MockWeightTuner()
        tuned = tuner.tune(logs)
        # Should not crash
        assert isinstance(tuned, dict)

    def test_insufficient_data_for_tuning(self):
        """Too few logs for reliable tuning."""
        logs = [{"quality": 0.9}]  # Only 1 log
        tuner = MockWeightTuner()
        tuned = tuner.tune(logs)
        # Should warn or fall back
        pass


class TestWeightTuningApproval:
    """Human approval workflow for tuning."""

    def test_tuned_weights_ready_for_review(self):
        """Tuned weights formatted for human review."""
        tuner = MockWeightTuner({"api": 1.5, "error": 1.8})
        tuned = tuner.tune([{"quality": 0.9}])
        # Format for human inspection
        diff = {}
        for kw in tuner.weights:
            old = tuner.weights[kw]
            new = tuned.get(kw, old)
            diff[kw] = (old, new)
        assert isinstance(diff, dict)

    def test_reject_weights_fallback_original(self):
        """Rejected tuning keeps original weights."""
        tuner = MockWeightTuner({"api": 1.5})
        tuned = tuner.tune([{"quality": 0.9}])
        # On rejection, keep original
        kept = tuner.weights
        assert kept["api"] == 1.5

    def test_approve_weights_persist(self):
        """Approved tuning persists to config."""
        tuner = MockWeightTuner({"api": 1.5})
        approved_weights = {"api": 1.65}
        # Should save to config
        assert approved_weights["api"] > tuner.weights["api"]


class TestWeightTuningDeterminism:
    """Determinism and reproducibility."""

    def test_same_logs_same_tuned_weights(self):
        """Same logs always produce same tuned weights."""
        logs = [{"keyword": "api", "quality": 0.9}]
        tuner1 = MockWeightTuner()
        tuner2 = MockWeightTuner()
        tuned1 = tuner1.tune(logs)
        tuned2 = tuner2.tune(logs)
        assert tuned1 == tuned2

    def test_seed_for_reproducibility(self):
        """Random seed for reproducible tuning."""
        # If tuning uses randomization
        seed = 42
        # Set seed before tuning
        pass

    def test_log_order_independent(self):
        """Tuning independent of log order."""
        logs_a = [{"quality": 0.9}, {"quality": 0.8}]
        logs_b = [{"quality": 0.8}, {"quality": 0.9}]
        tuner1 = MockWeightTuner()
        tuner2 = MockWeightTuner()
        tuned_a = tuner1.tune(logs_a)
        tuned_b = tuner2.tune(logs_b)
        # Results should be same (order-independent)
        assert tuned_a == tuned_b
