# Implementation Notes: task-017-repo-graph-queries

## What Was Built

### packages/repo-intelligence/src/repo_intelligence/graph_queries.py (created)
- `RepoGraphQueries`: `find_callers(symbol, depth)` via BFS over `CallEdge.caller_name`/`callee_id`/`callee_name`, cycle-safe (tracks visited targets); `find_importers(file_path, include_type)` resolves `ImportEdge.target_module` against derived module-name candidates for `file_path`, since `ImportEdge.source_module` is always the literal `"<current>"` placeholder — callers must supply an `import_edges_by_file: dict[str, list[ImportEdge]]` keyed by real file identity.
- `SymbolIndex`: `symbols_in_file(file_path)` — plain lookup over a caller-supplied `dict[str, list[Symbol]]`.
- `CodeMetricsAdapter`: `get_module_lines`/`get_module_functions` — reads real files, counts lines and AST `FunctionDef`/`AsyncFunctionDef` nodes (including nested functions). Returns 0 on missing file or syntax error rather than raising.

### packages/arch-intelligence/src/arch_intelligence/model_adapter.py (created)
- `ArchModelAdapter`: wraps `ArchitectureModel`/`Layer` (arch-intelligence's own types) plus a plain `dict[str, str]` (`file_to_module`, caller-supplied). Implements `get_layer`/`get_layer_for_module` (alias), `get_layers` (sorted by `Layer.number`), `get_modules`. Per ADR-016, constructor accepts no `repo_intelligence` type.

### packages/cli-commands/src/cli_commands/module_mapping.py (created)
- `path_to_module(file_path, repo_root)`: single shared file→dotted-module resolver, used by `repo_scanner.py` and consumed indirectly wherever `file_to_module` dicts are built, so all adapters agree on the same module identity for the same file.

### packages/cli-commands/src/cli_commands/dependency_graph_adapter.py (created)
- `DependencyGraphAdapter`: builds an internal module-level dependency graph from real `ImportEdge` data (resolving `target_module` by exact/suffix match against known modules, skipping unresolvable/external imports). `find_cycles()` uses a three-color DFS (white/gray/black), returns real simple cycles as lists of module names. This is a new implementation, separate from `arch_detector.py`'s private `_dag_shape()` heuristic (which returns depth/ratio floats, not cycle lists) — that method was not touched. Lives in `cli-commands` per ADR-016 (bridges `repo_intelligence.ImportEdge` into `arch_guardrails`'s `DepGraph` shape; only the Apps layer may do this).

### packages/cli-commands/src/cli_commands/repo_scanner.py (created)
- `scan_repository(path)`: walks a real directory tree (excluding `.`-prefixed dirs, `node_modules`, `venv`/`.venv`, `__pycache__`, `site-packages`, `dist`, `build`, `vendor`), runs `CallGraphBuilder`/`ImportGraphBuilder`/`SymbolExtractor` per file, builds `file_to_module`, and runs `LayerDetector.extract_layers()` (resolving `ImportEdge.target_module` to real `file_id`s via a private helper) to produce a real `ArchitectureModel`. Returns a `ScanResult` dataclass bundling everything `guardrails()`/`decide()` need.

### packages/cli-commands/src/cli_commands/commands.py (modified)
- `guardrails(path)`: real scan → `ArchModelAdapter` + `DependencyGraphAdapter` + `CodeMetricsAdapter` → `ArchitectureEnforcer.check_violations()` → formatted `CliReport`. Replaces the old unconditional `"No violations found!"` stub.
- `decide(intent)`: rejects empty intent explicitly (`success=False`) rather than silently defaulting to an unbounded cwd scan. If `intent` is a real file path, also runs `ChangePredictor.predict_impact()` via three small protocol-view adapter classes (`_CallGraphView`, `_ImportGraphView`, `_SymbolRegistryView`) wrapping `RepoGraphQueries`/`SymbolIndex`. Aggregates via real `DecisionEngine.decide()`. Accepts an optional `scan_path` kwarg so a non-file text intent can be bound to a specific repo instead of always defaulting to `.`.
- `plan()` and `refactor()` untouched (out of scope, per `files_forbid`), except leaving their pre-existing `path: str = None` signatures as-is (forbidden to touch) — I did NOT copy that pattern into my own new `guardrails()` signature; that one uses `path: str | None = None` and is mypy --strict clean.

### packages/repo-intelligence/src/repo_intelligence/__init__.py, packages/arch-intelligence/src/arch_intelligence/__init__.py (modified)
- Added new classes to `__all__` per ADR-015's public-API-contract rule.

### packages/cli-commands/tests/test_commands.py, packages/cli-commands/tests/test_edge_cases_exhaustive.py (modified)
- These pre-existed from the stub era and called `guardrails()`/`decide()` with no path or a plain text intent, which is fine for a stub returning instant fake strings but now triggers a real filesystem scan. Updated to point at real bounded fixture repos (`repos/click`, `repos/requests`) already cloned in this monorepo, or to use the new `scan_path` kwarg. Added explicit tests for empty-intent rejection, bad-path handling, and a grep-based check that the exact old stub literals (`"No violations found!"`, `"Recommended: Option A"`) are gone.

## What Was Deliberately NOT Built
- `plan()`/`refactor()` wiring — explicitly out of scope per spec.md.
- A fix to `ImportEdge.source_module` being the literal `"<current>"` — documented as a known constraint to route around, not fix, since `import_graph.py` is in `files_forbid`.
- General unbounded-cwd-scan protection for `guardrails()`/`decide()` (e.g. a max-file-count guard or `.gitignore`-aware exclusion) — the `_EXCLUDED_DIRS` set covers common vendor/build directories, but a user could still point `ortho guardrails` at an arbitrarily large real directory. This is a CLI-UX concern beyond this task's scope (see Honest Assessment below).

## Real Bug Found and Fixed During Implementation
Initial `decide(intent)` treated any non-existent-file intent (including `""`) as falling back to scanning `"."` (cwd) unconditionally. In this specific monorepo, cwd (`ortho/`) contains `repos/`, which holds 5 fully-cloned frameworks (django, flask, celery, langchain, sqlalchemy — 7,882 `.py` files total). `decide('')` therefore hung for 60+ seconds during manual smoke-testing. Fixed by: (1) rejecting empty intent explicitly with `success=False`, (2) adding an optional `scan_path` kwarg so callers with a non-file text intent can bind to a specific bounded directory instead of defaulting blindly to `.`. Also added `_EXCLUDED_DIRS` (`node_modules`, `venv`, `__pycache__`, etc.) to `repo_scanner.py`'s file walk, since the original walk only excluded dot-prefixed directories.

## Deviations from Spec
None beyond the ADR-016-mandated placement correction already applied to spec.md before BUILDER started (Component 3/4 file locations).

## Files Modified (exact paths)
- packages/repo-intelligence/src/repo_intelligence/graph_queries.py (new)
- packages/repo-intelligence/src/repo_intelligence/__init__.py (modified — added exports)
- packages/arch-intelligence/src/arch_intelligence/model_adapter.py (new)
- packages/arch-intelligence/src/arch_intelligence/__init__.py (modified — added export)
- packages/cli-commands/src/cli_commands/module_mapping.py (new)
- packages/cli-commands/src/cli_commands/dependency_graph_adapter.py (new)
- packages/cli-commands/src/cli_commands/repo_scanner.py (new)
- packages/cli-commands/src/cli_commands/commands.py (modified — guardrails/decide wired to real engines)
- packages/cli-commands/tests/test_commands.py (modified — bounded to real fixtures)
- packages/cli-commands/tests/test_edge_cases_exhaustive.py (modified — bounded to real fixtures)

## Verification Commands
```
mypy --strict packages/repo-intelligence/src/repo_intelligence/graph_queries.py packages/arch-intelligence/src/arch_intelligence/model_adapter.py packages/cli-commands/src/cli_commands/dependency_graph_adapter.py packages/cli-commands/src/cli_commands/module_mapping.py packages/cli-commands/src/cli_commands/repo_scanner.py --ignore-missing-imports
pytest packages/cli-commands/tests -v --no-cov
pytest packages/arch-guardrails/tests packages/change-planner/tests packages/decision-engine/tests packages/repo-intelligence/tests -q --no-cov
pytest packages/arch-intelligence/tests -q --no-cov --deselect packages/arch-intelligence/tests/test_phase5_3_benchmarks.py
```

## Honest Assessment: What Might Break
- **Layer-boundary false positives:** `LayerDetector`'s numeric layer assignment (topological depth, not true semantic layers) produced many `layer_boundaries` violations on `repos/click` that look overly broad (e.g. flagging `core` importing `types` as "Business cannot import Data"). This is `LayerDetector`'s existing heuristic (untouched, pre-existing code), not a defect introduced here — but it means `ortho guardrails`'s real output on arbitrary repos may be noisy. Worth a follow-up task to tune or suppress low-confidence layer violations.
- **No bound on scan size for arbitrary user-supplied paths:** if a pilot user runs `ortho guardrails` against a directory containing large vendored dependencies not covered by `_EXCLUDED_DIRS` (e.g. a `.git` submodule checked out under a non-standard name), the scan could be slow. The <30s acceptance bound was verified only against the 3 named fixture repos (click: 76 files/2.2s, flask: 83 files/2.1s, requests: 37 files/0.5s), not against arbitrarily large inputs.
- **`find_cycles`/`find_callers` are O(V·E)-ish** — fine at fixture-repo scale, undocumented behavior at much larger scale (thousands of files in a single scan target).
- **Pre-existing, unrelated:** `test_phase5_3_benchmarks.py::test_sqlalchemy_benchmark` fails on both clean master and this branch (confirmed via `git stash` before/after comparison) — expects `ArchStyle.FLAT`, gets `UNKNOWN` for `repos/sqlalchemy`, likely due to newer sqlalchemy test files using Python 3.14 t-string syntax that the indexer can't parse. Not touched or caused by this task; matches CLAUDE.md's already-documented Task-015 benchmark gap.
