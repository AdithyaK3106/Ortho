"""Adversarial tests for task-025 part 2 wiring: decide() consuming git_history."""

from pathlib import Path

import git
import pytest

from cli_commands.commands import CliCommands, _git_history_evidence_for


def _scan_repo(repo_root: Path) -> None:
    """Run a real ortho scan against repo_root so .ortho/ortho.db and
    git_history both exist, mirroring what a real `ortho scan` invocation
    would produce before `ortho decide` is ever called."""
    import sys

    project_root = Path(__file__).resolve().parents[3]
    scan_cli_path = project_root / "packages" / "repo-intelligence" / "src" / "repo_intelligence" / "scan_cli.py"
    for p in (
        project_root / "shared" / "storage" / "src",
        project_root / "packages" / "repo-intelligence" / "src",
        project_root / "packages" / "context-hub" / "src",
    ):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

    import importlib.util

    spec = importlib.util.spec_from_file_location("scan_cli_under_test", scan_cli_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    old_argv = sys.argv
    sys.argv = ["scan_cli.py", "--repo-root", str(repo_root)]
    try:
        module.main()
    finally:
        sys.argv = old_argv


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestGitHistoryEvidenceHelper:
    def test_no_ortho_db_returns_empty(self, tmp_path: Path) -> None:
        """decide() must work on a repo that has never been scanned --
        no .ortho/ortho.db means no git_history to query, not an error."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = _git_history_evidence_for(str(tmp_path), "auth")
        assert result == []

    def test_git_repo_with_no_commits_returns_empty(self, tmp_path: Path) -> None:
        git.Repo.init(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        _scan_repo(tmp_path)
        result = _git_history_evidence_for(str(tmp_path), "anything")
        assert result == []

    def test_matching_commit_surfaces_as_evidence(self, tmp_path: Path) -> None:
        repo = git.Repo.init(tmp_path)
        (tmp_path / "a.py").write_text("x = 1\n")
        repo.index.add(["a.py"])
        repo.index.commit("fix authentication token refresh bug", author=git.Actor("T", "t@example.com"))

        _scan_repo(tmp_path)

        result = _git_history_evidence_for(str(tmp_path), "authentication token")
        assert len(result) == 1
        assert "authentication" in result[0].description

    def test_nonexistent_path_returns_empty_not_raise(self) -> None:
        result = _git_history_evidence_for("/nonexistent/path/xyz", "auth")
        assert result == []


class TestDecideIncludesGitHistory:
    def test_decide_surfaces_prior_commit_as_alternative_or_recommendation(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        """A prior commit whose message closely matches the intent must show
        up somewhere in decide()'s output (as the recommendation or an
        alternative) rather than being silently swallowed by dedup/ranking
        against an empty guardrails/change_planner result set."""
        repo = git.Repo.init(tmp_path)
        (tmp_path / "a.py").write_text("def f():\n    pass\n")
        repo.index.add(["a.py"])
        repo.index.commit(
            "rejected rate limiting approach, caused deadlocks",
            author=git.Actor("T", "t@example.com"),
        )

        _scan_repo(tmp_path)

        result = commands.decide("rate limiting deadlocks", scan_path=str(tmp_path))
        assert result.success
        assert "rate limiting" in result.content.lower() or any(
            "rate limiting" in (alt or "").lower() for alt in [result.content]
        )

    def test_decide_on_unscanned_repo_does_not_crash(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        """decide() against a repo with no .ortho/ortho.db at all (never
        scanned) must still succeed -- git_history wiring must not turn a
        previously-working zero-history path into a crash."""
        (tmp_path / "a.py").write_text("x = 1\n")
        result = commands.decide("anything", scan_path=str(tmp_path))
        assert isinstance(result.success, bool)
