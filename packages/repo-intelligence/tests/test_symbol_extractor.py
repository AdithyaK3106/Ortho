"""Tests for SymbolExtractor - AST parsing and symbol extraction."""

import pytest
from pathlib import Path
from repo_intelligence.symbol_extractor import SymbolExtractor, Symbol


@pytest.fixture
def extractor():
    """Create a SymbolExtractor instance."""
    return SymbolExtractor()


@pytest.fixture
def sample_python_file(tmp_path):
    """Create a sample Python file for testing."""
    code = '''
"""Module docstring."""

def simple_function(x: int) -> int:
    """Extract me."""
    return x + 1

class MyClass:
    """A sample class."""

    def __init__(self, name: str):
        self.name = name

    def method(self) -> str:
        return self.name

    @property
    def prop(self):
        return self.name

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass

    class NestedClass:
        """Nested class."""
        pass

async def async_function():
    """Async function."""
    await something()

def decorator_function():
    @property
    def decorated():
        return "test"
    return decorated
'''
    file_path = tmp_path / "sample.py"
    file_path.write_text(code)
    return str(file_path)


class TestSymbolExtraction:
    """Test symbol extraction from Python files."""

    def test_extract_function_symbol(self, extractor, sample_python_file):
        """Extract function symbols from file."""
        symbols = extractor.extract_symbols(sample_python_file)
        function_symbols = [s for s in symbols if s.kind == 'function']

        assert len(function_symbols) > 0
        names = {s.name for s in function_symbols}
        assert 'simple_function' in names
        assert 'async_function' in names

    def test_extract_class_symbol(self, extractor, sample_python_file):
        """Extract class symbols from file."""
        symbols = extractor.extract_symbols(sample_python_file)
        class_symbols = [s for s in symbols if s.kind == 'class']

        assert len(class_symbols) > 0
        names = {s.name for s in class_symbols}
        assert 'MyClass' in names
        assert 'NestedClass' in names

    def test_extract_method_symbol(self, extractor, sample_python_file):
        """Extract method symbols from file."""
        symbols = extractor.extract_symbols(sample_python_file)
        method_symbols = [s for s in symbols if s.kind == 'method']

        assert len(method_symbols) > 0
        names = {s.name for s in method_symbols}
        assert 'method' in names
        assert '__init__' in names

    def test_symbol_has_qualified_name(self, extractor, sample_python_file):
        """Symbols should have qualified_name for nested items."""
        symbols = extractor.extract_symbols(sample_python_file)

        for symbol in symbols:
            assert symbol.qualified_name is not None
            if symbol.kind == 'method':
                assert '.' in symbol.qualified_name

    def test_symbol_line_numbers(self, extractor, sample_python_file):
        """Symbols should have correct line numbers."""
        symbols = extractor.extract_symbols(sample_python_file)

        for symbol in symbols:
            assert symbol.start_line > 0
            assert symbol.end_line >= symbol.start_line

    def test_empty_file(self, extractor, tmp_path):
        """Handle empty Python files."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        symbols = extractor.extract_symbols(str(empty_file))
        assert len(symbols) == 0

    def test_file_with_syntax_error(self, extractor, tmp_path):
        """Handle files with syntax errors gracefully."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken( x: int\n    return x")

        # Should raise or return empty list
        with pytest.raises(Exception):
            extractor.extract_symbols(str(bad_file))

    def test_nonexistent_file(self, extractor):
        """Handle nonexistent files."""
        with pytest.raises(FileNotFoundError):
            extractor.extract_symbols("/nonexistent/file.py")

    def test_symbol_docstring(self, extractor, sample_python_file):
        """Symbols should include docstrings if present."""
        symbols = extractor.extract_symbols(sample_python_file)

        simple_func = [s for s in symbols if s.name == 'simple_function']
        assert len(simple_func) > 0
        assert simple_func[0].docstring is not None
        assert "Extract me" in simple_func[0].docstring


class TestSymbolTypes:
    """Test that all symbol types are correctly identified."""

    def test_property_detection(self, extractor, sample_python_file):
        """Properties should be detected as methods."""
        symbols = extractor.extract_symbols(sample_python_file)
        methods = [s for s in symbols if s.kind == 'method']

        prop_symbols = [s for s in methods if s.name == 'prop']
        assert len(prop_symbols) > 0

    def test_staticmethod_detection(self, extractor, sample_python_file):
        """Static methods should be detected."""
        symbols = extractor.extract_symbols(sample_python_file)
        methods = [s for s in symbols if s.kind == 'method']

        static_symbols = [s for s in methods if s.name == 'static_method']
        assert len(static_symbols) > 0

    def test_classmethod_detection(self, extractor, sample_python_file):
        """Class methods should be detected."""
        symbols = extractor.extract_symbols(sample_python_file)
        methods = [s for s in symbols if s.kind == 'method']

        cls_symbols = [s for s in methods if s.name == 'class_method']
        assert len(cls_symbols) > 0


class TestLargeFile:
    """Test symbol extraction on larger files."""

    def test_large_file_performance(self, extractor, tmp_path):
        """Extract symbols from file with many functions."""
        large_code = "\n".join([
            f"def func_{i}():\n    return {i}"
            for i in range(100)
        ])
        large_file = tmp_path / "large.py"
        large_file.write_text(large_code)

        symbols = extractor.extract_symbols(str(large_file))
        functions = [s for s in symbols if s.kind == 'function']

        assert len(functions) == 100


class TestUnicodePath:
    """Test handling of Unicode in file paths and content."""

    def test_unicode_filename(self, extractor, tmp_path):
        """Handle Unicode characters in filenames."""
        unicode_file = tmp_path / "файл.py"
        unicode_file.write_text("def hello(): pass")

        symbols = extractor.extract_symbols(str(unicode_file))
        assert len(symbols) > 0

    def test_unicode_content(self, extractor, tmp_path):
        """Handle Unicode in Python code."""
        unicode_file = tmp_path / "unicode.py"
        unicode_file.write_text('def greet(name="мир"): pass')

        symbols = extractor.extract_symbols(str(unicode_file))
        functions = [s for s in symbols if s.kind == 'function']
        assert len(functions) > 0
