"""
Python Language Adapter

Implements LanguageAdapter interface for Python using tree-sitter.
"""

from pathlib import Path
from typing import Any, List
from dataclasses import dataclass

try:
    from tree_sitter import Language, Parser as _TreeSitterParser
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    _TREE_SITTER_AVAILABLE = False
    Language = None  # type: ignore[assignment,misc]
    _TreeSitterParser = None  # type: ignore[assignment,misc]

try:
    from tree_sitter_languages import get_language as _get_language
    _TS_LANGUAGES_AVAILABLE = True
except ImportError:
    _TS_LANGUAGES_AVAILABLE = False
    _get_language = None  # type: ignore[assignment]

from ..symbol_extractor import SymbolExtractor, Symbol
from ..import_graph import ImportGraphBuilder, ImportEdge


class PythonAdapter:
    """Adapts Python code analysis using tree-sitter."""

    def __init__(self) -> None:
        """Initialize Python adapter with tree-sitter grammar."""
        if not _TREE_SITTER_AVAILABLE:
            raise RuntimeError(
                "tree-sitter is required for PythonAdapter. "
                "Install with: pip install tree-sitter tree-sitter-languages"
            )
        if not _TS_LANGUAGES_AVAILABLE:
            raise RuntimeError(
                "tree-sitter-languages is required for PythonAdapter. "
                "Install with: pip install tree-sitter-languages"
            )
        try:
            self.language: Language = _get_language("python")
        except Exception as e:
            raise RuntimeError(f"Failed to load Python grammar: {e}")

        self.parser = _TreeSitterParser()
        self.parser.set_language(self.language)

    def parse(self, file_path: str) -> Any:
        """
        Parse a Python file and return its AST.

        Args:
            file_path: Path to the Python source file

        Returns:
            tree-sitter Tree object representing the AST
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "rb") as f:
            source_code = f.read()

        tree = self.parser.parse(source_code)
        if tree is None:
            raise ValueError(f"Failed to parse {file_path}")

        return tree

    def extract_symbols(self, tree: Any) -> List[Symbol]:
        """
        Extract symbols (functions, classes, methods) from Python AST.

        Args:
            tree: tree-sitter Tree object from parse()

        Returns:
            List of Symbol dataclass objects
        """
        extractor = SymbolExtractor()
        return extractor.extract(tree)

    def analyze_dependencies(self, tree: Any) -> List[ImportEdge]:
        """
        Extract import dependencies from Python AST.

        Args:
            tree: tree-sitter Tree object from parse()

        Returns:
            List of ImportEdge dataclass objects
        """
        builder = ImportGraphBuilder()
        return builder.build(tree)
