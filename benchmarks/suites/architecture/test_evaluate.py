"""Tests for suites/architecture/evaluate.py -- AC3.

Per spec.md AC3: evaluate() calls adapter.detect_architecture(repo_path),
reports Architecture Style Accuracy, Layer Detection Accuracy, Subsystem
Detection Accuracy (via cluster_match), Dependency Direction Accuracy.

NOTE on real observed contract (suites/architecture/evaluate.py, read
2026-07-09 while BUILDER's implementation was in progress -- test file
updated to match once seen, since spec.md itself does not pin exact metric
key names or dataset_item's container type):
  - dataset_item is a dict: ["name"], ["dataset_dir"], ["repo_path"]
  - ground_truth/architecture.json's "layers" field is a DICT
    {file: layer_number}, not a list -- matches gt.get("layers", {})
  - metric keys observed: architecture_style_accuracy, architecture_confidence,
    layer_precision/recall/f1, subsystem_mean_jaccard, subsystem_matched,
    subsystem_unmatched, dependency_direction_accuracy
  - cluster_match() returns {"mean_jaccard", "matched", "unmatched", "pairs"}
    (not a bare "accuracy" key)
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[2]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from suites.architecture.evaluate import evaluate
from core.result_model import SuiteResult
from core.config import BenchmarkConfig


class FakeAdapter:
    def __init__(self, style, confidence, layers, subsystems, alternative=None, evidence=None):
        self._style = style
        self._confidence = confidence
        self._layers = layers          # dict: file -> layer number
        self._subsystems = subsystems  # list of sets
        self._alternative = alternative
        self._evidence = evidence or []

    def detect_architecture(self, repo_path):
        return SimpleNamespace(
            style=self._style, confidence=self._confidence,
            layers=self._layers, subsystems=self._subsystems,
            alternative=self._alternative, evidence=self._evidence,
        )


@pytest.fixture
def config(tmp_path):
    return BenchmarkConfig(datasets_dir=tmp_path, output_dir=tmp_path)


def _dataset_item(tmp_path, gt_architecture, repo_name="flask", suites=None):
    dataset_dir = tmp_path / repo_name
    gt_dir = dataset_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    (gt_dir / "architecture.json").write_text(json.dumps(gt_architecture), encoding="utf-8")
    manifest = {
        "repo": repo_name, "commit": "abc", "schema_version": 1,
        "suites": suites or ["architecture"], "url": "x", "language": "python",
        "benchmark_version": "0.1.0", "size_loc": 100,
        "ground_truth_authored_by": "human", "ground_truth_date": "2026-07-09",
    }
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return {"name": repo_name, "dataset_dir": dataset_dir, "repo_path": dataset_dir}


class TestArchitectureEvaluate:
    def test_sample_returns_valid_suite_result(self, config, tmp_path):
        """SAMPLE: returns SuiteResult with style accuracy in metrics."""
        adapter = FakeAdapter("layered", 0.85, {}, [])
        gt = {"style": "layered", "layers": {}, "subsystems": []}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.suite == "architecture"

    def test_style_exact_match(self, config, tmp_path):
        adapter = FakeAdapter("layered", 0.85, {}, [])
        gt = {"style": "layered", "layers": {}, "subsystems": []}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("architecture_style_accuracy") == 1.0

    def test_style_mismatch(self, config, tmp_path):
        adapter = FakeAdapter("microservices", 0.60, {}, [])
        gt = {"style": "layered", "layers": {}, "subsystems": []}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("architecture_style_accuracy") == 0.0

    def test_ground_truth_missing_subsystems_key_partial_gt(self, config, tmp_path):
        """Common in hand-authored data: architecture.json has no 'subsystems'
        key at all (only style/layers authored). Must not KeyError -- real
        code uses gt.get("subsystems", []), tested here from the outside."""
        adapter = FakeAdapter("layered", 0.85, {}, [{"a.py", "b.py"}])
        gt = {"style": "layered", "layers": {}}  # no "subsystems" key
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"

    def test_ground_truth_missing_layers_key_partial_gt(self, config, tmp_path):
        """Symmetric case: only style + subsystems authored, no layers key."""
        adapter = FakeAdapter("layered", 0.85, {"a.py": 0}, [])
        gt = {"style": "layered", "subsystems": []}  # no "layers" key
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"

    def test_ground_truth_missing_layer_edges_key(self, config, tmp_path):
        """layer_edges (used for dependency_direction_accuracy) is optional
        in hand-authored ground truth -- must default sanely (real code:
        gt.get("layer_edges", []), and _layer_edges_respected([]) -> 1.0
        vacuously, matching the metrics module's empty-set convention)."""
        adapter = FakeAdapter("layered", 0.85, {"a.py": 0, "b.py": 1}, [])
        gt = {"style": "layered", "layers": {"a.py": 0, "b.py": 1}, "subsystems": []}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert result.metrics.get("dependency_direction_accuracy") == 1.0

    def test_detail_carries_per_comparison_data_not_rollup(self, config, tmp_path):
        """spec.md: 'SuiteResult.detail carries Ground Truth / Prediction /
        Correct? / Confidence per comparison -- not a single rolled-up score.'"""
        adapter = FakeAdapter("layered", 0.85, {}, [])
        gt = {"style": "layered", "layers": {}, "subsystems": []}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert isinstance(result.detail, dict)
        assert result.detail != {}
        assert "ground_truth_style" in result.detail
        assert "predicted_style" in result.detail

    def test_subsystem_cluster_match_wired_through(self, config, tmp_path):
        adapter = FakeAdapter("layered", 0.85, {}, [{"a.py", "b.py"}, {"c.py"}])
        gt = {"style": "layered", "layers": {},
              "subsystems": [["a.py", "b.py"], ["c.py"]]}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert "subsystem_mean_jaccard" in result.metrics
        assert result.metrics["subsystem_mean_jaccard"] == pytest.approx(1.0)

    def test_subsystem_predicted_cluster_matches_nothing(self, config, tmp_path):
        """A predicted subsystem that shares nothing with any expected
        cluster must not crash cluster_match's best-overlap pairing."""
        adapter = FakeAdapter("layered", 0.85, {}, [{"zzz.py", "yyy.py"}])
        gt = {"style": "layered", "layers": {}, "subsystems": [["a.py", "b.py"]]}
        item = _dataset_item(tmp_path, gt)
        result = evaluate(adapter, item, config)
        assert 0.0 <= result.metrics["subsystem_mean_jaccard"] <= 1.0
        assert result.metrics["subsystem_unmatched"] == 1

    def test_gated_suite_missing_from_manifest_raises(self, config, tmp_path):
        """architecture.json exists but manifest.json's suites doesn't list
        'architecture' -- ground_truth.py must reject this (fail loud)."""
        adapter = FakeAdapter("layered", 0.85, {}, [])
        gt = {"style": "layered", "layers": {}, "subsystems": []}
        item = _dataset_item(tmp_path, gt, suites=["repository"])  # architecture NOT listed
        with pytest.raises(Exception):
            evaluate(adapter, item, config)
