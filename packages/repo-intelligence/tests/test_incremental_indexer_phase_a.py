"""Tests for IncrementalIndexer (Phase A) — git diff logic."""

import pytest
from pathlib import Path
import tempfile
import subprocess
from repo_intelligence.incremental_indexer import (
    IncrementalIndexer,
    ChangedFile,
    NotAGitRepoError,
    MergeConflictError,
)


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=repo_root, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo_root,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=repo_root,
            capture_output=True,
        )
        yield repo_root


@pytest.fixture
def non_git_dir():
    """Create a temporary directory that is NOT a git repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestIncrementalIndexerBasic:
    """Basic functionality tests."""

    def test_is_git_repo_true(self, temp_git_repo):
        """Test is_git_repo() returns True for git repo."""
        indexer = IncrementalIndexer(temp_git_repo)
        assert indexer.is_git_repo() is True

    def test_is_git_repo_false(self, non_git_dir):
        """Test is_git_repo() returns False for non-git dir."""
        indexer = IncrementalIndexer(non_git_dir)
        assert indexer.is_git_repo() is False

    def test_init_with_repo_root(self, temp_git_repo):
        """Test initialization with repo root."""
        indexer = IncrementalIndexer(temp_git_repo)
        assert indexer.repo_root == temp_git_repo

    def test_get_changed_files_not_git_repo(self, non_git_dir):
        """Test get_changed_files() raises NotAGitRepoError for non-git dir."""
        indexer = IncrementalIndexer(non_git_dir)
        with pytest.raises(NotAGitRepoError):
            indexer.get_changed_files()


class TestIncrementalIndexerGitDiff:
    """Git diff detection tests."""

    def test_get_changed_files_added(self, temp_git_repo):
        """Test detecting added files."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create and commit initial file
        file1 = temp_git_repo / "file1.py"
        file1.write_text("# file 1")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Add new file
        file2 = temp_git_repo / "file2.py"
        file2.write_text("# file 2")
        subprocess.run(["git", "add", "file2.py"], cwd=temp_git_repo, capture_output=True)

        # Get changes since last commit
        changed = indexer.get_changed_files(since_commit='HEAD')
        added_files = [f.path for f in changed if f.is_added]

        assert "file2.py" in added_files

    def test_get_changed_files_modified(self, temp_git_repo):
        """Test detecting modified files."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create and commit file
        file1 = temp_git_repo / "file1.py"
        file1.write_text("# original")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Modify file
        file1.write_text("# modified")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)

        # Get changes
        changed = indexer.get_changed_files(since_commit='HEAD')
        modified_files = [f.path for f in changed if f.is_modified]

        assert "file1.py" in modified_files

    def test_get_changed_files_deleted(self, temp_git_repo):
        """Test detecting deleted files."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create and commit file
        file1 = temp_git_repo / "file1.py"
        file1.write_text("# content")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Delete file
        file1.unlink()
        subprocess.run(["git", "add", "-A"], cwd=temp_git_repo, capture_output=True)

        # Get changes
        changed = indexer.get_changed_files(since_commit='HEAD')
        deleted_files = [f.path for f in changed if f.is_deleted]

        assert "file1.py" in deleted_files


class TestIncrementalIndexerFullMode:
    """--full mode tests."""

    def test_get_changed_files_full_mode(self, temp_git_repo):
        """Test --full mode returns all tracked files."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create and commit multiple files
        for i in range(3):
            f = temp_git_repo / f"file{i}.py"
            f.write_text(f"# file {i}")
            subprocess.run(["git", "add", f"file{i}.py"], cwd=temp_git_repo, capture_output=True)

        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Get all files (full mode)
        changed = indexer.get_changed_files(strategy='full')

        assert len(changed) >= 3
        paths = [f.path for f in changed]
        assert "file0.py" in paths
        assert "file1.py" in paths
        assert "file2.py" in paths

    def test_get_changed_files_full_vs_git_diff(self, temp_git_repo):
        """Test full mode returns more files than incremental diff."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create initial files
        for i in range(3):
            f = temp_git_repo / f"file{i}.py"
            f.write_text(f"# file {i}")
            subprocess.run(["git", "add", f"file{i}.py"], cwd=temp_git_repo, capture_output=True)

        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Diff should be empty (no changes since last commit)
        diff_changed = indexer.get_changed_files(strategy='git', since_commit='HEAD')

        # Full should return all
        full_changed = indexer.get_changed_files(strategy='full')

        assert len(diff_changed) == 0
        assert len(full_changed) >= 3


class TestIncrementalIndexerFiltering:
    """File filtering tests."""

    def test_filter_python_files(self, temp_git_repo):
        """Test filter_python_files() extracts only .py files."""
        indexer = IncrementalIndexer(temp_git_repo)

        changes = [
            ChangedFile("file1.py", "A"),
            ChangedFile("file2.txt", "A"),
            ChangedFile("file3.py", "M"),
            ChangedFile("README.md", "A"),
        ]

        filtered = indexer.filter_python_files(changes)
        paths = [f.path for f in filtered]

        assert "file1.py" in paths
        assert "file3.py" in paths
        assert "file2.txt" not in paths
        assert "README.md" not in paths

    def test_filter_python_files_empty(self, temp_git_repo):
        """Test filter_python_files() with no Python files."""
        indexer = IncrementalIndexer(temp_git_repo)

        changes = [
            ChangedFile("file1.txt", "A"),
            ChangedFile("README.md", "M"),
        ]

        filtered = indexer.filter_python_files(changes)

        assert len(filtered) == 0


class TestIncrementalIndexerMergeConflicts:
    """Merge conflict detection tests."""

    def test_has_unmerged_changes_false(self, temp_git_repo):
        """Test has_unmerged_changes() returns False when no conflicts."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create initial commit
        file1 = temp_git_repo / "file1.py"
        file1.write_text("# content")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        assert indexer.has_unmerged_changes() is False

    def test_allow_unmerged_parameter(self, temp_git_repo):
        """Test allow_unmerged parameter allows skipping conflict check."""
        indexer = IncrementalIndexer(temp_git_repo)

        # Create initial file
        file1 = temp_git_repo / "file1.py"
        file1.write_text("# content")
        subprocess.run(["git", "add", "file1.py"], cwd=temp_git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=temp_git_repo, capture_output=True)

        # Should not raise even with allow_unmerged=True
        changed = indexer.get_changed_files(allow_unmerged=True)
        assert isinstance(changed, list)


class TestChangedFileDataclass:
    """Tests for ChangedFile dataclass."""

    def test_changed_file_properties(self):
        """Test ChangedFile properties."""
        added = ChangedFile("file1.py", "A")
        modified = ChangedFile("file2.py", "M")
        deleted = ChangedFile("file3.py", "D")

        assert added.is_added is True
        assert added.is_modified is False
        assert added.is_deleted is False

        assert modified.is_added is False
        assert modified.is_modified is True
        assert modified.is_deleted is False

        assert deleted.is_added is False
        assert deleted.is_modified is False
        assert deleted.is_deleted is True
