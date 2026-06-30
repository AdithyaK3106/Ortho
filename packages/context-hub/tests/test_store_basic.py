"""Basic integration tests for ArtifactStore."""

import pytest

from context_hub.store import ArtifactStore


class TestArtifactStoreBasic:
    """Test core ArtifactStore functionality."""

    def test_ingest_artifact(self, artifact_store, valid_artifact_request):
        """Ingest valid artifact returns artifact_id."""
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)
        assert artifact_id is not None
        assert isinstance(artifact_id, str)
        assert len(artifact_id) == 16

    def test_ingest_and_retrieve(self, artifact_store, valid_artifact_request):
        """Ingest artifact then retrieve it."""
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)
        artifact = artifact_store.get_artifact(artifact_id)

        assert artifact is not None
        assert artifact.id == artifact_id
        assert artifact.title == valid_artifact_request.title
        assert artifact.content == valid_artifact_request.content
        assert artifact.version == 1

    def test_ingest_invalid_artifact(self, artifact_store):
        """Ingest invalid artifact raises error."""
        from context_hub.ingestion import ArtifactIngestionRequest

        invalid_req = ArtifactIngestionRequest(
            type="",  # Invalid: empty type
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
        )

        with pytest.raises(ValueError, match="validation failed"):
            artifact_store.ingest_artifact(invalid_req)

    def test_versioning_same_content(self, artifact_store, valid_artifact_request):
        """Ingesting same content twice returns same artifact_id, version 1."""
        id1 = artifact_store.ingest_artifact(valid_artifact_request)
        id2 = artifact_store.ingest_artifact(valid_artifact_request)

        assert id1 == id2
        artifact = artifact_store.get_artifact(id1)
        assert artifact.version == 1

    def test_versioning_different_content(self, artifact_store, valid_artifact_request):
        """Ingesting different content increments version."""
        # First ingest
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)
        artifact_v1 = artifact_store.get_artifact(artifact_id)
        assert artifact_v1.version == 1

        # Modify and ingest again
        from context_hub.ingestion import ArtifactIngestionRequest

        modified_req = ArtifactIngestionRequest(
            type=valid_artifact_request.type,
            title=valid_artifact_request.title,
            content="Modified content",  # Different content
            source=valid_artifact_request.source,
            relevance_scope=valid_artifact_request.relevance_scope,
            tags=valid_artifact_request.tags,
        )

        artifact_id_v2 = artifact_store.ingest_artifact(modified_req)
        assert artifact_id_v2 == artifact_id  # Same ID
        artifact_v2 = artifact_store.get_artifact(artifact_id)
        assert artifact_v2.version == 2

    def test_get_artifact_history(self, artifact_store, valid_artifact_request):
        """Get artifact history retrieves all versions."""
        from context_hub.ingestion import ArtifactIngestionRequest

        # Ingest v1
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)

        # Ingest v2 (different content)
        v2_req = ArtifactIngestionRequest(
            type=valid_artifact_request.type,
            title=valid_artifact_request.title,
            content="Version 2 content",
            source=valid_artifact_request.source,
            relevance_scope=valid_artifact_request.relevance_scope,
            tags=valid_artifact_request.tags,
        )
        artifact_store.ingest_artifact(v2_req)

        # Ingest v3 (different content)
        v3_req = ArtifactIngestionRequest(
            type=valid_artifact_request.type,
            title=valid_artifact_request.title,
            content="Version 3 content",
            source=valid_artifact_request.source,
            relevance_scope=valid_artifact_request.relevance_scope,
            tags=valid_artifact_request.tags,
        )
        artifact_store.ingest_artifact(v3_req)

        # Get history
        history = artifact_store.get_artifact_history(artifact_id)
        assert len(history) == 3
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3

    def test_get_artifact_specific_version(self, artifact_store, valid_artifact_request):
        """Get specific artifact version."""
        from context_hub.ingestion import ArtifactIngestionRequest

        # Ingest v1
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)

        # Ingest v2
        v2_req = ArtifactIngestionRequest(
            type=valid_artifact_request.type,
            title=valid_artifact_request.title,
            content="Version 2",
            source=valid_artifact_request.source,
            relevance_scope=valid_artifact_request.relevance_scope,
            tags=valid_artifact_request.tags,
        )
        artifact_store.ingest_artifact(v2_req)

        # Get v1
        v1 = artifact_store.get_artifact_version(artifact_id, 1)
        assert v1.version == 1
        assert v1.content == valid_artifact_request.content

        # Get v2
        v2 = artifact_store.get_artifact_version(artifact_id, 2)
        assert v2.version == 2
        assert v2.content == "Version 2"

    def test_delete_artifact(self, artifact_store, valid_artifact_request):
        """Delete artifact removes it from store."""
        artifact_id = artifact_store.ingest_artifact(valid_artifact_request)
        artifact_store.delete_artifact(artifact_id)

        artifact = artifact_store.get_artifact(artifact_id)
        assert artifact is None
