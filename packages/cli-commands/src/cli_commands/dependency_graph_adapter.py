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
                target_module = self._resolve_target(edge.target_module, source_module)
                if target_module is None or target_module == source_module:
                    # A module can't have a real internal dependency on itself.
                    # Self-loops here are always a resolution artifact, not a
                    # genuine finding -- e.g. `import typing` (stdlib) inside
                    # a module named "...pkg.typing" suffix-matching back onto
                    # itself, or a package's own __init__.py importing one of
                    # its submodules by the package's short name. Silently
                    # dropping self-loops here (rather than filtering them out
                    # of find_cycles' output later) also protects
                    # layer_boundaries and find_importers/find_callers, which
                    # consume the same edges and would otherwise inherit the
                    # same false "imports itself" fact.
                    continue
                edges.append((source_module, target_module))
        return edges

    def _resolve_target(self, target_module: str, source_module: str) -> str | None:
        """Match a dotted import target against known module names.

        Exact match first, then suffix match (e.g. import target "app" matches
        known module "pkg.app"), skipping anything unresolvable (external/
        stdlib imports) rather than guessing. The importing module itself is
        excluded from suffix-match candidates: a stdlib/third-party import
        that happens to share its last dotted segment with the importing
        module's own name (e.g. `import typing` inside a module named
        "pkg.typing", or `import logging` inside "pkg.logging") must never
        resolve back onto the importer -- that misresolution corrupts the
        import graph itself (not just cycle detection), since exact-name
        collisions with common stdlib modules (typing, json, logging, queue,
        types, string, collections) are common in real repos.
        """
        if target_module == source_module:
            return None
        if target_module in self._module_names:
            return target_module
        for module in self._module_names:
            if module == source_module:
                continue
            if module.endswith(f".{target_module}") or module == target_module:
                return module
        return None

    def find_cycles(self) -> list[list[str]]:
        """Strongly-connected-component detection (Tarjan's algorithm).

        Reports each maximal set of mutually-reachable modules once, as one
        finding. A naive DFS back-edge enumeration instead reports one
        "cycle" per distinct path that re-enters an already-visited node --
        on a hub module many other modules import (e.g. a package's own
        top-level __init__, which everything imports for its public API),
        that produces one finding per import path through the same
        underlying strongly-connected region: verified on a real repo, one
        27-module cyclic region was reported as 19 near-duplicate
        "different" circular-dependency errors, each individually true but
        collectively describing one problem, not nineteen (see
        docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md). SCCs have no such
        path-count sensitivity: the same cyclic region is always exactly one
        component, regardless of how many modules happen to import into it.

        A single-node "component" (no self-loop, since get_edges() already
        drops those) is not a cycle and is excluded.
        """
        adjacency: dict[str, list[str]] = {}
        all_nodes: set[str] = set()
        for source, target in self.get_edges():
            adjacency.setdefault(source, []).append(target)
            all_nodes.add(source)
            all_nodes.add(target)

        index_counter = [0]
        index: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        on_stack: dict[str, bool] = {}
        stack: list[str] = []
        sccs: list[list[str]] = []

        def strongconnect(node: str) -> None:
            index[node] = index_counter[0]
            lowlink[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for neighbor in adjacency.get(node, []):
                if neighbor not in index:
                    strongconnect(neighbor)
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif on_stack.get(neighbor):
                    lowlink[node] = min(lowlink[node], index[neighbor])

            if lowlink[node] == index[node]:
                component: list[str] = []
                while True:
                    member = stack.pop()
                    on_stack[member] = False
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1:
                    sccs.append(component)

        for node in sorted(all_nodes):
            if node not in index:
                strongconnect(node)

        return sccs
