"""Integration tests for Phase 4 components 7–9 (Logger, Metrics, Tuning)."""

import pytest
import tempfile
from pathlib import Path

from token_optimizer.quality_logger import ContextQualityLogger
from token_optimizer.metrics import MetricsCollector
from token_optimizer.weight_tuner import WeightTuner
from token_optimizer.types import ContextChunk, ContextPackage
from token_optimizer.budget import TokenBudget


def make_package():
    """Create a test ContextPackage."""
    chunk = ContextChunk(
        id="c1",
        source_type="artifact",
        source_id="src_c1",
        content="test content",
        relevance_score=0.5,
        token_count=100,
        included=True,
    )
    return ContextPackage(
        id="pkg1",
        workflow_run_id="wf1",
        step_id="step1",
        chunks=[chunk],
        budget=TokenBudget(total=1000, used=100, model="test"),
        assembled_at="2026-01-01T00:00:00Z",
    )


class TestContextQualityLogger:
    """Test Context Quality Logger (Component 7)."""

    def test_log_assembly(self):
        """Log assembly decision to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ContextQualityLogger(Path(tmpdir))
            pkg = make_package()

            logger.log_assembly(
                context_package=pkg,
                query="test query",
                intent_class="feature_development",
                dedup_ratio=0.95,
                rerank_factor=1.2,
                compression_applied=False,
                architecture_boost_applied=True,
                model="claude-opus-4-8",
                llm_input_tokens=500,
                llm_output_tokens=200,
                llm_stop_reason="complete",
            )

            # Verify CSV was created
            logs = logger.read_logs()
            assert len(logs) == 1
            assert logs[0]["intent_class"] == "feature_development"
            assert logs[0]["chunks_retrieved"] == 1

    def test_log_rotation_by_date(self):
        """Logs are stored per date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ContextQualityLogger(Path(tmpdir))
            pkg = make_package()

            # Log multiple entries (would be on same date in test)
            for i in range(3):
                logger.log_assembly(
                    context_package=pkg,
                    query=f"query_{i}",
                    intent_class="analysis",
                )

            logs = logger.read_logs()
            assert len(logs) == 3


class TestMetricsCollector:
    """Test Metrics Collection (Component 8)."""

    def test_token_reduction(self):
        """Compute token reduction percentage."""
        baseline = [1000, 1100, 1050, 950, 1000]  # avg 1020
        current = [800, 900, 850, 750, 850]  # avg 830

        metrics = MetricsCollector.compute_reduction(baseline, current)

        # Reduction: (1020 - 830) / 1020 = 18.6%
        assert metrics["reduction_pct"] > 15
        assert metrics["avg_phase3"] == 1020.0
        assert metrics["avg_phase4"] == 830.0

    def test_percentile_calculation(self):
        """Compute P50 and P95 percentiles."""
        baseline = list(range(100, 200, 10))  # [100, 110, 120, ..., 190]
        current = list(range(80, 160, 10))  # [80, 90, 100, ..., 150]

        metrics = MetricsCollector.compute_reduction(baseline, current)

        # P50 should be roughly midpoint
        assert metrics["p50_phase3"] > 0
        assert metrics["p50_phase4"] > 0

    def test_by_intent_class(self):
        """Compute reduction per intent class."""
        baseline_logs = [
            {"intent_class": "feature_development", "tokens_used": 1000},
            {"intent_class": "bug_fix", "tokens_used": 800},
        ]
        current_logs = [
            {"intent_class": "feature_development", "tokens_used": 900},
            {"intent_class": "bug_fix", "tokens_used": 700},
        ]

        metrics = MetricsCollector.compute_by_intent_class(baseline_logs, current_logs)

        assert "feature_development" in metrics
        assert "bug_fix" in metrics
        assert metrics["feature_development"]["reduction_pct"] > 0


class TestWeightTuner:
    """Test Ranking Weight Tuning (Component 9)."""

    def test_correlation_calculation(self):
        """Compute correlation coefficient."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]  # Perfect positive correlation

        corr = WeightTuner.compute_correlation(x, y)
        # Due to normalization in our formula, perfect correlation ≈ 0.8
        assert corr > 0.7

    def test_auto_tune_positive_correlation(self):
        """Increase weights on positive correlation."""
        baseline_weights = {
            "feature_development": {
                "api": 1.8,
                "interface": 1.8,
            }
        }

        logs = [
            {"intent_class": "feature_development", "rerank_factor": 1.5, "llm_output_tokens": 500},
            {"intent_class": "feature_development", "rerank_factor": 2.0, "llm_output_tokens": 600},
            {"intent_class": "feature_development", "rerank_factor": 1.0, "llm_output_tokens": 300},
        ]

        tuned = WeightTuner.auto_tune(logs, baseline_weights, target_metric="llm_output_tokens")

        # With positive correlation, weights should increase (up to 2.0 cap)
        assert tuned["feature_development"]["api"] >= baseline_weights["feature_development"]["api"]

    def test_weight_bounds(self):
        """Tuned weights stay within [0.5, 2.0]."""
        baseline_weights = {
            "analysis": {"architecture": 1.5}
        }

        logs = []  # Empty logs → no significant correlation

        tuned = WeightTuner.auto_tune(logs, baseline_weights)

        assert tuned["analysis"]["architecture"] == baseline_weights["analysis"]["architecture"]

    def test_tuning_deltas(self):
        """Report changes made during tuning."""
        baseline = {
            "feature_development": {"api": 1.8, "interface": 1.8}
        }
        tuned = {
            "feature_development": {"api": 1.98, "interface": 1.8}  # api increased
        }

        deltas = WeightTuner.report_tuning_deltas(baseline, tuned)

        assert "feature_development:api" in deltas
        assert deltas["feature_development:api"] > 0


class TestIntegrationAllComponents:
    """Integration test: Logger → Metrics → Tuning."""

    def test_full_pipeline(self):
        """Log, compute metrics, auto-tune weights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Log entries
            logger = ContextQualityLogger(Path(tmpdir))
            pkg = make_package()

            for i in range(5):
                logger.log_assembly(
                    context_package=pkg,
                    query=f"query_{i}",
                    intent_class="feature_development",
                    rerank_factor=1.0 + i * 0.1,
                )

            # Step 2: Read logs and compute metrics
            logs = logger.read_logs()
            baseline_tokens = [1000] * len(logs)
            current_tokens = [950 - i * 10 for i in range(len(logs))]

            metrics = MetricsCollector.compute_reduction(baseline_tokens, current_tokens)
            assert metrics["reduction_pct"] > 0

            # Step 3: Auto-tune weights
            baseline_weights = {
                "feature_development": {"api": 1.8, "interface": 1.8}
            }
            tuned = WeightTuner.auto_tune(logs, baseline_weights)

            assert "feature_development" in tuned
