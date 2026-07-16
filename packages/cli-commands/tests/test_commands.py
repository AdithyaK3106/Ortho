"""CLI commands integration tests"""
from pathlib import Path

import pytest

from cli_commands.commands import CliCommands
from cli_commands.types import CliReport

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO = str(_REPO_ROOT / "repos" / "click")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestCommands:
    """Test CLI command execution"""

    def test_plan_command(self, commands: CliCommands) -> None:
        """ortho plan <intent> runs real feature planning against a bounded fixture"""
        result = commands.plan("add user search endpoint", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Feature Plan" in result.title

    def test_refactor_command(self, commands: CliCommands) -> None:
        """ortho refactor [path] runs a real scan against a real repo"""
        result = commands.refactor(_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Refactoring" in result.title

    def test_review_command_real_scan(self, commands: CliCommands) -> None:
        """ortho review [path] runs guardrails + decision summary in one scan"""
        result = commands.review(_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Review" in result.title
        assert "Scanned" in result.content

    def test_review_command_bad_path(self, commands: CliCommands) -> None:
        """review on a nonexistent path fails cleanly, not a crash"""
        result = commands.review("/definitely/not/a/real/path/xyz")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_review_includes_recommendation_when_violations_exist(self, commands: CliCommands) -> None:
        """review's decision summary only appears when there's something to decide about"""
        result = commands.review(_FIXTURE_REPO)
        if result.violations:
            assert "Recommended:" in result.content

    def test_review_severity_filter_matches_guardrails(self, commands: CliCommands) -> None:
        """review's severity filter behaves the same as guardrails'"""
        review_result = commands.review(_FIXTURE_REPO, severity_filter="error")
        guardrails_result = commands.guardrails(_FIXTURE_REPO, severity_filter="error")
        review_severities = {v.severity for v in (review_result.violations or [])}
        guardrails_severities = {v.severity for v in (guardrails_result.violations or [])}
        assert review_severities <= {"error"}
        assert review_severities == guardrails_severities

    def test_review_invalid_severity_filter_raises(self, commands: CliCommands) -> None:
        with pytest.raises(ValueError):
            commands.review(_FIXTURE_REPO, severity_filter="critical")

    def test_review_test_intelligence_section_appears_when_violations_exist(
        self, commands: CliCommands
    ) -> None:
        """Test Intelligence: review() on a repo with real violations must
        surface which flagged modules have real test coverage and which
        don't -- celery has real module_sizing/dependency_direction
        findings to exercise this against."""
        celery_repo = str(_REPO_ROOT / "repos" / "celery")
        if not Path(celery_repo).is_dir():
            pytest.skip("repos/celery fixture not present")
        result = commands.review(celery_repo)
        if result.violations:
            assert "Recommended tests" in result.content

    def test_feedback_command_records_and_returns_success(self, commands: CliCommands) -> None:
        result = commands.feedback(_FIXTURE_REPO, "module_sizing some.module", "reject", "test reason")
        assert isinstance(result, CliReport)
        assert result.success
        assert "test reason" in result.content

    def test_feedback_invalid_decision_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.feedback(_FIXTURE_REPO, "module_sizing some.module", "maybe")
        assert result.success is False

    def test_feedback_empty_finding_key_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.feedback(_FIXTURE_REPO, "", "accept")
        assert result.success is False

    def test_feedback_bad_repo_path_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.feedback("/definitely/not/a/real/path", "x y", "accept")
        assert result.success is False

    def test_reject_reason_surfaces_on_next_guardrails_run(self, commands: CliCommands) -> None:
        """End-to-end: reject a real finding with a reason, then confirm a
        fresh guardrails run cites that exact reason -- the roadmap's
        stated moat made real, not just unit-tested in isolation."""
        celery_repo = str(_REPO_ROOT / "repos" / "celery")
        if not Path(celery_repo).is_dir():
            pytest.skip("repos/celery fixture not present")

        first = commands.guardrails(celery_repo)
        if not first.violations:
            pytest.skip("no violations in fixture repo to attach feedback to")

        v = first.violations[0]
        finding_key = f"{v.rule_id} {v.location}"
        feedback_result = commands.feedback(
            celery_repo, finding_key, "reject", "confirmed false positive in this test"
        )
        assert feedback_result.success

        second = commands.guardrails(celery_repo)
        assert "confirmed false positive in this test" in second.content
        assert "Rejected before" in second.content

    def test_review_test_intelligence_excludes_test_modules_from_gaps(
        self, commands: CliCommands
    ) -> None:
        """A violation whose location includes a test file (e.g. a real
        cycle running through the repo's own test suite) must not
        recommend 'testing the test' -- test_* / *_test modules are
        excluded from the flagged-modules set entirely."""
        celery_repo = str(_REPO_ROOT / "repos" / "celery")
        if not Path(celery_repo).is_dir():
            pytest.skip("repos/celery fixture not present")
        result = commands.review(celery_repo)
        if "Coverage gaps" in result.content:
            gaps_section = result.content.split("Coverage gaps")[1]
            gap_lines = [l for l in gaps_section.splitlines() if l.strip().startswith("-")]
            for line in gap_lines:
                stem = line.strip("- ").rsplit(".", 1)[-1]
                assert not stem.startswith("test_"), f"test module leaked into gaps: {line}"
                assert not stem.endswith("_test"), f"test module leaked into gaps: {line}"

    def test_guardrails_command_real_scan(self, commands: CliCommands) -> None:
        """ortho guardrails check <path> runs a real scan against a real repo"""
        result = commands.guardrails(_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Architecture" in result.title
        assert "Scanned" in result.content or "violation" in result.content.lower() or "layer_boundaries" in result.content

    def test_guardrails_command_bad_path(self, commands: CliCommands) -> None:
        """guardrails on a nonexistent path fails cleanly, not a crash"""
        result = commands.guardrails("/definitely/not/a/real/path/xyz")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_decide_command_file_intent(self, commands: CliCommands) -> None:
        """ortho decide <file-path> runs real change-impact analysis"""
        target = str(_REPO_ROOT / "repos" / "requests" / "src" / "requests" / "models.py")
        result = commands.decide(target)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Decision" in result.title

    def test_decide_file_intent_honors_explicit_scan_path(self, commands: CliCommands) -> None:
        """A file intent with an explicit scan_path must scan that root, not
        silently narrow to the file's own parent directory -- an earlier
        version of this discarded the caller's explicit --scan-path every
        real caller (CLI, MCP) always passes, which broke test discovery
        for any repo where tests live in a sibling tests/ directory (the
        common layout)."""
        target = str(_REPO_ROOT / "repos" / "click" / "src" / "click" / "formatting.py")
        result = commands.decide(target, scan_path=_FIXTURE_REPO)
        assert result.success
        # click/tests/test_formatting.py is a real file only reachable if
        # the scan root was the repo root, not src/click/.
        assert "test_formatting" in result.content or "src.click.formatting" in result.content

    def test_decide_recommends_real_test_module_when_one_exists(self, commands: CliCommands) -> None:
        """Test Intelligence: click/src/click/formatting.py has a real
        matching test at click/tests/test_formatting.py -- decide() must
        surface it as a recommended test, not report a false coverage gap."""
        target = str(_REPO_ROOT / "repos" / "click" / "src" / "click" / "formatting.py")
        result = commands.decide(target, scan_path=_FIXTURE_REPO)
        assert result.success
        assert "Recommended tests" in result.content
        assert "test_formatting" in result.content

    def test_decide_reports_real_coverage_gap(self, commands: CliCommands) -> None:
        """click/src/click/core.py has no matching test_core.py anywhere in
        the repo -- must be reported as a genuine coverage gap, not
        silently omitted or fabricated as covered."""
        target = str(_REPO_ROOT / "repos" / "click" / "src" / "click" / "core.py")
        result = commands.decide(target, scan_path=_FIXTURE_REPO)
        assert result.success
        assert "Coverage gaps" in result.content

    def test_decide_command_text_intent_with_scan_path(self, commands: CliCommands) -> None:
        """ortho decide <text> with an explicit bounded scan_path"""
        result = commands.decide("improve code quality", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Decision" in result.title

    def test_decide_command_empty_intent(self, commands: CliCommands) -> None:
        """empty intent is rejected, not silently defaulted to an unbounded scan"""
        result = commands.decide("")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_report_has_content(self, commands: CliCommands) -> None:
        """Reports have content"""
        result = commands.plan("test", scan_path=_FIXTURE_REPO)
        assert result.content != ""
        assert "effort=" in result.content

    def test_guardrails_skips_file_with_syntax_error_without_crashing(self, tmp_path: Path) -> None:
        """A file with a real Python syntax error must be skipped (with a
        logged warning), not crash the whole scan — exercises repo_scanner's
        SyntaxError handling around CallGraphBuilder.extract_calls."""
        good_file = tmp_path / "good.py"
        good_file.write_text("def foo():\n    pass\n", encoding="utf-8")
        broken_file = tmp_path / "broken.py"
        broken_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

        result = CliCommands().guardrails(str(tmp_path))
        assert isinstance(result, CliReport)
        assert result.success

    def test_no_stub_literals_remain(self) -> None:
        """None of the four commands may contain the old unconditional-fake
        stub strings; all four must call their real backing engine."""
        source = Path(__file__).resolve().parents[1] / "src" / "cli_commands" / "commands.py"
        text = source.read_text(encoding="utf-8")
        assert "No violations found!" not in text  # old guardrails() stub (exact string, with "!")
        assert "Recommended: Option A" not in text  # old decide() stub
        assert "Path 1: Simple approach" not in text  # old plan() stub
        assert "[HIGH] Issue 1" not in text  # old refactor() stub
        assert "check_violations" in text  # guardrails() must call the real enforcer
        assert "DecisionEngine" in text  # decide() must call the real engine
        assert "FeaturePlanner" in text  # plan() must call the real planner
        assert "RefactoringAdvisor" in text  # refactor() must call the real advisor

    def test_ask_finds_real_match_with_evidence(self, commands: CliCommands) -> None:
        """ortho ask <question>: real repo, real graph evidence, no fabrication."""
        result = commands.ask(_FIXTURE_REPO, "how does formatting work", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "formatting" in result.content.lower()

    def test_ask_no_match_says_so_honestly(self, commands: CliCommands) -> None:
        result = commands.ask(_FIXTURE_REPO, "how does xyzzyplugh work", scan_path=_FIXTURE_REPO)
        assert result.success
        assert "No evidence found" in result.content

    def test_ask_empty_question_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.ask(_FIXTURE_REPO, "", scan_path=_FIXTURE_REPO)
        assert result.success is False

    def test_ask_stopwords_only_question_handled_honestly(self, commands: CliCommands) -> None:
        """A question with no extractable subject ('how does it work') must
        not silently search for a meaningless short word."""
        result = commands.ask(_FIXTURE_REPO, "how does it work", scan_path=_FIXTURE_REPO)
        assert result.success
        assert "Could not extract" in result.content

    def test_ask_bad_scan_path_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.ask(
            "/definitely/not/a/real/path", "how does auth work", scan_path="/definitely/not/a/real/path"
        )
        assert result.success is False
