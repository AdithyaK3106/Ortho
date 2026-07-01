"""Git metadata store: file churn tracking via git history."""

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

try:
    import git
except ImportError:
    git = None


logger = logging.getLogger(__name__)


@dataclass
class FileChurnMetadata:
    """Churn metrics for a file."""

    commit_count: int
    lines_added: int
    lines_removed: int
    last_modified: str


class GitMetadataStore:
    """Store and retrieve git history for files."""

    def __init__(self, db: sqlite3.Connection, repo_root: Path, repo_id: str):
        self.db = db
        self.repo_root = Path(repo_root)
        self.repo_id = repo_id
        self.git_repo = self._init_git_repo()

    def _init_git_repo(self):
        """Initialize git repository if available."""
        if not git:
            return None

        try:
            return git.Repo(self.repo_root)
        except git.InvalidGitRepositoryError:
            logger.debug(f"Not a git repo: {self.repo_root}")
            return None

    def load_git_history(self, file_id: str, file_rel_path: str) -> None:
        """
        Query git log for file, store in git_history table.

        Non-blocking: failures logged but not raised.
        """
        if not self.git_repo:
            return

        try:
            commits = list(self.git_repo.iter_commits(paths=file_rel_path, max_count=1000))
        except Exception as e:
            logger.warning(f"Failed to get git history for {file_rel_path}: {e}")
            return

        for commit in commits:
            self.db.execute(
                """
                INSERT OR IGNORE INTO git_history
                (file_id, repo_id, commit_hash, author, commit_date, message,
                 diff_lines_added, diff_lines_removed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    self.repo_id,
                    commit.hexsha,
                    commit.author.name,
                    commit.committed_datetime.isoformat(),
                    commit.message,
                    0,  # Simplified: full diff parsing deferred to Phase 2
                    0,
                ),
            )

        self.db.commit()

    def get_file_churn(self, file_id: str) -> FileChurnMetadata:
        """Return churn metrics: commit count, lines changed, last modified."""
        row = self.db.execute(
            """
            SELECT
                COUNT(*) as commit_count,
                SUM(COALESCE(diff_lines_added, 0)) as total_added,
                SUM(COALESCE(diff_lines_removed, 0)) as total_removed,
                MAX(commit_date) as last_modified
            FROM git_history
            WHERE file_id = ?
            """,
            (file_id,),
        ).fetchone()

        if not row:
            return FileChurnMetadata(
                commit_count=0,
                lines_added=0,
                lines_removed=0,
                last_modified=None,
            )

        return FileChurnMetadata(
            commit_count=row[0] or 0,
            lines_added=row[1] or 0,
            lines_removed=row[2] or 0,
            last_modified=row[3],
        )
