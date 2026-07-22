"""CLI-layer tests for workflow_cli.py's developer-facing output and defaults."""

import io
import os
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "commands"))
import workflow_cli as wc  # noqa: E402


@dataclass
class _FakeEvidence:
    error_message: Optional[str] = None
    approval_reason: Optional[str] = None


@dataclass
class _FakeRun:
    id: str
    intent_class: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    evidence: list = field(default_factory=list)


class TestPrintRunSurfacesFailureReason:
    """Regression: `Status: failed`/`Status: rejected` alone gives a
    developer nothing actionable -- the real reason already exists on the
    evidence record. _print_run must surface it, not require a direct DB
    query (a real bug this session was only found by inspecting the
    evidence_json column by hand)."""

    def test_failed_run_prints_the_real_error_message(self):
        run = _FakeRun(
            id="run-1",
            intent_class="feature_development",
            status="failed",
            started_at="2026-01-01T00:00:00",
            completed_at="2026-01-01T00:00:01",
            evidence=[_FakeEvidence(error_message="'SearchResult' object has no attribute 'id'")],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            wc._print_run(run)
        assert "Reason: 'SearchResult' object has no attribute 'id'" in buf.getvalue()

    def test_rejected_run_prints_the_rejection_reason(self):
        run = _FakeRun(
            id="run-2",
            intent_class="refactor",
            status="rejected",
            started_at="2026-01-01T00:00:00",
            completed_at="2026-01-01T00:00:01",
            evidence=[_FakeEvidence(approval_reason="User rejected workflow")],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            wc._print_run(run)
        assert "Reason: User rejected workflow" in buf.getvalue()

    def test_complete_run_prints_no_reason_line(self):
        run = _FakeRun(
            id="run-3",
            intent_class="analysis",
            status="complete",
            started_at="2026-01-01T00:00:00",
            completed_at="2026-01-01T00:00:01",
            evidence=[_FakeEvidence()],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            wc._print_run(run)
        assert "Reason:" not in buf.getvalue()

    def test_failed_run_with_no_evidence_does_not_crash(self):
        run = _FakeRun(
            id="run-4",
            intent_class="analysis",
            status="failed",
            started_at="2026-01-01T00:00:00",
            evidence=[],
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            wc._print_run(run)  # must not raise
        assert "Status: failed" in buf.getvalue()


class TestClassifyIntentDefaultsToKeyword:
    """Regression: classify_intent() previously tried the semantic router
    (a real HuggingFace transformer model) first on every call, including
    `ortho run --dry-run` -- observed live at ~2 minutes just to load the
    model, every time, for a 6-category classification the keyword path
    already agreed with in every real test this session. Keyword matching
    must be the default; the semantic router is opt-in only."""

    def test_default_uses_keyword_method_not_semantic_router(self, monkeypatch):
        monkeypatch.delenv("ORTHO_SEMANTIC_INTENT", raising=False)
        result = wc.classify_intent("refactor flask/app.py to split it into smaller modules")
        assert result.method == "keyword"

    def test_opt_in_env_var_is_the_only_way_to_reach_the_semantic_path(self, monkeypatch):
        """Without the opt-in, classify_intent must never even try to
        import the semantic router module (which is what actually
        triggers the slow model load)."""
        monkeypatch.delenv("ORTHO_SEMANTIC_INTENT", raising=False)
        # Sanity: the module-level cache starts unset; if classify_intent
        # ever touched the semantic path here it would flip this to
        # something other than None.
        wc._semantic_router = None
        wc.classify_intent("add rate limiting")
        assert wc._semantic_router is None
