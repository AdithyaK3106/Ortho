# Architecture Review: task-017-repo-graph-queries

## Module Boundary Evaluation

The task introduces adapter modules bridging `repo-intelligence`,
`arch-intelligence`, and consuming packages (`change-planner`,
`arch-guardrails`, `decision-engine`) via `cli-commands`.

**Problem found:** spec.md places `DependencyGraphAdapter` and part of
`ArchModelAdapter`'s file-resolution logic in
`packages/arch-intelligence/src/arch_intelligence/`, but both require
`ImportEdge` (a `repo_intelligence` type) as direct input. Per ADR-015's
layer table, **Intelligence cannot import from Intelligence** (only from
Storage/Shared). `arch-intelligence` importing `repo_intelligence.ImportEdge`
directly violates this row.

**Second gap:** ADR-015 (2026-07-12) enumerates 6 core packages across 3
layers and does not mention `change-planner`, `arch-guardrails`,
`decision-engine`, or `cli-commands` — all built in Phase 6, after ADR-015
was written. These packages have no assigned layer. This must be resolved
before BUILDER proceeds, not left implicit.

**Resolution (see Decision below):** classify the four Phase-6 packages,
and correct the file placement so no package instantiates another
Intelligence package's raw types directly.

## Dependency Analysis (corrected)

```
apps/cli, cli-commands (Apps layer — orchestrates everything, may import from any lower layer)
    ↓
change-planner, arch-guardrails, decision-engine  (NEW: "Engineering Copilot" layer — sits above Intelligence, consumes Intelligence output only via protocols/adapters, never raw Intelligence internals)
    ↓
repo-intelligence, arch-intelligence  (Intelligence layer — parallel, no cross-imports between them)
    ↓
context-hub, token-optimizer  (Storage layer)
    ↓
shared/*
```

Corrected component placement:

- `RepoGraphQueries`, `SymbolIndex`, `CodeMetricsAdapter` → stay in
  `packages/repo-intelligence` (consume only `repo_intelligence`'s own
  `CallEdge`/`ImportEdge`/`Symbol` — same-package, no boundary issue).
- `ArchModelAdapter` → stays in `packages/arch-intelligence` **but must not
  accept raw `ImportEdge`/file-path-resolution logic as a constructor
  input**. It may only consume `arch_intelligence`'s own `ArchitectureModel`/
  `Layer` plus a plain `dict[str, str]` (`file_to_module`) that the *caller*
  (cli-commands) computes. This keeps it same-package.
- `DependencyGraphAdapter` → **move to `packages/cli-commands`** (or a new
  thin package `packages/repo-graph-bridge` if BUILDER judges cli-commands
  is the wrong home — BUILDER's call, document in implementation-notes.md).
  It consumes `ImportEdge` (repo-intelligence, via `__all__`) and produces
  the `DepGraph` protocol shape that `arch-guardrails` (a new "Engineering
  Copilot" layer package) expects. Since it sits in Apps/cli-commands, which
  may import from any lower layer per ADR-015's table, this is compliant.
- The shared `path_to_module()` helper (spec.md, Notes for BUILDER) belongs
  in `cli-commands` alongside `DependencyGraphAdapter`, since both live at
  the orchestration point where file-to-module identity is first computed.

No circular dependencies: `cli-commands` depends on `change-planner` +
`arch-guardrails` + `decision-engine` depends on (nothing further down)
+ `repo-intelligence`/`arch-intelligence` independently. All one-way.

## API Contract Definitions

Unchanged from spec.md Components 1, 2, 5 (same-package adapters — no
cross-boundary contract). Component 3 (`ArchModelAdapter`) contract is
narrowed: constructor drops any parameter requiring repo-intelligence types
directly; `file_to_module` remains a plain `dict[str,str]`, which is a
primitive, not an Intelligence-layer type, so it does not count as a
cross-import.

Component 4 (`DependencyGraphAdapter`) relocates package but keeps its
`get_edges()`/`find_cycles()` interface unchanged.

Component 6 (CLI wiring) unchanged — `cli-commands` is exactly the layer
authorized to call into `change-planner`, `arch-guardrails`,
`decision-engine`, `repo-intelligence`, and `arch-intelligence` together.

## Data Flow Review

```
cli-commands.guardrails(path)
  → repo-intelligence: scan (CallGraphBuilder, ImportGraphBuilder, SymbolExtractor)
  → arch-intelligence: ArchitectureDetector.detect(...) → ArchitectureModel
  → cli-commands: build file_to_module dict (new: path_to_module helper)
  → arch-intelligence: ArchModelAdapter(model, file_to_module)      [same-package]
  → cli-commands: DependencyGraphAdapter(import_edges_by_file, file_to_module)  [relocated]
  → repo-intelligence: CodeMetricsAdapter(file_to_module)            [same-package]
  → arch-guardrails: ArchitectureEnforcer(arch_model_adapter, dep_graph_adapter, metrics_adapter).check_violations()
  → cli-commands: format CliReport
```

Validation happens at the boundary cli-commands controls (path exists,
scan succeeded) before handing data down to the analysis packages — correct
layer for validation per ADR-015 (Apps layer owns orchestration entry
points).

## Risk Flags

- **Security:** Low. No secrets, no network calls. Path traversal risk is
  pre-existing (any `ortho <path>` command can read arbitrary filesystem
  paths the user already has access to) — not new to this task, no
  additional exposure introduced.
- **Scalability:** ⚠ `find_callers` transitive traversal and `find_cycles`
  DFS are both potentially O(V·E) worst case. spec.md already requires a
  <30s real-repo bound test (click/flask/requests) — sufficient guardrail
  for this task's scope. Larger-repo performance is a documented future
  concern, not a blocker.
- **Extensibility:** ✓ Adapter pattern (wrapping protocols) means swapping
  repo-intelligence's internal representation later won't ripple into
  change-planner/arch-guardrails, which only see protocol-shaped objects.
- **Data Integrity:** N/A (read-only analysis, no writes to shared state).
- **Breaking Changes:** None — `commands.py`'s public method signatures
  (`guardrails(path=None)`, `decide(intent, **kwargs)`) are unchanged; only
  internal behavior changes from stub to real.

## ADR References

- **ADR-015 (Layer Boundaries)** — applies directly; corrected placement
  above brings the task into compliance. See ADR-016 below for the gap
  ADR-015 didn't cover.
- No other existing ADRs apply.

## New ADR Required

Yes — see `.ases/architecture/adrs/ADR-016-engineering-copilot-layer.md`,
status PROPOSED. ADR-015 predates Phase 6 and doesn't classify
`change-planner`/`arch-guardrails`/`decision-engine`/`cli-commands`. This
must be ACCEPTED (human approval) before or alongside this task's GATE 2,
since BUILDER's file placement depends on it.

## Verdict

**APPROVED, CONDITIONAL ON SPEC CORRECTION** — Architecture is sound once:
1. `DependencyGraphAdapter` moves from `packages/arch-intelligence` to
   `packages/cli-commands` (or a new bridge package, BUILDER's judgment,
   documented).
2. `ArchModelAdapter`'s constructor is confirmed to take only
   `arch_intelligence` types + a plain `dict[str,str]`, never a
   `repo_intelligence` type directly.
3. ADR-016 (below) is reviewed and accepted by human alongside GATE 2.

spec.md is being corrected now (same session, before BUILDER starts) rather
than sent back to a fresh PLANNER session, since the fix is a placement
correction, not a scope or contract change.
