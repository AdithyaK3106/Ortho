"""Tests for suites/impact/evaluate.py -- AC4.

Per spec.md AC4: for each ground-truth entry {"changed_file", "actually_impacted"},
calls adapter.analyze_impact(repo_path, changed_file), computes precision/
recall/F1, Blast Radius relative error, Risk Score Correlation (spearman).

Real observed contract (suites/impact/evaluate.py): dataset_item is a dict
["name"], ["dataset_dir"], ["repo_path"]. ImpactResult fields used:
impacted_files (list), blast_radius (int), risk_score (float). Metric keys:
impact_precision, impact_recall, impact_f1, blast_radius_mean_relative_error,
risk_score_correlation, entries_evaluated.

Per precision_recall_f1's real empty-set convention (see
validation/test_metrics.py interpretation decisions #2/#3): both-empty ->
1.0/1.0/1.0; empty-predicted+non-empty-expected -> precision=1.0, recall=0.0;
non-empty-predicted+empty-expected -> precision=0.0, recall=1.0.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[2]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from suites.impact.evaluate import evaluate
from core.result_model import SuiteResult
from core.config import BenchmarkConfig


class FakeAdapter:
    """impact_map: changed_file -> (predicted_impacted: list[str], risk_score: float)."""

    def __init__(self, impact_map):
        self._impact_map = impact_map

    def analyze_impact(self, repo_path, changed_file):
        predicted, risk = self._impact_map.get(changed_file, ([], 0.0))
        return SimpleNamespace(changed_file=changed_file, impacted_files=predicted,
                               risk_score=risk, blast_radius=len(predicted), evidence=[])


@pytest.fixture
def config(tmp_path):
    return BenchmarkConfig(datasets_dir=tmp_path, output_dir=tmp_path)


def _dataset_item(tmp_path, impact_entries, repo_name="flask"):
    dataset_dir = tmp_path / repo_name
    gt_dir = dataset_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    import json
    (gt_dir / "impact.json").write_text(json.dumps(impact_entries), encoding="utf-8")
    manifest = {
        "repo": repo_name, "commit": "abc", "schema_version": 1,
        "suites": ["impact"], "url": "x", "language": "python",
        "benchmark_version": "0.1.0", "size_loc": 100,
        "ground_truth_authored_by": "human", "ground_truth_date": "2026-07-09",
    }
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return {"name": repo_name, "dataset_dir": dataset_dir, "repo_path": dataset_dir}


class TestImpactEvaluate:
    def test_sample_returns_valid_suite_result(self, config, tmp_path):
        """SAMPLE: returns SuiteResult with precision/recall/f1 in metrics."""
        adapter = FakeAdapter({"a.py": (["b.py", "c.py"], 0.5)})
        entries = [{"changed_file": "a.py", "actually_impacted": ["b.py", "c.py"]}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.suite == "impact"
        assert "impact_f1" in result.metrics
        assert result.metrics["impact_f1"] == pytest.approx(1.0)

    def test_zero_blast_radius_is_a_valid_real_case(self, config, tmp_path):
        """spec.md task brief: 'a changed_file with actually_impacted = []
        (a commit that only touched one file) -- zero blast radius is a
        valid, real case, not an error.' Both predicted and actual empty ->
        precision_recall_f1's vacuous-perfect convention -> 1.0/1.0/1.0."""
        adapter = FakeAdapter({"lonely.py": ([], 0.0)})
        entries = [{"changed_file": "lonely.py", "actually_impacted": []}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"
        assert result.metrics.get("impact_precision") == 1.0
        assert result.metrics.get("impact_recall") == 1.0

    def test_zero_blast_radius_but_predicted_something(self, config, tmp_path):
        """Ground truth says zero blast radius but adapter over-predicts --
        precision must reflect the false positive (predicted non-empty,
        expected empty -> precision=0.0 per real convention)."""
        adapter = FakeAdapter({"lonely.py": (["oops.py"], 0.9)})
        entries = [{"changed_file": "lonely.py", "actually_impacted": []}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("impact_precision") == 0.0
        assert result.metrics.get("impact_recall") == 1.0  # vacuous: nothing to miss

    def test_blast_radius_relative_error_zero_actual_zero_predicted(self, config, tmp_path):
        """Real code's explicit branch: actual_count==0 and blast_radius==0
        -> relative error 0.0 (not a ZeroDivisionError from dividing by
        actual_count=0)."""
        adapter = FakeAdapter({"lonely.py": ([], 0.0)})
        entries = [{"changed_file": "lonely.py", "actually_impacted": []}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("blast_radius_mean_relative_error") == 0.0

    def test_blast_radius_relative_error_zero_actual_nonzero_predicted(self, config, tmp_path):
        """Real code's explicit branch: actual_count==0 but blast_radius>0
        -> relative error 1.0 (100% wrong, not divide-by-zero)."""
        adapter = FakeAdapter({"lonely.py": (["a.py", "b.py"], 0.5)})
        entries = [{"changed_file": "lonely.py", "actually_impacted": []}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("blast_radius_mean_relative_error") == 1.0

    def test_blast_radius_relative_error_nonzero_computed(self, config, tmp_path):
        adapter = FakeAdapter({"a.py": (["b.py", "c.py", "d.py"], 0.5)})
        entries = [{"changed_file": "a.py", "actually_impacted": ["b.py", "c.py"]}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        # |3 - 2| / 2 = 0.5
        assert result.metrics.get("blast_radius_mean_relative_error") == pytest.approx(0.5)

    def test_risk_score_correlation_across_multiple_entries(self, config, tmp_path):
        """Spearman between predicted risk score and len(actually_impacted)
        across ALL entries."""
        adapter = FakeAdapter({
            "a.py": (["x", "y", "z"], 0.9),
            "b.py": (["x"], 0.2),
        })
        entries = [
            {"changed_file": "a.py", "actually_impacted": ["x", "y", "z"]},
            {"changed_file": "b.py", "actually_impacted": ["x"]},
        ]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert "risk_score_correlation" in result.metrics
        assert result.metrics["risk_score_correlation"] == pytest.approx(1.0)

    def test_single_entry_correlation_does_not_crash(self, config, tmp_path):
        """spearman() on n=1 returns 0.0 (real convention) -- suite must not
        propagate a crash, and must report exactly that value."""
        adapter = FakeAdapter({"a.py": (["b.py"], 0.5)})
        entries = [{"changed_file": "a.py", "actually_impacted": ["b.py"]}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"
        assert result.metrics["risk_score_correlation"] == 0.0

    def test_empty_ground_truth_impact_entries(self, config, tmp_path):
        """impact.json is an empty list -- valid (dataset with no sampled
        commits yet). Real code's explicit empty-per_entry branch -> 0.0 for
        every mean metric, entries_evaluated=0, no crash."""
        adapter = FakeAdapter({})
        item = _dataset_item(tmp_path, [])
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"
        assert result.metrics["entries_evaluated"] == 0
        assert result.metrics["impact_precision"] == 0.0

    def test_detail_contains_per_entry_breakdown(self, config, tmp_path):
        adapter = FakeAdapter({"a.py": (["b.py"], 0.5)})
        entries = [{"changed_file": "a.py", "actually_impacted": ["b.py"]}]
        item = _dataset_item(tmp_path, entries)
        result = evaluate(adapter, item, config)
        assert "per_entry" in result.detail
        assert len(result.detail["per_entry"]) == 1

    def test_gated_suite_missing_from_manifest_raises(self, config, tmp_path):
        adapter = FakeAdapter({})
        dataset_dir = tmp_path / "flask"
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        import json
        (gt_dir / "impact.json").write_text("[]", encoding="utf-8")
        manifest = {
            "repo": "flask", "commit": "abc", "schema_version": 1,
            "suites": ["repository"],  # "impact" NOT listed
            "url": "x", "language": "python", "benchmark_version": "0.1.0",
            "size_loc": 100, "ground_truth_authored_by": "human",
            "ground_truth_date": "2026-07-09",
        }
        (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        item = {"name": "flask", "dataset_dir": dataset_dir, "repo_path": dataset_dir}
        with pytest.raises(Exception):
            evaluate(adapter, item, config)
