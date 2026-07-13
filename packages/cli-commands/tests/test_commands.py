"""CLI commands integration tests"""
import pytest

from cli_commands.commands import CliCommands
from cli_commands.types import CliReport


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestCommands:
    """Test CLI command execution"""

    def test_plan_command(self, commands: CliCommands) -> None:
        """ortho plan <intent>"""
        result = commands.plan("add user search endpoint")
        assert isinstance(result, CliReport)
        assert result.success
        assert "Feature Plan" in result.title

    def test_refactor_command(self, commands: CliCommands) -> None:
        """ortho refactor [path]"""
        result = commands.refactor("src/service.py")
        assert isinstance(result, CliReport)
        assert result.success
        assert "Refactoring" in result.title

    def test_guardrails_command(self, commands: CliCommands) -> None:
        """ortho guardrails check"""
        result = commands.guardrails()
        assert isinstance(result, CliReport)
        assert result.success
        assert "Architecture" in result.title

    def test_decide_command(self, commands: CliCommands) -> None:
        """ortho decide <intent>"""
        result = commands.decide("improve code quality")
        assert isinstance(result, CliReport)
        assert result.success
        assert "Decision" in result.title

    def test_report_has_content(self, commands: CliCommands) -> None:
        """Reports have content"""
        result = commands.plan("test")
        assert result.content != ""
        assert "Path" in result.content

    def test_all_commands_work(self, commands: CliCommands) -> None:
        """All commands execute"""
        assert commands.plan("a").success
        assert commands.refactor("b").success
        assert commands.guardrails("c").success
        assert commands.decide("d").success
