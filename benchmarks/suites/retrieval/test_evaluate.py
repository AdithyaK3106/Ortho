"""Tests for suites/retrieval/evaluate.py -- AC6.

Per spec.md AC6: for each question in retrieval.json
{"question", "expected_files", "expected_symbols"}, calls
adapter.retrieve(repo_path, question, k) for each k in config.retrieval_k,
computes Recall@k, Precision@k (k=5, k=10), MRR, NDCG@10.

Real observed contract (suites/retrieval/evaluate.py): dataset_item is a
dict ["name"], ["dataset_dir"], ["repo_path"]. Optionally calls
adapter.ingest_analysis_artifacts(repo_path) first (hasattr-guarded).
_expected_ids(question) = set(expected_files) | set(expected_symbols) --
a hit counts as relevant if ITS id matches EITHER an expected file or
expected symbol (both pools merged, not evaluated separately). retrieve()
is called once per question with max_k = max(all configured k's, NDCG_K=10),
then all metrics are sliced from that single hit list -- not one retrieve()
call per k. Metric keys: questions_evaluated, mrr, ndcg_at_10,
recall_at_{k}, precision_at_{k} for each k in config.retrieval_k.
core.metrics.ranking._hit_id(h) uses h.id if present, else h itself -- our
FakeAdapter returns RetrievalHit-like objects with `.id` per
adapters/interface.py's real RetrievalHit dataclass.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[2]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

from suites.retrieval.evaluate import evaluate
from core.result_model import SuiteResult
from core.config import BenchmarkConfig


def _hit(id_, score=1.0):
    return SimpleNamespace(id=id_, content="", relevance_score=score,
                           file_id=id_, symbol_id=None)


class FakeAdapter:
    """query_map: query -> list of hit ids (in rank order). retrieve() is
    called ONCE per question with max_k (see module docstring) -- we ignore
    the requested k and always return up to len(hits), matching how a real
    adapter behaves when asked for more than it has."""

    def __init__(self, query_map):
        self._query_map = query_map

    def retrieve(self, repo_path, query, k):
        hits = self._query_map.get(query, [])[:k]
        return [_hit(h) for h in hits]


@pytest.fixture
def config(tmp_path):
    return BenchmarkConfig(datasets_dir=tmp_path, output_dir=tmp_path, retrieval_k=(5, 10))


def _dataset_item(tmp_path, questions, repo_name="flask"):
    dataset_dir = tmp_path / repo_name
    gt_dir = dataset_dir / "ground_truth"
    gt_dir.mkdir(parents=True, exist_ok=True)
    import json
    (gt_dir / "retrieval.json").write_text(json.dumps(questions), encoding="utf-8")
    manifest = {
        "repo": repo_name, "commit": "abc", "schema_version": 1,
        "suites": ["retrieval"], "url": "x", "language": "python",
        "benchmark_version": "0.1.0", "size_loc": 100,
        "ground_truth_authored_by": "human", "ground_truth_date": "2026-07-09",
    }
    (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return {"name": repo_name, "dataset_dir": dataset_dir, "repo_path": dataset_dir}


class TestRetrievalEvaluate:
    def test_sample_returns_valid_suite_result(self, config, tmp_path):
        """SAMPLE: returns SuiteResult with recall@k etc. in metrics."""
        adapter = FakeAdapter({"how does routing work?": ["routing.py", "app.py"]})
        questions = [{"question": "how does routing work?",
                      "expected_files": ["routing.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.suite == "retrieval"

    def test_expected_files_absent_from_results_recall_zero(self, config, tmp_path):
        """A question with expected_files that don't appear anywhere in the
        adapter's retrieve() results -- recall=0, must not crash."""
        adapter = FakeAdapter({"obscure query": ["unrelated1.py", "unrelated2.py"]})
        questions = [{"question": "obscure query",
                      "expected_files": ["target.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"
        assert result.metrics.get("recall_at_5") == 0.0

    def test_all_k_values_from_config_reported(self, config, tmp_path):
        adapter = FakeAdapter({"q": ["a.py"] * 12})
        questions = [{"question": "q", "expected_files": ["a.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert "recall_at_5" in result.metrics
        assert "recall_at_10" in result.metrics
        assert "precision_at_5" in result.metrics
        assert "precision_at_10" in result.metrics

    def test_ndcg_reported(self, config, tmp_path):
        adapter = FakeAdapter({"q": ["a.py", "b.py"]})
        questions = [{"question": "q", "expected_files": ["a.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert "ndcg_at_10" in result.metrics
        assert result.metrics["ndcg_at_10"] == pytest.approx(1.0)  # hit at rank 1

    def test_mrr_reported(self, config, tmp_path):
        adapter = FakeAdapter({"q": ["a.py", "b.py"]})
        questions = [{"question": "q", "expected_files": ["a.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert "mrr" in result.metrics
        assert result.metrics["mrr"] == pytest.approx(1.0)

    def test_expected_symbols_also_count_as_relevant(self, config, tmp_path):
        """_expected_ids merges expected_files | expected_symbols -- a hit
        matching a SYMBOL id must count as relevant too, not just file ids."""
        adapter = FakeAdapter({"q": ["pkg.mod.some_symbol", "other.py"]})
        questions = [{"question": "q", "expected_files": [],
                      "expected_symbols": ["pkg.mod.some_symbol"]}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert result.metrics["mrr"] == pytest.approx(1.0)

    def test_empty_question_set(self, config, tmp_path):
        """Real code's explicit per_question=[] branch -> questions_evaluated=0,
        mean()->0.0 for every metric, no ZeroDivisionError."""
        adapter = FakeAdapter({})
        item = _dataset_item(tmp_path, [])
        result = evaluate(adapter, item, config)
        assert isinstance(result, SuiteResult)
        assert result.status != "FAILED"
        assert result.metrics["questions_evaluated"] == 0
        assert result.metrics["mrr"] == 0.0

    def test_averages_across_multiple_questions(self, config, tmp_path):
        adapter = FakeAdapter({
            "q1": ["a.py"],           # hit at rank 1
            "q2": ["x.py", "b.py"],   # hit at rank 2
        })
        questions = [
            {"question": "q1", "expected_files": ["a.py"], "expected_symbols": []},
            {"question": "q2", "expected_files": ["b.py"], "expected_symbols": []},
        ]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert result.metrics["mrr"] == pytest.approx((1.0 + 0.5) / 2)

    def test_no_relevant_items_found_for_any_question(self, config, tmp_path):
        adapter = FakeAdapter({"q": ["x.py", "y.py"]})
        questions = [{"question": "q", "expected_files": ["zzz.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert result.metrics["mrr"] == 0.0
        assert result.metrics["ndcg_at_10"] == 0.0

    def test_detail_contains_per_question_breakdown(self, config, tmp_path):
        adapter = FakeAdapter({"q": ["a.py"]})
        questions = [{"question": "q", "expected_files": ["a.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        result = evaluate(adapter, item, config)
        assert "per_question" in result.detail
        assert len(result.detail["per_question"]) == 1

    def test_ingest_analysis_artifacts_called_when_present(self, config, tmp_path):
        calls = []

        class FakeAdapterWithIngest(FakeAdapter):
            def ingest_analysis_artifacts(self, repo_path):
                calls.append(repo_path)

        adapter = FakeAdapterWithIngest({"q": ["a.py"]})
        questions = [{"question": "q", "expected_files": ["a.py"], "expected_symbols": []}]
        item = _dataset_item(tmp_path, questions)
        evaluate(adapter, item, config)
        assert len(calls) == 1

    def test_gated_suite_missing_from_manifest_raises(self, config, tmp_path):
        import json
        dataset_dir = tmp_path / "flask"
        gt_dir = dataset_dir / "ground_truth"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / "retrieval.json").write_text("[]", encoding="utf-8")
        manifest = {
            "repo": "flask", "commit": "abc", "schema_version": 1,
            "suites": ["repository"],  # "retrieval" NOT listed
            "url": "x", "language": "python", "benchmark_version": "0.1.0",
            "size_loc": 100, "ground_truth_authored_by": "human",
            "ground_truth_date": "2026-07-09",
        }
        (dataset_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        item = {"name": "flask", "dataset_dir": dataset_dir, "repo_path": dataset_dir}
        adapter = FakeAdapter({})
        with pytest.raises(Exception):
            evaluate(adapter, item, config)
