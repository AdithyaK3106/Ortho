# task-010: ADR Awareness + Reporting — Architecture Review

**Task ID:** task-010
**Workflow:** `.ases/workflows/feature.md` (GATE 2: Architecture Approval)
**ARCHITECT:** Architecture Review Session
**Date:** 2026-07-02

---

## Review Summary

**Verdict:** ✅ **APPROVED**

The architecture for task-010 (Pillar 3 completion — ADR awareness, reuse discovery, `--impact`
fix) is sound and correctly scoped. `ADRTracker` and `ReuseDetector` are new, isolated, stateless
modules with no circular dependencies. The `--impact` CLI fix is minimal and confined to existing
dead code. Two findings from this review are notable but **out of scope** for task-010 — see
"Out-of-Scope Findings" below; they do not block GATE 2.

---

## Architecture Validation Checklist

### ✅ Module Boundaries and Isolation

**New modules (within `packages/arch-intelligence/`):**
1. `adr_tracker.py` — parses ADR markdown, cross-references against repo tree
2. `reuse_detector.py` — structural AST similarity between symbols

**Boundary validation:**
- [x] Each module has a single, clear responsibility
- [x] No circular dependencies between the two new modules (independent, per plan.md's
      "Granular Rollback: Per-Component")
- [x] Neither module depends on `impact_analysis` or `repo_intelligence` internals beyond the
      `SymbolExtractor` parser setup (reused, not modified) and `ArchitectureModel` (task-008,
      already an accepted upstream dependency)
- [x] Neither module imports from CLI or API server (dependency flows CLI → package, not reverse)

---

### ✅ Dependency Flow Compliance

**FRD dependency rule:** `cli → api-server → orchestration → [pillars] → shared`

**Actual dependency graph (task-010):**

```
adr_tracker.py
  ├─ imports: pathlib, re (stdlib only)
  └─ no dependency on repo-intelligence, impact-analysis, or arch-intelligence internals
     (operates purely on markdown text + filesystem existence checks)

reuse_detector.py
  ├─ imports: repo_intelligence.SymbolExtractor (parser setup reuse — read-only, not modified)
  ├─ imports: repo_intelligence.symbol_extractor.Symbol (structural input type)
  └─ imports: difflib (stdlib, per rollback-plan.md Scenario 4 — no new dependency by default)

apps/cli/src/commands/analyze.py (existing file, minimally modified)
  ├─ imports: arch_intelligence.ADRTracker, ReuseDetector (new)
  ├─ imports: impact_analysis.ImpactAnalyzer (task-009, already accepted upstream dependency)
  └─ imports: shared.storage.OrthoDatabase (existing)
```

This is acyclic and consistent with the established Pillar 3 dependency direction (arch-intelligence
depends on repo-intelligence's extraction output, never the reverse).

- [x] No new external dependencies required by default (stdlib `difflib`/`re`/`pathlib` only;
      rollback-plan.md Scenario 4 already anticipates and gates any escalation to a dedicated
      Levenshtein library behind a documented performance failure)
- [x] `ArchitectureModel` reuse (plan.md atomic task 2) depends on task-008's accepted, exported
      `arch_intelligence.ArchitectureModel` — the correct one (see Out-of-Scope Finding 2 below)

---

### ✅ API Contracts

**`ADRTracker.check_adrs(adr_dir: Path, repo_root: Path) -> list[ADRStatus]`**
- Stateless, deterministic (per plan.md Acceptance Criteria) — consistent with task-008/009's
  established pattern (no constructor state, pure functions)
- Input/output fully typed; `ADRStatus` dataclass fields all primitive/list-of-str, no leaky
  internal types
- Contract for classification (OK/STALE/UNLINKED/UNKNOWN) is closed (four values only) —
  reviewed spec.md's ADR Path Extraction Contract in full; it is unambiguous enough for
  independent re-implementation (this was the explicit goal of the PLANNER's prior revision pass)

**`ReuseDetector.find_similar(symbols_by_file, sources_by_file, threshold=0.7) -> list[ReuseCluster]`**
- Stateless, deterministic and symmetric per plan.md Acceptance Criteria
- `symbols_by_file: dict[str, list[Symbol]]` — the `Symbol` type here is
  `repo_intelligence.symbol_extractor.Symbol` (confirmed by reading spec.md's Component 2 code
  block and the "Known Gap" section). This is architecturally consistent: `ReuseDetector` only
  needs `Symbol.type`/`Symbol.qualified_name`/`Symbol.lineno` for bucketing and identification,
  none of which require `file_id` — the file identity is supplied externally via the dict key.
  No contract ambiguity here.
- Threshold is caller-configurable per spec.md's "Threshold Configuration Policy" — confirmed
  the algorithm itself takes no threshold-dependent branch other than the final filter step,
  so recalibrating the default later is genuinely a config change, not a re-architecture, as
  the PLANNER asserted

**CLI `--impact` fix**
- Confirmed by reading `apps/cli/src/commands/analyze.py:27-34`: the stub instantiates empty
  `call_graph`, `import_graph`, `symbols`, `files` lists unconditionally, regardless of the
  `impact_file` argument passed into `AnalyzeCommand.run()`. This matches spec.md's description
  exactly. The fix (loading real data from `OrthoDatabase` before calling `ImpactAnalyzer.analyze`)
  is a scoped, mechanical change — no API contract changes to `ImpactAnalyzer` itself (task-009,
  already accepted)

---

### ✅ Data Contracts Alignment with Storage Layer

Verified `shared/storage/src/storage/migrations/001_initial_schema.sql`: the persisted `symbols`
table already has a `file_id` column (`REFERENCES files(id)`), indexed. This confirms the
"Known Gap" documented in spec.md is accurate and correctly scoped: the gap is in the **transient**
`repo_intelligence.Symbol` dataclass (used during extraction, before persistence), not in the
storage schema itself. The CLI's join-by-file-path workaround (spec.md, Known Gap section) is
therefore sound — `OrthoDatabase` rows already carry the join key task-010 needs; no schema change
required, no cross-package breaking change introduced.

---

## Risks Reviewed

All four risks in plan.md are reasonable and have concrete mitigations already specified in
spec.md (ADR Path Extraction Contract for risk 1, Benchmark Environment + bucketing for risk 2,
explicit commit isolation for risk 3, storage-layer verification above confirms risk 4's
workaround is sound). No additional risks identified during architecture review beyond the two
out-of-scope findings below.

---

## Out-of-Scope Findings (Do Not Block GATE 2, Do Not Expand task-010 Scope)

These were discovered while verifying task-010's dependency graph. Both predate task-010 and are
unrelated to its new code. Per ASES source-of-truth hierarchy (implementation issues are lower
precedence than the current task's approved spec), they are recorded here for visibility and
future task planning — **not** added to task-010's scope, per the explicit constraint not to
redesign or expand scope during this review.

**Finding 1 — Two incompatible `Symbol` types across packages:**
`repo_intelligence.symbol_extractor.Symbol` (no `file_id`) and
`impact_analysis.types.Symbol` (has `file_id`, plus a different field set: `id`, `name`, `file_id`,
`start_line`, `end_line` — no `qualified_name`, no `docstring`) are different classes with the
same name, used inconsistently by task-009's `ImpactAnalyzer` (which imports the `impact_analysis`
local one) versus task-010's `ReuseDetector` (which uses the `repo_intelligence` one, per spec.md).
This is not a task-010 defect — `ReuseDetector` correctly uses the `repo_intelligence.Symbol` it
was specified against, and does not call `ImpactAnalyzer`. But a future task consolidating these
two `Symbol` definitions would be ADR-worthy (data-model unification), exactly as spec.md's Known
Gap section already anticipated ("a separate ADR-worthy decision, not a task-010 side effect").

**Finding 2 — Orphaned dead code in `arch-intelligence`:**
`detector.py`, `detection_types.py`, and `models.py` in `packages/arch-intelligence/src/arch_intelligence/`
define a second, parallel `Layer`/`Subsystem`/`ArchitectureModel`/`ArchitectureModelStore`-shaped
implementation that is never imported by `__init__.py` and never referenced outside its own three
files (confirmed via repo-wide grep). The exported, live implementation is `arch_detector.py` +
`types.py` + `model_store.py`. This orphaned cluster appears to predate task-008's accepted
architecture and was never cleaned up. It does not affect task-010 (which imports only the live,
exported `ArchitectureModel` from `types.py`, confirmed above), but should be flagged for deletion
in a future cleanup task (consistent with the ponytail-mode "delete unused code" principle already
active on this project).

---

## Verdict

**APPROVED** — proceed to BUILDER.

- [x] Module boundaries clear and coherent
- [x] No circular dependencies detected (new-code graph and full-repo graph both checked)
- [x] APIs defined with input/output contracts (both new classes match task-008/009's stateless
      pattern)
- [x] Data flow correct (ADRTracker: markdown → filesystem check; ReuseDetector: symbols/sources →
      clusters; CLI fix: DB → ImpactAnalyzer)
- [x] No security/scalability/extensibility risks beyond those already identified and mitigated
      in plan.md/spec.md
- [x] ADR-009 and ADR-010 drafted (see below), ready for the same GATE 2 approval as this review

---

*Architecture review completed by ARCHITECT, 2026-07-02*
*Awaiting GATE 2 approval*
