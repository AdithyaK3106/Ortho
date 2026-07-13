from unittest.mock import Mock
from typing import Any

import pytest


@pytest.fixture
def mock_arch_model() -> Any:
    """Mock architecture model"""
    mock = Mock()
    mock.get_layers = Mock(return_value=["presentation", "business", "data"])
    mock.get_layer_for_module = Mock(return_value="unknown")
    mock.get_modules = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_dep_graph() -> Any:
    """Mock dependency graph"""
    mock = Mock()
    mock.get_edges = Mock(return_value=[])
    mock.find_cycles = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_metrics() -> Any:
    """Mock code metrics"""
    mock = Mock()
    mock.get_module_lines = Mock(return_value=400)
    mock.get_module_functions = Mock(return_value=30)
    return mock
