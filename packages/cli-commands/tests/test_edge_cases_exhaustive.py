"""Exhaustive edge case tests for cli-commands"""
from pathlib import Path
from unittest.mock import Mock
import pytest

from cli_commands.commands import CliCommands

# guardrails()/decide()/plan()/refactor() now all run a real filesystem
# scan. Bare "." from this repo's cwd would walk repos/ (7800+ vendored
# files across multiple cloned frameworks) — bound these tests to a small
# real fixture instead. (plan()/refactor() were fake stubs, ignoring all
# arguments, when this file was first written; task-019 wired them to
# real engines, so calls that previously used arbitrary/fictional paths
# now need a real bounded target or must expect success=False from a
# genuine FileNotFoundError.)
_SMALL_FIXTURE = str(Path(__file__).resolve().parents[3] / "repos" / "requests")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_empty_intent(self, commands: CliCommands) -> None:
        """Empty intent string is rejected without scanning (success=False)"""
        result = commands.plan("")
        assert result is not None
        assert result.success is False

    def test_whitespace_intent(self, commands: CliCommands) -> None:
        """Whitespace-only intent is truthy as a str, so it is NOT rejected
        by the empty-string check — it reaches the real scan/engine."""
        result = commands.plan("   \n\t  ", scan_path=_SMALL_FIXTURE)
        assert result is not None
        assert result.success is True

    def test_very_long_intent(self, commands: CliCommands) -> None:
        """100K character intent, bounded scan"""
        long_intent = "add " + "x" * 100000
        result = commands.plan(long_intent, scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_shell_injection_intent(self, commands: CliCommands) -> None:
        """Intent with shell metacharacters must not be interpreted by a
        shell (no subprocess/os.system is used anywhere in plan()'s path,
        by construction) and must not crash the classifier/renderer."""
        result = commands.plan("add $(malicious_command)", scan_path=_SMALL_FIXTURE)
        assert result is not None
        assert result.success is True

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
        """Valid plan call, bounded scan"""
        result = commands.plan("add authentication", scan_path=_SMALL_FIXTURE)
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
        """Guardrails check with a nonexistent path fails cleanly.

        Regression: a bare "src/" is a path that happens to genuinely
        exist relative to this package's own cwd during a pytest run
        (packages/cli-commands/src/), so guardrails() correctly scanned it
        and succeeded -- the opposite of what this test asserts. A path
        guaranteed not to exist under any cwd is required to actually test
        the "nonexistent path" case.
        """
        result = commands.guardrails("definitely/not/a/real/path/xyz")
        assert result is not None
        assert result.success is False

    def test_decide_with_valid_intent(self, commands: CliCommands) -> None:
        """Valid decide call, bounded to a real fixture repo"""
        result = commands.decide("add feature", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_output_format_valid(self, commands: CliCommands) -> None:
        """Output should have required fields"""
        result = commands.plan("add feature", scan_path=_SMALL_FIXTURE)
        assert hasattr(result, "title")
        assert hasattr(result, "content")
        assert hasattr(result, "success")

    def test_exit_code_success(self, commands: CliCommands) -> None:
        """Success should be boolean"""
        result = commands.plan("add feature", scan_path=_SMALL_FIXTURE)
        assert isinstance(result.success, bool)

    def test_none_input_handling(self, commands: CliCommands) -> None:
        """None input is falsy, rejected without scanning (success=False)"""
        result = commands.plan(None)
        assert result is not None
        assert result.success is False

    def test_numeric_intent(self, commands: CliCommands) -> None:
        """Numeric intent is truthy (not "" and not None), so it reaches
        FeaturePlanner._classify_feature_type, which calls .lower() on
        it — a real crash risk for a non-str intent that `not intent`
        alone does not guard against."""
        result = commands.plan(123, scan_path=_SMALL_FIXTURE)  # type: ignore[arg-type]
        assert result is not None
        assert result.success is False

    def test_special_chars_in_intent(self, commands: CliCommands) -> None:
        """Intent with special characters"""
        result = commands.plan("add $feature@home#test", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_newlines_in_intent(self, commands: CliCommands) -> None:
        """Intent with newlines"""
        result = commands.plan("add\nfeature\nwith\nnewlines", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_tabs_in_intent(self, commands: CliCommands) -> None:
        """Intent with tabs"""
        result = commands.plan("add\t\tfeature\t\twith\t\ttabs", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_very_long_path(self, commands: CliCommands) -> None:
        """Very long, nonexistent file path fails fast (FileNotFoundError
        before any scan starts) rather than hanging."""
        long_path = "/" + "/".join(["dir"] * 1000) + "/file.py"
        result = commands.refactor(long_path)
        assert result is not None
        assert result.success is False

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
        result = commands.plan("AdD FEature WiTh CaSeS", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_repeated_spaces(self, commands: CliCommands) -> None:
        """Intent with repeated spaces"""
        result = commands.plan("add     feature     with     spaces", scan_path=_SMALL_FIXTURE)
        assert result is not None

    def test_refactor_no_path(self, commands: CliCommands) -> None:
        """Refactor with no path argument defaults to '.'; call it with cwd
        already changed to a small real fixture so the default-to-cwd
        behavior is exercised without scanning the whole monorepo."""
        import os

        original_cwd = os.getcwd()
        os.chdir(_SMALL_FIXTURE)
        try:
            result = commands.refactor()
        finally:
            os.chdir(original_cwd)
        assert result is not None
        assert result.success is True
