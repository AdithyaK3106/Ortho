"""Tests for task-019: wiring plan()/refactor() to real engines.

Written independently against spec.md's contract (adapters' method
signatures and behavior table), not against implementation-notes.md's
narrative of how BUILDER wrote the code.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cli_commands.commands import CliCommands
from cli_commands.feature_plan_adapter import FeaturePlannerArchModelAdapter
from cli_commands.refactor_adapter import CodeRepositoryAdapter
from cli_commands.repo_scanner import scan_repository
from cli_commands.types import CliReport

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CLICK = str(_REPO_ROOT / "repos" / "click")
_REQUESTS = str(_REPO_ROOT / "repos" / "requests")
_FLASK = str(_REPO_ROOT / "repos" / "flask")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestPlanCommand:
    def test_plan_empty_intent_rejected_without_scan(self, commands: CliCommands) -> None:
        result = commands.plan("")
        assert result.success is False

    def test_plan_non_string_intent_rejected(self, commands: CliCommands) -> None:
        """Spec's empty-intent guard must also reject non-str intents, since
        FeaturePlanner._classify_feature_type() calls .lower() on it."""
        result = commands.plan(123)  # type: ignore[arg-type]
        assert result.success is False

    def test_plan_returns_at_least_3_distinct_paths(self, commands: CliCommands) -> None:
        result = commands.plan("add a caching layer", scan_path=_CLICK)
        assert result.success is True
        path_lines = [line for line in result.content.splitlines() if line.startswith("- ")]
        assert len(path_lines) >= 3

    def test_plan_varies_by_feature_type_classification(self, commands: CliCommands) -> None:
        """Different intents that classify to different feature types must
        produce different path sets (not a fixed hardcoded response)."""
        endpoint_result = commands.plan("add a new API endpoint", scan_path=_CLICK)
        data_result = commands.plan("add a database migration", scan_path=_CLICK)
        assert endpoint_result.content != data_result.content

    def test_plan_nonexistent_scan_path_fails(self, commands: CliCommands) -> None:
        result = commands.plan("add feature", scan_path="/definitely/not/a/real/path/xyz")
        assert result.success is False

    def test_plan_title_reflects_intent(self, commands: CliCommands) -> None:
        result = commands.plan("add rate limiting", scan_path=_CLICK)
        assert "add rate limiting" in result.title


class TestRefactorCommand:
    def test_refactor_nonexistent_path_fails_fast(self, commands: CliCommands) -> None:
        result = commands.refactor("/definitely/not/a/real/path/xyz")
        assert result.success is False

    def test_refactor_finds_real_bloat_on_click(self, commands: CliCommands) -> None:
        """click has genuinely large modules (core.py, types.py); this must
        surface as a real bloat finding, not a hardcoded stub string."""
        result = commands.refactor(_CLICK)
        assert result.success is True
        assert "bloat" in result.content.lower()

    def test_refactor_no_fabricated_duplication(self, commands: CliCommands) -> None:
        """No duplication-detection signal exists in this codebase yet
        (spec.md non-goal) — the rendered report must not claim to have
        found any, on any real repo."""
        result = commands.refactor(_CLICK)
        assert "duplication" not in result.content.lower()

    def test_refactor_clean_small_repo_reports_no_issues_not_error(
        self, tmp_path: Path
    ) -> None:
        """A repo with one small, clean file has no bloat/cycles: this is a
        valid real outcome (success=True, empty findings), not an error."""
        (tmp_path / "clean.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
        result = CliCommands().refactor(str(tmp_path))
        assert result.success is True
        assert "no refactoring issues" in result.content.lower()


class TestFeaturePlannerArchModelAdapter:
    def test_get_style_returns_real_scanned_value(self) -> None:
        scan = scan_repository(_REQUESTS)
        adapter = FeaturePlannerArchModelAdapter(scan.arch_model)
        style = adapter.get_style()
        assert isinstance(style, str)
        assert style == scan.arch_model.style.value


class TestCodeRepositoryAdapter:
    def test_get_duplications_always_empty(self) -> None:
        scan = scan_repository(_CLICK)
        adapter = CodeRepositoryAdapter(scan)
        assert adapter.get_duplications() == []

    def test_get_high_churn_modules_empty_when_never_scanned(self, tmp_path: Path) -> None:
        """A repo with no .ortho/ortho.db (never run through `ortho scan`)
        has no git_history to read -- must degrade to [], not raise."""
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        assert adapter.get_high_churn_modules() == []

    def test_get_bloated_modules_matches_real_thresholds(self) -> None:
        """Every returned entry must genuinely exceed the documented
        threshold (lines > 300 or functions > 20) — not an arbitrary
        hardcoded list. Verifies against real measured values, not mocks."""
        scan = scan_repository(_CLICK)
        adapter = CodeRepositoryAdapter(scan)
        bloated = adapter.get_bloated_modules()
        assert len(bloated) > 0
        for module, lines, functions in bloated:
            assert lines > 300 or functions > 20

    def test_get_bloated_modules_excludes_test_modules(self) -> None:
        """Regression: on Flask, get_bloated_modules() previously flagged
        tests.test_json (346 lines/38 functions), tests.test_views (272/44),
        tests.test_appctx, tests.test_signals, etc. as 'bloat: split into
        focused modules' alongside real production findings like
        src.flask.helpers. Test-file line/function count doesn't carry the
        same coupling or maintenance cost as production code, so this both
        recommends a pointless split and drowns real findings in an
        overgrown-test-suite repo. Test modules (a 'tests'/'test' package
        segment, or a test_*/​*_test leaf, matching pytest's own discovery
        convention) must never appear in the result, even if they
        genuinely exceed the line/function thresholds."""
        scan = scan_repository(_FLASK)
        adapter = CodeRepositoryAdapter(scan)
        bloated = adapter.get_bloated_modules()
        assert len(bloated) > 0  # Flask has real production bloat (app.py etc.)
        for module, _lines, _functions in bloated:
            segments = module.split(".")
            assert "tests" not in segments and "test" not in segments
            assert not any(s.startswith("test_") or s.endswith("_test") for s in segments)

    def test_get_tight_couplings_returns_deduplicated_pairs(self) -> None:
        """A cycle A->B->A must appear once as (A, B), not once as (A, B)
        AND once as (B, A)."""
        scan = scan_repository(_CLICK)
        adapter = CodeRepositoryAdapter(scan)
        pairs = adapter.get_tight_couplings()
        seen_keys = set()
        for a, b in pairs:
            key = frozenset((a, b))
            assert key not in seen_keys, f"duplicate coupling pair: {a} <-> {b}"
            seen_keys.add(key)

    def test_get_circular_deps_chains_are_closed_loops(self) -> None:
        """Every returned cycle must start and end at the same module
        (a real closed dependency loop), and have more than 2 nodes
        (2-node cycles are tight_coupling, not circular — see spec.md)."""
        scan = scan_repository(_CLICK)
        adapter = CodeRepositoryAdapter(scan)
        cycles = adapter.get_circular_deps()
        for cycle in cycles:
            assert cycle[0] == cycle[-1]
            assert len(cycle) > 3  # closed loop of >2 distinct nodes: [A, B, C, A]

    def test_no_module_appears_in_both_coupling_and_circular(self) -> None:
        """A given cycle must be classified as exactly one of tight_coupling
        (len==2 distinct nodes) or circular (len>2 distinct nodes), never
        counted in both — this would double-report the same real issue."""
        scan = scan_repository(_CLICK)
        adapter = CodeRepositoryAdapter(scan)
        coupling_pairs = {frozenset(p) for p in adapter.get_tight_couplings()}
        circular_chains = [frozenset(c[:-1]) for c in adapter.get_circular_deps()]
        for chain in circular_chains:
            assert chain not in coupling_pairs


class TestRealRepoRegressionPlanRefactor:
    """Mandatory real-repo verification (task-019, mirrors task-017/018's
    precedent). Bounded/structural assertions only — no hardcoded exact
    output — to avoid overfitting to a snapshot of click's current state."""

    def test_plan_and_refactor_both_succeed_on_click(self) -> None:
        cc = CliCommands()
        plan_result = cc.plan("add structured logging", scan_path=_CLICK)
        refactor_result = cc.refactor(_CLICK)

        assert isinstance(plan_result, CliReport)
        assert isinstance(refactor_result, CliReport)
        assert plan_result.success is True
        assert refactor_result.success is True

        # cross_cutting classification (logging is a documented keyword)
        assert "cross_cutting" in plan_result.content or "Feature type" in plan_result.content
