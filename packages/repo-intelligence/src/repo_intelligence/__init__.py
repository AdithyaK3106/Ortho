"""
Repo Intelligence Package

Language-specific code analysis adapters and symbol extraction.
"""

# PythonAdapter requires tree-sitter + tree-sitter-languages at runtime.
# It is intentionally imported with a soft guard so that the rest of the
# package (ImportGraphBuilder, CallGraphBuilder, etc.) remains importable
# in environments where tree-sitter is not installed.
try:
    from .adapters.python_adapter import PythonAdapter
except RuntimeError:
    PythonAdapter = None  # type: ignore[assignment,misc]
from .symbol_extractor import SymbolExtractor, Symbol
from .import_graph import ImportGraphBuilder, ImportEdge
from .call_graph import CallGraphBuilder, CallEdge, CallGraphError
from .dependency_graph import DependencyGraphBuilder, DependencyEdge
from .module_detector import ModuleDetector, Module
from .incremental_indexer import IncrementalIndexer, IndexDelta, NotAGitRepoError

__all__ = [
    "PythonAdapter",
    "SymbolExtractor",
    "Symbol",
    "ImportGraphBuilder",
    "ImportEdge",
    "CallGraphBuilder",
    "CallEdge",
    "CallGraphError",
    "DependencyGraphBuilder",
    "DependencyEdge",
    "ModuleDetector",
    "Module",
    "IncrementalIndexer",
    "IndexDelta",
    "NotAGitRepoError",
]
