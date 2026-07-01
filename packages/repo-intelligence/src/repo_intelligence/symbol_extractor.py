"""
Symbol Extractor

Walks tree-sitter AST and extracts code symbols (functions, classes, methods).
"""

from dataclasses import dataclass
from typing import Any, List, Optional
from pathlib import Path
from tree_sitter import Language, Parser


@dataclass
class Symbol:
    """Represents a code symbol (function, class, method)."""

    name: str
    qualified_name: str
    type: str  # 'function', 'class', 'method'
    lineno: int
    docstring: Optional[str] = None

    @property
    def kind(self) -> str:
        """Alias for type (test compatibility)."""
        return self.type

    @property
    def start_line(self) -> int:
        """Alias for lineno (test compatibility)."""
        return self.lineno


class SymbolExtractor:
    """Extracts symbols from Python source code."""

    def __init__(self) -> None:
        """Initialize parser."""
        self._parser: Optional[Parser] = None

    def _get_parser(self) -> Parser:
        """Get or create tree-sitter parser."""
        if self._parser is None:
            from tree_sitter_languages import get_language
            self._parser = Parser()
            self._parser.set_language(get_language("python"))
        return self._parser

    def extract_symbols(self, file_path: Path, source: Optional[str] = None) -> List[Symbol]:
        """
        Extract symbols from Python source code.

        Args:
            file_path: Path to file (for reference/logging)
            source: Python source code as string. If not provided, reads from file_path.

        Returns:
            List of Symbol objects
        """
        try:
            # If source not provided, read from file
            if source is None:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source = f.read()
                except (FileNotFoundError, OSError):
                    return []

            parser = self._get_parser()
            tree = parser.parse(source.encode("utf-8"))
            if tree is None:
                return []
            return self.extract(tree)
        except Exception:
            return []

    def extract(self, tree: Any) -> List[Symbol]:
        """
        Extract all symbols from tree-sitter AST.

        Args:
            tree: tree-sitter Tree object

        Returns:
            List of Symbol objects
        """
        symbols: List[Symbol] = []
        self._walk_tree(tree.root_node, symbols, qualifier="")
        return symbols

    def _walk_tree(
        self, node: Any, symbols: List[Symbol], qualifier: str
    ) -> None:
        """
        Recursively walk AST and extract symbols.

        Args:
            node: Current tree-sitter node
            symbols: Accumulator list of symbols
            qualifier: Current class/scope qualifier for nested symbols
        """
        if node.type == "function_definition":
            name = self._get_node_name(node)
            if name:
                qualified_name = (
                    f"{qualifier}.{name}" if qualifier else name
                )
                lineno = node.start_point[0] + 1
                docstring = self._extract_docstring(node)
                symbols.append(
                    Symbol(
                        name=name,
                        qualified_name=qualified_name,
                        type="method" if qualifier else "function",
                        lineno=lineno,
                        docstring=docstring,
                    )
                )

        elif node.type == "class_definition":
            name = self._get_node_name(node)
            if name:
                qualified_name = (
                    f"{qualifier}.{name}" if qualifier else name
                )
                lineno = node.start_point[0] + 1
                docstring = self._extract_docstring(node)
                symbols.append(
                    Symbol(
                        name=name,
                        qualified_name=qualified_name,
                        type="class",
                        lineno=lineno,
                        docstring=docstring,
                    )
                )
                # Recursively extract methods from class
                for child in node.children:
                    if child.type == "block":
                        self._walk_tree(child, symbols, qualifier=qualified_name)

        # Continue walking children
        for child in node.children:
            if child.type != "block" or node.type != "class_definition":
                self._walk_tree(child, symbols, qualifier)

    def _get_node_name(self, node: Any) -> Optional[str]:
        """
        Extract name from function or class definition node.

        Args:
            node: tree-sitter node of type function_definition or class_definition

        Returns:
            Name of the function/class, or None if not found
        """
        for child in node.children:
            if child.type == "identifier":
                return child.text.decode("utf-8")
        return None

    def _extract_docstring(self, node: Any) -> Optional[str]:
        """
        Extract docstring from function or class definition.

        Args:
            node: tree-sitter node

        Returns:
            Docstring content, or None if not found
        """
        for child in node.children:
            if child.type == "block":
                for inner in child.children:
                    if inner.type == "expression_statement":
                        for inner_inner in inner.children:
                            if inner_inner.type == "string":
                                docstring_raw = inner_inner.text.decode("utf-8")
                                # Remove quotes
                                if docstring_raw.startswith(('"""', "'''")):
                                    return docstring_raw[3:-3].strip()
                                elif docstring_raw.startswith(('"', "'")):
                                    return docstring_raw[1:-1].strip()
        return None
