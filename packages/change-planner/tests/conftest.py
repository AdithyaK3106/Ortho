from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_call_graph() -> Any:
    """Mock call graph for testing"""
    mock = Mock()
    mock.find_callers = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_import_graph() -> Any:
    """Mock import graph for testing"""
    mock = Mock()
    mock.find_importers = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_symbol_registry() -> Any:
    """Mock symbol registry for testing"""
    mock = Mock()
    mock.symbols_in_file = Mock(return_value=[])
    return mock


@pytest.fixture
def mock_arch_model() -> Any:
    """Mock architecture model for testing"""
    mock = Mock()
    mock.get_layer = Mock(return_value="unknown")
    mock.modules = []
    return mock
