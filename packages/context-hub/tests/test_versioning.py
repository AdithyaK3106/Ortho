"""Tests for artifact versioning logic."""

import pytest

from context_hub.versioning import (
    check_content_changed,
    get_artifact_version_count,
    get_next_version,
    make_artifact_id,
    make_content_hash,
)


class TestVersioning:
    """Test artifact versioning and content change detection."""

    def test_make_artifact_id_deterministic(self):
        """Same inputs produce same artifact ID."""
        id1 = make_artifact_id("repo1", "Title", "source.md", "abc123")
        id2 = make_artifact_id("repo1", "Title", "source.md", "abc123")
        assert id1 == id2

    def test_make_artifact_id_different_title(self):
        """Different title produces different ID."""
        id1 = make_artifact_id("repo1", "Title A", "source.md", "abc123")
        id2 = make_artifact_id("repo1", "Title B", "source.md", "abc123")
        assert id1 != id2

    def test_make_artifact_id_length(self):
        """Artifact ID is exactly 16 characters."""
        artifact_id = make_artifact_id("repo1", "Title", "source.md", "hash")
        assert len(artifact_id) == 16
        assert all(c in "0123456789abcdef" for c in artifact_id)

    def test_make_content_hash_deterministic(self):
        """Same content produces same hash."""
        hash1 = make_content_hash("Content here")
        hash2 = make_content_hash("Content here")
        assert hash1 == hash2

    def test_make_content_hash_different_content(self):
        """Different content produces different hash."""
        hash1 = make_content_hash("Content A")
        hash2 = make_content_hash("Content B")
        assert hash1 != hash2

    def test_make_content_hash_length(self):
        """Content hash is SHA256 (64 chars)."""
        content_hash = make_content_hash("Content")
        assert len(content_hash) == 64
        assert all(c in "0123456789abcdef" for c in content_hash)

    def test_get_next_version_first_artifact(self, temp_db):
        """First artifact has version 1."""
        next_ver = get_next_version(temp_db, "artifact-001")
        assert next_ver == 1

    def test_get_next_version_existing(self, temp_db):
        """Next version increments correctly."""
        artifact_id = "test-artifact"

        # Insert version 1
        temp_db.execute(
            "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
            "created_at, last_modified, relevance_scope, content_hash, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, "repo1", "adr", "Title", "Content v1", "source.md",
             "2026-06-30T00:00:00", "2026-06-30T00:00:00", "global", "hash1", 1)
        )

        # Insert version 2
        temp_db.execute(
            "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
            "created_at, last_modified, relevance_scope, content_hash, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, "repo1", "adr", "Title", "Content v2", "source.md",
             "2026-06-30T00:00:00", "2026-06-30T00:00:00", "global", "hash2", 2)
        )
        temp_db.commit()

        next_ver = get_next_version(temp_db, artifact_id)
        assert next_ver == 3

    def test_check_content_changed_first_artifact(self, temp_db):
        """First artifact always shows content changed."""
        artifact_id = "new-artifact"
        is_changed = check_content_changed(temp_db, artifact_id, "newhash")
        assert is_changed is True

    def test_check_content_changed_same_hash(self, temp_db):
        """Same content hash shows no change."""
        artifact_id = "test-artifact"
        content_hash = "samehash123"

        # Insert version 1
        temp_db.execute(
            "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
            "created_at, last_modified, relevance_scope, content_hash, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, "repo1", "adr", "Title", "Content", "source.md",
             "2026-06-30T00:00:00", "2026-06-30T00:00:00", "global", content_hash, 1)
        )
        temp_db.commit()

        is_changed = check_content_changed(temp_db, artifact_id, content_hash)
        assert is_changed is False

    def test_check_content_changed_different_hash(self, temp_db):
        """Different hash shows content changed."""
        artifact_id = "test-artifact"

        # Insert with hash1
        temp_db.execute(
            "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
            "created_at, last_modified, relevance_scope, content_hash, version) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (artifact_id, "repo1", "adr", "Title", "Content v1", "source.md",
             "2026-06-30T00:00:00", "2026-06-30T00:00:00", "global", "hash1", 1)
        )
        temp_db.commit()

        # Check with different hash
        is_changed = check_content_changed(temp_db, artifact_id, "hash2")
        assert is_changed is True

    def test_get_artifact_version_count_no_versions(self, temp_db):
        """No versions returns 0."""
        count = get_artifact_version_count(temp_db, "nonexistent")
        assert count == 0

    def test_get_artifact_version_count_multiple_versions(self, temp_db):
        """Correctly counts all versions."""
        artifact_id = "test-artifact"

        # Insert 3 versions
        for v in range(1, 4):
            temp_db.execute(
                "INSERT INTO artifacts (id, repo_id, type, title, content, source, "
                "created_at, last_modified, relevance_scope, content_hash, version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (artifact_id, "repo1", "adr", "Title", f"Content v{v}", "source.md",
                 "2026-06-30T00:00:00", "2026-06-30T00:00:00", "global", f"hash{v}", v)
            )
        temp_db.commit()

        count = get_artifact_version_count(temp_db, artifact_id)
        assert count == 3
