from unittest.mock import Mock
from typing import Any

import pytest


@pytest.fixture
def mock_arch_model() -> Any:
    """Mock architecture model"""
    mock = Mock()
    mock.get_style = Mock(return_value="layered")
    return mock
