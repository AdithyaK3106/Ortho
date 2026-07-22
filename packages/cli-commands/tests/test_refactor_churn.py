"""Adversarial tests for task-025 part 3: git-history-backed churn detection
in CodeRepositoryAdapter.get_high_churn_modules().
"""

from pathlib import Path

import git
import pytest

from cli_commands.commands import CliCommands
from cli_commands.refactor_adapter import CodeRepositoryAdapter, _HIGH_CHURN_COMMIT_THRESHOLD
from cli_commands.repo_scanner import scan_repository


def _scan_via_ortho_scan(repo_root: Path) -> None:
    """Run the real `ortho scan` entry point so .ortho/ortho.db + git_history
    exist, exactly as they would before a real `ortho refactor` call."""
    import sys
    import importlib.util

    project_root = Path(__file__).resolve().parents[3]
    scan_cli_path = project_root / "packages" / "repo-intelligence" / "src" / "repo_intelligence" / "scan_cli.py"
    for p in (
        project_root / "shared" / "storage" / "src",
        project_root / "packages" / "repo-intelligence" / "src",
        project_root / "packages" / "context-hub" / "src",
    ):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    spec = importlib.util.spec_from_file_location("scan_cli_under_test_churn", scan_cli_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    old_argv = sys.argv
    sys.argv = ["scan_cli.py", "--repo-root", str(repo_root)]
    try:
        module.main()
    finally:
        sys.argv = old_argv


def _commit_n_times(repo: "git.Repo", repo_root: Path, filename: str, n: int) -> None:
    f = repo_root / filename
    for i in range(n):
        f.write_text(f"x = {i}\n")
        repo.index.add([filename])
        repo.index.commit(f"edit {i}", author=git.Actor("T", "t@example.com"))


class TestHighChurnDetection:
    def test_module_above_threshold_is_flagged(self, tmp_path: Path) -> None:
        repo = git.Repo.init(tmp_path)
        _commit_n_times(repo, tmp_path, "hot.py", _HIGH_CHURN_COMMIT_THRESHOLD + 1)

        _scan_via_ortho_scan(tmp_path)

        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        churned = adapter.get_high_churn_modules()
        assert "hot" in churned

    def test_module_at_exactly_threshold_is_not_flagged(self, tmp_path: Path) -> None:
        """Boundary check: the spec says '> 20', not '>= 20' -- a module with
        exactly the threshold commit count must NOT be flagged."""
        repo = git.Repo.init(tmp_path)
        _commit_n_times(repo, tmp_path, "warm.py", _HIGH_CHURN_COMMIT_THRESHOLD)

        _scan_via_ortho_scan(tmp_path)

        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        churned = adapter.get_high_churn_modules()
        assert "warm" not in churned

    def test_module_below_threshold_is_not_flagged(self, tmp_path: Path) -> None:
        repo = git.Repo.init(tmp_path)
        _commit_n_times(repo, tmp_path, "cold.py", 3)

        _scan_via_ortho_scan(tmp_path)

        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        churned = adapter.get_high_churn_modules()
        assert "cold" not in churned

    def test_test_module_excluded_even_if_high_churn(self, tmp_path: Path) -> None:
        """A frequently-edited test file must never appear in the
        "high churn, prioritize for refactoring" debt list -- matches the
        same test-module exclusion get_bloated_modules() already applies."""
        repo = git.Repo.init(tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        f = tests_dir / "test_hot.py"
        for i in range(_HIGH_CHURN_COMMIT_THRESHOLD + 5):
            f.write_text(f"x = {i}\n")
            repo.index.add(["tests/test_hot.py"])
            repo.index.commit(f"edit {i}", author=git.Actor("T", "t@example.com"))

        _scan_via_ortho_scan(tmp_path)

        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        churned = adapter.get_high_churn_modules()
        assert not any("test_hot" in m for m in churned)

    def test_no_git_repo_returns_empty(self, tmp_path: Path) -> None:
        """A plain directory, never a git repo -- churn lookup must not
        raise just because `ortho scan` was still run against it."""
        (tmp_path / "a.py").write_text("x = 1\n")
        _scan_via_ortho_scan(tmp_path)
        scan = scan_repository(str(tmp_path))
        adapter = CodeRepositoryAdapter(scan)
        assert adapter.get_high_churn_modules() == []

    def test_refactor_command_surfaces_debt_finding_end_to_end(self, tmp_path: Path) -> None:
        """Full path: real git history -> real scan -> ortho refactor's
        rendered report actually mentions the churned module."""
        repo = git.Repo.init(tmp_path)
        _commit_n_times(repo, tmp_path, "hot.py", _HIGH_CHURN_COMMIT_THRESHOLD + 1)

        _scan_via_ortho_scan(tmp_path)

        result = CliCommands().refactor(str(tmp_path))
        assert result.success
        assert "debt" in result.content.lower()
        assert "hot" in result.content.lower()
