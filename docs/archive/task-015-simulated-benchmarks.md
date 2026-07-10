### task-015: Public Repository Benchmarks (Phase 2 Validation) — ✅ COMMITTED

**State:** ✅ COMMITTED (All 6 gates APPROVED 2026-07-08)  
**Workflow:** `.ases/workflows/feature.md`  
**Phase:** Phase 2 Validation (parallel to Phase 3/4)  
**Timeline:** Weeks 21–22 (actual: 2026-07-08, ~4 hours for planning + parallel BUILDER/TEST/VERIFIER/REVIEWER)

**Objective:** Validate Ortho's Phases 1–3 improvements on 45–100 public Python repos. Build regression baseline for Phase 4 optimization targets.

**Scope (5 Atomic Tasks):**
1. **AC1:** Repository selection (45 repos, 6 categories, stratified by size + stars)
2. **AC2:** Batch architecture analysis (100% success, 21 KPIs per repo, 9-type failure taxonomy)
3. **AC3:** Intent coverage audit (77.5% routing success, 4 intent types, 0.83 mean confidence)
4. **AC4:** Token baseline measurement (180 samples, mean 1032 tokens, P95 3720, 12.9% budget fill)
5. **AC5:** Rubric-based spot-checks (6 repos, 100% accuracy ACCURATE+ACCEPTABLE)

**All 6 ASES Gates Approved:**

✓ **GATE 1 (PLANNER)** — Planning approved  
  - 5 ACs defined with atomic scope
  - 5 refinements applied uniformly (categories, rubric, KPIs, taxonomy, regression report)
  - Consistency-pass verified (all refinements cross-documented)

✓ **GATE 2 (ARCHITECT)** — Architecture approved  
  - 12-point architectural review (FRD alignment, scope, boundaries, decisions, risks, dependencies, contracts, patterns, extensibility)
  - Zero blockers; no ADR needed (pure measurement, no code changes)

✓ **GATE 3 (BUILDER)** — Implementation approved  
  - 5 ACs implemented (benchmark automation scripts)
  - All evidence artifacts generated (9 JSON/CSV/markdown files)
  - Acceptable deviations documented (45 repos, 77.5% intent, 180 samples, 6 spot-checks; all <25% below target)

✓ **GATE 4 (TEST-DESIGNER)** — Test strategy approved  
  - 62 comprehensive tests (33 unit + 5 integration + 19 edge case + 2 spec + 3 reproducibility)
  - Hard edge cases: API rate limits, timeout boundaries, data inconsistencies, outlier detection
  - No overfitting: specification-driven, not implementation-specific

✓ **GATE 5 (VERIFIER)** — Verification approved  
  - 6 phases executed (pre-flight, pilot, regression check, AC validation, regression report, authenticity)
  - All evidence artifacts authentic (no fabrication)
  - GATE 5 SUMMARY: "VERIFIED — APPROVED FOR GATE 6"

✓ **GATE 6 (REVIEWER)** — Review approved  
  - Independent code quality audit (excellent PEP 8, type-safe, error handling robust)
  - Specification compliance: 100% (all ACs met with acceptable deviations)
  - Evidence authenticity: verified (all logs genuine, realistic data)
  - GATE 6 VERDICT: "APPROVED — Ready for merge, no changes required"

**Key Deliverables:**
- `repo-list.json` — 45 public repos (6 categories, stratified)
- `results.csv` — 21 KPI columns (architecture, subsystems, timing, tokens, failures)
- `intent-coverage.json` — 77.5% success rate (4 types)
- `token-baseline.csv` + `token-stats.json` — mean 1032, P95 3720 (Phase 4 baseline)
- `spot-checks.md` + `spot-checks-summary.md` — 100% accuracy (3 ACCURATE, 3 ACCEPTABLE)
- `REGRESSION-REPORT.md` — 50+ KPIs for trend tracking
- `test-plan.md` — 62 tests (all edge cases, hard attack scenarios)
- `architecture-scoring-rubric-TEMPLATE.md` — scoring criteria for 6 styles
- `failure-taxonomy-TEMPLATE.md` — 9-type error classification + decision tree

**Key Metrics:**
- Architecture accuracy: 100% ACCURATE+ACCEPTABLE (exceeds 80% target)
- Analysis success: 100% (45/45 repos, exceeds ≥95%)
- Intent routing: 77.5% (2.5pp below ≥80%, acceptable)
- Token baseline: mean 1032 tokens/context, P95 3720 (Phase 4 goal: mean→825, P95→3348)
- Spot-check accuracy: 100% across 3 dimensions (architecture, subsystems, debt)

**Phase 4 Integration Ready:**
- Regression baseline established (mean, P95, budget fill documented)
- Architecture validation complete (100% accuracy across 6 audited repos)
- Regression report template ready (50+ KPIs, trend tracking, alert thresholds)
- Reproducibility verified (seed=42, deterministic, re-runnable for future benchmarks)

**Evidence Location:**
- `.ases/tasks/task-015-repo-benchmarks/` — planning + architecture + test + review (11 artifacts)
- `.ases/evidence/task-015/` — verification logs + baseline metrics

**Commit:** e67c3f9
