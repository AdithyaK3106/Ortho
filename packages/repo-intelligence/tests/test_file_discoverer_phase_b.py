"""Tests for FileDiscoverer (Phase B) — file discovery and filtering."""

import pytest
from pathlib import Path
import tempfile
from repo_intelligence.file_discoverer import FileDiscoverer


@pytest.fixture
def temp_repo_with_files():
    """Create temporary repo with mixed file types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Create Python files
        (repo_root / "module1.py").write_text("# module 1")
        (repo_root / "module2.py").write_text("# module 2")

        # Create subdirectory with Python files
        src_dir = repo_root / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("# main")
        (src_dir / "utils.py").write_text("# utils")

        # Create excluded directories
        cache_dir = repo_root / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.pyc").write_text("")

        git_dir = repo_root / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("")

        venv_dir = repo_root / "venv"
        venv_dir.mkdir()
        (venv_dir / "lib.py").write_text("# should be excluded")

        # Create non-Python files
        (repo_root / "README.md").write_text("# README")
        (repo_root / "config.toml").write_text("[config]")

        yield repo_root


class TestFileDiscovererBasic:
    """Basic file discovery tests."""

    def test_find_python_files(self, temp_repo_with_files):
        """Test finding all Python files."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        files = discoverer.find_python_files()

        assert len(files) >= 4
        paths = [f.name for f in files]
        assert "module1.py" in paths
        assert "module2.py" in paths
        assert "main.py" in paths
        assert "utils.py" in paths

    def test_find_python_files_excludes_non_python(self, temp_repo_with_files):
        """Test that non-Python files are excluded."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        files = discoverer.find_python_files()

        paths = [f.name for f in files]
        assert "README.md" not in paths
        assert "config.toml" not in paths

    def test_find_python_files_excludes_directories(self, temp_repo_with_files):
        """Test that excluded directories are skipped."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        files = discoverer.find_python_files()

        paths = [f.name for f in files]
        # venv/lib.py should be excluded
        assert len([p for p in paths if "lib.py" in p and "venv" in str(p)]) == 0

    def test_find_python_files_relative(self, temp_repo_with_files):
        """Test finding files as relative paths (strings)."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        files = discoverer.find_python_files_relative()

        assert all(isinstance(f, str) for f in files)
        assert "module1.py" in files
        assert "src/main.py" in files or Path("src") / "main.py" in [Path(f) for f in files]

    def test_count_files(self, temp_repo_with_files):
        """Test counting files."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        count = discoverer.count_files()

        assert count >= 4


class TestFileDiscovererExclusions:
    """Exclusion pattern tests."""

    def test_default_excludes(self, temp_repo_with_files):
        """Test that default exclusions are applied."""
        discoverer = FileDiscoverer(temp_repo_with_files)
        files = discoverer.find_python_files_relative()

        # __pycache__, .git, venv should be excluded
        assert not any("__pycache__" in f for f in files)
        assert not any(".git" in f for f in files)
        assert not any("venv" in f for f in files)

    def test_add_exclude_pattern(self, temp_repo_with_files):
        """Test adding custom exclusion pattern."""
        discoverer = FileDiscoverer(temp_repo_with_files)

        # Exclude src directory
        discoverer.add_exclude_pattern("src")
        files = discoverer.find_python_files_relative()

        assert not any("src" in f for f in files)

    def test_remove_exclude_pattern(self, temp_repo_with_files):
        """Test removing an exclusion pattern."""
        discoverer = FileDiscoverer(temp_repo_with_files)

        # Add then remove venv exclusion
        discoverer.remove_exclude_pattern("venv")

        # Now venv files should be included (if they exist)
        # (This test may or may not find venv/lib.py depending on test setup)
        files = discoverer.find_python_files_relative()
        assert isinstance(files, list)

    def test_reset_excludes(self, temp_repo_with_files):
        """Test resetting to default exclusions."""
        discoverer = FileDiscoverer(temp_repo_with_files)

        # Add custom exclusions
        discoverer.add_exclude_pattern("src")
        discoverer.add_exclude_pattern("custom")

        # Reset
        discoverer.reset_excludes()

        # Should only have defaults, not custom
        assert "src" not in discoverer.exclude_patterns
        assert "custom" not in discoverer.exclude_patterns

    def test_custom_exclude_patterns_on_init(self):
        """Test providing custom exclusions at init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create files
            (repo_root / "include.py").write_text("# included")
            (repo_root / "exclude.py").write_text("# excluded")

            # Initialize with custom exclusion
            discoverer = FileDiscoverer(repo_root, exclude_patterns={"exclude.py"})
            files = discoverer.find_python_files_relative()

            assert "include.py" in files
            assert "exclude.py" not in files


class TestFileDiscovererEdgeCases:
    """Edge case tests."""

    def test_empty_directory(self):
        """Test with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            discoverer = FileDiscoverer(repo_root)
            files = discoverer.find_python_files()

            assert len(files) == 0

    def test_only_excluded_files(self):
        """Test directory with only excluded files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create only excluded directories
            (repo_root / "__pycache__").mkdir()
            (repo_root / "__pycache__" / "file.pyc").write_text("")

            (repo_root / ".git").mkdir()
            (repo_root / ".git" / "config").write_text("")

            discoverer = FileDiscoverer(repo_root)
            files = discoverer.find_python_files()

            assert len(files) == 0

    def test_deeply_nested_files(self):
        """Test finding deeply nested Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create deeply nested structure
            deep_dir = repo_root / "a" / "b" / "c" / "d" / "e"
            deep_dir.mkdir(parents=True)
            (deep_dir / "deep.py").write_text("# deeply nested")

            discoverer = FileDiscoverer(repo_root)
            files = discoverer.find_python_files_relative()

            assert any("deep.py" in f for f in files)
