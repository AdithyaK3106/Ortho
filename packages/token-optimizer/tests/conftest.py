"""Pytest configuration for token-optimizer tests."""

import pytest
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Add repo root and src paths to sys.path so 'packages.X' imports work
_repo_root = Path(__file__).parent.parent.parent.parent  # .../ortho/
_src_root = Path(__file__).parent.parent / "src"  # .../token-optimizer/src/

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))


@dataclass
class MockArtifact:
    """Mock search result for testing without a real ArtifactStore.

    Field names match the real context_hub.search.result.SearchResult
    contract (artifact_id, not id; no estimated_tokens field at all --
    assembler.py derives token_count from real content length). A prior
    version of this mock used .id/.estimated_tokens, attributes the real
    SearchResult doesn't have; every test here passed while the real
    code path crashed with "'SearchResult' object has no attribute 'id'"
    the moment a real, non-empty ArtifactStore.search() result reached it.
    estimated_tokens is kept as an explicit testing convenience (so
    budget-fitting tests can assert exact counts) rather than derived
    from content length here, since content length is what the real
    assembler now uses -- this mock still controls it directly for
    deterministic test fixtures.
    """
    artifact_id: str
    content: str
    estimated_tokens: int
    relevance_score: float = 0.0


@dataclass
class MockArtifactStore:
    """Mock ArtifactStore for testing."""
    artifacts: List[MockArtifact]

    def search(self, query: str, artifact_type: str = None, limit: int = 50):
        """Return all artifacts (mock search) -- matches the real
        ArtifactStore.search(query, artifact_type=None, limit=50) signature,
        not the repo_id= kwarg the real one never accepted."""
        return self.artifacts


@pytest.fixture
def mock_artifact_store():
    """Fixture: Create mock artifact store with sample data."""
    artifacts = [
        MockArtifact(artifact_id="a1", content="Auth logic", estimated_tokens=100, relevance_score=0.9),
        MockArtifact(artifact_id="a2", content="Database config", estimated_tokens=50, relevance_score=0.7),
        MockArtifact(artifact_id="a3", content="API endpoints", estimated_tokens=200, relevance_score=0.8),
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


@pytest.fixture
def mock_skills():
    """Fixture: Create list of mock skills for testing."""
    class MockSkill:
        def __init__(self, display_name, system_prompt):
            self.display_name = display_name
            self.system_prompt = system_prompt

    return [
        MockSkill("Code Review", "Review the following code."),
        MockSkill("Testing", "Write tests for the following code."),
    ]


@pytest.fixture
def sample_artifacts_tie_breaking():
    """Fixture: Create list of artifacts for tie-breaking tests - same relevance score, different tokens."""
    return [
        # These three have identical relevance score - should be ordered by token count ascending
        MockArtifact(artifact_id="a_artifact", content="Smallest tokens", estimated_tokens=100, relevance_score=0.8),
        MockArtifact(artifact_id="m_artifact", content="Medium tokens", estimated_tokens=150, relevance_score=0.8),
        MockArtifact(artifact_id="z_artifact", content="Largest tokens", estimated_tokens=200, relevance_score=0.8),
    ]
