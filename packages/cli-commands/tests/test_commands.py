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
