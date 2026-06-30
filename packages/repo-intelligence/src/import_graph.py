"""
Import Graph Builder

Extracts import statements from Python AST and builds dependency graph.
"""

from dataclasses import dataclass
from typing import Any, List, Set, Optional


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

        Args:
            node: Current tree-sitter node
            edges: Accumulator list of import edges
        """
        if node.type == "import_statement":
            self._process_import_statement(node, edges)

        elif node.type == "import_from_statement":
            self._process_import_from_statement(node, edges)

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
        Extract module name from 'import X' statement.

        Args:
            node: tree-sitter node

        Returns:
            Module name, or None if not found
        """
        for child in node.children:
            if child.type == "dotted_name" or child.type == "identifier":
                return child.text.decode("utf-8")
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
                if child.text.decode("utf-8") not in ("import", "."):
                    return child.text.decode("utf-8")
        return None

    def _is_relative_import(self, node: Any) -> bool:
        """
        Check if import is relative (starts with .).

        Args:
            node: tree-sitter node

        Returns:
            True if relative import, False otherwise
        """
        text = node.text.decode("utf-8")
        return text.lstrip().startswith("from .")
