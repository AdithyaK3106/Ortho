"""Adapts real scan data to refactoring_advisor's CodeRepository Protocol.

get_duplications() and get_high_churn_modules() return [] unconditionally:
no code-similarity detector or git-history integration exists in this
codebase yet (see task-019 plan.md "Out of Scope"). This is a documented
gap, not fabricated data.
"""

from __future__ import annotations

from impact_analysis.dependency_health import DependencyHealthAnalyzer
from impact_analysis.types import ImportEdge as HealthImportEdge

from cli_commands.repo_scanner import ScanResult

_BLOAT_LINES_THRESHOLD = 300
_BLOAT_FUNCTIONS_THRESHOLD = 20


def _resolve_target_file_id(
    target_module: str, module_to_file_id: dict[str, str]
) -> str | None:
    target_file_id = module_to_file_id.get(target_module)
    if target_file_id is not None:
        return target_file_id
    for module, file_id in module_to_file_id.items():
        if module.endswith(f".{target_module}"):
            return file_id
    return None


class CodeRepositoryAdapter:
    def __init__(self, scan: ScanResult) -> None:
        self._scan = scan
        self._metrics = None  # set lazily to avoid import cycle at module load
        self._health_edges = self._build_health_edges(scan)
        self._cycles: list[list[str]] | None = None

    @staticmethod
    def _build_health_edges(scan: ScanResult) -> list[HealthImportEdge]:
        module_to_file_id = {
            module: file_id for file_id, module in scan.file_to_module.items()
        }
        edges: list[HealthImportEdge] = []
        for file_key, import_edges in scan.import_edges_by_file.items():
            for edge in import_edges:
                target_file_id = _resolve_target_file_id(
                    edge.target_module, module_to_file_id
                )
                edges.append(
                    HealthImportEdge(
                        importer_file_id=file_key,
                        imported_file_id=target_file_id,
                        imported_module=edge.target_module,
                        is_external=target_file_id is None,
                    )
                )
        return edges

    def _get_cycles(self) -> list[list[str]]:
        if self._cycles is None:
            self._cycles = DependencyHealthAnalyzer().find_cycles(self._health_edges)
        return self._cycles

    def _to_module(self, file_id: str) -> str:
        return self._scan.file_to_module.get(file_id, file_id)

    def get_tight_couplings(self) -> list[tuple[str, str]]:
        seen: set[frozenset[str]] = set()
        result: list[tuple[str, str]] = []
        for cycle in self._get_cycles():
            # find_cycles returns closed chains [A, B, ..., A]; a 2-node
            # cycle is A -> B -> A, i.e. 3 entries with first == last.
            if len(cycle) == 3 and cycle[0] == cycle[-1]:
                a, b = cycle[0], cycle[1]
                key = frozenset((a, b))
                if key not in seen:
                    seen.add(key)
                    result.append((self._to_module(a), self._to_module(b)))
        return result

    def get_circular_deps(self) -> list[list[str]]:
        result = []
        for cycle in self._get_cycles():
            if len(cycle) > 3 or (len(cycle) == 3 and cycle[0] != cycle[-1]):
                result.append([self._to_module(fid) for fid in cycle])
        return result

    def get_bloated_modules(self) -> list[tuple[str, int, int]]:
        from repo_intelligence.graph_queries import CodeMetricsAdapter

        metrics = CodeMetricsAdapter(self._scan.file_to_module)
        modules = set(self._scan.file_to_module.values())
        result: list[tuple[str, int, int]] = []
        for module in modules:
            lines = metrics.get_module_lines(module)
            functions = metrics.get_module_functions(module)
            if lines > _BLOAT_LINES_THRESHOLD or functions > _BLOAT_FUNCTIONS_THRESHOLD:
                result.append((module, lines, functions))
        return result

    def get_duplications(self) -> list[tuple[str, str, float]]:
        return []

    def get_high_churn_modules(self) -> list[str]:
        return []
