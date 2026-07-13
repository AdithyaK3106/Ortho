from unittest.mock import Mock
from typing import Any

import pytest


@pytest.fixture
def mock_change_predictions() -> list[Any]:
    """Mock change planner predictions"""
    return []


@pytest.fixture
def mock_feature_paths() -> list[Any]:
    """Mock feature paths"""
    return []


@pytest.fixture
def mock_refactoring_issues() -> list[Any]:
    """Mock refactoring issues"""
    return []


@pytest.fixture
def mock_guardrail_violations() -> list[Any]:
    """Mock guardrail violations"""
    return []
