"""Tests for artifact ingestion validation."""

import pytest

from context_hub.ingestion import (
    ArtifactIngestionRequest,
    ValidationResult,
    validate_ingestion,
)


class TestIngestionValidation:
    """Test artifact ingestion validation contract."""

    def test_validate_valid_request(self, valid_artifact_request):
        """Valid request passes validation."""
        result = validate_ingestion(valid_artifact_request)
        assert result.is_valid is True
        assert result.errors == []

    def test_validate_missing_type(self):
        """Missing type rejected."""
        req = ArtifactIngestionRequest(
            type="",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("type" in err for err in result.errors)

    def test_validate_invalid_type(self):
        """Invalid type rejected."""
        req = ArtifactIngestionRequest(
            type="invalid_type",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("one of" in err for err in result.errors)

    def test_validate_empty_title(self):
        """Empty title rejected."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("title" in err for err in result.errors)

    def test_validate_empty_content(self):
        """Empty content rejected."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="",
            source="source",
            relevance_scope="global",
            tags=[],
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("content" in err for err in result.errors)

    def test_validate_invalid_scope(self):
        """Invalid relevance scope rejected."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="invalid",
            tags=[],
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("relevance_scope" in err for err in result.errors)

    def test_validate_tags_not_list(self):
        """Tags must be list."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags="not-a-list",  # type: ignore
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("list" in err for err in result.errors)

    def test_validate_tag_non_string(self):
        """Tags must contain strings."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[123],  # type: ignore
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("string" in err for err in result.errors)

    def test_validate_optional_related_symbols(self):
        """Related symbols optional."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
            related_symbols=None,
        )
        result = validate_ingestion(req)
        assert result.is_valid is True

    def test_validate_related_symbols_list(self):
        """Related symbols must be list."""
        req = ArtifactIngestionRequest(
            type="adr",
            title="Title",
            content="Content",
            source="source",
            relevance_scope="global",
            tags=[],
            related_symbols="not-a-list",  # type: ignore
        )
        result = validate_ingestion(req)
        assert result.is_valid is False
        assert any("related_symbols" in err for err in result.errors)
