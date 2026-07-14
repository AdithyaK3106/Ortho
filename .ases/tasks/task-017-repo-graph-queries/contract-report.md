TASK:           task-017-repo-graph-queries
TIMESTAMP:      2026-07-14

## Contract Summary

Total public APIs examined: 5 classes, 10 methods (incl. constructors)
Matched (spec = arch = impl = tests): 15
Missing (in spec, absent from implementation): 0
Unexpected (in implementation or tests, absent from spec): 0

## Constructor Comparison

| Class | Specification | Architecture Review | Builder Implementation | Tests Expect | Match? |
|---|---|---|---|---|---|
| RepoGraphQueries | `__init__(self, call_edges: list[CallEdge], import_edges_by_file: dict[str, list[ImportEdge]])` (spec.md Component 1) | not separately elaborated (same-package, no cross-boundary concern) | `__init__(self, call_edges: list[CallEdge], import_edges_by_file: dict[str, list[ImportEdge]]) -> None` (graph_queries.py:23-29) | `RepoGraphQueries([_edge(...)], {})` / `RepoGraphQueries([], edges_by_file)` (test_graph_queries.py:34,85) | ✅ |
| SymbolIndex | `__init__(self, symbols_by_file: dict[str, list[Symbol]])` (spec.md Component 2) | n/a | `__init__(self, symbols_by_file: dict[str, list[Symbol]]) -> None` (graph_queries.py:101) | `SymbolIndex({"file.py": symbols})` (test_graph_queries.py: TestSymbolIndex, multiple) | ✅ |
| CodeMetricsAdapter | `__init__(self, file_to_module: dict[str, str])` (spec.md Component 5) | n/a | `__init__(self, file_to_module: dict[str, str]) -> None` (graph_queries.py:111) | `CodeMetricsAdapter({str(fixture): "mymodule"})` (test_graph_queries.py: TestCodeMetricsAdapter, multiple) | ✅ |
| ArchModelAdapter | `__init__(self, model: ArchitectureModel, file_to_module: dict[str, str])` — corrected in spec.md to explicitly forbid any repo_intelligence type (architecture-review.md, ADR-016) | same constraint, explicit: "must only accept arch_intelligence's own types plus plain primitives" | `__init__(self, model: ArchitectureModel, file_to_module: dict[str, str]) -> None` (model_adapter.py:16) — no repo_intelligence import present in file | `ArchModelAdapter(model, {"file_a": "mod_a"})` (test_model_adapter.py, multiple) | ✅ |
| DependencyGraphAdapter | `__init__(self, import_edges_by_file: dict[str, list[ImportEdge]], file_to_module: dict[str, str])`, relocated to `packages/cli-commands` per ADR-016 | explicit placement requirement: cli-commands only, bridges repo_intelligence.ImportEdge into arch_guardrails DepGraph shape | `__init__(self, import_edges_by_file: dict[str, list[ImportEdge]], file_to_module: dict[str, str]) -> None` (dependency_graph_adapter.py:19-26), located at `packages/cli-commands/src/cli_commands/dependency_graph_adapter.py` | `DependencyGraphAdapter(import_edges_by_file, file_to_module)` (test_dependency_graph_adapter.py, multiple), test file located at `packages/cli-commands/tests/test_dependency_graph_adapter.py` | ✅ |

## Method Comparison

| Method | Specification Signature | Builder Signature | Test Call Pattern | Return Type Match | Match? |
|---|---|---|---|---|---|
| RepoGraphQueries.find_callers | `find_callers(self, symbol: str, depth: int = 1) -> list[str]` | `find_callers(self, symbol: str, depth: int = 1) -> list[str]` (graph_queries.py:31) | `.find_callers("target", depth=1)`, `.find_callers("target", depth=2)` — positional+kwarg matches signature (test_graph_queries.py:35,46) | ✅ | ✅ |
| RepoGraphQueries.find_importers | `find_importers(self, file_path: str, include_type: bool = False) -> list[tuple[str,str]] \| list[str]` | same (graph_queries.py:63-67) | `.find_importers("target.py", include_type=False)`, `.find_importers("target.py", include_type=True)` (test_graph_queries.py, TestFindImporters) | ✅ (both branches exercised) | ✅ |
| SymbolIndex.symbols_in_file | `symbols_in_file(self, file_path: str) -> list[str]` | same (graph_queries.py:104) | `.symbols_in_file("file.py")` (test_graph_queries.py, TestSymbolIndex) | ✅ | ✅ |
| CodeMetricsAdapter.get_module_lines | `get_module_lines(self, module: str) -> int` | same (graph_queries.py:117) | `.get_module_lines("mymodule")` (test_graph_queries.py, TestCodeMetricsAdapter) | ✅ | ✅ |
| CodeMetricsAdapter.get_module_functions | `get_module_functions(self, module: str) -> int` | same (graph_queries.py:127) | `.get_module_functions("mymodule")` (test_graph_queries.py, TestCodeMetricsAdapter) | ✅ | ✅ |
| ArchModelAdapter.get_layer | `get_layer(self, module: str) -> str` | same (model_adapter.py:29) | `.get_layer("mod_a")` (test_model_adapter.py, multiple) | ✅ | ✅ |
| ArchModelAdapter.get_layer_for_module | `get_layer_for_module(self, module: str) -> str` (alias of get_layer) | same, implemented as alias (model_adapter.py:32-33) | `.get_layer_for_module("mod_a")` compared directly to `.get_layer("mod_a")` (test_model_adapter.py:test_get_layer_for_module_matches_get_layer) | ✅ | ✅ |
| ArchModelAdapter.get_layers | `get_layers(self) -> list[str]`, sorted by Layer.number | same (model_adapter.py:35-36) | `.get_layers()` compared against expected number-ascending order (test_model_adapter.py:test_get_layers_ordering_by_number) | ✅ | ✅ |
| ArchModelAdapter.get_modules | `get_modules(self) -> list[str]` | same (model_adapter.py:38-43) | `.get_modules()` (test_model_adapter.py, multiple) | ✅ | ✅ |
| DependencyGraphAdapter.get_edges | `get_edges(self) -> list[tuple[str,str]]` | same (dependency_graph_adapter.py:28) | `.get_edges()` (test_dependency_graph_adapter.py, TestGetEdges) | ✅ | ✅ |
| DependencyGraphAdapter.find_cycles | `find_cycles(self) -> list[list[str]]` | same (dependency_graph_adapter.py:55) | `.find_cycles()` (test_dependency_graph_adapter.py, TestFindCycles) | ✅ | ✅ |

## Dataclass Comparison

No new dataclasses introduced by this task (all 5 new classes are plain classes wrapping existing spec/architecture dataclasses — `ArchitectureModel`, `Layer`, `CallEdge`, `ImportEdge`, `Symbol` — all pre-existing, untouched by this task).

## Verdict

**VERDICT: Contract Valid**

All 5 constructors and 10 methods match across spec.md, architecture-review.md (including its ADR-016-driven corrections), the actual BUILDER implementation (verified by reading the real `.py` files, not implementation-notes.md prose), and the actual TEST-DESIGNER test code (verified by reading real test call sites, not test-plan.md prose). No stateful-constructor-vs-stateless mismatch (the exact failure class this gate exists to catch, per task-008's history) was found — every constructor signature in tests exactly matches the corresponding `__init__` in implementation, with the same argument count, order, and shape. The one contract that changed mid-task (`DependencyGraphAdapter`'s file location and `ArchModelAdapter`'s constrained constructor, both driven by ADR-016) is reflected consistently across all four sources: spec.md was corrected before BUILDER started (GATE 2), and both BUILDER's implementation and TEST-DESIGNER's tests independently landed on the corrected placement/shape.

## Recommendation

Proceed to VERIFIER.
