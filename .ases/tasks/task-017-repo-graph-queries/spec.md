task: task-017-repo-graph-queries
title: Repo graph query layer + CLI wiring for guardrails/decide
owner: Solo Developer
created: 2026-07-14
status: DRAFT
architecture_impact: MAJOR (new adapter modules bridging 3 packages; architect review required)
architecture_review: APPROVED CONDITIONAL (see architecture-review.md) — spec corrected below per that review. Requires ADR-016 (Engineering Copilot layer) human acceptance alongside GATE 2.

objective: Build 6 missing query methods as real logic over real repo-intelligence/arch-intelligence output, then wire cli_commands.guardrails() and cli_commands.decide() to call the real ArchitectureEnforcer/ChangePredictor/DecisionEngine instead of returning hardcoded stub strings.

files_create:
  - packages/repo-intelligence/src/repo_intelligence/graph_queries.py
  - packages/repo-intelligence/tests/test_graph_queries.py
  - packages/arch-intelligence/src/arch_intelligence/model_adapter.py
  - packages/arch-intelligence/tests/test_model_adapter.py
  - packages/cli-commands/src/cli_commands/dependency_graph_adapter.py
  - packages/cli-commands/src/cli_commands/module_mapping.py
  - packages/cli-commands/tests/test_dependency_graph_adapter.py
  - packages/cli-commands/tests/test_module_mapping.py

files_modify:
  - packages/cli-commands/src/cli_commands/commands.py
  - packages/cli-commands/tests/test_commands.py
  - packages/repo-intelligence/src/repo_intelligence/__init__.py (add new exports)
  - packages/arch-intelligence/src/arch_intelligence/__init__.py (add new exports)

files_forbid:
  - packages/cli-commands/src/cli_commands/commands.py::CliCommands.plan (do not touch)
  - packages/cli-commands/src/cli_commands/commands.py::CliCommands.refactor (do not touch)
  - packages/arch-intelligence/src/arch_intelligence/arch_detector.py (read-only; do not modify existing style-detection heuristic)
  - packages/repo-intelligence/src/repo_intelligence/dependency_graph.py (this is the EXTERNAL package dependency graph — unrelated, do not touch or confuse with the new internal DependencyGraphAdapter)

contract_in: Real filesystem repo paths (e.g. repos/click) — Python source trees
contract_out: |
  CliReport objects (packages/cli-commands/src/cli_commands/types.py) containing
  real GuardrailViolation / Decision data serialized to human-readable text.

---

## Component 1: `RepoGraphQueries` (call graph + import graph queries)

**File:** `packages/repo-intelligence/src/repo_intelligence/graph_queries.py`

### Interface

```python
class RepoGraphQueries:
    def __init__(self, call_edges: list[CallEdge], import_edges_by_file: dict[str, list[ImportEdge]]) -> None:
        """
        call_edges: flat list from CallGraphBuilder.build_call_graph() across all files
        import_edges_by_file: maps real file path -> list of ImportEdge extracted from that file
          (caller must supply this mapping since ImportEdge.source_module is always "<current>"
           and does not carry real file identity — see Known Constraint below)
        """

    def find_callers(self, symbol: str, depth: int = 1) -> list[str]:
        """
        Return caller_name values of CallEdge entries whose callee_id or callee_name
        matches `symbol` (exact string match), traversing transitively up to `depth` hops
        via caller->callee chains. depth=1 returns only direct callers.
        Must not infinite-loop on cyclic call graphs (recursive functions).
        Returns a list with no duplicates, order not significant.
        """

    def find_importers(self, file_path: str, include_type: bool = False) -> list[tuple[str, str]] | list[str]:
        """
        Return files (from import_edges_by_file keys) that import `file_path`'s
        target module. If include_type=True, return (importer_file, import_type)
        tuples; else return importer_file strings only.
        Resolution is via target_module matching the module name derived from
        file_path (e.g. "pkg/mod.py" -> "pkg.mod" and "mod"), not via source_module
        (which is always "<current>" in raw ImportEdge data and must be ignored
        for resolution — the caller-supplied dict key is the real source).
        """
```

### Known Constraint (do not "fix" upstream — document and route around it)

`ImportEdge.source_module` (`repo_intelligence/import_graph.py:16,105,127`) is
hardcoded to the literal string `"<current>"` at extraction time. The real
source file identity is known only by the code that called
`extract_imports(file_path, source)` for that specific file. Therefore
`RepoGraphQueries` requires the caller to pass `import_edges_by_file: dict[str,
list[ImportEdge]]` (file path -> edges extracted from that file) rather than a
flat list. Do not modify `import_graph.py` to "fix" `source_module` — that is
out of scope and forbidden (see `files_forbid`).

### Test Coverage (12+ cases)

| Case | Input | Expected | Notes |
|---|---|---|---|
| Direct caller found | 1 CallEdge caller->target | `[caller]` | Normal path |
| No callers | target has no incoming edges | `[]` | Edge case |
| Transitive depth=2 | A calls B calls target | depth=1: `[B]`; depth=2: `[A, B]` | Traversal |
| Recursive function | target calls itself | terminates, no infinite loop | Cycle safety |
| Duplicate edges | same caller->target twice | caller listed once | Dedup |
| Symbol not found | unknown symbol string | `[]` | Fallback |
| Empty call_edges | `[]` | `[]` | Edge case |
| Direct importer found | 1 ImportEdge target=file's module | `[importer_file]` | Normal path |
| include_type=True | same as above | `[(importer_file, "import")]` | Type included |
| No importers | file imported by nobody | `[]` | Edge case |
| Star import type | import_type="star" preserved... wait, ImportEdge only has 'from'/'import'/'relative' — test whichever types extract_imports actually returns | matches real import_type string | Correctness against real enum values, not assumed ones |
| Empty import_edges_by_file | `{}` | `[]` | Edge case |
| Real-repo scan | run against `repos/click/src/click/core.py` | returns non-crashing list (empty or populated); assert no exception | Real-repo test (mandatory) |

---

## Component 2: `SymbolIndex`

**File:** `packages/repo-intelligence/src/repo_intelligence/graph_queries.py` (same file, second class)

### Interface

```python
class SymbolIndex:
    def __init__(self, symbols_by_file: dict[str, list[Symbol]]) -> None:
        """symbols_by_file: real file path -> Symbol list from SymbolExtractor.extract_symbols()"""

    def symbols_in_file(self, file_path: str) -> list[str]:
        """Return Symbol.name for every symbol in symbols_by_file[file_path]. [] if file_path unknown."""
```

### Test Coverage (6+ cases)

| Case | Input | Expected |
|---|---|---|
| Known file, symbols present | file with 3 Symbol objects | list of 3 names |
| Unknown file | file_path not in dict | `[]` |
| Empty symbols list for file | file present, `[]` value | `[]` |
| Duplicate names in file | 2 Symbol objects, same name (overload-like) | both returned (no forced dedup — names aren't unique identifiers here) |
| Empty dict | `{}` | `[]` for any file_path |
| Real-repo scan | `repos/flask/src/flask/app.py` via real `SymbolExtractor` | non-empty list, no exception |

---

## Component 3: `ArchModelAdapter`

**File:** `packages/arch-intelligence/src/arch_intelligence/model_adapter.py`

**Layer constraint (ADR-016):** this class lives in `arch-intelligence` and
therefore may only accept `arch_intelligence`'s own types plus plain
primitives (`dict[str, str]`) as constructor arguments. It must NOT accept
any `repo_intelligence` type (e.g. `ImportEdge`, `CallEdge`, `Symbol`)
directly — that would be an Intelligence-to-Intelligence import, forbidden
by ADR-015. The `file_to_module` dict is built by the caller (`cli-commands`,
Apps layer) and passed in as a plain `dict[str, str]`, which is not an
Intelligence-layer type.

### Interface

```python
class ArchModelAdapter:
    def __init__(self, model: ArchitectureModel, file_to_module: dict[str, str]) -> None:
        """
        model: ArchitectureModel from arch_intelligence.types (has .layers: list[Layer], each with file_ids)
        file_to_module: maps file_id -> a module identifier string (plain dict, caller-supplied;
          arch-intelligence's ArchitectureModel keys layers by file_ids, not module names,
          so this mapping bridges that gap without arch-intelligence importing repo_intelligence types)
        """

    def get_layer(self, module: str) -> str:
        """change_planner.predictor.ArchitectureModel protocol. Return Layer.name whose
        file_ids (mapped through file_to_module) contains `module`. Return "unknown" if not found."""

    def get_layers(self) -> list[str]:
        """arch_guardrails.enforcer.ArchModel protocol. Return [layer.name for layer in model.layers],
        ordered by Layer.number ascending (this ordering is load-bearing: enforcer's
        _check_layer_boundaries compares list index to detect upward deps)."""

    def get_layer_for_module(self, module: str) -> str:
        """Same resolution as get_layer(). Both protocols need this; implement once, alias the other."""

    def get_modules(self) -> list[str]:
        """Return all distinct values of file_to_module.values() that appear in any layer's file_ids."""
```

### Test Coverage (10+ cases)

| Case | Input | Expected |
|---|---|---|
| Module in layer 0 | file_to_module maps to layer 0's file_ids | returns layer 0's name |
| Module not in any layer | unmapped module string | "unknown" |
| get_layers ordering | layers with number=[2,0,1] | returned in number-ascending name order |
| Empty layers | `ArchitectureModel(layers=[])` | get_layers() = `[]`, get_layer() = "unknown" |
| get_modules dedup | 2 files map to same module string | module listed once |
| get_modules empty | empty file_to_module | `[]` |
| Layer with no file_ids | `Layer(file_ids=[])` | contributes no modules, still appears in get_layers() |
| get_layer_for_module == get_layer | same module input | identical output (protocol alias correctness) |
| Unknown file_id in mapping | file_to_module has key not in any Layer.file_ids | that module resolves to "unknown" |
| Real-repo scan | build ArchitectureModel via real ArchitectureDetector against `repos/requests`, wrap in adapter | no exception, get_layers() returns list (possibly empty if style=UNKNOWN) |

---

## Component 4: `DependencyGraphAdapter` (internal import-based dep graph + cycle detection)

**File:** `packages/cli-commands/src/cli_commands/dependency_graph_adapter.py`

**Layer placement (ADR-016):** this class lives in `cli-commands` (Apps
layer), NOT `arch-intelligence`, because it directly consumes
`repo_intelligence.ImportEdge` (via `repo_intelligence`'s `__all__`) to
produce the `DepGraph` protocol shape `arch-guardrails` (Engineering
Copilot layer) expects. Apps layer is the only layer permitted to bridge
two different lower-layer packages' raw types in one place per ADR-016.
Do not move this back into `arch-intelligence` or `repo-intelligence`.

### Interface

```python
class DependencyGraphAdapter:
    def __init__(self, import_edges_by_file: dict[str, list[ImportEdge]], file_to_module: dict[str, str]) -> None:
        """
        Builds an internal file-level (resolved to module-level via file_to_module)
        dependency graph from real ImportEdge data. This is NOT
        repo_intelligence.dependency_graph.DependencyGraphBuilder (that builds
        EXTERNAL package deps from requirements.txt — unrelated, do not touch).
        """

    def get_edges(self) -> list[tuple[str, str]]:
        """Return (source_module, target_module) pairs, source resolved via
        import_edges_by_file's key -> file_to_module, target resolved via
        ImportEdge.target_module matched against file_to_module's values
        (best-effort substring/suffix match since target_module is a dotted
        import path, e.g. "pkg.mod", and file_to_module values may be "pkg/mod.py"
        style — document exact matching rule used in implementation-notes.md)."""

    def find_cycles(self) -> list[list[str]]:
        """
        Return all simple cycles in the directed graph from get_edges(), using
        DFS-based cycle detection (e.g. three-color / Tarjan SCC filtered to
        SCCs of size > 1, or SCCs of size 1 with a self-loop). Each cycle is a
        list of module names in cycle order. Empty list if acyclic.
        This is a NEW, separate implementation from arch_detector.py's private
        _dag_shape() heuristic (which returns depth/ratio floats, not cycle
        lists) — do not modify or call that private method.
        """
```

### Test Coverage (12+ cases)

| Case | Input | Expected |
|---|---|---|
| No edges | empty import_edges_by_file | get_edges() = `[]`, find_cycles() = `[]` |
| Simple acyclic chain | A imports B imports C | get_edges() has 2 edges, find_cycles() = `[]` |
| Direct 2-cycle | A imports B, B imports A | find_cycles() returns `[["A","B"]]` (or `[["B","A"]]` — order within cycle documented, not asserted exact rotation) |
| 3-node cycle | A->B->C->A | find_cycles() returns one 3-element cycle |
| Self-import (A imports A) | edge case | detected as a 1-node cycle, or documented as ignored — pick one behavior and test it explicitly |
| Two independent cycles | A<->B and C<->D in same graph | find_cycles() returns 2 separate cycles |
| Unmapped target_module | ImportEdge target not resolvable to any known module | edge excluded from get_edges() (external/stdlib import), not crash |
| Large acyclic graph | 50 files, linear import chain | find_cycles() = `[]`, completes without exponential blowup |
| Duplicate edges | same source->target import edge twice | get_edges() may include duplicate or dedup — pick one, document, test it |
| get_edges determinism | same input twice | same output twice (no dependence on dict/set iteration order) |
| Real-repo scan | `repos/click` full import scan | completes in <30s, no exception, returns a list (cycles or empty) |
| Real-repo cycle detection | scan a repo/subset with a KNOWN hand-verified circular import (construct one small real fixture package with a genuine A<->B circular import if none exists in click/flask/requests) | find_cycles() correctly reports it |

---

## Component 5: `CodeMetricsAdapter`

**File:** `packages/repo-intelligence/src/repo_intelligence/graph_queries.py` (same file, third class) OR separate file — BUILDER's choice, document in implementation-notes.md

### Interface

```python
class CodeMetricsAdapter:
    def __init__(self, file_to_module: dict[str, str]) -> None:
        """file_to_module: real file path -> module identifier"""

    def get_module_lines(self, module: str) -> int:
        """Read the real file(s) mapped to `module`, count non-blank lines via len(f.readlines())
        (or equivalent). Sum if multiple files map to same module. Return 0 if module unknown
        or file unreadable (do not crash on missing file)."""

    def get_module_functions(self, module: str) -> int:
        """Count function/method definitions via ast.parse + counting FunctionDef/AsyncFunctionDef
        nodes in the real file(s) mapped to `module`. Return 0 if module unknown or unparseable."""
```

### Test Coverage (10+ cases)

| Case | Input | Expected |
|---|---|---|
| Real file, known line count | small real fixture file with N known lines | returns N (exact match) |
| Unknown module | not in file_to_module | 0 |
| Missing file on disk | mapped path doesn't exist | 0, no exception |
| Empty file | 0-byte file | 0 |
| Function count, known file | fixture with 3 top-level defs | 3 |
| Function count with classes | fixture with 2 methods in 1 class | 2 (methods count as functions) |
| Nested functions | fixture with a function defined inside another | both counted (documented: nested functions count) |
| Syntax error in file | unparseable Python | 0, no exception (graceful degradation) |
| Multiple files same module | 2 files map to same module string | lines/functions summed across both |
| Real-repo scan | `repos/requests/src/requests/models.py` | returns positive int for both lines and functions, no exception |

---

## Component 6: CLI wiring

**File:** `packages/cli-commands/src/cli_commands/commands.py` (modify existing `CliCommands` class)

### Behavior

```python
def guardrails(self, path: str = None, **kwargs) -> CliReport:
    """
    1. Scan real repo at `path` (default: cwd) via repo-intelligence
       (CallGraphBuilder, ImportGraphBuilder, SymbolExtractor over all .py files).
    2. Run ArchitectureDetector to get an ArchitectureModel.
    3. Build file_to_module mapping (path -> dotted module path, relative to repo root).
    4. Wrap in ArchModelAdapter, DependencyGraphAdapter, CodeMetricsAdapter.
    5. Call ArchitectureEnforcer(arch_model, dep_graph, metrics).check_violations().
    6. Format violations into CliReport.content (one line per violation:
       "[{severity}] {rule_id} at {location}: {message} -> {suggested_fix}").
    7. If zero violations, content states "No violations found" truthfully
       (i.e. only after a real scan ran, not as an unconditional default).
    """

def decide(self, intent: str, **kwargs) -> CliReport:
    """
    1. Treat `intent` as a file path if it exists on disk (change-impact mode);
       otherwise treat as a text description (guardrails-only mode — no
       ChangePredictor call possible without a target file).
    2. Scan repo containing `intent` (or cwd) via same pipeline as guardrails().
    3. If intent is a real file: also run ChangePredictor.predict_impact(intent).
    4. Aggregate via DecisionEngine.decide(intent, sources={"arch_guardrails": violations, "change_planner": [impact_prediction] if available}).
    5. Format Decision into CliReport.content (recommended option + reasoning + top alternatives).
    """
```

### Test Coverage (10+ cases) — in `packages/cli-commands/tests/test_commands.py`

| Case | Input | Expected |
|---|---|---|
| guardrails on real clean repo | small real fixture with no violations | CliReport.success=True, content truthfully states no violations, but only reachable after a real scan executed (assert scan was actually invoked — e.g. via a spy/real side effect, not just string match) |
| guardrails on repo with real violation | fixture with a deliberately introduced circular import | content includes "dependency_direction" or equivalent real rule_id from actual GuardrailViolation |
| guardrails on nonexistent path | path doesn't exist | CliReport.success=False (not a crash, not a silent fake success) |
| guardrails default path (None) | no path given | scans cwd, does not crash |
| decide with real file path | path to real .py file in a scanned repo | content reflects real ImpactPrediction data (e.g. affected_modules from real call/import graph) |
| decide with non-path intent string | e.g. "add caching" | falls back to guardrails-only aggregation, does not crash trying to treat it as a file |
| decide empty intent | "" | handled without exception; success reflects real error handling, not swallowed |
| Real-repo scan | `ortho guardrails repos/click` end-to-end | completes, CliReport.content contains real rule_ids or a truthful zero-violations statement |
| No stub leakage | any guardrails/decide call | content never contains the literal old stub strings ("No violations found!" as an unconditional default, "[HIGH] Issue 1") — grep test asserting these exact old literals are gone from source |
| success=False on internal exception | force a scan error (e.g. permission-denied mock) | CliReport.success=False, no unhandled exception propagates to caller |

---

## Integration Points

```
[CLI: ortho guardrails <path>]
  → scan path (CallGraphBuilder, ImportGraphBuilder, SymbolExtractor, ArchitectureDetector)
  → build file_to_module mapping
  → RepoGraphQueries / SymbolIndex / ArchModelAdapter / DependencyGraphAdapter / CodeMetricsAdapter
  → ArchitectureEnforcer.check_violations()
  → CliReport

[CLI: ortho decide <intent>]
  → same scan pipeline
  → ChangePredictor.predict_impact() (if intent is a file)
  → ArchitectureEnforcer.check_violations()
  → DecisionEngine.decide(intent, sources={...})
  → CliReport
```

---

## Acceptance Criteria (GATE 4 requirements)

- [ ] 60+ test cases across all 6 components (12+12+10+12+10+10 minimum from tables above)
- [ ] 100% test pass rate (pytest -v)
- [ ] Every test file imports its real product module (no test-only mocks of the unit under test)
- [ ] ≥1 property-based test (hypothesis, ≥10 generated cases) — recommended target: `find_cycles` (property: adding a reverse edge between any two connected nodes either preserves or creates ≥1 cycle) or `find_callers` (property: depth=N+1 result is a superset of depth=N result)
- [ ] ≥1 real-repo scan test per component (against `repos/click`, `repos/flask`, or `repos/requests` — already cloned in the repo)
- [ ] No external API calls in tests
- [ ] Edge cases documented (empty, null/missing, cyclic, unreadable file, syntax error)
- [ ] mypy --strict passes on all new files
- [ ] No TODO comments
- [ ] Old stub literals verifiably removed (grep-based test)
- [ ] Regression: full existing suite (303 tests) still passes

## Notes for BUILDER

- Do not modify `import_graph.py`, `call_graph.py`, `dependency_graph.py`, or `arch_detector.py` — build adapters that consume their existing output as-is. The `source_module = "<current>"` limitation in `ImportEdge` is a known constraint, not a bug to fix in this task.
- **Layer placement is not optional** — see architecture-review.md and ADR-016. `ArchModelAdapter` stays in `arch-intelligence` and must never import `repo_intelligence` types. `DependencyGraphAdapter` lives in `cli-commands` because it bridges `repo_intelligence.ImportEdge` into the `arch-guardrails` `DepGraph` shape — Apps layer is the only permitted place for that bridge.
- `file_to_module` mapping (file path -> dotted module string) is needed by several adapter components. Build one shared helper, `path_to_module(file_path: Path, repo_root: Path) -> str`, in `packages/cli-commands/src/cli_commands/module_mapping.py` (new file), used consistently everywhere a caller needs to build this dict, to avoid slightly-different implementations that silently disagree.
- If a real 2-node circular import fixture does not already exist in `repos/click`, `repos/flask`, or `repos/requests`, TEST-DESIGNER is authorized to add ONE small fixture package under `packages/cli-commands/tests/fixtures/circular_import_fixture/` with two files that genuinely `import` each other — this is a test fixture, not a change to a cloned third-party repo.
