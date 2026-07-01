"""Tests for FastAPI server."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_endpoint_returns_ok(self, client):
        """Health check should return 200 with ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSearchEndpoint:
    """Test search endpoint."""

    def test_search_without_query_param(self, client):
        """Search without query param should return error."""
        response = client.get("/api/v1/search")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "results" in data

    def test_search_with_empty_query(self, client):
        """Search with empty query should return error."""
        response = client.get("/api/v1/search?q=")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "query required"

    def test_search_with_query_returns_results(self, client):
        """Search should return results structure."""
        response = client.get("/api/v1/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert data["query"] == "test"


class TestArtifactEndpoint:
    """Test artifact creation endpoint."""

    def test_create_artifact_missing_name(self, client):
        """Create artifact without name should return error."""
        response = client.post("/api/v1/artifacts?content=test")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_create_artifact_missing_content(self, client):
        """Create artifact without content should return error."""
        response = client.post("/api/v1/artifacts?name=test")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    def test_create_artifact_success(self, client):
        """Create artifact with name and content."""
        response = client.post("/api/v1/artifacts?name=test&content=test+content")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test"
        assert data["created"] is True
        assert "id" in data
