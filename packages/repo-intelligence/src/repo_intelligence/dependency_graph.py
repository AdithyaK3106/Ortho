"""Dependency graph builder for requirements.txt and pyproject.toml parsing."""

from pathlib import Path
from typing import List
import tomllib
import re


class DependencyEdge:
    """Represents a project dependency."""
    def __init__(
        self,
        repo_id: str,
        package_name: str,
        version: str = None,
        is_external: bool = True,
    ):
        self.repo_id = repo_id
        self.package_name = package_name
        self.version = version
        self.is_external = is_external

    def to_dict(self):
        return {
            "repo_id": self.repo_id,
            "package_name": self.package_name,
            "version": self.version,
            "is_external": self.is_external,
        }


class DependencyGraphBuilder:
    """Extract external dependencies from requirements.txt and pyproject.toml."""

    def __init__(self, repo_root: Path):
        """
        Initialize dependency graph builder.

        Args:
            repo_root: Project root directory
        """
        self.repo_root = Path(repo_root)
        self.edges = []

    def build_dependency_graph(self, repo_id: str) -> List[DependencyEdge]:
        """
        Parse requirements.txt and pyproject.toml for dependencies.

        Args:
            repo_id: Repository identifier

        Returns:
            List of DependencyEdge objects
        """
        dependencies = {}

        # Parse requirements.txt
        req_file = self.repo_root / "requirements.txt"
        if req_file.exists():
            dependencies.update(self._parse_requirements_txt(req_file))

        # Parse pyproject.toml (Poetry format takes precedence)
        pyproject_file = self.repo_root / "pyproject.toml"
        if pyproject_file.exists():
            dependencies.update(self._parse_pyproject_toml(pyproject_file))

        # Build edges
        edges = []
        for package_name, version in dependencies.items():
            edge = DependencyEdge(repo_id, package_name, version, is_external=True)
            edges.append(edge)

        return edges

    def _parse_requirements_txt(self, file_path: Path) -> dict:
        """Parse requirements.txt and return {package_name: version}."""
        packages = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    package_name, version = self._parse_requirement_line(line)
                    if package_name:
                        packages[package_name] = version
        except Exception:
            pass
        return packages

    def _parse_pyproject_toml(self, file_path: Path) -> dict:
        """Parse pyproject.toml and return {package_name: version}."""
        packages = {}
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)

            # Extract Poetry dependencies
            if "tool" in data and "poetry" in data["tool"]:
                poetry = data["tool"]["poetry"]
                if "dependencies" in poetry:
                    for pkg_name, spec in poetry["dependencies"].items():
                        if pkg_name == "python":
                            continue
                        version = self._extract_version(spec) if isinstance(spec, str) else "*"
                        packages[pkg_name] = version

                if "optional-dependencies" in poetry:
                    for group, deps in poetry["optional-dependencies"].items():
                        for pkg_name, spec in deps.items():
                            if pkg_name not in packages:
                                version = self._extract_version(spec) if isinstance(spec, str) else "*"
                                packages[pkg_name] = version
        except Exception:
            pass
        return packages

    def _parse_requirement_line(self, line: str) -> tuple:
        """Parse a single requirement line (PEP 508 format)."""
        line = line.split(";")[0].strip()
        if not line:
            return None, None

        match = re.match(r"^([a-zA-Z0-9\-_.]+)\s*(.*)$", line)
        if not match:
            return None, None

        package_name = match.group(1).lower()
        version_spec = match.group(2).strip() if match.group(2) else None

        return package_name, version_spec

    def _extract_version(self, spec: str) -> str:
        """Extract version string from Poetry spec."""
        if isinstance(spec, dict):
            if "version" in spec:
                return spec["version"]
            return "*"
        return spec if spec else "*"
