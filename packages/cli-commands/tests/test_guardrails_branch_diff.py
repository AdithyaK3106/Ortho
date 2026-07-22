"""Adversarial tests for task-025 part 4: guardrails --against-branch."""

from pathlib import Path

import git
import pytest

from cli_commands.commands import CliCommands, BranchNotFoundError, _changed_modules_against_branch


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


def _make_repo_with_branches(tmp_path: Path) -> "git.Repo":
    """main branch: pkg/a.py, pkg/b.py both exist and are unchanged since
    the branch point. feature branch (checked out as current HEAD): only
    pkg/a.py is modified."""
    repo = git.Repo.init(tmp_path)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "a.py").write_text("def f():\n    pass\n")
    (pkg / "b.py").write_text("def g():\n    pass\n")
    repo.index.add(["pkg/__init__.py", "pkg/a.py", "pkg/b.py"])
    repo.index.commit("initial", author=git.Actor("T", "t@example.com"))
    repo.git.branch("main")

    repo.git.checkout("-b", "feature")
    (pkg / "a.py").write_text("def f():\n    return 1\n")
    repo.index.add(["pkg/a.py"])
    repo.index.commit("modify a", author=git.Actor("T", "t@example.com"))

    return repo


class TestChangedModulesAgainstBranch:
    def test_only_changed_file_is_returned(self, tmp_path: Path) -> None:
        _make_repo_with_branches(tmp_path)
        modules = _changed_modules_against_branch(str(tmp_path), "main")
        assert modules == {"pkg.a"}

    def test_nonexistent_branch_raises_branch_not_found(self, tmp_path: Path) -> None:
        _make_repo_with_branches(tmp_path)
        with pytest.raises(BranchNotFoundError):
            _changed_modules_against_branch(str(tmp_path), "does-not-exist")

    def test_non_git_directory_raises_branch_not_found(self, tmp_path: Path) -> None:
        (tmp_path / "a.py").write_text("x = 1\n")
        with pytest.raises(BranchNotFoundError):
            _changed_modules_against_branch(str(tmp_path), "main")

    def test_non_python_changed_files_are_ignored(self, tmp_path: Path) -> None:
        repo = _make_repo_with_branches(tmp_path)
        (tmp_path / "README.md").write_text("docs change\n")
        repo.index.add(["README.md"])
        repo.index.commit("docs", author=git.Actor("T", "t@example.com"))
        modules = _changed_modules_against_branch(str(tmp_path), "main")
        assert modules == {"pkg.a"}

    def test_deleted_file_still_resolves_to_a_module(self, tmp_path: Path) -> None:
        """A file deleted on the feature branch still appears in `git diff
        --name-only` -- path_to_module must resolve it from the string path
        alone without needing the file to exist on disk."""
        repo = _make_repo_with_branches(tmp_path)
        (tmp_path / "pkg" / "b.py").unlink()
        repo.index.remove(["pkg/b.py"])
        repo.index.commit("remove b", author=git.Actor("T", "t@example.com"))
        modules = _changed_modules_against_branch(str(tmp_path), "main")
        assert "pkg.b" in modules


class TestGuardrailsAgainstBranch:
    def test_bad_branch_returns_failure_report_not_raise(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        _make_repo_with_branches(tmp_path)
        result = commands.guardrails(str(tmp_path), against_branch="nonexistent-branch")
        assert result.success is False
        assert "nonexistent-branch" in result.content

    def test_title_reflects_against_branch(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        _make_repo_with_branches(tmp_path)
        result = commands.guardrails(str(tmp_path), against_branch="main")
        assert "main" in result.title

    def test_without_against_branch_behaves_exactly_as_before(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        """Regression guard: omitting --against-branch must produce the
        exact same title/content shape as pre-task-025 guardrails()."""
        _make_repo_with_branches(tmp_path)
        result = commands.guardrails(str(tmp_path))
        assert result.title == f"Architecture Check: {str(tmp_path)}"

    def test_violation_outside_changed_files_is_excluded(
        self, commands: CliCommands, tmp_path: Path
    ) -> None:
        """A repo whose only violation lives in an unchanged module must
        report 'no violations' in --against-branch mode, even if a
        whole-repo scan would have found it."""
        repo = git.Repo.init(tmp_path)
        # Deliberately bloated unchanged module (>300 lines) to trigger a
        # real bloat-style finding via guardrails' own detectors, isolated
        # from whatever the feature branch touches.
        big = tmp_path / "bloated.py"
        big.write_text("\n".join(f"x{i} = {i}" for i in range(400)) + "\n")
        small = tmp_path / "small.py"
        small.write_text("y = 1\n")
        repo.index.add(["bloated.py", "small.py"])
        repo.index.commit("initial", author=git.Actor("T", "t@example.com"))
        repo.git.branch("main")

        repo.git.checkout("-b", "feature")
        small.write_text("y = 2\n")
        repo.index.add(["small.py"])
        repo.index.commit("touch small only", author=git.Actor("T", "t@example.com"))

        result = commands.guardrails(str(tmp_path), against_branch="main")
        assert result.success is True
        assert "bloated" not in result.content
