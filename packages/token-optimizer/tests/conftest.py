"""Pytest configuration for token-optimizer tests."""

import pytest
from dataclasses import dataclass
from typing import List


@dataclass
class MockArtifact:
    """Mock Artifact for testing without real ArtifactStore."""
    id: str
    content: str
    estimated_tokens: int
    relevance_score: float = 0.0


@dataclass
class MockArtifactStore:
    """Mock ArtifactStore for testing."""
    artifacts: List[MockArtifact]

    def search(self, query: str, repo_id: str = None):
        """Return all artifacts (mock search)."""
        return self.artifacts


@pytest.fixture
def mock_artifact_store():
    """Fixture: Create mock artifact store with sample data."""
    artifacts = [
        MockArtifact(id="a1", content="Auth logic", estimated_tokens=100, relevance_score=0.9),
        MockArtifact(id="a2", content="Database config", estimated_tokens=50, relevance_score=0.7),
        MockArtifact(id="a3", content="API endpoints", estimated_tokens=200, relevance_score=0.8),
    ]
    return MockArtifactStore(artifacts=artifacts)


@pytest.fixture
def mock_agent():
    """Fixture: Create mock agent."""
    class MockAgent:
        system_prompt = "You are a helpful coding assistant."
        display_name = "Coder"
    return MockAgent()


@pytest.fixture
def mock_skill():
    """Fixture: Create mock skill."""
    class MockSkill:
        display_name = "Code Review"
        system_prompt = "Review the following code and provide feedback."
        content = "Review the following code and provide feedback."
    return MockSkill()
