"""Internal (module-level) dependency graph + cycle detection.

Built from real repo_intelligence.ImportEdge data. This is NOT
repo_intelligence.dependency_graph.DependencyGraphBuilder, which builds
EXTERNAL package dependencies from requirements.txt/pyproject.toml — that
is unrelated and untouched by this task.

Per ADR-016, this bridge lives in cli-commands (Apps layer) because it
combines repo_intelligence.ImportEdge with arch_guardrails's DepGraph
protocol shape — a cross-package bridge that only the Apps layer may do.
"""

from __future__ import annotations

from repo_intelligence.import_graph import ImportEdge


class DependencyGraphAdapter:
    def __init__(
        self,
        import_edges_by_file: dict[str, list[ImportEdge]],
        file_to_module: dict[str, str],
    ) -> None:
        self.import_edges_by_file = import_edges_by_file
        self.file_to_module = file_to_module
        self._module_names = set(file_to_module.values())

    def get_edges(self) -> list[tuple[str, str]]:
        edges: list[tuple[str, str]] = []
        for file_path, import_edges in self.import_edges_by_file.items():
            source_module = self.file_to_module.get(file_path)
            if source_module is None:
                continue
            for edge in import_edges:
                target_module = self._resolve_target(edge.target_module)
                if target_module is None:
                    continue
                edges.append((source_module, target_module))
        return edges

    def _resolve_target(self, target_module: str) -> str | None:
        """Match a dotted import target against known module names.

        Exact match first, then suffix match (e.g. import target "app" matches
        known module "pkg.app"), skipping anything unresolvable (external/
        stdlib imports) rather than guessing.
        """
        if target_module in self._module_names:
            return target_module
        for module in self._module_names:
            if module.endswith(f".{target_module}") or module == target_module:
                return module
        return None

    def find_cycles(self) -> list[list[str]]:
        """DFS-based simple cycle detection (three-color algorithm)."""
        adjacency: dict[str, list[str]] = {}
        for source, target in self.get_edges():
            adjacency.setdefault(source, []).append(target)

        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {}
        cycles: list[list[str]] = []
        stack: list[str] = []

        def visit(node: str) -> None:
            color[node] = GRAY
            stack.append(node)
            for neighbor in adjacency.get(node, []):
                state = color.get(neighbor, WHITE)
                if state == WHITE:
                    visit(neighbor)
                elif state == GRAY:
                    idx = stack.index(neighbor)
                    cycle = stack[idx:]
                    if cycle not in cycles:
                        cycles.append(list(cycle))
            stack.pop()
            color[node] = BLACK

        all_nodes = set(adjacency.keys()) | {t for targets in adjacency.values() for t in targets}
        for node in sorted(all_nodes):
            if color.get(node, WHITE) == WHITE:
                visit(node)

        return cycles
