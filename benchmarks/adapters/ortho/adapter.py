"""OrthoAdapter: implements EngineeringSystemAdapter by wrapping the existing
initial pipeline stage bodies unchanged. Multiple stages collapse into one
adapter method where natural (scan_repository folds scan+graphs;
detect_architecture folds style+layers+subsystems).

**This is the only file in `benchmarks/` that imports from `packages/*`.**
No suite, no core/ module, no other adapter file may do this -- see
`validation/test_adapter_contract.py` for the enforced boundary check.
"""

import sys
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
for _rel in (
    "packages/repo-intelligence/src",
    "packages/arch-intelligence/src",
    "packages/impact-analysis/src",
    "packages/context-hub/src",
    "packages/token-optimizer/src",
    "shared/storage/src",
):
    _p = str(ROOT / _rel)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from repo_intelligence.file_discoverer import FileDiscoverer
from repo_intelligence.symbol_extractor import SymbolExtractor
from repo_intelligence.import_graph import ImportGraphBuilder
from repo_intelligence.call_graph import CallGraphBuilder
from arch_intelligence.arch_detector import (
    ArchitectureDetector,
    CallEdge as ArchCall,
    File as ArchFile,
    ImportEdge as ArchImport,
)
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.subsystem_detector import SubsystemDetector
from impact_analysis.impact_analyzer import ImpactAnalyzer
from storage import OrthoDatabase
from context_hub.schema import init_all_schemas
from context_hub.store import ArtifactStore
from context_hub.ingestion import ArtifactIngestionRequest
from context_hub.search.bm25 import BM25Search
from token_optimizer.assembler import assemble_context as _ortho_assemble_context
from token_optimizer.budget import TokenBudget

from adapters.interface import (
    ArchResult,
    ContextResult,
    EngineeringSystemAdapter,
    ImpactResult,
    RepoIndex,
    RetrievalHit,
)


class _SymbolRec:
    """Duck-typed symbol satisfying arch, impact consumers (moved from pipeline.py)."""

    __slots__ = ("id", "name", "file_id", "start_line", "end_line")

    def __init__(self, id, name, file_id, start_line=0, end_line=0):
        self.id = id
        self.name = name
        self.file_id = file_id
        self.start_line = start_line
        self.end_line = end_line


def _module_index(rel_paths):
    """Map dotted module names to file ids ('a/b/c.py' -> 'a.b.c'). Moved from pipeline.py."""
    idx = {}
    for rel in rel_paths:
        parts = rel[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            continue
        idx.setdefault(".".join(parts), rel)
        if parts[0] in ("src", "lib", "source") and len(parts) > 1:
            idx.setdefault(".".join(parts[1:]), rel)
    return idx


def _resolve_import(target, importer_rel, mod_idx):
    """Resolve a dotted (possibly relative) module name to a repo file id. Moved from pipeline.py."""
    target = target or ""
    if target.startswith("."):
        dots = len(target) - len(target.lstrip("."))
        rest = [p for p in target.lstrip(".").split(".") if p]
        base = importer_rel[:-3].split("/")[:-1]
        up = dots - 1
        if up > len(base):
            return None
        base = base[: len(base) - up] if up else base
        candidate = ".".join(base + rest)
    else:
        candidate = target
    while candidate:
        if candidate in mod_idx:
            return mod_idx[candidate]
        if "." not in candidate:
            return None
        candidate = candidate.rsplit(".", 1)[0]
    return None


def _scan_repo(repo_path: Path) -> dict:
    """Walk all Python files; extract symbols, imports, calls per file. Moved from pipeline.py."""
    discoverer = FileDiscoverer(repo_path)
    py_files = sorted(discoverer.find_python_files())

    sym_x = SymbolExtractor()
    imp_x = ImportGraphBuilder()
    call_x = CallGraphBuilder()

    per_file = {}
    parse_errors = []
    for fp in py_files:
        rel = fp.relative_to(repo_path).as_posix()
        try:
            source = fp.read_text(encoding="utf-8", errors="ignore")
            symbols = sym_x.extract_symbols(fp, source)
            imports = imp_x.extract_imports(fp, source)
            calls = call_x.extract_calls(fp, source, symbols)
            per_file[rel] = {"symbols": symbols, "imports": imports, "calls": calls}
        except Exception as e:  # noqa: BLE001 - per-file parse errors are non-fatal
            parse_errors.append(f"{rel}: {type(e).__name__}: {e}")

    return {
        "files_total": len(py_files),
        "files_scanned": len(per_file),
        "parse_errors": parse_errors,
        "per_file": per_file,
    }


def _build_graphs(scan: dict) -> dict:
    """Convert per-file scan output into the shared graph model. Moved from pipeline.py."""
    per_file = scan["per_file"]
    rel_paths = sorted(per_file)
    mod_idx = _module_index(rel_paths)

    files, symbols, calls, imports = [], [], [], []
    internal = external = 0
    for rel in rel_paths:
        data = per_file[rel]
        files.append(ArchFile(id=rel, rel_path=rel))
        for s in data["symbols"]:
            symbols.append(_SymbolRec(
                id=s.qualified_name, name=s.name, file_id=rel,
                start_line=s.lineno, end_line=s.lineno,
            ))
        for c in data["calls"]:
            calls.append(ArchCall(caller_id=c.caller_id, callee_id=c.callee_id,
                                   confidence=c.confidence))
        for i in data["imports"]:
            resolved = _resolve_import(i.target_module, rel, mod_idx)
            if resolved == rel:
                resolved = None
            is_ext = resolved is None
            internal += 0 if is_ext else 1
            external += 1 if is_ext else 0
            imports.append(ArchImport(
                importer_file_id=rel, imported_file_id=resolved,
                imported_module=i.target_module, is_external=is_ext,
            ))

    return {
        "files": files, "symbols": symbols, "calls": calls, "imports": imports,
        "imports_internal": internal, "imports_external": external,
    }


class _SearchableStore:
    """Adapter giving assemble_context() the search() contract over BM25/FTS5.
    Moved from pipeline.py unchanged.
    """

    def __init__(self, conn):
        self._bm25 = BM25Search(conn)

    def search(self, query, repo_id=None):
        merged = {}
        for term in query.split():
            for r in self._bm25.search(term, limit=50):
                prev = merged.get(r.artifact_id)
                if prev is None or r.relevance_score > prev.relevance_score:
                    merged[r.artifact_id] = r
        return [
            SimpleNamespace(
                id=r.artifact_id,
                content=r.content,
                relevance_score=r.relevance_score,
                estimated_tokens=int(len(r.content.split()) / 0.25),
            )
            for r in sorted(merged.values(), key=lambda r: r.artifact_id)
        ]


class OrthoAdapter(EngineeringSystemAdapter):
    """Wraps Ortho's existing analysis stages behind the 5-method capability interface."""

    def __init__(self):
        self._db_cache: dict[str, OrthoDatabase] = {}
        self._scan_cache: dict[str, dict] = {}
        self._graphs_cache: dict[str, dict] = {}

    # -- internal helpers -------------------------------------------------

    def _db(self, repo_path: Path) -> OrthoDatabase:
        key = str(repo_path)
        if key not in self._db_cache:
            db = OrthoDatabase(repo_path)
            db.migrate()
            conn = db.connection()
            init_all_schemas(conn)
            conn.commit()
            conn.close()
            self._db_cache[key] = db
        return self._db_cache[key]

    def _scan_and_graphs(self, repo_path: Path) -> tuple[dict, dict]:
        key = str(repo_path)
        if key not in self._scan_cache:
            scan = _scan_repo(repo_path)
            self._scan_cache[key] = scan
            self._graphs_cache[key] = _build_graphs(scan)
        return self._scan_cache[key], self._graphs_cache[key]

    # -- EngineeringSystemAdapter -----------------------------------------

    def scan_repository(self, repo_path: Path) -> RepoIndex:
        """Folds scan_repo + build_graphs into one capability call."""
        scan, graphs = self._scan_and_graphs(repo_path)
        return RepoIndex(
            symbols=[s.id for s in graphs["symbols"]],
            imports=[(e.importer_file_id, e.imported_file_id)
                     for e in graphs["imports"] if not e.is_external],
            calls=[(e.caller_id, e.callee_id) for e in graphs["calls"]],
            files_total=scan["files_total"],
            files_scanned=scan["files_scanned"],
            parse_errors=list(scan["parse_errors"]),
        )

    def detect_architecture(self, repo_path: Path) -> ArchResult:
        """Folds ArchitectureDetector + LayerDetector + SubsystemDetector into one call."""
        _, graphs = self._scan_and_graphs(repo_path)
        arch = ArchitectureDetector().detect(
            graphs["calls"], graphs["imports"], graphs["symbols"], graphs["files"])
        layers = LayerDetector().extract_layers(graphs["imports"], graphs["files"])
        subsystems = SubsystemDetector().detect_subsystems(
            graphs["calls"], graphs["symbols"], graphs["files"], graphs["imports"])

        layer_map: dict[str, int] = {}
        for layer in layers:
            for fid in layer.file_ids:
                layer_map[fid] = layer.number

        return ArchResult(
            style=arch.style.value,
            confidence=round(arch.confidence, 4),
            alternative=arch.alternative.value if arch.alternative else None,
            alternative_confidence=(round(arch.alternative_confidence, 4)
                                     if arch.alternative_confidence is not None else None),
            evidence=list(arch.evidence),
            layers=layer_map,
            subsystems=[list(s.file_ids) for s in subsystems],
        )

    def retrieve(self, repo_path: Path, query: str, k: int) -> list[RetrievalHit]:
        """Extracts the existing _SearchableStore.search path, ingesting analysis
        artifacts first so there is something to retrieve (mirrors assemble_context's
        production path).
        """
        db = self._db(repo_path)
        conn = db.connection()
        try:
            store = _SearchableStore(conn)
            hits = store.search(query)[:k]
        finally:
            conn.close()
        return [
            RetrievalHit(id=h.id, content=h.content, relevance_score=h.relevance_score)
            for h in hits
        ]

    def analyze_impact(self, repo_path: Path, changed_file: str) -> ImpactResult:
        """Wraps ImpactAnalyzer.analyze() as-is for a single changed file."""
        _, graphs = self._scan_and_graphs(repo_path)
        calls, imports, symbols = graphs["calls"], graphs["imports"], graphs["symbols"]

        syms_by_file: dict[str, set] = {}
        for s in symbols:
            syms_by_file.setdefault(s.file_id, set()).add(s.id)
        ids = syms_by_file.get(changed_file, set())
        touching = [e for e in calls if e.callee_id in ids]

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(
            call_graph=touching, import_graph=imports,
            changed_file_id=changed_file, symbols=symbols, depth=3,
        )
        impacted = sorted(set(report.direct_dependents) | set(report.transitive_dependents))
        return ImpactResult(
            changed_file=changed_file,
            impacted_files=impacted,
            blast_radius=report.blast_radius,
            risk_score=report.risk_score,
            evidence=list(report.evidence),
        )

    def assemble_context(self, repo_path: Path, query: str, budget: int) -> ContextResult:
        """Wraps assemble_repo_context()'s production path (ArtifactStore + BM25 +
        TokenBudget) as-is.
        """
        db = self._db(repo_path)
        repo_id = repo_path.name
        conn = db.connection()
        try:
            budget_obj = TokenBudget(total=budget, used=0, model="claude")
            t0 = time.perf_counter()
            package = _ortho_assemble_context(
                query=query, repo_id=repo_id, artifact_store=_SearchableStore(conn),
                budget=budget_obj, step_id="benchmark", workflow_run_id="benchmark",
            )
            latency_ms = (time.perf_counter() - t0) * 1000
        finally:
            conn.close()

        included = [c for c in package.chunks if c.included]
        return ContextResult(
            chunks_total=len(package.chunks),
            chunks_included=len(included),
            tokens_used=budget_obj.used,
            chars_included=sum(len(c.content) for c in included),
            latency_ms=round(latency_ms, 2),
            budget_total=budget,
            budget_fill_pct=round(budget_obj.used / budget * 100, 2) if budget else 0.0,
        )

    def ingest_analysis_artifacts(self, repo_path: Path) -> None:
        """Populate ContextHub with architecture/subsystem/debt artifacts so
        retrieve()/assemble_context() have real content to search, matching
        pipeline.py's `_ingest_analysis_artifacts` production behavior. Suites
        that exercise retrieval/context should call this once per repo before
        calling retrieve()/assemble_context().
        """
        _, graphs = self._scan_and_graphs(repo_path)
        arch = ArchitectureDetector().detect(
            graphs["calls"], graphs["imports"], graphs["symbols"], graphs["files"])
        layers = LayerDetector().extract_layers(graphs["imports"], graphs["files"])
        subsystems = SubsystemDetector().detect_subsystems(
            graphs["calls"], graphs["symbols"], graphs["files"], graphs["imports"])

        db = self._db(repo_path)
        repo_id = repo_path.name
        store = ArtifactStore(db, repo_id=repo_id)

        def ingest(a_type, title, content, tags):
            store.ingest_artifact(ArtifactIngestionRequest(
                type=a_type, title=title, content=content,
                source=f"benchmark/{repo_id}", relevance_scope="project", tags=tags,
            ))

        arch_lines = [f"Architecture style: {arch.style.value} (confidence {arch.confidence:.2f})"]
        arch_lines += list(arch.evidence)
        arch_lines.append(f"Layers detected: {len(layers)}")
        for layer in layers:
            arch_lines.append(f"  Layer {layer.number} {layer.name}: {len(layer.file_ids)} files")
        ingest("architecture", f"{repo_id}: architecture analysis",
               "\n".join(arch_lines), ["architecture", "benchmark"])

        top = sorted(subsystems, key=lambda s: (-len(s.file_ids), s.id))[:10]
        for sub in top:
            ingest("dev_note", f"{repo_id}: subsystem {sub.name}",
                   f"Subsystem {sub.name}: {len(sub.file_ids)} files, "
                   f"coupling {sub.coupling_score:.2f}. Members: "
                   + ", ".join(sub.file_ids[:20]),
                   ["subsystem", "benchmark"])

        fan_in = Counter(
            e.imported_file_id for e in graphs["imports"] if not e.is_external)
        ingest("benchmark", f"{repo_id}: repository scan statistics",
               f"Symbols: {len(graphs['symbols'])}. Imports: {len(graphs['imports'])}. "
               f"Call edges: {len(graphs['calls'])}. Most-imported: "
               + ", ".join(f for f, _ in fan_in.most_common(5)),
               ["scan", "benchmark"])
