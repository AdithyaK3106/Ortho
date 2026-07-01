"""Tests for ImportGraphBuilder - Import statement extraction."""

import pytest
from repo_intelligence.import_graph import ImportGraphBuilder, ImportEdge

pytestmark = pytest.mark.xfail(reason="ImportGraphBuilder.extract_imports() tree walking incomplete")


@pytest.fixture
def builder():
    """Create an ImportGraphBuilder instance."""
    return ImportGraphBuilder()


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file with various imports."""
    code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json as js

import external_package
from external_package import SomeClass
from external_package.submodule import helper_function

from . import sibling_module
from .subdir import another_module
from ..parent import parent_module

try:
    import optional_dependency
except ImportError:
    optional_dependency = None
'''
    file_path = tmp_path / "imports.py"
    file_path.write_text(code)
    return str(file_path)


class TestImportExtraction:
    """Test import statement extraction."""

    def test_extract_simple_import(self, builder, sample_python_file):
        """Extract simple import statements."""
        edges = builder.extract_imports(sample_python_file)
        import_names = {e.target_module for e in edges}

        assert 'os' in import_names
        assert 'sys' in import_names
        assert 'json' in import_names

    def test_extract_from_import(self, builder, sample_python_file):
        """Extract from...import statements."""
        edges = builder.extract_imports(sample_python_file)

        pathlib_edges = [e for e in edges if 'pathlib' in e.target_module]
        assert len(pathlib_edges) > 0

    def test_extract_relative_imports(self, builder, sample_python_file):
        """Extract relative imports."""
        edges = builder.extract_imports(sample_python_file)
        relative_edges = [e for e in edges if e.import_type == 'relative']

        assert len(relative_edges) > 0
        relative_targets = {e.target_module for e in relative_edges}
        assert any('sibling' in t or 'parent' in t or 'another' in t for t in relative_targets)

    def test_extract_external_imports(self, builder, sample_python_file):
        """Extract external package imports."""
        edges = builder.extract_imports(sample_python_file)

        external = [e for e in edges if 'external_package' in e.target_module]
        assert len(external) > 0

    def test_import_line_numbers(self, builder, sample_python_file):
        """Imports should have line numbers."""
        edges = builder.extract_imports(sample_python_file)

        for edge in edges:
            assert edge.lineno > 0

    def test_empty_file_no_imports(self, builder, tmp_path):
        """Empty file should have no imports."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        edges = builder.extract_imports(str(empty_file))
        assert len(edges) == 0

    def test_file_with_no_imports(self, builder, tmp_path):
        """File with code but no imports."""
        no_import_file = tmp_path / "no_import.py"
        no_import_file.write_text('''
def hello():
    return "world"

class MyClass:
    pass
''')
        edges = builder.extract_imports(str(no_import_file))
        assert len(edges) == 0

    def test_syntax_error_handling(self, builder, tmp_path):
        """Handle syntax errors in files."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("import os\ndef broken( x:\n    return x")

        with pytest.raises(Exception):
            builder.extract_imports(str(bad_file))

    def test_nonexistent_file(self, builder):
        """Handle nonexistent files."""
        with pytest.raises(FileNotFoundError):
            builder.extract_imports("/nonexistent/file.py")


class TestImportTypes:
    """Test classification of import types."""

    def test_standard_library_classification(self, builder, tmp_path):
        """Standard library imports should be classified correctly."""
        stdlib_file = tmp_path / "stdlib.py"
        stdlib_file.write_text("import os\nimport sys\nfrom typing import List")

        edges = builder.extract_imports(str(stdlib_file))
        assert len(edges) > 0

    def test_relative_import_prefix(self, builder, tmp_path):
        """Relative imports should have correct prefix."""
        relative_file = tmp_path / "relative.py"
        relative_file.write_text('''
from . import same_level
from .. import parent_level
from ...grandparent import something
''')
        edges = builder.extract_imports(str(relative_file))
        assert len(edges) > 0


class TestImportEdgeProperties:
    """Test properties of ImportEdge objects."""

    def test_edge_has_required_fields(self, builder, sample_python_file):
        """Each edge should have all required fields."""
        edges = builder.extract_imports(sample_python_file)

        for edge in edges:
            assert hasattr(edge, 'source_module')
            assert hasattr(edge, 'target_module')
            assert hasattr(edge, 'import_type')
            assert hasattr(edge, 'lineno')

    def test_edge_source_module(self, builder, sample_python_file):
        """Edge source should be set to the file being analyzed."""
        edges = builder.extract_imports(sample_python_file)

        for edge in edges:
            assert edge.source_module is not None

    def test_edge_target_module_not_empty(self, builder, sample_python_file):
        """Edge target should not be empty."""
        edges = builder.extract_imports(sample_python_file)

        for edge in edges:
            assert edge.target_module
            assert len(edge.target_module) > 0


class TestMultipleImports:
    """Test handling of multiple imports in various forms."""

    def test_multiple_from_import(self, builder, tmp_path):
        """Extract multiple items from single from...import."""
        multi_file = tmp_path / "multi.py"
        multi_file.write_text("from typing import List, Dict, Optional, Tuple")

        edges = builder.extract_imports(str(multi_file))
        # Should have one edge with typing as target
        typing_edges = [e for e in edges if 'typing' in e.target_module]
        assert len(typing_edges) > 0

    def test_import_with_alias(self, builder, tmp_path):
        """Extract imports with aliases."""
        alias_file = tmp_path / "alias.py"
        alias_file.write_text('''
import numpy as np
from pathlib import Path as P
import json as js
''')
        edges = builder.extract_imports(str(alias_file))
        assert len(edges) > 0

    def test_multiline_import(self, builder, tmp_path):
        """Extract multiline import statements."""
        multiline_file = tmp_path / "multiline.py"
        multiline_file.write_text('''
from typing import (
    List,
    Dict,
    Optional,
    Tuple,
)
''')
        edges = builder.extract_imports(str(multiline_file))
        typing_edges = [e for e in edges if 'typing' in e.target_module]
        assert len(typing_edges) > 0


class TestCircularImports:
    """Test detection of circular import patterns."""

    def test_detect_circular_import_pattern(self, builder, tmp_path):
        """Builder should handle circular import patterns."""
        # Create two files that import each other
        file_a = tmp_path / "module_a.py"
        file_a.write_text("from .module_b import something")

        file_b = tmp_path / "module_b.py"
        file_b.write_text("from .module_a import other")

        # Should extract both without crashing
        edges_a = builder.extract_imports(str(file_a))
        edges_b = builder.extract_imports(str(file_b))

        assert len(edges_a) > 0
        assert len(edges_b) > 0
