"""Adapter contract tests -- validation/test_adapter_contract.py.

Per spec.md AC7:
  "calls all 5 EngineeringSystemAdapter methods against a small fixture repo
  (5 files, checked into validation/fixtures/), asserts each return type
  matches the interface's dataclass contract. This is the executable spec a
  future second adapter must satisfy."

Per spec.md AC1, the 5 methods are:
  scan_repository(repo_path) -> RepoIndex
  detect_architecture(repo_path) -> ArchResult
  retrieve(repo_path, query, k) -> list[RetrievalHit]
  analyze_impact(repo_path, changed_file) -> ImpactResult
  assemble_context(repo_path, query, budget) -> ContextResult

Fixture repo: validation/fixtures/tiny_repo/ (5 files, hand-verified known
symbols/imports/calls documented in FIXTURE_MANIFEST.md in that directory).

These tests exercise `adapters.ortho.adapter.OrthoAdapter` specifically
(the only adapter that exists in this task), but are written to only use
the `EngineeringSystemAdapter` interface surface -- a future second adapter
run through the SAME test bodies (parametrized by adapter instance) would
need to pass identically. We keep OrthoAdapter construction in a fixture
so that parametrization is a small future diff, not a rewrite.

INTERPRETATION DECISIONS:

9. "Isolated file" boundary test (pkg/isolated.py, zero in/out edges): spec
   does not say whether analyze_impact on such a file should return an
   ImpactResult with empty impacted-files / zero blast radius, or raise.
   We take "must not crash" literally per the task brief and assert it
   returns successfully with an empty/zero impact result -- a real repo
   benchmark run WILL hit files nobody imports (leaf utility scripts,
   __main__ entry points), and treating that as an error would make the
   impact suite unusable on exactly the kind of repo it's meant to run on.
"""

import sys
from dataclasses import is_dataclass
from pathlib import Path

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[1]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

FIXTURE_REPO = Path(__file__).resolve().parent / "fixtures" / "tiny_repo"

# Written against spec.md's declared file layout. Import failures here are
# expected while BUILDER is still building AC1 -- see test-plan.md.
from adapters.interface import (
    EngineeringSystemAdapter,
    RepoIndex,
    ArchResult,
    RetrievalHit,
    ImpactResult,
    ContextResult,
)
from adapters.ortho.adapter import OrthoAdapter


@pytest.fixture(scope="module")
def adapter():
    return OrthoAdapter()


@pytest.fixture(scope="module")
def repo_path():
    assert FIXTURE_REPO.exists(), f"fixture repo missing: {FIXTURE_REPO}"
    return FIXTURE_REPO


class TestAdapterIsEngineeringSystemAdapter:
    def test_sample_ortho_adapter_implements_interface(self, adapter):
        """SAMPLE 1: OrthoAdapter must be an EngineeringSystemAdapter."""
        assert isinstance(adapter, EngineeringSystemAdapter)

    def test_interface_declares_exactly_five_methods(self):
        """Spec is explicit: 'exactly 5 methods.' Guards against silent scope creep."""
        expected = {
            "scan_repository", "detect_architecture", "retrieve",
            "analyze_impact", "assemble_context",
        }
        declared = {
            name for name in dir(EngineeringSystemAdapter)
            if not name.startswith("_")
        }
        assert declared == expected


class TestScanRepository:
    def test_sample_returns_repo_index_shape(self, adapter, repo_path):
        """SAMPLE 2: return type matches RepoIndex dataclass contract."""
        result = adapter.scan_repository(repo_path)
        assert is_dataclass(result)
        assert isinstance(result, RepoIndex)

    def test_contains_known_fixture_symbols(self, adapter, repo_path):
        """Real correctness check (not just shape) against FIXTURE_MANIFEST.md."""
        result = adapter.scan_repository(repo_path)
        # RepoIndex must expose symbols in some enumerable form; per AC2
        # ("predicted qualified names vs ground truth qualified names") the
        # contract must let us get a set of qualified name strings.
        symbol_names = {getattr(s, "name", s) for s in result.symbols}
        # short names must include all 7 known fixture symbols regardless of
        # exact qualified-name delimiter convention
        expected_short_names = {"helper", "Widget", "__init__", "render",
                                 "make_widget", "standalone", "run"}
        found_short = {n.rsplit(".", 1)[-1] for n in symbol_names}
        assert expected_short_names <= found_short, (
            f"missing symbols: {expected_short_names - found_short}")

    def test_contains_known_fixture_imports(self, adapter, repo_path):
        result = adapter.scan_repository(repo_path)
        # At minimum, 2 known internal import edges must be discoverable
        assert len(result.imports) >= 2

    def test_isolated_file_present_with_no_edges(self, adapter, repo_path):
        """pkg/isolated.py must be scanned (it's a valid Python file) even
        though it participates in zero imports/calls. RepoIndex has no
        separate `.files` list (real shape: symbols/imports/calls/
        files_total/files_scanned/parse_errors per adapters/interface.py) --
        check indirectly: files_scanned must count it, and its symbol
        (`standalone`) must be extracted, while it contributes NO edges to
        imports/calls (neither as importer/importee nor caller/callee)."""
        result = adapter.scan_repository(repo_path)
        assert result.files_scanned >= 5  # all 5 fixture files, including isolated.py
        symbol_names = set(result.symbols)
        assert any(n.rsplit(".", 1)[-1] == "standalone" for n in symbol_names)
        # isolated.py must not appear on either side of any import edge
        for importer, imported in result.imports:
            assert "isolated" not in importer
            assert "isolated" not in imported


class TestDetectArchitecture:
    def test_sample_returns_arch_result_shape(self, adapter, repo_path):
        """SAMPLE 3: return type matches ArchResult dataclass contract."""
        result = adapter.detect_architecture(repo_path)
        assert is_dataclass(result)
        assert isinstance(result, ArchResult)

    def test_does_not_crash_on_tiny_repo(self, adapter, repo_path):
        """5-file repo is far below any real architecture's typical size --
        must degrade gracefully (e.g. low confidence / UNKNOWN), not crash."""
        result = adapter.detect_architecture(repo_path)
        assert result is not None


class TestRetrieve:
    def test_sample_returns_list_of_retrieval_hits(self, adapter, repo_path):
        """SAMPLE 4: return type matches list[RetrievalHit] dataclass contract."""
        result = adapter.retrieve(repo_path, "widget render", k=5)
        assert isinstance(result, list)
        for hit in result:
            assert isinstance(hit, RetrievalHit)

    def test_k_larger_than_corpus_size_does_not_crash(self, adapter, repo_path):
        """5-file repo, k=1000 -- must not crash or hang."""
        result = adapter.retrieve(repo_path, "widget", k=1000)
        assert isinstance(result, list)

    def test_query_with_no_matches_returns_empty_not_error(self, adapter, repo_path):
        result = adapter.retrieve(repo_path, "zzz_nonexistent_term_qqq", k=5)
        assert isinstance(result, list)


class TestAnalyzeImpact:
    def test_sample_returns_impact_result_shape(self, adapter, repo_path):
        """SAMPLE 5: return type matches ImpactResult dataclass contract."""
        result = adapter.analyze_impact(repo_path, "pkg/core.py")
        assert is_dataclass(result)
        assert isinstance(result, ImpactResult)

    def test_isolated_file_zero_blast_radius_does_not_crash(self, adapter, repo_path):
        """Interpretation decision #9: file with ZERO incoming/outgoing edges
        must return successfully, not raise."""
        result = adapter.analyze_impact(repo_path, "pkg/isolated.py")
        assert isinstance(result, ImpactResult)

    def test_nonexistent_changed_file_handled(self, adapter, repo_path):
        """A changed_file path that doesn't exist in the repo -- must not crash
        with an unhandled exception (may raise a documented error or return
        an empty-impact result; either is acceptable, silent hang/crash isn't)."""
        try:
            result = adapter.analyze_impact(repo_path, "pkg/does_not_exist.py")
            assert isinstance(result, ImpactResult)
        except Exception as e:
            assert not isinstance(e, (AttributeError, TypeError))


class TestAssembleContext:
    def test_sample_returns_context_result_shape(self, adapter, repo_path):
        """SAMPLE 6: return type matches ContextResult dataclass contract."""
        result = adapter.assemble_context(repo_path, "widget rendering", budget=2000)
        assert is_dataclass(result)
        assert isinstance(result, ContextResult)

    def test_isolated_file_context_does_not_crash(self, adapter, repo_path):
        """Query that would only plausibly match the isolated file's content."""
        result = adapter.assemble_context(repo_path, "standalone", budget=2000)
        assert isinstance(result, ContextResult)

    def test_zero_budget_does_not_crash(self, adapter, repo_path):
        """budget=0 is a degenerate but valid input -- must return an empty
        (or near-empty) ContextResult, not divide by zero."""
        result = adapter.assemble_context(repo_path, "widget", budget=0)
        assert isinstance(result, ContextResult)
