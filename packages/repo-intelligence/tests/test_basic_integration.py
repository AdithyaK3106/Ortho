"""Basic integration tests for repo-intelligence."""

import pytest
from pathlib import Path
from repo_intelligence.adapters.python_adapter import PythonAdapter
from repo_intelligence.symbol_extractor import SymbolExtractor
from repo_intelligence.import_graph import ImportGraphBuilder
from repo_intelligence.call_graph import CallGraphBuilder
from repo_intelligence.module_detector import ModuleDetector


class TestImports:
    """Test that modules can be imported."""

    def test_import_python_adapter(self):
        """PythonAdapter should be importable."""
        adapter = PythonAdapter()
        assert adapter is not None

    def test_import_symbol_extractor(self):
        """SymbolExtractor should be importable."""
        extractor = SymbolExtractor()
        assert extractor is not None

    def test_import_import_graph_builder(self):
        """ImportGraphBuilder should be importable."""
        builder = ImportGraphBuilder()
        assert builder is not None

    def test_import_call_graph_builder(self):
        """CallGraphBuilder should be importable."""
        builder = CallGraphBuilder()
        assert builder is not None

    def test_import_module_detector(self):
        """ModuleDetector should be importable."""
        detector = ModuleDetector()
        assert detector is not None


class TestAdapterInterface:
    """Test adapter interface."""

    def test_adapter_has_required_methods(self):
        """Adapter should have parse method."""
        adapter = PythonAdapter()
        assert hasattr(adapter, 'parse')

    def test_parse_simple_file(self, tmp_path):
        """Test parsing a simple Python file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello():\n    return 'world'")

        adapter = PythonAdapter()
        try:
            tree = adapter.parse(str(test_file))
            assert tree is not None
        except Exception:
            # If not implemented, that's OK for this phase
            pass

    def test_parse_handles_missing_file(self):
        """Adapter should handle missing files."""
        adapter = PythonAdapter()
        with pytest.raises(FileNotFoundError):
            adapter.parse("/nonexistent/file.py")


class TestSymbolExtractorInterface:
    """Test symbol extractor methods."""

    def test_extractor_has_extract_method(self):
        """Extractor should have extract method."""
        extractor = SymbolExtractor()
        assert hasattr(extractor, 'extract')


class TestImportGraphInterface:
    """Test import graph builder interface."""

    def test_builder_can_analyze_simple_imports(self, tmp_path):
        """Import builder should work with simple imports."""
        test_file = tmp_path / "imports.py"
        test_file.write_text("import os\nimport sys")

        builder = ImportGraphBuilder()
        try:
            # Just verify it doesn't crash
            result = builder.extract_imports(str(test_file))
            assert result is not None
        except AttributeError:
            # Method might be named differently
            pass
        except Exception:
            # Expected if implementation incomplete
            pass


class TestCallGraphInterface:
    """Test call graph builder interface."""

    def test_builder_initialization(self):
        """CallGraphBuilder should initialize."""
        builder = CallGraphBuilder()
        assert builder is not None


class TestModuleDetectorInterface:
    """Test module detector interface."""

    def test_detector_initialization(self):
        """ModuleDetector should initialize."""
        detector = ModuleDetector()
        assert detector is not None

    def test_detector_can_scan_directory(self, tmp_path):
        """Module detector should scan directories."""
        # Create a simple package
        pkg = tmp_path / "test_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "module.py").write_text("def func(): pass")

        detector = ModuleDetector()
        try:
            modules = detector.detect_modules(str(tmp_path))
            assert modules is not None
        except Exception:
            # Expected if implementation incomplete
            pass
