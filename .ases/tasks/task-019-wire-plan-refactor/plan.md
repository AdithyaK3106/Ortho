# Plan — task-019-wire-plan-refactor

## Goal
Wire `CliCommands.plan()` and `CliCommands.refactor()` to the real
`feature-planner` and `refactoring-advisor` engines, replacing the current
100%-hardcoded stub output, following the same real-scan-and-adapt pattern
established in task-017 for `guardrails()`/`decide()`.

## Current State
- `plan(intent)` returns a fixed 3-line string regardless of `intent`.
- `refactor(path)` returns a fixed 2-line string regardless of `path`.
- Both engines they should call already exist and are fully tested in
  isolation (`feature-planner`: 
  `FeaturePlanner(arch_model).plan_feature(intent) -> FeaturePlan`;
  `refactoring-advisor`: `RefactoringAdvisor(repo).find_issues() ->
  list[RefactoringIssue]`) but have zero real callers — same situation
  `arch-guardrails`/`change-planner` were in before task-017.

## Scope

### plan()
- Adapt `ArchModelAdapter`'s already-scanned `arch_model` to satisfy
  `feature_planner.planner.ArchitectureModel` Protocol (`get_style() ->
  str`). Real data: `scan.arch_model.style` (an `ArchStyle` enum, currently
  always `ArchStyle.UNKNOWN` since no style detector is wired into
  `scan_repository` yet — this is an honest gap, not something task-019
  fabricates a value for).
- Call `FeaturePlanner(adapter).plan_feature(intent)`, render `FeaturePlan`
  (paths, effort/risk/rationale per path) as CLI text.
- Reject empty intent immediately (`success=False`), mirroring `decide()`.

### refactor()
- Adapt real scan data to satisfy `refactoring_advisor.advisor.CodeRepository`
  Protocol (5 methods). Real signal exists for 3 of 5:
  - `get_tight_couplings()` / `get_circular_deps()`: derive from
    `DependencyHealthAnalyzer.find_cycles()` (already built in
    `impact-analysis`, currently zero real callers) over import edges
    resolved to file-ids (reusing `repo_scanner._build_layer_import_edges`'s
    resolution approach — module-name edges have no file-id in
    `repo_intelligence.import_graph.ImportEdge`, but `impact_analysis.types
    .ImportEdge` needs file-ids, so a resolution step is required). 2-node
    cycles -> tight coupling; length > 2 -> circular dependency.
  - `get_bloated_modules()`: real, from `CodeMetricsAdapter.get_module_lines`
    / `get_module_functions()` (already built, task-017, zero real callers
    in refactor path) over every module in the scanned repo, threshold
    lines > 300 or functions > 20 (chosen to surface real bloat in
    repos/click's largest modules during verification, documented in
    architecture-review.md).
  - `get_duplications()` / `get_high_churn_modules()`: **no real signal
    source exists in this codebase** (no code-similarity detector, no git
    history integration wired into cli-commands). Return `[]` for both.
    This is a deliberate, documented gap — NOT faked data — same category
    as task-017's "plan()/refactor() are fake stubs" flag in
    `docs/mcp-server-contract.md`.
- Call `RefactoringAdvisor(repo).find_issues()`, render
  `list[RefactoringIssue]` as CLI text (type, location, severity,
  recommendation, effort, confidence).
- Reject nonexistent path immediately (`success=False`), mirroring
  `guardrails()`'s `FileNotFoundError` handling.

## Out of Scope
- Building a code-similarity detector for duplications.
- Building git-history churn analysis.
- Building an architecture-style detector (layered/microservices
  classification) — `ArchStyle.UNKNOWN` is accepted as real, honest input.
- ContextHub memory capture (task-020, explicitly ordered after this task).

## Acceptance Criteria
1. `plan(intent)` returns a `FeaturePlan`-derived report with >=3 distinct
   paths, varying by `intent`'s classified feature type.
2. `plan("")` returns `success=False` without calling the scan/engine.
3. `refactor(path)` returns real bloat + real cycle findings for an actual
   scanned repo (verified against `repos/click`), with zero duplications/
   churn items (both empty, not fabricated).
4. `refactor("/nonexistent")` returns `success=False`.
5. Existing `guardrails()`/`decide()` behavior is byte-for-byte unchanged
   (regression guard).
6. mypy --strict introduces zero new errors.
7. Real-repo verification test against `repos/click` for both commands
   (anti-overfitting: assertions on bounded/structural properties, not
   exact hardcoded output).
