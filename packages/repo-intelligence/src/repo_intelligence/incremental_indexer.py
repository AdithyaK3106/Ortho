"""Incremental indexer using git diff to detect changed files."""

from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import subprocess


class IndexDelta:
    """Result of incremental indexing."""
    def __init__(
        self,
        added_symbols: List = None,
        modified_symbols: List = None,
        removed_symbols: List = None,
    ):
        self.added_symbols = added_symbols or []
        self.modified_symbols = modified_symbols or []
        self.removed_symbols = removed_symbols or []


class NotAGitRepoError(Exception):
    """Raised when .git directory not found."""
    pass


class IncrementalIndexer:
    """Incremental indexer for git-based change detection."""

    def __init__(self, repo_root: Path, storage):
        """
        Initialize incremental indexer.

        Args:
            repo_root: Project root directory
            storage: OrthoDatabase instance
        """
        self.repo_root = Path(repo_root)
        self.storage = storage

    def index_incremental(self) -> IndexDelta:
        """
        Compute git diff and re-index only changed files.

        Returns:
            IndexDelta with added, modified, removed symbols

        Raises:
            NotAGitRepoError: If .git does not exist or git fails
        """
        if not (self.repo_root / ".git").exists():
            raise NotAGitRepoError(f"Not a git repository: {self.repo_root}")

        # Get last indexed timestamp
        last_indexed = self._get_last_indexed_timestamp()

        # Compute git diff
        changed_files = self._compute_git_diff(last_indexed)

        # Re-index changed files
        delta = self._reindex_changed_files(changed_files)

        # Update timestamp
        self._update_last_indexed_timestamp()

        return delta

    def _get_last_indexed_timestamp(self) -> str:
        """Get last indexed timestamp from database."""
        try:
            cursor = self.storage.db.cursor()
            cursor.execute(
                "SELECT last_indexed_at FROM repositories WHERE root_path = ? ORDER BY last_indexed_at DESC LIMIT 1",
                (str(self.repo_root),),
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def _compute_git_diff(self, last_indexed: str) -> dict:
        """
        Compute git diff since last indexed time.

        Returns:
            dict with 'added', 'modified', 'deleted' file lists
        """
        changed_files = {"added": [], "modified": [], "deleted": []}

        try:
            if last_indexed:
                cmd = [
                    "git",
                    "diff",
                    "--name-status",
                    f"{last_indexed}...HEAD",
                ]
            else:
                cmd = ["git", "ls-files", "--others", "--exclude-standard"]

            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    if last_indexed:
                        status, file_path = line.split("\t", 1)
                        if status == "A":
                            changed_files["added"].append(file_path)
                        elif status == "M":
                            changed_files["modified"].append(file_path)
                        elif status == "D":
                            changed_files["deleted"].append(file_path)
                    else:
                        changed_files["added"].append(line)

        except subprocess.TimeoutExpired:
            raise NotAGitRepoError("git diff timeout")
        except Exception as e:
            raise NotAGitRepoError(f"git diff failed: {e}")

        return changed_files

    def _reindex_changed_files(self, changed_files: dict) -> IndexDelta:
        """Re-index changed files and return delta."""
        delta = IndexDelta()

        for file_path in changed_files["added"]:
            self._reindex_file(file_path, delta, "added")

        for file_path in changed_files["modified"]:
            self._remove_file_entries(file_path)
            self._reindex_file(file_path, delta, "modified")

        for file_path in changed_files["deleted"]:
            self._remove_file_entries(file_path)
            delta.removed_symbols.append(file_path)

        return delta

    def _reindex_file(self, file_path: str, delta: IndexDelta, operation: str):
        """Re-index a single file (placeholder for symbol/call extraction)."""
        full_path = self.repo_root / file_path
        if full_path.exists() and full_path.suffix == ".py":
            if operation == "added":
                delta.added_symbols.append(file_path)
            elif operation == "modified":
                delta.modified_symbols.append(file_path)

    def _remove_file_entries(self, file_path: str):
        """Remove all entries for a file from database."""
        try:
            cursor = self.storage.db.cursor()
            cursor.execute(
                "DELETE FROM symbols WHERE file_id IN (SELECT id FROM files WHERE path = ?)",
                (file_path,),
            )
            cursor.execute(
                "DELETE FROM call_edges WHERE caller_id IN (SELECT id FROM symbols WHERE file_id IN (SELECT id FROM files WHERE path = ?))",
                (file_path,),
            )
            self.storage.db.commit()
        except Exception:
            pass

    def _update_last_indexed_timestamp(self):
        """Update last_indexed_at timestamp in database."""
        try:
            now = datetime.now().isoformat()
            cursor = self.storage.db.cursor()
            cursor.execute(
                "UPDATE repositories SET last_indexed_at = ? WHERE root_path = ?",
                (now, str(self.repo_root)),
            )
            self.storage.db.commit()
        except Exception:
            pass
