# Architecture Review — task-019-wire-plan-refactor

**Verdict:** APPROVED

## Layer Compliance (ADR-015 / ADR-016)
`cli-commands` (Apps layer) already imports `arch-guardrails`,
`change-planner`, `decision-engine` (Engineering-Copilot layer, ADR-016)
directly — task-017 established this is a permitted one-way dependency.
This task adds two more same-layer imports: `feature-planner` and
`refactoring-advisor`, both already-existing Engineering-Copilot packages.
Additionally, `refactor_adapter.py` needs `impact-analysis`'s
`DependencyHealthAnalyzer` — checked: `impact-analysis` has zero
Intelligence-layer imports of its own (pure dataclasses + DFS/BFS over
plain lists), so it sits at the same layer as `arch-guardrails`/
`change-planner`. No cycle, no new ADR required.

No Intelligence-to-Intelligence import is introduced: `feature-planner`
only depends on its own `ArchitectureModel` Protocol (structural typing,
satisfied by a new adapter in `cli-commands`, same pattern as
`ArchModelAdapter`). `refactoring-advisor` only depends on its own
`CodeRepository` Protocol, likewise satisfied by a new `cli-commands`
adapter.

## Data Flow
`plan()`: `scan_repository()` -> `FeaturePlannerArchModelAdapter(scan
.arch_model)` -> `FeaturePlanner.plan_feature(intent)` -> render.

`refactor()`: `scan_repository()` -> `CodeRepositoryAdapter(scan)` (which
internally builds `impact_analysis.types.ImportEdge` file-id edges via the
same resolution logic as `_build_layer_import_edges`, then runs
`DependencyHealthAnalyzer.find_cycles()` and `CodeMetricsAdapter`) ->
`RefactoringAdvisor.find_issues()` -> render.

No new persistent state, no I/O beyond the existing `scan_repository()`
file walk.

## Blast Radius
Two new files, two method bodies in `commands.py`. Zero changes to
`guardrails()`/`decide()` or any already-shipped engine package. Matches
rollback-plan.md.

## Design Decision Worth Flagging
`CodeRepositoryAdapter.get_duplications()`/`.get_high_churn_modules()`
returning `[]` unconditionally is an architectural statement, not a bug:
it says "ortho does not yet have a duplication or churn signal," which is
true, and is preferable to synthesizing fake numbers. This should be
revisited as its own future task (churn needs git integration; duplication
needs an AST/token similarity pass) — out of scope here.

## Verdict
APPROVED — no ADR needed, layer rules hold, blast radius is small and
additive, matches task-017's precedent exactly.
