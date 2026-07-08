"""Root pytest configuration for Ortho monorepo.

This conftest.py ensures that pytest can find packages namespace imports
from any package's tests, and exports common test fixtures.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List

# Add the repo root to sys.path so pytest can resolve 'packages.X' imports
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))


# Common test fixtures and mocks exported for use by all packages
class MockArtifact:
    """Mock Artifact for testing without real ArtifactStore."""
    def __init__(self, id: str, estimated_tokens: int, relevance_score: float = 0.0, content: str = "", **kwargs):
        """Initialize MockArtifact. Accepts extra kwargs for flexibility in tests."""
        self.id = id
        self.content = content
        self.estimated_tokens = estimated_tokens
        self.relevance_score = relevance_score
        # Store any extra kwargs as attributes for test flexibility
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class MockArtifactStore:
    """Mock ArtifactStore for testing."""
    artifacts: List[MockArtifact]

    def search(self, query: str, repo_id: str = None):
        """Return all artifacts (mock search)."""
        return self.artifacts
