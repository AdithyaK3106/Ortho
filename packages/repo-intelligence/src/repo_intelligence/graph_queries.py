"""Query adapters over repo-intelligence's flat edge/symbol output.

CallGraphBuilder, ImportGraphBuilder, and SymbolExtractor each produce flat
lists (CallEdge, ImportEdge, Symbol). Consumers (change-planner,
arch-guardrails) need queryable lookups (find_callers, find_importers,
symbols_in_file). These adapters bridge that gap without modifying the
underlying builders.
"""

from __future__ import annotations

import ast
from pathlib import Path

from repo_intelligence.call_graph import CallEdge
from repo_intelligence.import_graph import ImportEdge
from repo_intelligence.symbol_extractor import Symbol


class RepoGraphQueries:
    """Queryable view over call edges and per-file import edges."""

    def __init__(
        self,
        call_edges: list[CallEdge],
        import_edges_by_file: dict[str, list[ImportEdge]],
    ) -> None:
        self.call_edges = call_edges
        self.import_edges_by_file = import_edges_by_file

    def find_callers(self, symbol: str, depth: int = 1) -> list[str]:
        """Return callers of `symbol`, transitively up to `depth` hops."""
        if depth < 1:
            return []

        # direct callees -> callers, for one BFS hop
        direct_callers_of: dict[str, set[str]] = {}
        for edge in self.call_edges:
            direct_callers_of.setdefault(edge.callee_id, set()).add(edge.caller_name)
            direct_callers_of.setdefault(edge.callee_name, set()).add(edge.caller_name)

        found: set[str] = set()
        frontier = {symbol}
        visited_targets: set[str] = set()

        for _ in range(depth):
            next_frontier: set[str] = set()
            for target in frontier:
                if target in visited_targets:
                    continue
                visited_targets.add(target)
                callers = direct_callers_of.get(target, set())
                for caller in callers:
                    if caller not in found:
                        found.add(caller)
                        next_frontier.add(caller)
            if not next_frontier:
                break
            frontier = next_frontier

        return sorted(found)

    def find_importers(
        self, file_path: str, include_type: bool = False
    ) -> list[tuple[str, str]] | list[str]:
        """Return files that import `file_path`'s module.

        Resolution matches ImportEdge.target_module against module names
        derived from file_path, since ImportEdge.source_module is always
        the literal "<current>" placeholder and carries no real identity.
        """
        candidates = self._module_candidates(file_path)

        results: list[tuple[str, str]] = []
        seen: set[str] = set()
        for importer_file, edges in self.import_edges_by_file.items():
            if importer_file == file_path:
                continue
            for edge in edges:
                if edge.target_module in candidates and importer_file not in seen:
                    seen.add(importer_file)
                    results.append((importer_file, edge.import_type))
                    break

        if include_type:
            return results
        return [name for name, _ in results]

    @staticmethod
    def _module_candidates(file_path: str) -> set[str]:
        """Derive plausible dotted-module names for a file path."""
        p = Path(file_path.replace("\\", "/"))
        stem = p.stem
        dotted = ".".join(p.with_suffix("").parts)
        return {stem, dotted, dotted.lstrip("./").replace("/", ".")}


class SymbolIndex:
    """Queryable view over per-file symbol lists."""

    def __init__(self, symbols_by_file: dict[str, list[Symbol]]) -> None:
        self.symbols_by_file = symbols_by_file

    def symbols_in_file(self, file_path: str) -> list[str]:
        return [s.name for s in self.symbols_by_file.get(file_path, [])]


class CodeMetricsAdapter:
    """Real line/function counts per module, computed from source files."""

    def __init__(self, file_to_module: dict[str, str]) -> None:
        self.file_to_module = file_to_module
        self._files_by_module: dict[str, list[str]] = {}
        for file_path, module in file_to_module.items():
            self._files_by_module.setdefault(module, []).append(file_path)

    def get_module_lines(self, module: str) -> int:
        total = 0
        for file_path in self._files_by_module.get(module, []):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    total += len(f.readlines())
            except OSError:
                continue
        return total

    def get_module_functions(self, module: str) -> int:
        total = 0
        for file_path in self._files_by_module.get(module, []):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    source = f.read()
            except OSError:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total += 1
        return total
