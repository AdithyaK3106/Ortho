"""Incremental indexer using git diff to detect changed files."""

from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import subprocess


@dataclass
class ChangedFile:
    """Represents a changed file in git diff."""
    path: str
    status: str  # 'A' (added), 'M' (modified), 'D' (deleted), 'R' (renamed)

    @property
    def is_added(self) -> bool:
        return self.status == 'A'

    @property
    def is_modified(self) -> bool:
        return self.status == 'M'

    @property
    def is_deleted(self) -> bool:
        return self.status == 'D'


@dataclass
class IndexDelta:
    """Result of incremental indexing."""
    added_files: List[str]
    modified_files: List[str]
    deleted_files: List[str]
    errors: List[str]

    @property
    def total_changed(self) -> int:
        return len(self.added_files) + len(self.modified_files) + len(self.deleted_files)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class NotAGitRepoError(Exception):
    """Raised when .git directory not found."""
    pass


class MergeConflictError(Exception):
    """Raised when unmerged files are detected."""
    pass


class IncrementalIndexer:
    """Incremental indexer for git-based change detection."""

    def __init__(self, repo_root: Path) -> None:
        """
        Initialize incremental indexer.

        Args:
            repo_root: Project root directory
        """
        self.repo_root = Path(repo_root)
        self._is_git_repo: bool | None = None  # Cache git repo status

    def is_git_repo(self) -> bool:
        """
        Check if repository is a valid git repository.

        Returns:
            True if .git exists, False otherwise
        """
        if self._is_git_repo is None:
            self._is_git_repo = (self.repo_root / ".git").exists()
        return self._is_git_repo

    def get_changed_files(self, strategy: str = 'git', since_commit: str | None = None, allow_unmerged: bool = False) -> List[ChangedFile]:
        """
        Detect changed files via git diff or full scan.

        Args:
            strategy: 'git' (diff-based) or 'full' (no change detection, index all files)
            since_commit: Git reference for diff (e.g., 'HEAD~1', 'HEAD'). If None, uses HEAD.
            allow_unmerged: If True, skip merge conflict check and index unmerged files anyway.

        Returns:
            List of ChangedFile objects

        Raises:
            NotAGitRepoError: If not a git repository
            MergeConflictError: If unmerged files detected and allow_unmerged=False
        """
        if not self.is_git_repo():
            raise NotAGitRepoError(f"Not a git repository: {self.repo_root}")

        if strategy == 'full':
            return self._get_all_files()

        # Check for merge conflicts unless explicitly allowed
        if not allow_unmerged:
            self._check_merge_conflicts()

        # Get git diff
        return self._compute_git_diff(since_commit or 'HEAD')

    def _check_merge_conflicts(self) -> None:
        """
        Check for unmerged files (merge conflicts).

        Raises:
            MergeConflictError: If unmerged files detected
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.startswith("UU "):  # Unmerged both modified
                        raise MergeConflictError(
                            f"Merge conflict detected: {line[3:]}. "
                            "Resolve conflicts before re-indexing."
                        )
        except subprocess.TimeoutExpired:
            raise NotAGitRepoError("git status timeout")
        except MergeConflictError:
            raise
        except Exception as e:
            raise NotAGitRepoError(f"Failed to check merge status: {e}")

    def _compute_git_diff(self, since_commit: str) -> List[ChangedFile]:
        """
        Compute git diff between since_commit and HEAD.

        Args:
            since_commit: Git reference (e.g., 'HEAD', 'HEAD~1')

        Returns:
            List of ChangedFile objects (A, M, D statuses)

        Raises:
            NotAGitRepoError: If git diff fails
        """
        changed_files: List[ChangedFile] = []

        # Reject option-shaped refs so a value like "--output=..." can't be
        # parsed by git as a flag (argument injection).
        if since_commit.startswith("-"):
            raise NotAGitRepoError(f"Invalid git reference: {since_commit}")

        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", "--diff-filter=AMDR", since_commit, "--"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise NotAGitRepoError(f"git diff failed: {result.stderr}")

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) == 2:
                    status, file_path = parts
                    changed_files.append(ChangedFile(file_path, status))

        except subprocess.TimeoutExpired:
            raise NotAGitRepoError("git diff timeout")
        except NotAGitRepoError:
            raise
        except Exception as e:
            raise NotAGitRepoError(f"git diff failed: {e}")

        return changed_files

    def _get_all_files(self) -> List[ChangedFile]:
        """
        Get all tracked files (for --full flag).

        Returns:
            List of all files marked as 'A' (added for full index)
        """
        all_files: List[ChangedFile] = []

        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise NotAGitRepoError(f"git ls-files failed: {result.stderr}")

            for line in result.stdout.strip().split("\n"):
                if line:
                    all_files.append(ChangedFile(line, 'A'))

        except subprocess.TimeoutExpired:
            raise NotAGitRepoError("git ls-files timeout")
        except NotAGitRepoError:
            raise
        except Exception as e:
            raise NotAGitRepoError(f"git ls-files failed: {e}")

        return all_files

    def filter_python_files(self, changed_files: List[ChangedFile]) -> List[ChangedFile]:
        """
        Filter changed files to only Python files.

        Args:
            changed_files: List of ChangedFile objects

        Returns:
            Filtered list containing only .py files
        """
        return [f for f in changed_files if f.path.endswith('.py')]

    def has_unmerged_changes(self) -> bool:
        """
        Check if repository has unmerged changes (merge in progress).

        Returns:
            True if unmerged files exist, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "ls-files", "--unmerged"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except Exception:
            return False
