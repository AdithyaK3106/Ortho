"""Tests for git metadata and project memory."""

import pytest

from context_hub.git_metadata import FileChurnMetadata, GitMetadataStore
from context_hub.project_memory import ProjectMemory
from context_hub.staleness import StalenessDetector


class TestProjectMemory:
    """Test project memory key/value store."""

    def test_project_memory_set_get(self, temp_db):
        """Set and get project memory."""
        memory = ProjectMemory(temp_db, "test-repo")
        memory.set("primary_language", "python")

        value = memory.get("primary_language")
        assert value == "python"

    def test_project_memory_get_nonexistent(self, temp_db):
        """Get nonexistent key returns None."""
        memory = ProjectMemory(temp_db, "test-repo")
        value = memory.get("nonexistent_key")
        assert value is None

    def test_project_memory_list_all(self, temp_db):
        """List all facts."""
        memory = ProjectMemory(temp_db, "test-repo")
        memory.set("primary_language", "python")
        memory.set("test_framework", "pytest")
        memory.set("api_style", "REST")

        all_facts = memory.list_all()
        assert len(all_facts) == 3
        assert all_facts["primary_language"] == "python"
        assert all_facts["test_framework"] == "pytest"
        assert all_facts["api_style"] == "REST"

    def test_project_memory_list_all_empty(self, temp_db):
        """List all on empty repo."""
        memory = ProjectMemory(temp_db, "test-repo")
        all_facts = memory.list_all()
        assert all_facts == {}

    def test_project_memory_update(self, temp_db):
        """Update existing key."""
        memory = ProjectMemory(temp_db, "test-repo")
        memory.set("language", "python")
        memory.set("language", "typescript")

        value = memory.get("language")
        assert value == "typescript"

    def test_project_memory_repo_isolation(self, temp_db):
        """Facts isolated per repo."""
        memory1 = ProjectMemory(temp_db, "repo1")
        memory2 = ProjectMemory(temp_db, "repo2")

        memory1.set("language", "python")
        memory2.set("language", "typescript")

        assert memory1.get("language") == "python"
        assert memory2.get("language") == "typescript"


class TestGitMetadata:
    """Test git metadata store."""

    def test_get_file_churn_no_history(self, temp_db):
        """File with no git history returns zeros."""
        git_store = GitMetadataStore(temp_db, None, "repo1")
        churn = git_store.get_file_churn("nonexistent_file_id")

        assert churn.commit_count == 0
        assert churn.lines_added == 0
        assert churn.lines_removed == 0
        assert churn.last_modified is None

    def test_get_file_churn_with_commits(self, temp_db, temp_git_repo):
        """File churn calculated correctly."""
        repo_path, file_rel_path = temp_git_repo
        git_store = GitMetadataStore(temp_db, repo_path, "repo1")

        # Load git history
        file_id = "test_file_id"
        git_store.load_git_history(file_id, file_rel_path)

        # Get churn
        churn = git_store.get_file_churn(file_id)
        assert churn.commit_count == 2  # 2 commits in fixture
        assert churn.last_modified is not None

    def test_git_metadata_non_git_repo(self, temp_db, tmp_path):
        """Non-git repo handled gracefully."""
        git_store = GitMetadataStore(temp_db, tmp_path, "repo1")
        # Should not raise
        git_store.load_git_history("file_id", "somefile.py")

        churn = git_store.get_file_churn("file_id")
        assert churn.commit_count == 0


class TestStalenessDetector:
    """Test staleness detection."""

    def test_staleness_non_file_artifact(self, temp_db, artifact_store, tmp_path):
        """Non-file artifacts never stale."""
        from context_hub.ingestion import ArtifactIngestionRequest

        req = ArtifactIngestionRequest(
            type="adr",
            title="Manual ADR",
            content="This is a manual entry",
            source="manual",  # Non-file source
            relevance_scope="global",
            tags=[],
        )
        artifact_id = artifact_store.ingest_artifact(req)

        detector = StalenessDetector(temp_db, tmp_path)
        report = detector.check_staleness(artifact_id)

        assert report.is_stale is False
        assert report.reason == "non-file artifact"

    def test_staleness_file_deleted(self, temp_db, artifact_store, tmp_path):
        """Deleted file marked stale."""
        from context_hub.ingestion import ArtifactIngestionRequest
        from pathlib import Path

        # Create a temp file
        temp_file = tmp_path / "test.md"
        temp_file.write_text("Content")

        req = ArtifactIngestionRequest(
            type="adr",
            title="Test",
            content="Content",
            source="test.md",
            relevance_scope="global",
            tags=[],
        )
        artifact_id = artifact_store.ingest_artifact(req)

        # Delete the file
        temp_file.unlink()

        detector = StalenessDetector(temp_db, tmp_path)
        report = detector.check_staleness(artifact_id)

        assert report.is_stale is True
        assert "deleted" in report.reason

    def test_staleness_content_unchanged(self, temp_db, artifact_store, tmp_path):
        """Unchanged content not stale."""
        from context_hub.ingestion import ArtifactIngestionRequest

        # Create file with specific content
        temp_file = tmp_path / "test.md"
        content = "This is the test content"
        temp_file.write_text(content)

        req = ArtifactIngestionRequest(
            type="adr",
            title="Test",
            content=content,
            source="test.md",
            relevance_scope="global",
            tags=[],
        )
        artifact_id = artifact_store.ingest_artifact(req)

        detector = StalenessDetector(temp_db, tmp_path)
        report = detector.check_staleness(artifact_id)

        assert report.is_stale is False
        assert report.reason == "up-to-date"

    def test_staleness_content_changed(self, temp_db, artifact_store, tmp_path):
        """Changed content marked stale."""
        from context_hub.ingestion import ArtifactIngestionRequest

        # Create file
        temp_file = tmp_path / "test.md"
        temp_file.write_text("Original content")

        req = ArtifactIngestionRequest(
            type="adr",
            title="Test",
            content="Original content",
            source="test.md",
            relevance_scope="global",
            tags=[],
        )
        artifact_id = artifact_store.ingest_artifact(req)

        # Modify file
        temp_file.write_text("Modified content")

        detector = StalenessDetector(temp_db, tmp_path)
        report = detector.check_staleness(artifact_id)

        assert report.is_stale is True
        assert "content mismatch" in report.reason
