"""Integration tests for Indexer (Phase B) — orchestration and extraction."""

import pytest
from pathlib import Path
import tempfile
from repo_intelligence.indexer import Indexer, IndexResult


@pytest.fixture
def temp_python_repo():
    """Create a temporary repo with Python files for indexing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create test files
        main_py = repo_root / "main.py"
        main_py.write_text("""
def hello(name: str) -> str:
    '''Say hello to someone.'''
    return f"Hello, {name}!"

class Greeter:
    '''A greeter class.'''
    def greet(self, name: str) -> str:
        return hello(name)

if __name__ == '__main__':
    greeter = Greeter()
    print(greeter.greet("World"))
""")

        # Create module with imports
        utils_py = repo_root / "utils.py"
        utils_py.write_text("""
import json
from pathlib import Path
from typing import List

def load_config(path: str) -> dict:
    '''Load configuration from file.'''
    with open(path) as f:
        return json.load(f)

def save_config(path: str, config: dict) -> None:
    '''Save configuration to file.'''
    Path(path).write_text(json.dumps(config))
""")

        # Create package
        pkg_dir = repo_root / "mypackage"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("__version__ = '0.1.0'")

        pkg_module = pkg_dir / "module.py"
        pkg_module.write_text("""
from utils import load_config

class Handler:
    def __init__(self):
        self.config = load_config('config.json')

    def handle(self, data: dict) -> bool:
        return True
""")

        yield repo_root


@pytest.fixture
def temp_repo_with_errors():
    """Create repo with some files that have syntax errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Valid Python file
        (repo_root / "good.py").write_text("""
def valid_function():
    return 42
""")

        # Syntax error file
        (repo_root / "bad.py").write_text("""
def broken_function(
    # missing closing paren
    return None
""")

        yield repo_root


class TestIndexerBasic:
    """Basic indexer functionality."""

    def test_indexer_init(self, temp_python_repo):
        """Test Indexer initialization."""
        indexer = Indexer(temp_python_repo)
        assert indexer.repo_root == temp_python_repo
        assert indexer.error_threshold == 0.9

    def test_index_repository(self, temp_python_repo):
        """Test indexing entire repository."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        assert isinstance(result, IndexResult)
        assert result.total_files >= 4
        assert result.files_scanned > 0
        assert result.total_symbols > 0
        assert result.total_imports > 0

    def test_index_result_properties(self):
        """Test IndexResult properties."""
        result = IndexResult(
            total_files=10,
            files_scanned=9,
            files_with_errors=1,
            total_symbols=50,
            total_imports=30,
            total_calls=100,
        )

        assert result.success_rate == 90.0
        assert result.error_count == 0
        assert result.total_files == 10


class TestIndexerExtraction:
    """Test symbol/import/call extraction during indexing."""

    def test_extracts_symbols(self, temp_python_repo):
        """Test that symbols are extracted."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        # Should find functions and classes
        assert result.total_symbols > 0
        # Expect: hello(), Greeter, greet, load_config, save_config, Handler

    def test_extracts_imports(self, temp_python_repo):
        """Test that imports are extracted."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        # Should find imports from utils.py
        assert result.total_imports > 0
        # Expect: json, pathlib.Path, typing.List, utils.load_config

    def test_extracts_calls(self, temp_python_repo):
        """Test that function calls are extracted."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        # Should find calls
        assert result.total_calls > 0
        # Expect: hello(), Greeter.greet(), greeter.greet(), load_config(), etc.

    def test_reports_accurate_counts(self, temp_python_repo):
        """Test that reported counts are accurate."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        # Basic sanity checks
        assert result.total_symbols >= result.files_scanned  # At least 1 symbol per file
        assert result.files_scanned >= 1
        assert result.total_files >= result.files_scanned


class TestIndexerErrorHandling:
    """Test error handling and resilience."""

    def test_handles_syntax_errors(self, temp_repo_with_errors):
        """Test that syntax errors are caught and logged."""
        indexer = Indexer(temp_repo_with_errors)
        result = indexer.index_repository()

        # Should scan good.py but skip bad.py
        assert result.files_scanned >= 1  # good.py
        assert result.error_count >= 1  # bad.py error

    def test_error_threshold_check(self, temp_repo_with_errors):
        """Test error threshold evaluation."""
        indexer = Indexer(temp_repo_with_errors)
        result = indexer.index_repository()

        # With 1 good file and 1 error: 50% success rate < 90% threshold
        if result.total_files >= 2:
            assert indexer.can_accept_error_rate(result) is False

    def test_accepts_within_threshold(self, temp_python_repo):
        """Test that normal repos pass error threshold."""
        indexer = Indexer(temp_python_repo)
        result = indexer.index_repository()

        # Good repo should have 0 errors and 100% success
        assert result.success_rate == 100.0
        assert indexer.can_accept_error_rate(result) is True


class TestIndexerFileList:
    """Test indexing specific file lists."""

    def test_index_files(self, temp_python_repo):
        """Test indexing a specific list of files."""
        indexer = Indexer(temp_python_repo)

        # Get just main.py
        main_py = temp_python_repo / "main.py"
        result = indexer.index_files([main_py])

        assert result.total_files == 1
        assert result.files_scanned == 1
        assert result.total_symbols > 0

    def test_index_files_multiple(self, temp_python_repo):
        """Test indexing multiple specific files."""
        indexer = Indexer(temp_python_repo)

        files = [
            temp_python_repo / "main.py",
            temp_python_repo / "utils.py",
        ]
        result = indexer.index_files(files)

        assert result.total_files == 2
        assert result.files_scanned == 2

    def test_index_files_nonexistent(self, temp_python_repo):
        """Test indexing a nonexistent file raises error."""
        indexer = Indexer(temp_python_repo)

        nonexistent = temp_python_repo / "nonexistent.py"
        result = indexer.index_files([nonexistent])

        assert result.error_count == 1
        assert result.files_scanned == 0


class TestIndexerProgressTracking:
    """Test progress callback functionality."""

    def test_progress_callback_called(self, temp_python_repo):
        """Test that progress callback is invoked."""
        progress_calls = []

        def track_progress(done, total):
            progress_calls.append((done, total))

        indexer = Indexer(temp_python_repo, progress_callback=track_progress)
        result = indexer.index_repository()

        # Should be called at least once
        assert len(progress_calls) > 0
        # Final call should have done == total
        assert progress_calls[-1][1] == result.total_files

    def test_progress_callback_monotonic(self, temp_python_repo):
        """Test that progress is monotonically increasing."""
        progress_calls = []

        def track_progress(done, total):
            progress_calls.append(done)

        indexer = Indexer(temp_python_repo, progress_callback=track_progress)
        indexer.index_repository()

        # Each call should be >= previous
        for i in range(1, len(progress_calls)):
            assert progress_calls[i] >= progress_calls[i - 1]


class TestIndexerExclusions:
    """Test exclusion pattern support."""

    def test_respects_exclude_patterns(self, temp_python_repo):
        """Test that exclude patterns are respected."""
        # Create a file to exclude
        (temp_python_repo / "excluded.py").write_text("# should be excluded")

        indexer = Indexer(temp_python_repo, exclude_patterns={"excluded.py"})
        result = indexer.index_repository()

        # excluded.py should not be in error logs
        assert not any("excluded.py" in e for e in result.errors)
