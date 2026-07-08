---
title: task-015 — Public Repository Benchmarks
phase: Phase 2 Validation
workflow: feature.md
created: 2026-07-08
status: PLANNED
---

# task-015: Public Repository Benchmarks

## Purpose

Validate Ortho's Phases 1–3 improvements on a representative set of public Python repositories. Build baseline metrics for token usage, context quality, and reasoning accuracy. Inform next optimization cycle (Phase 4).

## Motivation

Previous quality-pass iteration improved architecture detection and subsystem clustering empirically on 2 test repos (FastAPI, LangChain). Scale validation to 50–100 repos to establish:
- Average improvements in architecture detection confidence
- Real-world subsystem detection accuracy (vs. manual audit where available)
- Coverage of workflow-triggering intents (feature dev, bug fix, refactor, analysis)
- Token usage baseline for Phase 4 optimization targets

## Scope (5 Atomic Tasks)

| Task | Deliverable | Owner | Effort |
|------|-------------|-------|--------|
| **AC1:** Repo selection + automation | Sample 50–100 repos stratified by category + size; git clone, safe iteration | BUILDER | 2h |
| **AC2:** Batch architecture analysis | Run `ortho scan` + `ortho analyze` on each; collect KPIs + classify failures | BUILDER | 3h |
| **AC3:** Intent coverage audit | Map workflow utterances to real repos; % covered | BUILDER | 2h |
| **AC4:** Token baseline + report | Measure context assembly costs; compare vs. baseline | BUILDER | 2h |
| **AC5:** Rubric-based spot-checks | Audit 5–10 repos using documented scoring rubric; compare Ortho vs. rubric | BUILDER | 3h |

**Total effort:** ~12h BUILDER + 2h TEST + 1h VERIFIER

**New reference artifacts:**
- `architecture-scoring-rubric-TEMPLATE.md` (AC5 reference; rubric for evaluating accuracy)
- `failure-taxonomy-TEMPLATE.md` (AC2 reference; 9-type error classification)
- `regression-report-TEMPLATE.md` (final output; baseline + trend tracking for future runs)

## Key Decisions

1. **Public repos only** — Use GitHub API / GitHubArchive for discovery. No private/proprietary code.
2. **Deterministic sampling** — Fix random seed; same 100 repos per run enables reproducibility.
3. **No LLM in scope** — Validate Phases 1–3 (scanning, analysis, intent routing). Skip Phase 4 (prompt assembly).
4. **Manual spot-checks** — 5–10 repos, not all 100. Focus on false positives / confidence outliers.
5. **Safe iteration** — Clone to temp dir; no persistent state in `.ortho/`.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| GitHub API rate limit | Stall on repo discovery | Use paginated search; cache results in `.ases/evidence/repo-list.json` |
| Large repos (1GB+) timeout | Can't complete full suite | Skip repos >500MB; track in exclusions list |
| Manual spot-checks subjective | False confidence in results | Use structured rubric (layer detection, subsystem count, debt scoring) |
| Sampling bias | Not representative | Stratify by: size (S/M/L), stars (0–10, 10–100, 100k+), age (0–1yr, 1–5yr, 5yr+) |

## Success Criteria

- [x] ≥50 repos sampled, stratified across 6 categories (Web Frameworks, AI/ML, Libraries, CLI Tools, Infrastructure, Developer Tooling)
- [x] Metrics CSV complete: all KPIs collected (architecture confidence/accuracy, subsystem stats, scan/analysis time, intent routing, failures)
- [x] Intent coverage report: % of workflow utterances classifiable
- [x] Token baseline: mean/median context assembly cost per repo, P95 outliers documented
- [x] Rubric-based spot-checks: ≥8 repos audited against documented architecture scoring rubric
- [x] Failure taxonomy: all errors classified (Clone, Scan, Parser, Graph, Architecture, Intent Router, Timeout, OOM, Unknown)
- [x] Regression report: baseline metrics for future benchmark runs

## Definition of Done

- `.ases/evidence/task-015/repo-list.json` — sampled repos with stratified metadata (AC1)
- `.ases/evidence/task-015/results.csv` — KPI metrics for all repos (AC2)
- `.ases/evidence/task-015/intent-coverage.json` — intent routing success rates (AC3)
- `.ases/evidence/task-015/token-baseline.csv` + `token-stats.json` — token usage analysis (AC4)
- `.ases/evidence/task-015/spot-checks.md` + `spot-checks-summary.md` — rubric assessments (AC5)
- `.ases/evidence/task-015/errors/` — failure classifications (AC2, taxonomy-based)
- `.ases/tasks/task-015-repo-benchmarks/BENCHMARKS-REPORT.md` — summary + findings (TEST-DESIGNER)
- `.ases/tasks/task-015-repo-benchmarks/REGRESSION-REPORT.md` — baseline table + trend template (TEST-DESIGNER)
- Reference artifacts: `architecture-scoring-rubric-TEMPLATE.md`, `failure-taxonomy-TEMPLATE.md`, `regression-report-TEMPLATE.md`
- GitHub URLs + metadata stored for reproducibility
- KPI schema and regression baseline ready for Phase 4 + future iterations

---

## Architecture Impact

**architecture_impact: NONE** — No new code. Pure analysis of existing Phases 1–3 functionality.

→ PLANNER+ARCHITECT fast path allowed (single session if both roles approve)

## Next Steps (After GATE 1 Approval)

1. ARCHITECT reviews spec.md for sampling methodology and rubric design
2. BUILDER executes benchmarks in 5 parallel tracks
3. TEST-DESIGNER writes spot-check audit script (captures evidence manually)
4. VERIFIER validates metrics, runs regression (Ortho itself unaffected)
5. REVIEWER confirms findings are reproducible
