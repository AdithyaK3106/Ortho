"""
Import Graph Builder

Extracts import statements from Python AST and builds dependency graph.
"""

from dataclasses import dataclass
from typing import Any, List, Set, Optional
from pathlib import Path


@dataclass(frozen=True)
class ImportEdge:
    """Represents an import dependency between modules."""

    source_module: str
    target_module: str
    import_type: str  # 'from', 'import', 'relative'
    lineno: int


class ImportGraphBuilder:
    """Builds import dependency graph from Python AST."""

    def __init__(self) -> None:
        """Initialize the import graph builder."""
        self.visited: Set[str] = set()

    def extract_imports(self, file_path: Path, source: Optional[str] = None) -> List[ImportEdge]:
        """
        Extract imports from Python source code.

        Args:
            file_path: Path to file (for reference/logging)
            source: Python source code as string. If not provided, reads from file_path.

        Returns:
            List of ImportEdge objects
        """
        # If source not provided, read from file
        if source is None:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
            except (FileNotFoundError, OSError):
                return []

        # Parse with tree-sitter
        from tree_sitter_languages import get_language
        from tree_sitter import Parser

        parser = Parser()
        parser.set_language(get_language("python"))
        tree = parser.parse(source.encode("utf-8"))
        if tree is None:
            return []
        return self.build(tree)

    def build(self, tree: Any) -> List[ImportEdge]:
        """
        Extract all import statements from tree-sitter AST.

        Args:
            tree: tree-sitter Tree object

        Returns:
            List of ImportEdge objects
        """
        edges: List[ImportEdge] = []
        self._walk_tree(tree.root_node, edges)
        return edges

    def _walk_tree(self, node: Any, edges: List[ImportEdge]) -> None:
        """
        Recursively walk AST and extract import statements.

        Does not descend into function_definition bodies: an import inside
        a function only executes when that function runs, not at module
        load time, so it can't participate in a load-time circular-import
        failure the way a module-level import can. Counting it the same as
        a top-level import produces false-positive cycles -- e.g. Django's
        django/contrib/auth/__init__.py deliberately imports
        `.models.AnonymousUser` inside get_user()/aget_user() specifically
        to avoid a real cycle with auth.models, which imports auth
        top-level. Treating that deferred import as a top-level edge
        reports the exact cycle Django engineered around as if it still
        existed.

        Args:
            node: Current tree-sitter node
            edges: Accumulator list of import edges
        """
        if node.type == "import_statement":
            self._process_import_statement(node, edges)

        elif node.type == "import_from_statement":
            self._process_import_from_statement(node, edges)

        if node.type == "function_definition":
            return

        # Continue walking children
        for child in node.children:
            self._walk_tree(child, edges)

    def _process_import_statement(
        self, node: Any, edges: List[ImportEdge]
    ) -> None:
        """
        Process 'import X' statement.

        Args:
            node: tree-sitter node of type import_statement
            edges: Accumulator list of import edges
        """
        lineno = node.start_point[0] + 1
        target = self._extract_import_name(node)
        if target:
            edge = ImportEdge(
                source_module="<current>",
                target_module=target,
                import_type="import",
                lineno=lineno,
            )
            edges.append(edge)

    def _process_import_from_statement(
        self, node: Any, edges: List[ImportEdge]
    ) -> None:
        """
        Process 'from X import Y' statement.

        Args:
            node: tree-sitter node of type import_from_statement
            edges: Accumulator list of import edges
        """
        lineno = node.start_point[0] + 1
        import_type = "relative" if self._is_relative_import(node) else "from"
        target = self._extract_from_import_name(node)
        if target:
            edge = ImportEdge(
                source_module="<current>",
                target_module=target,
                import_type=import_type,
                lineno=lineno,
            )
            edges.append(edge)

    def _extract_import_name(self, node: Any) -> Optional[str]:
        """
        Extract module name from 'import X' or 'import X as Y' statement.

        Returns the actual module name (not the alias).

        Args:
            node: tree-sitter node (import_statement)

        Returns:
            Module name, or None if not found
        """
        # Look for aliased_import or dotted_name/identifier
        for child in node.children:
            if child.type == "aliased_import":
                # Structure: dotted_name/identifier as alias
                for subchild in child.children:
                    if subchild.type == "dotted_name":
                        return str(subchild.text.decode("utf-8"))
                    elif subchild.type == "identifier":
                        # Check if this is before 'as'
                        idx = child.children.index(subchild)
                        if idx + 1 < len(child.children) and child.children[idx + 1].type == "as":
                            return str(subchild.text.decode("utf-8"))
                        elif idx + 1 >= len(child.children):
                            # Last child, no 'as' after
                            return str(subchild.text.decode("utf-8"))
            elif child.type == "dotted_name":
                return str(child.text.decode("utf-8"))
            elif child.type == "identifier":
                # Check if next is "as"
                idx = node.children.index(child)
                if idx + 1 < len(node.children) and node.children[idx + 1].type == "as":
                    return str(child.text.decode("utf-8"))
                elif idx + 1 >= len(node.children):
                    return str(child.text.decode("utf-8"))
        return None

    def _extract_from_import_name(self, node: Any) -> Optional[str]:
        """
        Extract module name from 'from X import Y' statement.

        Args:
            node: tree-sitter node

        Returns:
            Module name from 'from X' part, or None if not found
        """
        from_seen = False
        for child in node.children:
            if child.type == "from":
                from_seen = True
            elif from_seen and (
                child.type == "dotted_name" or child.type == "identifier"
            ):
                if str(child.text.decode("utf-8")) not in ("import", "."):
                    return str(child.text.decode("utf-8"))
        return None

    def _is_relative_import(self, node: Any) -> bool:
        """
        Check if import is relative (starts with .).

        Args:
            node: tree-sitter node

        Returns:
            True if relative import, False otherwise
        """
        text = str(node.text.decode("utf-8"))
        return text.lstrip().startswith("from .")
