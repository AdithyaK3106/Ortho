"""Project memory: structured key/value store for project facts."""

import sqlite3
from datetime import datetime
from typing import Optional


class ProjectMemory:
    """Structured key/value store for project-level facts."""

    def __init__(self, db: sqlite3.Connection, repo_id: str):
        self.db = db
        self.repo_id = repo_id

    def set(self, key: str, value: str, source: str = "manual") -> None:
        """
        Store a project fact.

        Examples:
        - set('primary_language', 'python')
        - set('test_framework', 'pytest')
        - set('api_style', 'REST')
        - set('auth_approach', 'JWT')
        """
        self.db.execute(
            """
            INSERT OR REPLACE INTO project_memory
            (key, repo_id, value, source, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (key, self.repo_id, value, source, datetime.now().isoformat()),
        )
        self.db.commit()

    def get(self, key: str) -> Optional[str]:
        """Retrieve a project fact."""
        row = self.db.execute(
            "SELECT value FROM project_memory WHERE key = ? AND repo_id = ?",
            (key, self.repo_id),
        ).fetchone()
        return row[0] if row else None

    def list_all(self) -> dict[str, str]:
        """List all facts for this repo."""
        rows = self.db.execute(
            "SELECT key, value FROM project_memory WHERE repo_id = ?",
            (self.repo_id,),
        ).fetchall()
        return {row[0]: row[1] for row in rows}
