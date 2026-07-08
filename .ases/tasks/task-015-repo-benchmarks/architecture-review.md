---
title: task-015 Architecture Review
task: Public Repository Benchmarks
workflow: feature.md
phase: GATE 2 — ARCHITECT Approval
created: 2026-07-08
reviewer: ARCHITECT
verdict: APPROVED
---

# Architecture Review — task-015

**Verdict: ✅ APPROVED**

This review confirms that task-015's plan and specification are architecturally sound, aligned with the FRD, risk-aware, and ready for implementation.

---

## 1. Alignment with FRD & Mission

### FRD Compliance ✓

**FRD Section 10 (Pillar 5 — Token Optimizer):**
- Pillar 5 features include: "Intent-aware reranker, Duplicate remover, Graph expander, Token budget manager, Context compressor, Architecture-aware retrieval, Model context adapter, Prompt assembler, Context quality logger"
- FRD explicitly states: "Even though the full optimizer isn't built until Phase 4, define this interface during Phase 1" (token budget interface — task-014 ✓)

**task-015 Role:**
- task-014 implemented token budget foundation (COMMITTED)
- task-015 establishes the baseline for Phase 4 optimization targets
- Validates Phases 1–3 empirically (architecture detection, subsystem clustering, intent routing)
- FRD Section 16 (Phase 2 exit criteria): "architecture style detected with confidence score" — task-015 AC5 validates this ✓

**Mission Alignment:**
- Ortho mission: "Deliver engineering intelligence around LLMs by understanding repositories deeply"
- task-015 validates Phase 2 reasoning (architecture detection, impact analysis, intent routing) on real-world repos
- Prepares data-driven targets for Phase 4 optimization (20% token reduction goal)

### Phase Positioning ✓

- **Phase 1 (Weeks 1–8):** Foundation complete (tasks 1–5 + quality-pass)
- **Phase 2 (Weeks 9–14):** Reasoning complete (tasks 6–10, architecture + impact + ADRs)
- **Phase 3 (Weeks 15–22):** Execution complete (tasks 11–14, intent routing + orchestration + token budget)
- **task-015:** Phase 2/3 validation (non-blocking, runs parallel to Phase 4 prep)
- **Phase 4 (Weeks 23–28):** Optimization (token optimizer advanced features, uses task-015 baseline)

**Rationale:** task-015 validates that Phase 1–3 improvements (from quality-pass on 2 repos) scale to 50–100 repos. If they don't, Phase 4 optimization has the wrong target. If they do, Phase 4 has a reliable baseline.

---

## 2. Scope & Boundaries

### Scope ✓ (Pure Analysis, No Code)

**What task-015 Does NOT Do:**
- ❌ Write new Ortho code
- ❌ Modify production modules (repo-intelligence, orchestration, token-optimizer)
- ❌ Change architecture detection algorithms
- ❌ Add new features to any pillar
- ❌ Integrate LLM or prompt assembly

**What task-015 Does:**
- ✅ Runs existing Ortho pipeline on 50–100 public repos
- ✅ Collects metrics (confidence, accuracy, performance, tokens, failures)
- ✅ Classifies errors using fixed taxonomy (diagnosis only, no fixes)
- ✅ Validates predictions against rubric (manual judgment, no code changes)
- ✅ Establishes baseline for regression tracking (comparison tool, not optimization)

**Architecture Impact:** NONE — no module changes, no dependencies added, no new packages.

→ Boundary is clean: task-015 is a **measurement system**, not a feature system.

### 5 Acceptance Criteria (Clear Atomic Scope) ✓

| AC | Scope | Dependencies | Owner | Effort |
|----|-------|-------------|-------|--------|
| AC1 | Repo sampling + stratification | GitHub API, git | BUILDER | 2h |
| AC2 | Batch analysis + KPI collection | Existing `ortho scan/analyze` | BUILDER | 3h |
| AC3 | Intent routing validation | Existing IntentRouter (task-012) | BUILDER | 2h |
| AC4 | Token baseline measurement | Existing `assemble_context()` (task-014) | BUILDER | 2h |
| AC5 | Rubric-based manual audit | Human judgment + rubric (provided) | BUILDER | 3h |

**No AC depends on Phase 4 optimization code.** All ACs use existing Phase 1–3 modules (repo-intelligence, orchestration, token-optimizer foundation).

**Total effort: ~12h BUILDER** — consistent with plan.

---

## 3. Architecture Decisions

### Decision 1: 6 Repository Categories ✓

**Rationale:**
- GitHub search filters alone don't guarantee representative sampling
- Categories (Web, AI/ML, Libraries, CLI, Infrastructure, Tooling) cover real Ortho use cases
- Stratification prevents bias toward popular repos (FastAPI, TensorFlow dominate stars but aren't the only targets)

**Trade-off:**
- Pro: Representative sample, transparent inclusion criteria
- Con: Requires manual category assignment (BUILDER defines search queries per category)

**Mitigations:**
- Documented queries per category (spec.md AC1)
- Stratification within categories (by size + stars)
- Exclusions tracked (spec.md AC1: repos.json + exclusions.json)

**Verdict:** Sound decision. Categories are well-chosen for Ortho's mission (repo understanding).

---

### Decision 2: Deterministic Sampling (random.seed=42) ✓

**Rationale:**
- Same seed → same 100 repos on each run (reproducibility)
- Enables regression tracking (future runs compare against baseline)
- Allows audit trail (if someone suspects sampling bias, re-run proves it's deterministic)

**Trade-off:**
- Pro: Reproducible, trackable, enables trend analysis
- Con: One-time snapshot (doesn't capture repos added to GitHub after sampling date)

**Mitigation:** Regression report template (regression-report-TEMPLATE.md) documents sampling date, commit, seed — allows future team to interpret baseline in context.

**Verdict:** Sound. Reproducibility is critical for benchmarking.

---

### Decision 3: Rubric-Based Accuracy Evaluation (Not ML/Embeddings) ✓

**Rationale:**
- Task-015 is validation, not optimization → objective criteria preferred
- Rubric documents scoring rules explicitly (layering structure, dependency direction, cohesion — measurable)
- Avoids false precision: "I think this is layered @ 0.92" vs. "Criteria A, B, C met; confidence 0.9 expected"

**Trade-off:**
- Pro: Objective, auditable, no ML infrastructure needed
- Con: 5–10 manual spot-checks (not 100 repos), inherent sampling bias

**Mitigation:**
- Spot-checks stratified by size + category (spec.md AC5)
- Rubric applied consistently across all repos (single evaluator, reference document)
- Accuracy = rubric-predicted vs. Ortho-detected (documented in spot-checks.md)

**Verdict:** Sound. Rubric trades speed for objectivity; 5–10 repos sufficient for validation (not training).

---

### Decision 4: 9-Type Failure Taxonomy (Decision Tree) ✓

**Rationale:**
- Generic error logging ("failed") doesn't diagnose problems
- 9 types map to architectural layers (clone→git, scan→parsing, graph→graph construction, architecture→detection, etc.)
- Decision tree is exhaustive (every error falls into one type)

**Trade-off:**
- Pro: Actionable diagnostics (Clone Failure → network issue; Parser Failure → syntax error; etc.)
- Con: Requires error classification step (BUILDER parses every error message)

**Mitigation:**
- Decision tree documented (failure-taxonomy-TEMPLATE.md)
- Logging template provided (spec.md AC2)
- Clear decision order (clone → scan → parser → graph → architecture → intent → timeout → OOM → unknown)

**Verdict:** Sound. Taxonomy enables trend analysis ("X% Parser Failures suggests syntax issues in sampled repos").

---

### Decision 5: Regression Report as Baseline Artifact ✓

**Rationale:**
- Phase 4 needs a target: "Reduce token usage 20%"
- Current state must be captured before optimization begins
- Regression baseline enables future runs to measure "better" vs. "worse"

**Trade-off:**
- Pro: Quantitative targets, measurable improvement, prevents regression
- Con: Requires maintenance (future BUILDER teams must populate REGRESSION-REPORT.md every run)

**Mitigation:**
- Template provided (regression-report-TEMPLATE.md) — 50+ KPIs, trend tracking, alert thresholds
- Clear hand-off to TEST-DESIGNER (spec.md Evidence Contract)
- Documentation on how to interpret baseline (reproducibility section)

**Verdict:** Sound. Regression baseline is essential infrastructure for continuous improvement.

---

## 4. Risk Assessment

### Identified Risks ✓

| Risk | Severity | Mitigation | Status |
|------|----------|-----------|--------|
| GitHub API rate limit (60 req/hr) | Medium | Cache results in repo-list.json; skip rate-limited repos | ✓ Mitigated |
| Large repos timeout (>500MB) | Low | Skip repos >500MB; track in exclusions | ✓ Mitigated |
| Manual spot-checks subjective | Medium | Use structured rubric (provided) | ✓ Mitigated |
| Sampling bias (e.g., all web frameworks) | Low | Stratify by category + size + stars | ✓ Mitigated |
| AC2 failures block GATE 5 | Low | Accept ≥95% success rate (5% acceptable failures) | ✓ Threshold documented |
| Rubric interpretation inconsistent | Low | Single human auditor (consistency); reference rubric (spec.md AC5) | ✓ Mitigated |

**No unmitigated risks.** All risks have documented thresholds or workarounds.

---

## 5. Data Flow & Dependencies

### Clean Dependency Chain ✓

```
AC1: Repo Sampling
  ├─ GitHub API (external)
  ├─ git clone (system)
  └─ Output: repo-list.json

AC2: Batch Analysis
  ├─ Input: repo-list.json (from AC1)
  ├─ Dependencies: `ortho scan`, `ortho analyze` (Phase 1–3 modules)
  ├─ Failure Taxonomy (reference doc, no code)
  └─ Output: results.csv, errors/*

AC3: Intent Coverage
  ├─ Input: sampled repos (from AC2, subset)
  ├─ Dependencies: IntentRouter (task-012, Phase 3)
  └─ Output: intent-coverage.json

AC4: Token Baseline
  ├─ Input: results from AC2
  ├─ Dependencies: `assemble_context()` (task-014, Phase 3)
  └─ Output: token-baseline.csv, token-stats.json

AC5: Spot-Checks
  ├─ Input: results from AC2 (stratified subset)
  ├─ Dependencies: Architecture Scoring Rubric (reference doc)
  └─ Output: spot-checks.md, spot-checks-summary.md

Final Reports:
  ├─ BENCHMARKS-REPORT.md (TEST-DESIGNER aggregates AC1–5)
  └─ REGRESSION-REPORT.md (TEST-DESIGNER creates baseline for Phase 4)
```

**No circular dependencies.** Flow is linear AC1→2→3→4→5 (except AC3 branch-parallel).

**Dependencies on Phase 1–3 modules are read-only** (no modifications to repo-intelligence, orchestration, token-optimizer).

---

## 6. Test Strategy & Verification

### AC-Level Verification ✓

| AC | How Verified | Owner | Gate |
|----|------|-------|------|
| AC1 | repo-list.json exists; ≥50 repos, all 6 categories, ≥95% clones succeed | VERIFIER reads artifact | GATE 5 |
| AC2 | results.csv complete; ≥50 rows, all KPI columns, <5% fatal errors | VERIFIER reads CSV + error logs | GATE 5 |
| AC3 | intent-coverage.json has success_rate ≥80%, breakdowns by type | VERIFIER reads JSON | GATE 5 |
| AC4 | token-stats.json has all fields (mean, median, p95, outliers) | VERIFIER reads JSON | GATE 5 |
| AC5 | spot-checks-summary.md has accuracy % for each dimension (arch, subsystem, debt) | VERIFIER reads markdown | GATE 5 |

**Verification is 100% artifact-based** (no code testing). VERIFIER checks file existence, format, and completeness.

### No Hidden Assumptions ✓

- Expected metrics documented (spec.md "Expected Test Metrics")
- Success thresholds explicit (≥50 repos, ≥80% intent success, ≥95% analysis success)
- Reference documents provided (rubric, taxonomy, regression template)
- No dependencies on "Ortho improvements" or "better algorithms" — just runs existing code

---

## 7. Deliverables & Contracts

### Evidence Contract ✓

All artifacts traceable to AC (spec.md "Evidence Contract"):

**AC1 Artifacts:**
- repo-list.json (sampled metadata)
- exclusions.json (skipped repos + reasons)

**AC2 Artifacts:**
- results.csv (KPI metrics)
- results/*.log (ortho output per repo)
- errors/*.error (failures classified by type)

**AC3 Artifacts:**
- intent-coverage.json (coverage stats)

**AC4 Artifacts:**
- token-baseline.csv (samples)
- token-stats.json (aggregate stats)

**AC5 Artifacts:**
- spot-checks.md (rubric assessments)
- spot-checks-summary.md (accuracy %)

**Reference Documents:**
- architecture-scoring-rubric-TEMPLATE.md (AC5 reference)
- failure-taxonomy-TEMPLATE.md (AC2 reference)

**Final Reports:**
- BENCHMARKS-REPORT.md (TEST-DESIGNER summary)
- REGRESSION-REPORT.md (TEST-DESIGNER baseline)

**Total: 15 artifacts, all documented, all traceable to AC.**

---

## 8. Architecture Patterns & Principles

### Principle: Evidence Before Confidence ✓

- FRD Principle 4: "Evidence before confidence — Never accept LLM output without verification artifacts"
- task-015 embodies this: rubric-based validation, not subjective confidence
- Each accuracy claim backed by specific rubric criteria + file examples

### Principle: Simplicity Over Cleverness ✓

- No ML models, no embeddings, no LLM fallback
- Rubric-based scoring is straightforward, auditable, and reproducible
- Failure taxonomy is decision tree (not NLP or heuristics)

### Principle: Each Module Has One Job ✓

- AC1: sampling
- AC2: execution + metric collection
- AC3: intent routing validation
- AC4: token accounting
- AC5: accuracy validation

No module does double duty. Clear responsibilities.

### Principle: Model-Agnostic Architecture ✓

- task-015 validates Phases 1–3 (which are model-agnostic by design)
- Baseline metrics (regression-report-TEMPLATE.md) are independent of Phase 4 implementation choice
- Phase 4 can use LLM-based reranker, ML embeddings, or pure Python — baseline still applies

---

## 9. Extensibility & Future-Proofing

### Phase 4 Integration ✓

- Baseline KPIs feed Phase 4 targets (20% token reduction = current_mean × 0.8)
- Regression report template enables comparative analysis (future benchmarks vs. baseline)
- Trend tracking (regression-report-TEMPLATE.md) captures what improved, what regressed

### Future Benchmark Runs ✓

- Same seed (42) enables reproducibility
- Category + stratification parameters documented → future BUILDER can re-run with confidence
- Regression template provides structure for consistent metrics across runs

### Extensibility ✓

- Task-015 does NOT lock in Phase 4 optimization strategy
- Could optimize with: reranker (ML-based), dedup (semantic or rule-based), compression (LLM or heuristic)
- Baseline metrics remain valid regardless of Phase 4 implementation

---

## 10. Consistency & Completeness Verification

### Cross-Document Consistency ✓

- **plan.md:** 5 ACs + risks + success criteria (updated with refinements)
- **spec.md:** Detailed AC definitions + KPI schema + rubric integration (updated with refinements)
- **rollback-plan.md:** Low-risk cleanup procedures (unchanged)
- **Reference templates:** 3 new documents (rubric, taxonomy, regression-report)
- **CONSISTENCY-PASS.md:** Verification that all refinements applied uniformly ✓

**All documents cross-reference consistently.** No contradictions detected.

### Specification Completeness ✓

- Every AC has: definition, how-to, acceptance criteria, expected metrics, evidence artifact
- No ambiguity about success thresholds (≥50 repos, ≥80% intent success, ≥95% analysis success)
- Reference documents provided (rubric, taxonomy, regression template)

---

## 11. Risk-Aware Decisions

### Acceptable Failures ✓

- Accept ≤5% failure rate in AC2 (≥95% analysis success)
- Accept manual judgment in AC5 (5–10 repos, not all 100)
- Accept GitHub API rate limiting (cache + skip)

All documented in plan.md "Risks & Mitigations".

### Non-Rollback Repair Flows ✓

Rollback-plan.md documents scenarios where issues are fixed, not reverted:
- AC2 5% failures → document in errors/ and continue
- AC5 spot-checks reveal inconsistencies → flag in BENCHMARKS-REPORT.md as findings
- GitHub rate limit → cache results and resume next session

---

## 12. Architectural Alignment

### Pillars Integration ✓

- **Pillar 1 (Repo Intelligence):** task-015 validates `ortho scan` on diverse repos
- **Pillar 2 (ContextHub):** task-015 validates context assembly costs (AC4)
- **Pillar 3 (Arch Intelligence):** task-015 validates architecture detection + subsystem clustering (AC2, AC5)
- **Pillar 4 (Orchestration):** task-015 validates intent routing (AC3)
- **Pillar 5 (Token Optimizer):** task-015 establishes token baseline (AC4)

No pillar left untested. Clean validation coverage.

### No Architecture Violations ✓

- No new packages introduced
- No circular dependencies
- No tight coupling between ACs
- No modifications to production code
- No external service dependencies (GitHub API is read-only discovery)

---

## ADR Recommendation

### No ADR Required ✓

**Rationale:**
- task-015 is pure analysis (no implementation decision)
- No new code, no new module boundaries, no new storage schema
- Decisions (rubric-based validation, taxonomy, regression baseline) are all documented inline in spec.md

**If task-015 led to architecture changes → ADR would be required.** Since it doesn't, no ADR.

---

## Summary & Verdict

### Architecture Assessment

| Dimension | Status | Notes |
|-----------|--------|-------|
| FRD Alignment | ✅ | Validates Phase 2 exit criteria + prepares Phase 4 targets |
| Scope Clarity | ✅ | 5 ACs, pure analysis, no code changes |
| Boundaries | ✅ | Clean separation: AC1→5 linear, no circular deps |
| Risk Mitigation | ✅ | All risks have documented thresholds or workarounds |
| Dependencies | ✅ | Only Phase 1–3 modules (read-only), no new packages |
| Deliverables | ✅ | 15 artifacts, all documented, traceable to AC |
| Test Strategy | ✅ | 100% artifact-based verification, no hidden assumptions |
| Principles | ✅ | Evidence-based, simple, modular, model-agnostic |
| Extensibility | ✅ | Phase 4 can use any optimization strategy; baseline remains valid |

### Gate 2 Verdict

**✅ APPROVED — Ready for GATE 3 (BUILDER execution)**

**Conditions:**
- None. Plan and specification are sound.

**Next Steps:**
1. BUILDER executes 5 ACs (atomic tasks)
2. TEST-DESIGNER (fresh session) writes verification checks
3. VERIFIER validates artifacts + metrics
4. REVIEWER confirms reproducibility + findings

---

## Appendix: Reference Materials

**For BUILDER:**
- spec.md: AC1–5 with detailed how-to
- failure-taxonomy-TEMPLATE.md: decision tree for error classification
- architecture-scoring-rubric-TEMPLATE.md: scoring criteria for each style

**For TEST-DESIGNER:**
- spec.md "Expected Test Metrics": baseline expectations per AC
- regression-report-TEMPLATE.md: structure for final reports
- Evidence Contract (spec.md): artifact checklist

**For VERIFIER:**
- Definition of Done (plan.md): artifacts to check
- Expected Test Metrics (spec.md): thresholds to validate
- Evidence Contract (spec.md): mapping AC → artifact

---

*Architecture Review version: 1.0 | Completed: 2026-07-08 | Status: APPROVED for GATE 3*
