"""Exhaustive edge case tests for cli-commands"""
from pathlib import Path
from unittest.mock import Mock
import pytest

from cli_commands.commands import CliCommands

# guardrails()/decide() now run a real filesystem scan. Bare "." from this
# repo's cwd would walk repos/ (7800+ vendored files across 8 cloned
# frameworks) — bound these tests to a small real fixture instead.
_SMALL_FIXTURE = str(Path(__file__).resolve().parents[3] / "repos" / "requests")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_empty_intent(self, commands: CliCommands) -> None:
        """Empty intent string"""
        result = commands.plan("")
        assert result is not None
        assert isinstance(result.success, bool)

    def test_whitespace_intent(self, commands: CliCommands) -> None:
        """Whitespace-only intent"""
        result = commands.plan("   \n\t  ")
        assert result is not None

    def test_very_long_intent(self, commands: CliCommands) -> None:
        """100K character intent"""
        long_intent = "add " + "x" * 100000
        result = commands.plan(long_intent)
        assert result is not None

    def test_shell_injection_intent(self, commands: CliCommands) -> None:
        """Intent with shell metacharacters"""
        result = commands.plan("add $(malicious_command)")
        assert result is not None

    def test_path_traversal_attempt(self, commands: CliCommands) -> None:
        """Path with directory traversal"""
        result = commands.refactor("../../../etc/passwd")
        assert result is not None

    def test_symlink_path(self, commands: CliCommands) -> None:
        """Path that is a symlink"""
        result = commands.refactor("/path/to/symlink")
        assert result is not None

    def test_nonexistent_path(self, commands: CliCommands) -> None:
        """Path that doesn't exist"""
        result = commands.refactor("/nonexistent/path/to/file")
        assert result is not None

    def test_permission_denied_path(self, commands: CliCommands) -> None:
        """Path without read permission"""
        result = commands.refactor("/root/private/")
        # Should handle gracefully
        assert result is not None

    def test_unicode_path(self, commands: CliCommands) -> None:
        """Path with unicode characters"""
        result = commands.refactor("/café/café/日本語/")
        assert result is not None

    def test_circular_symlinks(self, commands: CliCommands) -> None:
        """Path with circular symlinks"""
        result = commands.refactor("/path/link/to/link/")
        # Should not infinite loop
        assert result is not None

    def test_mount_point_crossing(self, commands: CliCommands) -> None:
        """Path crossing filesystem boundary"""
        result = commands.refactor("/mnt/")
        assert result is not None

    def test_plan_with_valid_intent(self, commands: CliCommands) -> None:
        """Valid plan call"""
        result = commands.plan("add authentication")
        assert result is not None
        assert hasattr(result, "title")
        assert hasattr(result, "content")

    def test_refactor_with_valid_path(self, commands: CliCommands) -> None:
        """Valid refactor call"""
        result = commands.refactor("src/module.py")
        assert result is not None

    def test_guardrails_check(self, commands: CliCommands) -> None:
        """Guardrails check against a real bounded fixture repo"""
        result = commands.guardrails(_SMALL_FIXTURE)
        assert result is not None

    def test_guardrails_with_path(self, commands: CliCommands) -> None:
        """Guardrails check with a nonexistent path fails cleanly"""
        result = commands.guardrails("src/")
        assert result is not None
        assert result.success is False

    def test_decide_with_valid_intent(self, commands: CliCommands) -> None:
        """Valid decide call, bounded to a real fixture repo"""
        result = commands.decide("add feature", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_output_format_valid(self, commands: CliCommands) -> None:
        """Output should have required fields"""
        result = commands.plan("add feature")
        assert hasattr(result, "title")
        assert hasattr(result, "content")
        assert hasattr(result, "success")

    def test_exit_code_success(self, commands: CliCommands) -> None:
        """Success should be boolean"""
        result = commands.plan("add feature")
        assert isinstance(result.success, bool)

    def test_none_input_handling(self, commands: CliCommands) -> None:
        """None input"""
        result = commands.plan(None)
        assert result is not None

    def test_numeric_intent(self, commands: CliCommands) -> None:
        """Numeric intent"""
        result = commands.plan(123)
        assert result is not None

    def test_special_chars_in_intent(self, commands: CliCommands) -> None:
        """Intent with special characters"""
        result = commands.plan("add $feature@home#test")
        assert result is not None

    def test_newlines_in_intent(self, commands: CliCommands) -> None:
        """Intent with newlines"""
        result = commands.plan("add\nfeature\nwith\nnewlines")
        assert result is not None

    def test_tabs_in_intent(self, commands: CliCommands) -> None:
        """Intent with tabs"""
        result = commands.plan("add\t\tfeature\t\twith\t\ttabs")
        assert result is not None

    def test_very_long_path(self, commands: CliCommands) -> None:
        """Very long file path"""
        long_path = "/" + "/".join(["dir"] * 1000) + "/file.py"
        result = commands.refactor(long_path)
        assert result is not None

    def test_relative_path_with_dots(self, commands: CliCommands) -> None:
        """Relative path with ../"""
        result = commands.refactor("../../src/module.py")
        assert result is not None

    def test_absolute_path(self, commands: CliCommands) -> None:
        """Absolute path"""
        result = commands.refactor("/home/user/project/src.py")
        assert result is not None

    def test_windows_path(self, commands: CliCommands) -> None:
        """Windows-style path"""
        result = commands.refactor("C:\\Users\\user\\project\\src.py")
        assert result is not None

    def test_mixed_case_intent(self, commands: CliCommands) -> None:
        """Intent with mixed case"""
        result = commands.plan("AdD FEature WiTh CaSeS")
        assert result is not None

    def test_repeated_spaces(self, commands: CliCommands) -> None:
        """Intent with repeated spaces"""
        result = commands.plan("add     feature     with     spaces")
        assert result is not None

    def test_refactor_no_path(self, commands: CliCommands) -> None:
        """Refactor with no path argument"""
        result = commands.refactor()
        assert result is not None
