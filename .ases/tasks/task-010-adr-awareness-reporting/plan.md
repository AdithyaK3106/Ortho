---
name: task-010-plan
type: plan
phase: Phase 2, Week 13-14
task_id: task-010-adr-awareness-reporting
---

# Task-010 Plan: ADR Awareness + Reporting

## Feature Summary

Implement the final two Pillar 3 features from the FRD feature table (line 843-854): **ADR awareness**
(cross-reference ADRs against actual code) and **reuse discovery** (find similar code patterns via
AST-level similarity). Wire both into the `ortho analyze` CLI, which today has ADR/reuse commands
undefined and an `--impact` flag that is a stub (loads empty graphs — see
`apps/cli/src/commands/analyze.py:31-34`). This closes Phase 2 per FRD line 1897-1908.

## Scope (In)

1. **ADRTracker** (`packages/arch-intelligence/src/arch_intelligence/adr_tracker.py`)
   - Parse ADRs from `.ases/architecture/adrs/*.md` (status, referenced file/module paths)
   - Cross-reference referenced paths against the current repo tree
   - Flag: ADR references a path that no longer exists (STALE), an ADR with no code references
     found at all (UNLINKED), and code files matching an ADR's declared scope that the ADR text
     never mentions (UNDOCUMENTED) — reported as a hint, not a hard failure
2. **ReuseDetector** (`packages/arch-intelligence/src/arch_intelligence/reuse_detector.py`)
   - AST-level similarity between functions/methods using the existing `Symbol` extraction
     (structural comparison, not text diff — normalize identifiers, compare shape)
   - Report clusters of similar symbols above a caller-configurable similarity threshold
     (0.7 default for Phase 2, see spec.md Component 2) with confidence + evidence
3. **CLI wiring** (`apps/cli/src/commands/analyze.py`, `apps/cli/src/commands/analyze.ts`)
   - `ortho analyze --adr-check` → ADRTracker report
   - `ortho analyze --reuse` → ReuseDetector report
   - Fix `--impact <file>` to load real call/import graphs from `OrthoDatabase` instead of the
     empty-list stub (currently dead code — blocks the FRD Phase 2 exit criterion
     "`ortho analyze --impact src/auth/service.py` lists all affected files")
4. Two ADRs: **ADR-009** (ADR parsing/cross-ref strategy: regex/markdown-section based, not an AST
   of markdown) and **ADR-010** (reuse similarity algorithm: normalized AST tree hash + structural
   diff, no ML/embeddings — stays local-first per FRD principle)

## Scope (Out)

- No embeddings-based semantic reuse detection (sqlite-vec is Pillar 2/ContextHub territory, not
  Pillar 3; would also break local-first-no-ML-dependency precedent)
- No auto-fix of stale ADRs or auto-generation of new ADRs — reporting only, per FRD "Cross-reference
  ADRs against actual code" (read-only analysis)
- No cross-language reuse detection (Python AST only, consistent with current adapter scope)
- No UI/dashboard — text/JSON CLI output only, matching task-009's pattern

## Atomic Tasks

1. **ADRTracker core** (60 min) — parse ADR markdown files, extract status + referenced paths,
   compare against `Path.exists()` on repo tree. Depends on: none.
2. **ADRTracker cross-ref against ArchitectureModel** (45 min) — use task-008's `ArchitectureModel`
   (layers/subsystems) to flag files in detected subsystems with no owning ADR when subsystem has
   >3 files (heuristic, not mandatory). Depends on: Task 1.
3. **ReuseDetector core** (90 min) — structural AST comparison of `Symbol` bodies using existing
   tree-sitter parse (reuse `SymbolExtractor`'s parser setup), similarity scoring, clustering.
   Depends on: none (parallel to Task 1-2).
4. **ReuseDetector confidence + evidence** (45 min) — similarity score, matched-lines evidence,
   dedup near-identical clusters. Depends on: Task 3.
5. **CLI integration + `--impact` fix** (60 min) — wire ADRTracker/ReuseDetector into
   `analyze.py`/`analyze.ts`, replace `--impact` stub with real `OrthoDatabase` graph loads calling
   task-009's `ImpactAnalyzer`. Depends on: Tasks 1-4, task-009's `ImpactAnalyzer` (already merged).

## Risks

| Risk | Mitigation |
|------|------------|
| ADR markdown format has no strict schema (free-form prose sections) | Parse conservatively per the fully-specified ADR Path Extraction Contract in spec.md (File:/Code: lines, markdown links, backtick-quoted path-shaped spans only); false negatives (missed refs) are acceptable, false positives (wrong STALE flags) are not — bias toward under-reporting |
| AST similarity is O(n²) over all symbol pairs — real codebases commonly have symbol counts in the hundreds to low thousands | Bucket by symbol type + rough size (line count) before pairwise compare; document complexity ceiling per the Benchmark Environment policy in spec.md (see "Note on Timing Assertions") rather than a fixed wall-clock number |
| `--impact` stub fix touches code outside this task's new files (existing `AnalyzeCommand.run`) | Scope this as an explicit, minimal deviation — spec.md documents exact before/after diff, no other changes to `AnalyzeCommand` |
| `ImpactAnalyzer`/`Symbol`/`ImportEdge` have no `file_id` field to map symbols back to files (see spec.md Known Gaps) | Document as pre-existing gap inherited from task-002/003/009, not introduced here; work around it using file path as the join key since `OrthoDatabase` stores per-file rows |

## Acceptance Criteria (Binary)

- [ ] `ADRTracker.check_adrs()` classifies every discovered ADR as exactly one of
      OK / STALE / UNLINKED / UNKNOWN, for any directory of ADR markdown files (zero or more)
- [ ] `ADRTracker.check_adrs()` is deterministic: identical ADR directory contents always produce
      identical `ADRStatus` results, in stable sorted order, across repeat runs
- [ ] `ReuseDetector.find_similar()` returns a `ReuseCluster` for every pair (or group) of symbols
      whose structural similarity meets or exceeds the configured threshold, whenever such
      qualifying symbols exist in the input; returns `[]` when none qualify
- [ ] `ReuseDetector.find_similar()` is deterministic and symmetric: identical symbol/source input
      always produces identical clusters, and similarity(a, b) == similarity(b, a)
- [ ] `ortho analyze --adr-check` and `ortho analyze --reuse` produce a valid, well-formed report
      (text or JSON per `--format`) for any repository, including one with zero ADRs or zero
      reusable code — an empty result set is valid, a crash or malformed output is not
- [ ] `ortho analyze --impact <file>` returns graph-derived `ImpactReport` data (direct/transitive
      dependents computed from real call/import graphs) whenever the target repository has been
      indexed and dependency data exists for the file — replacing the current behavior of always
      returning an empty report regardless of input
- [ ] Zero regressions: full `pytest` suite (all packages) passes at the same rate as before this task

See **Validation Baseline** in spec.md for the specific repository/values used to observe this
behavior during development; those observations are informational, not part of this criteria list.

## Dependencies

- task-008 (ArchitectureModel, Layer, Subsystem) — MERGED, available
- task-009 (ImpactAnalyzer, DebtScorer, DependencyHealthAnalyzer) — MERGED, available
- Existing `SymbolExtractor` (tree-sitter parser setup) — reused, not modified

*Plan created by PLANNER, 2026-07-02*
*Awaiting GATE 1 approval*
