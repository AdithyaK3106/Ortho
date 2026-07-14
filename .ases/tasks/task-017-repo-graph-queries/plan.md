# Plan: task-017-repo-graph-queries

**Phase:** 7.1
**Owner:** Solo Developer
**Created:** 2026-07-14

## Feature Summary

`ortho guardrails` and `ortho decide` currently return hardcoded stub strings
(`packages/cli-commands/src/cli_commands/commands.py`) — they never call the
real `ArchitectureEnforcer`, `ChangePredictor`, or `DecisionEngine` classes
that already exist and are tested. Those engines depend on six query methods
(`find_callers`, `find_importers`, `symbols_in_file`, `get_layers`,
`get_layer_for_module`, `get_modules`, `get_edges`, `find_cycles`,
`get_module_lines`, `get_module_functions`) that do not exist anywhere in
`repo-intelligence` or `arch-intelligence` — those packages only expose flat
edge lists (`CallEdge`, `ImportEdge`) and plain dataclasses
(`ArchitectureModel`, `Layer`).

This task builds the missing query layer as real graph logic over real
edge-list output, then wires `cli-commands` to use it. No overfitting: query
methods must be validated against real cloned repos in `repos/` (click,
flask, requests), not synthetic fixtures shaped to make assertions pass.

## Why

Per the vNext strategy (Ortho vNext memory), Review is the pilot wedge.
`ortho guardrails` is the review command. Right now it is vaporware — running
it teaches a pilot user nothing about their code. This is the highest-value
gap between "current Ortho" and "something a pilot could use."

## Atomic Tasks

1. **Build `RepoGraphQueries` adapter** (`packages/repo-intelligence`) —
   wraps `CallGraphBuilder`/`ImportGraphBuilder` output into queryable
   objects satisfying `change_planner.predictor.CallGraph` and `ImportGraph`
   protocols. ~60-90 min.
2. **Build `SymbolIndex` adapter** (`packages/repo-intelligence`) — wraps
   `SymbolExtractor` output to satisfy `SymbolRegistry` protocol
   (`symbols_in_file`). ~30 min.
3. **Build `ArchModelAdapter`** (`packages/arch-intelligence`) — wraps
   `ArchitectureModel`/`Layer` dataclasses to satisfy `change_planner`'s
   `ArchitectureModel` protocol (`get_layer`) and `arch_guardrails`'s
   `ArchModel` protocol (`get_layers`, `get_layer_for_module`,
   `get_modules`). ~45 min.
4. **Build `DependencyGraphAdapter`** (`packages/arch-intelligence`) —
   builds an internal (not external-package) dependency graph from
   `ImportEdge` data resolved to real file paths, exposes `get_edges`,
   `find_cycles` (Tarjan/DFS-based, returns actual cycle lists — not the
   existing private `_dag_shape` depth/ratio heuristic). Satisfies
   `arch_guardrails.enforcer.DepGraph` protocol. ~90 min.
5. **Build `CodeMetricsAdapter`** (`packages/repo-intelligence`) — computes
   real line counts and function counts per module from source files.
   Satisfies `arch_guardrails.enforcer.CodeMetrics` protocol. ~30 min.
6. **Wire `cli_commands.commands.guardrails()`** — replace stub with real
   scan → adapters → `ArchitectureEnforcer.check_violations()` → formatted
   `CliReport`. ~45 min.
7. **Wire `cli_commands.commands.decide()`** — replace stub with real
   scan → adapters → `ChangePredictor.predict_impact()` +
   `ArchitectureEnforcer.check_violations()` → `DecisionEngine.decide()` →
   formatted `CliReport`. ~45 min.

`plan()` and `refactor()` stubs are explicitly OUT OF SCOPE (feature-planner
and refactoring-advisor wiring is a separate future task).

## Dependencies

None (no other in-flight task touches these files).

## Risks

| Risk | Mitigation |
|---|---|
| `ImportEdge.source_module` is always `"<current>"` (not real file identity) | DependencyGraphAdapter must resolve source identity from which file was scanned, not trust the edge field — documented explicitly in spec.md |
| Cycle detection reimplementing existing `_dag_shape` heuristic differently could produce inconsistent architecture signals | New `find_cycles` is scoped to `arch-guardrails` use only; does not replace or alter `arch_detector.py`'s existing heuristic |
| Real-repo scans (click/flask/requests) may be slow or reveal parsing edge cases (syntax errors in vendored code, huge files) | TEST-DESIGNER instructed to test against real repos in `repos/`; BUILDER must handle file-read/parse errors gracefully (skip + continue, not crash) |
| Scope creep into `plan()`/`refactor()` stubs | Explicitly forbidden in spec.md `files_forbid` |

## Acceptance Criteria (binary, testable)

- `ortho guardrails <path>` on a real cloned repo (e.g. `repos/click`)
  returns real `GuardrailViolation` objects derived from actual scanned
  code, not the hardcoded string `"No violations found!"`.
- `ortho decide <intent>` on a real file path returns a real `Decision`
  aggregating real `ImpactPrediction` and `GuardrailViolation` data.
- All 6 query methods pass their own unit + property + real-repo tests.
- No regression in existing 303 passing tests.

## Rollback Trigger

If wiring introduces a crash on any of the 3 fixture repos, or query layer
cannot achieve `mypy --strict` compliance within scope, roll back to stub
implementation (git revert) and re-scope as smaller sub-tasks.
