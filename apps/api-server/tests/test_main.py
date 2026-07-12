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


class TestAPIStructure:
    """Test that API structure is correct."""

    def test_api_running(self, client):
        """API should respond to health check."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_404_on_unknown_endpoint(self, client):
        """Unknown endpoints should return 404."""
        response = client.get("/api/v1/unknown")
        assert response.status_code == 404
