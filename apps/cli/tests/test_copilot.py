"""CLI-layer tests for the copilot argparse bridge — `apps/cli/src/commands/copilot.py`.

Derived STRICTLY from task-021 spec.md (bridge contract + behavior table) and
plan.md AC1-AC4/AC6. Style mirrors test_context.py / test_analyze.py: the bridge
is exercised as a real subprocess — the same code path
apps/cli/src/commands/copilot.ts spawns via runPython — never by importing
bridge internals. No mocking of CliCommands (AC6 real-fixture discipline).

Contract under test (spec.md):
    python copilot.py guardrails --path <dir>
    python copilot.py decide <intent> --scan-path <dir>
    python copilot.py plan <intent> --scan-path <dir>
    python copilot.py refactor --path <dir>

Protocol: prints `report.title`, blank line, `report.content` to stdout;
exit code 0 iff `report.success` else 1. --path/--scan-path are REQUIRED at
the bridge level (the TS side always supplies them). Per architecture-review.md,
a failed report is PRINTED to stdout BEFORE the nonzero exit — the failure text
must be visible even when the exit code is 1.

Scan discipline: every scan is bounded to the small real fixture `repos/click`
(spec.md's own verification target) or a tiny tmp repo — never cwd, never the
monorepo root. Expensive subprocess runs are module-scoped and shared across
assertions to keep suite time sane.

Known expected side effect: each successful run appends a workflow_run row to
`repos/click/.ortho/ortho.db` (task-020 memory capture, gitignored). Tests do
NOT assert on row counts there — the DB accumulates across runs.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_COPILOT_SCRIPT = Path(__file__).parent.parent / "src" / "commands" / "copilot.py"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO = _PROJECT_ROOT / "repos" / "click"
# Real file inside the fixture — behavior table: `ortho decide src/core.py`
# (a real file path intent) triggers change-impact on that file's parent dir.
_FIXTURE_FILE = _FIXTURE_REPO / "src" / "click" / "utils.py"

# Real scans of repos/click take seconds; argparse/early-reject paths are fast.
_SCAN_TIMEOUT = 300
_FAST_TIMEOUT = 60


def _run(*args: str, timeout: int = _SCAN_TIMEOUT) -> subprocess.CompletedProcess:
    """Invoke the bridge exactly as the TS command spawns it (list-form args,
    real subprocess). PYTHONIOENCODING is pinned so captured pipes decode
    deterministically on Windows — production uses stdio inherit, where the
    console handles encoding; this only stabilizes the test harness."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, str(_COPILOT_SCRIPT), *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )


# ---------------------------------------------------------------------------
# Module-scoped end-to-end runs (one real scan each, shared across assertions)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def guardrails_ok():
    """`copilot.py guardrails --path repos/click` — plan.md AC1."""
    return _run("guardrails", "--path", str(_FIXTURE_REPO))


@pytest.fixture(scope="module")
def plan_ok():
    """`copilot.py plan "add caching" --scan-path repos/click` — plan.md AC2."""
    return _run("plan", "add caching", "--scan-path", str(_FIXTURE_REPO))


@pytest.fixture(scope="module")
def decide_ok():
    """`copilot.py decide "improve code quality" --scan-path repos/click` — AC2."""
    return _run("decide", "improve code quality", "--scan-path", str(_FIXTURE_REPO))


@pytest.fixture(scope="module")
def refactor_ok():
    """`copilot.py refactor --path repos/click` — plan.md AC2."""
    return _run("refactor", "--path", str(_FIXTURE_REPO))


class TestEndToEndSuccess:
    """All four subcommands run end-to-end against the real bounded fixture
    (no mocking of CliCommands), exit 0, and print the real report."""

    def test_guardrails_exits_zero(self, guardrails_ok):
        assert guardrails_ok.returncode == 0, guardrails_ok.stderr

    def test_guardrails_prints_report_title(self, guardrails_ok):
        # Real CliCommands title format ("Architecture Check: <target>") —
        # assert the stable prefix, not the exact full string.
        assert "Architecture Check" in guardrails_ok.stdout

    def test_guardrails_output_structure_title_blank_content(self, guardrails_ok):
        """Spec: `report.title`, blank line, `report.content` — exactly."""
        lines = guardrails_ok.stdout.splitlines()
        assert len(lines) >= 3, f"expected title/blank/content, got: {lines!r}"
        assert "Architecture Check" in lines[0]
        assert lines[1].strip() == ""
        assert any(line.strip() for line in lines[2:]), "report content is empty"

    def test_plan_exits_zero(self, plan_ok):
        assert plan_ok.returncode == 0, plan_ok.stderr

    def test_plan_prints_report_title_and_content(self, plan_ok):
        assert "Feature Plan" in plan_ok.stdout
        lines = plan_ok.stdout.splitlines()
        assert len(lines) >= 3
        assert lines[1].strip() == ""

    def test_decide_exits_zero(self, decide_ok):
        assert decide_ok.returncode == 0, decide_ok.stderr

    def test_decide_prints_report_title(self, decide_ok):
        assert "Decision" in decide_ok.stdout

    def test_refactor_exits_zero(self, refactor_ok):
        assert refactor_ok.returncode == 0, refactor_ok.stderr

    def test_refactor_prints_report_title(self, refactor_ok):
        assert "Refactoring" in refactor_ok.stdout


class TestExitCodeMapping:
    """Exit code 0 iff report.success, else 1 — and the failure report is
    still printed to stdout BEFORE the nonzero exit (architecture-review.md)."""

    def test_guardrails_nonexistent_path_exits_one(self):
        result = _run(
            "guardrails",
            "--path",
            str(_PROJECT_ROOT / "definitely" / "not" / "a" / "real" / "path" / "xyz"),
            timeout=_FAST_TIMEOUT,
        )
        assert result.returncode == 1, (
            f"failed report must map to exit 1, got {result.returncode}; "
            f"stderr: {result.stderr}"
        )

    def test_guardrails_nonexistent_path_still_prints_failure_report(self):
        """The nuance from architecture-review.md: the report text is written
        to stdout before sys.exit(1) — a failing run is not silent."""
        result = _run(
            "guardrails",
            "--path",
            str(_PROJECT_ROOT / "definitely" / "not" / "a" / "real" / "path" / "xyz"),
            timeout=_FAST_TIMEOUT,
        )
        assert result.returncode == 1
        assert result.stdout.strip() != "", "failure report missing from stdout"
        assert "Architecture Check" in result.stdout

    def test_refactor_nonexistent_path_exits_nonzero_with_report(self):
        result = _run(
            "refactor",
            "--path",
            str(_PROJECT_ROOT / "no" / "such" / "dir" / "anywhere"),
            timeout=_FAST_TIMEOUT,
        )
        assert result.returncode == 1
        assert "Refactoring" in result.stdout


class TestEmptyIntentDefenseInDepth:
    """The TS layer validates empty intents before spawning, but the bridge is
    directly invocable — CliCommands' own rejection is defense-in-depth:
    failure report + exit 1, never a crash/traceback. Anti-overfitting:
    assert exit code and success=False semantics ('Cannot ...'), not exact
    full report strings."""

    def test_plan_empty_intent_exits_one_with_failure_report(self):
        result = _run("plan", "", "--scan-path", str(_FIXTURE_REPO), timeout=_FAST_TIMEOUT)
        assert result.returncode == 1
        assert "cannot" in result.stdout.lower()

    def test_plan_empty_intent_does_not_traceback(self):
        result = _run("plan", "", "--scan-path", str(_FIXTURE_REPO), timeout=_FAST_TIMEOUT)
        assert "Traceback" not in result.stderr

    def test_decide_empty_intent_exits_one_with_failure_report(self):
        result = _run("decide", "", "--scan-path", str(_FIXTURE_REPO), timeout=_FAST_TIMEOUT)
        assert result.returncode == 1
        assert "cannot" in result.stdout.lower()
        assert "Traceback" not in result.stderr


class TestArgparseRejections:
    """Bridge-level argparse failures: nonzero exit (argparse convention is 2,
    but only nonzero is contractual), usage/error on stderr."""

    def test_guardrails_missing_required_path_exits_nonzero(self):
        result = _run("guardrails", timeout=_FAST_TIMEOUT)
        assert result.returncode != 0
        assert result.stderr.strip() != ""

    def test_refactor_missing_required_path_exits_nonzero(self):
        result = _run("refactor", timeout=_FAST_TIMEOUT)
        assert result.returncode != 0

    def test_plan_missing_required_scan_path_exits_nonzero(self):
        result = _run("plan", "add caching", timeout=_FAST_TIMEOUT)
        assert result.returncode != 0

    def test_decide_missing_required_scan_path_exits_nonzero(self):
        result = _run("decide", "improve code quality", timeout=_FAST_TIMEOUT)
        assert result.returncode != 0

    def test_plan_missing_intent_positional_exits_nonzero(self):
        result = _run("plan", "--scan-path", str(_FIXTURE_REPO), timeout=_FAST_TIMEOUT)
        assert result.returncode != 0

    def test_unknown_subcommand_exits_nonzero(self):
        result = _run("frobnicate", "--path", str(_FIXTURE_REPO), timeout=_FAST_TIMEOUT)
        assert result.returncode != 0
        assert result.stderr.strip() != ""

    def test_no_subcommand_at_all_exits_nonzero(self):
        result = _run(timeout=_FAST_TIMEOUT)
        assert result.returncode != 0


class TestIntentPassthrough:
    """Weird intents survive the subprocess boundary (list-form args — no shell
    quoting layer) without crashing the bridge."""

    @pytest.fixture(scope="class")
    def tiny_repo(self, tmp_path_factory):
        """A minimal real repo so passthrough runs stay bounded and fast —
        the scan is real (no mocking), just tiny."""
        repo = tmp_path_factory.mktemp("tiny_repo")
        (repo / "app.py").write_text(
            "def handler(x):\n    return x\n", encoding="utf-8"
        )
        return repo

    def test_plan_intent_with_spaces_quotes_and_unicode(self, tiny_repo):
        intent = 'add "quoted" caching layer — with spaces & ünïcode'
        result = _run("plan", intent, "--scan-path", str(tiny_repo))
        assert result.returncode == 0, result.stderr
        assert "Feature Plan" in result.stdout
        assert "Traceback" not in result.stderr

    def test_decide_intent_with_special_characters(self, tiny_repo):
        intent = "should we migrate auth? (v2 -> v3) [50% done] $HOME 'quotes'"
        result = _run("decide", intent, "--scan-path", str(tiny_repo))
        assert result.returncode == 0, result.stderr
        assert "Decision" in result.stdout
        assert "Traceback" not in result.stderr

    def test_decide_real_file_path_intent(self):
        """Behavior table: `ortho decide <real file>` — a file-path intent runs
        change-impact analysis on that file's parent dir. Passes through the
        bridge unchanged; --scan-path is still supplied (the TS side always
        sends one) but the file intent takes precedence per CliCommands."""
        assert _FIXTURE_FILE.is_file(), f"fixture missing: {_FIXTURE_FILE}"
        result = _run("decide", str(_FIXTURE_FILE), "--scan-path", str(_FIXTURE_REPO))
        assert result.returncode == 0, result.stderr
        assert "Decision" in result.stdout
