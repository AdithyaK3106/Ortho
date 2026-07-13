from unittest.mock import Mock
from typing import Any

import pytest


@pytest.fixture
def mock_repo() -> Any:
    """Mock code repository"""
    mock = Mock()
    mock.get_tight_couplings = Mock(return_value=[])
    mock.get_duplications = Mock(return_value=[])
    mock.get_bloated_modules = Mock(return_value=[])
    mock.get_circular_deps = Mock(return_value=[])
    mock.get_high_churn_modules = Mock(return_value=[])
    return mock
