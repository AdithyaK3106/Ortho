"""Adapts real scan data to refactoring_advisor's CodeRepository Protocol.

get_duplications() returns [] unconditionally: no code-similarity detector
exists in this codebase yet (see task-019 plan.md "Out of Scope"). This is
a documented gap, not fabricated data.

get_high_churn_modules() (task-025 part 3) reads git_history from
.ortho/ortho.db when present -- best-effort, since scan_repository() always
runs an in-memory scan regardless of whether `ortho scan` has ever been run
against this repo, so a git-history-backed answer may not be available.
"""

from __future__ import annotations

from pathlib import Path

from impact_analysis.dependency_health import DependencyHealthAnalyzer
from impact_analysis.types import ImportEdge as HealthImportEdge

from cli_commands.repo_scanner import ScanResult

_BLOAT_LINES_THRESHOLD = 300
_BLOAT_FUNCTIONS_THRESHOLD = 20

# A module needs more than a handful of commits to be meaningfully "high
# churn" rather than just recently created; flat threshold, not a
# configurable curve (ponytail: revisit only if a pilot shows this is wrong).
_HIGH_CHURN_COMMIT_THRESHOLD = 20


def _is_test_module(module: str) -> bool:
    """True if the dotted module name matches pytest/unittest's own
    discovery convention (a "tests" package segment, or a leaf named
    test_*/​*_test) -- not a new heuristic, the same rule the ecosystem's
    own tooling already treats as authoritative. A 384-line file with 47
    test functions doesn't carry the coupling/maintenance cost of 384
    lines of production code the way app.py's 1625 lines do; flagging it
    as "bloat: split into focused modules" recommends restructuring test
    files for a cost they don't actually impose, and on any repo with a
    substantial test suite it drowns the real findings in noise.
    """
    segments = module.split(".")
    return any(s == "tests" or s == "test" for s in segments) or any(
        s.startswith("test_") or s.endswith("_test") for s in segments
    )


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
            if _is_test_module(module):
                continue
            lines = metrics.get_module_lines(module)
            functions = metrics.get_module_functions(module)
            if lines > _BLOAT_LINES_THRESHOLD or functions > _BLOAT_FUNCTIONS_THRESHOLD:
                result.append((module, lines, functions))
        return result

    def get_duplications(self) -> list[tuple[str, str, float]]:
        return []

    def get_high_churn_modules(self) -> list[str]:
        """Modules with more than _HIGH_CHURN_COMMIT_THRESHOLD commits in
        git_history. Best-effort: no .ortho/ortho.db (repo never scanned),
        no git repo, or any DB error all degrade to an empty list -- a
        missing churn signal must never fail the whole refactor report.
        """
        try:
            from repo_intelligence.index_store import mint_repo_id, _mint
            from storage import OrthoDatabase
            from context_hub import GitMetadataStore

            repo_root = self._scan.repo_root
            if not (repo_root / ".ortho" / "ortho.db").exists():
                return []

            db = OrthoDatabase(repo_root)
            repo_id = mint_repo_id(repo_root)
            conn = db.connection()
            try:
                git_store = GitMetadataStore(conn, repo_root, repo_id)
                result: list[str] = []
                for file_key, module in self._scan.file_to_module.items():
                    if _is_test_module(module):
                        continue
                    try:
                        rel_path = str(Path(file_key).relative_to(repo_root)).replace("\\", "/")
                    except ValueError:
                        continue
                    file_id = _mint(repo_id, rel_path)
                    churn = git_store.get_file_churn(file_id)
                    if churn.commit_count > _HIGH_CHURN_COMMIT_THRESHOLD:
                        result.append(module)
                return result
            finally:
                conn.close()
        except Exception:
            return []
