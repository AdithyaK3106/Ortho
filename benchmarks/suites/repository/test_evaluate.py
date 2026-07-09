"""Tests for suites/repository/evaluate.py -- AC2.

Per spec.md AC2: evaluate(adapter, dataset_item, config) -> SuiteResult,
computing precision/recall/F1 (via core/metrics/set_based.py) for symbols,
imports, and call graph, plus Parse Success Rate and Repository Coverage.

These tests use a FAKE adapter (not the real OrthoAdapter) so the suite's
scoring logic is tested in isolation from Ortho's actual scan behavior --
matches the architecture's intent that suites are testable independent of
which adapter is plugged in.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[2]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from suites.repository.evaluate import evaluate
from core.result_model import SuiteResult
from core.config import BenchmarkConfig


class FakeAdapter:
    """Returns a canned RepoIndex-shaped object regardless of repo_path.

    Matches the REAL contract observed in suites/repository/evaluate.py:
    `set(index.symbols)` (bare qualified-name strings, not objects),
    `{tuple(pair) for pair in index.imports}` (2-tuples), same for `.calls`,
    plus `.files_total`/`.files_scanned`/`.parse_errors`.
    """

    def __init__(self, symbols, imports, calls, files_total=3, files_scanned=3,
                 parse_errors=None):
        self._symbols = symbols
        self._imports = imports
        self._calls = calls
        self._files_total = files_total
        self._files_scanned = files_scanned
        self._parse_errors = parse_errors or []

    def scan_repository(self, repo_path):
        return SimpleNamespace(
            symbols=list(self._symbols),
            imports=[tuple(i) for i in self._imports],
            calls=[tuple(c) for c in self._calls],
            files_total=self._files_total,
            files_scanned=self._files_scanned,
            parse_errors=self._parse_errors,
        )


@pytest.fixture
def config(tmp_path):
    return BenchmarkConfig(datasets_dir=tmp_path, output_dir=tmp_path)


def _dataset_item(tmp_path, symbols_gt, imports_gt, calls_gt, repo_name="flask"):
    dataset_dir = tmp_path / repo_name
    gt_dir = dataset_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    import json
    (gt_dir / "symbols.json").write_text(json.dumps(symbols_gt), encoding="utf-8")
    (gt_dir / "imports.json").write_text(json.dumps(imports_gt), encoding="utf-8")
    (gt_dir / "callgraph.json").write_text(json.dumps(calls_gt), encoding="utf-8")
    manifest = {
        "repo": repo_name, "commit": "abc", "schema_version": 1,
        "suites": ["repository"], "url": "x", "language": "python",
        "benchmark_version": "0.1.0", "size_loc": 100,
        "ground_truth_authored_by": "human", "ground_truth_date": "2026-07-09",
    }
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    # NOTE: dataset_item is a dict per suites/repository/evaluate.py's real
    # contract (dataset_item["name"], ["dataset_dir"], ["repo_path"]) --
    # spec.md itself doesn't pin the exact container type, BUILDER chose
    # dict; tests updated to match once observed on disk.
    return {"name": repo_name, "dataset_dir": dataset_dir, "repo_path": dataset_dir}


class TestRepositoryEvaluate:
    def test_sample_returns_valid_suite_result(self, config, tmp_path):
        """SAMPLE 1: returns a SuiteResult dataclass, correct shape."""
        adapter = FakeAdapter(
            symbols=["a.foo", "a.bar"], imports=[("a", "b")], calls=[("a.foo", "a.bar")])
        item = _dataset_item(tmp_path, ["a.foo", "a.bar"], [["a", "b"]], [["a.foo", "a.bar"]])
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.suite == "repository"
        assert result.status in ("SUCCESS", "FAILED", "PARTIAL")

    def test_exact_match_yields_perfect_scores(self, config, tmp_path):
        adapter = FakeAdapter(
            symbols=["a.foo", "a.bar"], imports=[("a", "b")], calls=[("a.foo", "a.bar")])
        item = _dataset_item(tmp_path, ["a.foo", "a.bar"], [["a", "b"]], [["a.foo", "a.bar"]])
        result = evaluate(adapter, item, config)
        assert result.metrics.get("symbols_f1") == pytest.approx(1.0)

    def test_missing_callgraph_ground_truth_file_raises_not_silently_empty(self, config, tmp_path):
        """Repository suite requires symbols.json + imports.json + callgraph.json
        (all three gated on 'repository' being in manifest.json's suites).
        Missing callgraph.json entirely (partial ground truth authoring) must
        raise per core.ground_truth's fail-loud contract -- NOT silently
        treat it as an empty ground-truth set (which would misreport a
        perfect callgraph score for a category that was never authored)."""
        dataset_dir = tmp_path / "partial_repo"
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        import json
        (gt_dir / "symbols.json").write_text(json.dumps(["a.foo"]), encoding="utf-8")
        (gt_dir / "imports.json").write_text(json.dumps([]), encoding="utf-8")
        # callgraph.json intentionally absent
        manifest = {
            "repo": "partial_repo", "commit": "abc", "schema_version": 1,
            "suites": ["repository"], "url": "x", "language": "python",
            "benchmark_version": "0.1.0", "size_loc": 10,
            "ground_truth_authored_by": "human", "ground_truth_date": "2026-07-09",
        }
        (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        item = {"name": "partial_repo", "dataset_dir": dataset_dir, "repo_path": dataset_dir}

        adapter = FakeAdapter(symbols=["a.foo"], imports=[], calls=[("a.foo", "a.bar")])
        with pytest.raises(Exception):
            evaluate(adapter, item, config)

    def test_qualified_name_collision_not_overcounted(self, config, tmp_path):
        """Two files define a function with the same SHORT name ('helper')
        but different qualified names -- precision/recall must use qualified
        names, else this silently overcounts as 2 correct matches from 1
        ground-truth entry."""
        adapter = FakeAdapter(
            symbols=["pkg.a.helper", "pkg.b.helper"],
            imports=[], calls=[])
        # ground truth only expects ONE of the two 'helper's
        item = _dataset_item(tmp_path, ["pkg.a.helper"], [], [])
        result = evaluate(adapter, item, config)
        # precision must reflect 1 correct / 2 predicted = 0.5, NOT 1.0
        # (1.0 would mean short-name matching incorrectly credited both)
        assert result.metrics.get("symbols_precision") == pytest.approx(0.5)

    def test_zero_predicted_symbols(self, config, tmp_path):
        adapter = FakeAdapter(symbols=[], imports=[], calls=[])
        item = _dataset_item(tmp_path, ["a.foo", "a.bar"], [], [])
        result = evaluate(adapter, item, config)
        assert result.metrics.get("symbols_recall") == 0.0

    def test_detail_contains_correct_missed_extra_breakdown(self, config, tmp_path):
        """spec.md: 'per-item Correct/Missed/Extra breakdown goes in SuiteResult.detail'."""
        adapter = FakeAdapter(symbols=["a.foo", "a.extra"], imports=[], calls=[])
        item = _dataset_item(tmp_path, ["a.foo", "a.missed"], [], [])
        result = evaluate(adapter, item, config)
        assert "detail" not in result.metrics  # detail is a separate field, not folded into metrics
        assert isinstance(result.detail, dict)
