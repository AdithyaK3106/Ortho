"""Test fixtures and configuration for ContextHub tests."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from context_hub.embedding import NullEmbedding
from context_hub.ingestion import ArtifactIngestionRequest
from context_hub.schema import init_all_schemas
from context_hub.store import ArtifactStore


@pytest.fixture
def temp_db():
    """Create a temporary in-memory SQLite database."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    init_all_schemas(db)
    yield db
    db.close()


@pytest.fixture
def artifact_store(temp_db):
    """Create an ArtifactStore instance with test database."""
    class MockDatabase:
        def __init__(self, conn):
            self._conn = conn

        def connection(self):
            return self._conn

    return ArtifactStore(
        db=MockDatabase(temp_db),
        repo_id="test-repo",
        embedding_provider=NullEmbedding(),
    )


@pytest.fixture
def valid_artifact_request():
    """Sample valid artifact ingestion request."""
    return ArtifactIngestionRequest(
        type="adr",
        title="ADR-001: Storage Strategy",
        content="We have decided to use SQLite for local storage...",
        source="docs/adr/ADR-001.md",
        relevance_scope="global",
        tags=["storage", "decision"],
        related_symbols=None,
    )


@pytest.fixture
def authentication_artifact():
    """Sample authentication artifact for search testing."""
    return ArtifactIngestionRequest(
        type="spec",
        title="Authentication Flow",
        content="The authentication system uses JWT tokens for session management.",
        source="docs/authentication.md",
        relevance_scope="global",
        tags=["auth", "security"],
    )


@pytest.fixture
def large_artifact():
    """Sample large artifact (1MB) for edge case testing."""
    return ArtifactIngestionRequest(
        type="frd",
        title="Large FRD",
        content="X" * 1_000_000,
        source="docs/frd.md",
        relevance_scope="global",
        tags=["large"],
    )


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for git metadata testing."""
    import git

    # ignore_cleanup_errors: on Windows, gitpython can hold handles into .git
    # during teardown, which otherwise fails the whole test as a fixture error
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        repo = git.Repo.init(tmpdir)
        try:
            # Create a sample file and commit
            sample_file = Path(tmpdir) / "sample.txt"
            sample_file.write_text("Initial content")
            repo.index.add([str(sample_file)])
            repo.index.commit("Initial commit", author=git.Actor("Test", "test@example.com"))

            # Modify and commit again
            sample_file.write_text("Modified content")
            repo.index.add([str(sample_file)])
            repo.index.commit("Second commit", author=git.Actor("Test", "test@example.com"))

            yield Path(tmpdir), "sample.txt"
        finally:
            repo.close()


@pytest.fixture
def sample_embedding():
    """Sample 1536-dimensional embedding for testing."""
    return [0.1] * 1536
