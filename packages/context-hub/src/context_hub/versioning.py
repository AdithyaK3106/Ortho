"""Artifact versioning logic: immutable versions, hash-based identity."""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


def make_artifact_id(repo_id: str, title: str, source: str, content_hash: str) -> str:
    """
    Generate stable artifact ID (hash-based, not timestamp).

    Ensures same artifact (repo + title + source + content) always gets same ID.
    """
    base = f"{repo_id}:{title}:{source}:{content_hash[:8]}"
    return hashlib.sha256(base.encode()).hexdigest()[:16]


def make_content_hash(content: str) -> str:
    """Generate SHA256 hash of content for versioning."""
    return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class VersionInfo:
    """Information about an artifact version."""

    artifact_id: str
    version: int
    content_hash: str
    is_latest: bool


def get_next_version(db: sqlite3.Connection, artifact_id: str) -> int:
    """Get the next version number for an artifact."""
    row = db.execute(
        "SELECT MAX(version) FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()
    max_version = row[0] if row and row[0] else 0
    return max_version + 1


def check_content_changed(
    db: sqlite3.Connection, artifact_id: str, new_content_hash: str
) -> bool:
    """Check if artifact content has changed since last version."""
    row = db.execute(
        "SELECT content_hash FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1",
        (artifact_id,),
    ).fetchone()

    if not row:
        return True  # No existing version, content "changed" (from nothing)

    return row[0] != new_content_hash


def get_artifact_version_count(db: sqlite3.Connection, artifact_id: str) -> int:
    """Get total number of versions for an artifact."""
    row = db.execute(
        "SELECT COUNT(*) FROM artifacts WHERE id = ?", (artifact_id,)
    ).fetchone()
    return row[0] if row else 0
