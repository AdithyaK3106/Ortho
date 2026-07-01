"""File discovery and filtering for repository scanning."""

from pathlib import Path
from typing import List, Set


class FileDiscoverer:
    """Discovers Python files in a repository with configurable exclusions."""

    # Default exclusion patterns
    DEFAULT_EXCLUDES = {
        '__pycache__',
        '.git',
        '.gitignore',
        '.venv',
        'venv',
        'node_modules',
        '.ortho',
        'dist',
        'build',
        '*.egg-info',
        '.pytest_cache',
        '.mypy_cache',
        '__pycache__',
    }

    def __init__(self, repo_root: Path, exclude_patterns: Set[str] | None = None) -> None:
        """
        Initialize file discoverer.

        Args:
            repo_root: Repository root directory
            exclude_patterns: Set of patterns to exclude (in addition to defaults)
        """
        self.repo_root = Path(repo_root)
        self.exclude_patterns = self.DEFAULT_EXCLUDES.copy()
        if exclude_patterns:
            self.exclude_patterns.update(exclude_patterns)

    def find_python_files(self) -> List[Path]:
        """
        Recursively find all Python files in repository.

        Returns:
            List of absolute Path objects to .py files

        Yields:
            Only files matching .py extension that are not in excluded directories
        """
        python_files: List[Path] = []

        for item in self.repo_root.rglob('*.py'):
            if self._should_include(item):
                python_files.append(item)

        return sorted(python_files)

    def find_python_files_relative(self) -> List[str]:
        """
        Find all Python files, return as relative paths (string).

        Returns:
            List of relative path strings (repo_root-relative)
        """
        absolute_paths = self.find_python_files()
        return [str(p.relative_to(self.repo_root)) for p in absolute_paths]

    def _should_include(self, file_path: Path) -> bool:
        """
        Check if file should be included (not excluded).

        Args:
            file_path: Absolute path to file

        Returns:
            True if file should be included, False if excluded
        """
        # Check if any part of the path matches an exclusion pattern
        for part in file_path.parts:
            if part in self.exclude_patterns:
                return False

            # Check for wildcard patterns (e.g., *.egg-info)
            for pattern in self.exclude_patterns:
                if '*' in pattern:
                    if part.endswith(pattern.replace('*', '')):
                        return False

        return True

    def count_files(self) -> int:
        """
        Count total number of Python files found.

        Returns:
            Number of .py files in repository
        """
        return len(self.find_python_files())

    def add_exclude_pattern(self, pattern: str) -> None:
        """
        Add an exclusion pattern at runtime.

        Args:
            pattern: Pattern to exclude (e.g., '*.pyc', '__pycache__')
        """
        self.exclude_patterns.add(pattern)

    def remove_exclude_pattern(self, pattern: str) -> None:
        """
        Remove an exclusion pattern.

        Args:
            pattern: Pattern to stop excluding
        """
        self.exclude_patterns.discard(pattern)

    def reset_excludes(self) -> None:
        """Reset exclusion patterns to defaults."""
        self.exclude_patterns = self.DEFAULT_EXCLUDES.copy()
