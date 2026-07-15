"""Real repo scan pipeline: walks a directory of .py files and produces the
data structures guardrails()/decide() need. Lives in cli-commands (Apps
layer, per ADR-016) since it bridges repo-intelligence and arch-intelligence
output for a single orchestration entry point.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from arch_intelligence.arch_detector import ArchitectureDetector
from arch_intelligence.arch_detector import File as ArchFile
from arch_intelligence.arch_detector import ImportEdge as AIImportEdge
from arch_intelligence.arch_detector import Symbol as AISymbol
from arch_intelligence.layer_detector import LayerDetector
from arch_intelligence.types import ArchitectureModel, ArchStyle
from repo_intelligence.call_graph import CallGraphBuilder, CallEdge
from repo_intelligence.import_graph import ImportGraphBuilder, ImportEdge
from repo_intelligence.symbol_extractor import SymbolExtractor, Symbol

from cli_commands.module_mapping import path_to_module


@dataclass
class _LayerImportEdge:
    importer_file_id: str
    imported_file_id: str


_logger = logging.getLogger(__name__)


_EXCLUDED_DIRS = frozenset({
    "node_modules", "venv", ".venv", "env", "__pycache__",
    "site-packages", "dist", "build", "vendor",
})


@dataclass
class ScanResult:
    repo_root: Path
    file_to_module: dict[str, str]
    call_edges: list[CallEdge]
    import_edges_by_file: dict[str, list[ImportEdge]]
    symbols_by_file: dict[str, list[Symbol]]
    arch_model: ArchitectureModel


def scan_repository(path: str) -> ScanResult:
    """Scan a real directory tree of Python files and build all analysis inputs."""
    repo_root = Path(path).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")

    py_files = sorted(
        p for p in repo_root.rglob("*.py")
        if not any(part.startswith(".") or part in _EXCLUDED_DIRS for part in p.parts)
    )

    call_builder = CallGraphBuilder()
    import_builder = ImportGraphBuilder()
    symbol_extractor = SymbolExtractor()

    file_to_module: dict[str, str] = {}
    call_edges: list[CallEdge] = []
    import_edges_by_file: dict[str, list[ImportEdge]] = {}
    symbols_by_file: dict[str, list[Symbol]] = {}
    arch_files: list[ArchFile] = []

    for py_file in py_files:
        file_key = str(py_file)
        module = path_to_module(py_file, repo_root)
        file_to_module[file_key] = module

        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        try:
            call_edges.extend(call_builder.extract_calls(py_file, source))
        except SyntaxError as e:
            # CallGraphBuilder uses ast.parse and raises SyntaxError on
            # malformed source; this is the only exception it can produce.
            _logger.warning("Skipping call-graph extraction for %s: %s", file_key, e)

        # ImportGraphBuilder (tree-sitter) and SymbolExtractor both parse
        # malformed source without raising, returning [] internally instead —
        # no try/except needed here; a wrapping except would be dead code.
        import_edges_by_file[file_key] = import_builder.extract_imports(py_file, source)
        symbols_by_file[file_key] = symbol_extractor.extract_symbols(py_file, source)

        arch_files.append(ArchFile(id=file_key, rel_path=str(py_file.relative_to(repo_root))))

    layer_edges = _build_layer_import_edges(import_edges_by_file, file_to_module, arch_files)
    layers = LayerDetector().extract_layers(layer_edges, arch_files)

    ai_import_graph = _build_ai_import_graph(import_edges_by_file, file_to_module)
    ai_symbols = _build_ai_symbols(symbols_by_file)
    style_result = ArchitectureDetector().detect(call_edges, ai_import_graph, ai_symbols, arch_files)

    arch_model = ArchitectureModel(
        repo_id=str(repo_root),
        style=style_result.style,
        style_confidence=style_result.confidence,
        # Layer names (Data/Business/Presentation) only mean something when
        # the repo actually has a layered-style hierarchy; a flat/microservices/
        # unknown-style repo gets fake tier labels from pure topological depth
        # otherwise, and guardrails reports disagreements with that fiction as
        # errors (see docs/archive/PRODUCTION_AUDIT_2026-07-15.md finding).
        layers=layers if _style_implies_layers(style_result.style, style_result.confidence) else [],
    )

    return ScanResult(
        repo_root=repo_root,
        file_to_module=file_to_module,
        call_edges=call_edges,
        import_edges_by_file=import_edges_by_file,
        symbols_by_file=symbols_by_file,
        arch_model=arch_model,
    )


def _build_layer_import_edges(
    import_edges_by_file: dict[str, list[ImportEdge]],
    file_to_module: dict[str, str],
    arch_files: list[ArchFile],
) -> list[_LayerImportEdge]:
    """Resolve ImportEdge.target_module to a real file_id for LayerDetector,
    which needs importer_file_id/imported_file_id, not module name strings."""
    module_to_file_id = {module: file_id for file_id, module in file_to_module.items()}

    edges: list[_LayerImportEdge] = []
    for file_key, import_edges in import_edges_by_file.items():
        for edge in import_edges:
            target_file_id = module_to_file_id.get(edge.target_module)
            if target_file_id is None:
                for module, file_id in module_to_file_id.items():
                    if module.endswith(f".{edge.target_module}"):
                        target_file_id = file_id
                        break
            if target_file_id is not None and target_file_id != file_key:
                edges.append(_LayerImportEdge(importer_file_id=file_key, imported_file_id=target_file_id))
    return edges


def _build_ai_import_graph(
    import_edges_by_file: dict[str, list[ImportEdge]],
    file_to_module: dict[str, str],
) -> list[AIImportEdge]:
    """Convert repo_intelligence ImportEdges to arch_intelligence's shape
    (adds imported_file_id/is_external) for ArchitectureDetector.detect()."""
    module_to_file_id = {module: file_id for file_id, module in file_to_module.items()}

    edges: list[AIImportEdge] = []
    for file_key, import_edges in import_edges_by_file.items():
        for edge in import_edges:
            target_file_id = module_to_file_id.get(edge.target_module)
            if target_file_id is None:
                for module, file_id in module_to_file_id.items():
                    if module.endswith(f".{edge.target_module}"):
                        target_file_id = file_id
                        break
            edges.append(AIImportEdge(
                importer_file_id=file_key,
                imported_file_id=target_file_id or "",
                imported_module=edge.target_module,
                is_external=target_file_id is None,
            ))
    return edges


def _build_ai_symbols(symbols_by_file: dict[str, list[Symbol]]) -> list[AISymbol]:
    """Flatten repo_intelligence's per-file symbol dict into arch_intelligence's
    flat (id, name, file_id) shape for ArchitectureDetector.detect()."""
    symbols: list[AISymbol] = []
    for file_key, file_symbols in symbols_by_file.items():
        for sym in file_symbols:
            symbols.append(AISymbol(id=f"{file_key}::{sym.name}", name=sym.name, file_id=file_key))
    return symbols


# Styles whose Data/Business/Presentation (or equivalent) layer labels reflect
# a real detected hierarchy, not just topological depth in the import graph.
# FLAT/MICROSERVICES/UNKNOWN/LOW_CONFIDENCE repos get no layers at all --
# reporting "layer_boundaries" violations against a fabricated tier structure
# is the primary source of guardrails false positives (see
# docs/archive/PRODUCTION_AUDIT_2026-07-15.md).
_LAYER_BEARING_STYLES = frozenset({ArchStyle.LAYERED, ArchStyle.MVC, ArchStyle.HEXAGONAL})
_MIN_LAYER_CONFIDENCE = 0.45


def _style_implies_layers(style: ArchStyle, confidence: float) -> bool:
    return style in _LAYER_BEARING_STYLES and confidence >= _MIN_LAYER_CONFIDENCE
