"""Staleness detector: flag artifacts whose source has changed."""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class StalenessReport:
    """Report on artifact staleness."""

    is_stale: bool
    reason: str
    last_verified_at: str


class StalenessDetector:
    """Detect if artifact source content has changed."""

    def __init__(self, db: sqlite3.Connection, repo_root: Path):
        self.db = db
        self.repo_root = Path(repo_root)

    def check_staleness(self, artifact_id: str) -> StalenessReport:
        """
        Compare artifact.content_hash against live file content.

        Non-file artifacts (manual, generated) are never stale.
        File artifacts are stale if source file missing or content changed.
        """
        # Get artifact
        row = self.db.execute(
            "SELECT source, content_hash FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1",
            (artifact_id,),
        ).fetchone()

        if not row:
            return StalenessReport(
                is_stale=True,
                reason="artifact not found",
                last_verified_at=datetime.now().isoformat(),
            )

        source, content_hash = row

        # Non-file artifacts are never stale
        if not source.startswith(("/", ".")) or source in ("manual", "generated"):
            return StalenessReport(
                is_stale=False,
                reason="non-file artifact",
                last_verified_at=datetime.now().isoformat(),
            )

        # Check if file exists
        file_path = self.repo_root / source
        if not file_path.exists():
            return StalenessReport(
                is_stale=True,
                reason="source file deleted",
                last_verified_at=datetime.now().isoformat(),
            )

        # Check if content changed
        try:
            live_content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            return StalenessReport(
                is_stale=True,
                reason=f"cannot read file: {e}",
                last_verified_at=datetime.now().isoformat(),
            )

        live_hash = hashlib.sha256(live_content.encode()).hexdigest()
        is_stale = live_hash != content_hash

        return StalenessReport(
            is_stale=is_stale,
            reason="content mismatch" if is_stale else "up-to-date",
            last_verified_at=datetime.now().isoformat(),
        )
