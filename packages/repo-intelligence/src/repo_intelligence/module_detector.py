"""Module detector for identifying Python packages and namespace packages."""

from pathlib import Path
from typing import List


class Module:
    """Represents a Python package or namespace package."""
    def __init__(
        self,
        name: str,
        root_path: Path,
        type: str,
        file_paths: List[Path],
    ):
        self.name = name
        self.root_path = root_path
        self.type = type  # "regular" | "namespace"
        self.file_paths = file_paths

    def to_dict(self):
        return {
            "name": self.name,
            "root_path": str(self.root_path),
            "type": self.type,
            "file_paths": [str(f) for f in self.file_paths],
        }


class ModuleDetector:
    """Detect Python packages (regular and namespace packages)."""

    def __init__(self, repo_root: Path):
        """
        Initialize module detector.

        Args:
            repo_root: Project root directory
        """
        self.repo_root = Path(repo_root)
        self._ignore_dirs = {
            "__pycache__", ".pytest_cache", ".tox", "venv", "env",
            ".venv", ".env", "build", "dist", ".git", ".venv",
        }

    def detect_modules(self) -> List[Module]:
        """
        Detect Python packages and namespace packages.

        Returns:
            List of Module objects (regular and namespace packages)
        """
        modules = []
        visited = set()

        for py_file in self.repo_root.rglob("*.py"):
            if self._should_skip(py_file):
                continue

            package = self._find_package_root(py_file)
            if package and package not in visited:
                visited.add(package)
                module = self._create_module(package)
                if module:
                    modules.append(module)

        return modules

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        parts = file_path.parts
        for part in parts:
            if part in self._ignore_dirs or part.startswith("."):
                return True
        if file_path.name == "__init__.py":
            return True
        return False

    def _find_package_root(self, py_file: Path) -> Path:
        """Find the package root directory for a Python file."""
        current = py_file.parent
        while current != self.repo_root and current != current.parent:
            init_file = current / "__init__.py"
            if init_file.exists():
                return current
            current = current.parent

        if self._has_python_files(py_file.parent):
            return py_file.parent

        return None

    def _has_python_files(self, directory: Path) -> bool:
        """Check if directory contains Python files (but not just __init__.py)."""
        for item in directory.iterdir():
            if item.suffix == ".py" and item.name != "__init__.py":
                return True
        return False

    def _create_module(self, package_root: Path) -> Module:
        """Create a Module object for a package."""
        init_file = package_root / "__init__.py"
        is_regular = init_file.exists()
        module_type = "regular" if is_regular else "namespace"

        module_name = self._compute_module_name(package_root)
        file_paths = self._collect_python_files(package_root)

        if file_paths:
            return Module(module_name, package_root, module_type, file_paths)
        return None

    def _compute_module_name(self, package_root: Path) -> str:
        """Compute fully qualified module name."""
        parts = []
        current = package_root

        while current != self.repo_root and current != current.parent:
            parts.append(current.name)
            current = current.parent

        parts.reverse()
        return ".".join(parts)

    def _collect_python_files(self, package_root: Path) -> List[Path]:
        """Collect all Python files in package."""
        files = []
        for py_file in package_root.glob("*.py"):
            if py_file.name != "__init__.py":
                files.append(py_file)
        return files
