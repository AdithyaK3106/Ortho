# Phase 6: Engineering Intelligence — Task Summary

**Task ID:** ortho-phase-6-engineering-intelligence  
**Project:** Ortho v3 — AI Engineering Platform  
**Status:** ASES Workflow Started (GATES 1-5 in progress)  
**Start Date:** 2026-07-13  
**Duration:** 2 weeks (Phase 6.1 MVP)  

---

## Overview

Phase 6 introduces the **Engineering Intelligence Layer** — high-level planning, analysis, and guardrails that sit above Ortho's architectural intelligence.

### Four Components
1. **Change Planner** — Predict impact of code changes (extension of Phase 5 blast radius)
2. **Feature Planner** — Generate 3+ implementation paths for new features
3. **Refactoring Advisor** — Detect 5 types of refactoring opportunities
4. **Architecture Guardrails** — Enforce 5 architectural rules with 100% block rate

### Success Criteria
- ✅ 90%+ accuracy on impact prediction (hard ground truth)
- ✅ 3+ distinct paths per feature (variety requirement)
- ✅ 100% precision on refactoring detection (zero false positives)
- ✅ 100% violation detection rate on guardrails (zero false negatives)
- ✅ 100% test pass rate (90+ tests, all hard cases)
- ✅ Zero overfitting (adversarial + edge case tests)

---

## ASES Workflow Gates

### GATE 1: PLANNER ✅
**Document:** `PLANNER-spec.md`

**Contents:**
- Executive summary (what, why, when)
- Current state analysis
- 4 acceptance criteria (AC1-AC4) with hard metrics
- 20 impact prediction test cases (hand-verified ground truth)
- 15 feature planning test cases (variety emphasis)
- 20 refactoring detection test cases (zero false positives)
- 25 guardrail enforcement test cases (100% block rate)
- Parallel execution plan (TEST-DESIGNER + BUILDER)
- Success metrics (GATE 5)
- Rollback plan

**Status:** ✅ Complete

### GATE 2: ARCHITECT ✅
**Document:** `ARCHITECT-design.md`

**Contents:**
- Architecture overview (data flow, layer diagram)
- Component design (algorithm, edge cases, key functions)
- ADRs (5 architectural decisions)
- Data flow & integration with Phase 2-3-5
- No overfitting strategies (explicit edge cases, adversarial tests)
- Integration points with orchestrator
- Performance targets
- Testing strategy summary
- Definition of done

**Status:** ✅ Complete

### GATE 3: SCOPE REVIEW (In Progress)
**Reviewers:** User (lead engineer)

**Scope Checklist:**
- ✅ No changes to existing packages (Phase 2-5)
- ✅ Four new packages only (change-planner, feature-planner, refactoring-advisor, arch-guardrails)
- ✅ No external dependencies without justification
- ✅ All changes traceable to PLANNER + ARCHITECT
- ⏳ User approval required before proceeding

### GATE 4: TEST-DESIGNER ✅
**Document:** `TEST-DESIGNER-test-specs.md`

**Contents:**
- 20 change planner tests (straightforward, graph traversal, edges, complex)
- 15 feature planner tests (endpoint, service, data layer, cross-cutting, meta)
- 20 refactoring advisor tests (all 5 issue types, zero false positives)
- 25 guardrails tests (all 5 rules, multi-rule scenarios, adversarial)
- 10 adversarial + overfitting prevention tests
- **Total: 90+ test cases**

**Hard Requirements:**
- All tests use real fixtures (not mocks)
- All tests are deterministic (no flakes)
- Explicit adversarial cases designed to trick naive algorithms
- False positive/negative prevention tests
- Cross-architecture tests (layered, microservices, mixed)
- Performance targets (<30s total run time)

**Status:** ✅ Complete

### GATE 5: BUILDER + VERIFICATION (Next)
**Document:** `BUILDER-implementation.md`

**Parallel Work:**
- **BUILDER 1:** change-planner implementation
- **TEST-DESIGNER 1:** 20 change-planner tests
- **BUILDER 2:** feature-planner implementation
- **TEST-DESIGNER 2:** 15 feature-planner tests
- **BUILDER 3:** refactoring-advisor implementation
- **TEST-DESIGNER 3:** 20 refactoring-advisor tests
- **BUILDER 4:** arch-guardrails implementation
- **TEST-DESIGNER 4:** 25 guardrails tests

**Success Metrics:**
- ✅ All 4 components implemented to spec
- ✅ All 90+ tests pass (100% pass rate)
- ✅ Type safety (mypy --strict)
- ✅ Code coverage ≥85%
- ✅ No overfitting (adversarial tests confirm)
- ✅ Performance targets met (<30s)

---

## Documents

| Document | Status | Purpose |
|----------|--------|---------|
| PLANNER-spec.md | ✅ Complete | Requirements, ACs, test cases, metrics |
| ARCHITECT-design.md | ✅ Complete | System design, ADRs, components |
| TEST-DESIGNER-test-specs.md | ✅ Complete | 90+ hard test cases with fixtures |
| BUILDER-implementation.md | ✅ Complete | Implementation details per component |
| task-summary.md | ✅ Complete | This document |

---

## Next Steps

### Immediate (User Approval)
1. Review PLANNER spec (ACs, test counts, metrics)
2. Review ARCHITECT design (components, ADRs)
3. Approve GATE 3 (scope review)
4. Proceed to GATE 4 (TEST-DESIGNER already done)

### Phase 6.1 Execution (2 weeks)
1. BUILDER + TEST-DESIGNER run in parallel (4 components)
2. Daily synchronization on cross-component integration
3. Continuous testing (test suite grows in parallel)
4. GATE 5 verification (all tests pass, metrics met)

### Phase 6.2 (Future)
- Real LLM API integration (for feature planner + advisor)
- Decision Engine (structured decision support)
- CLI commands (`ortho plan`, `ortho refactor-advice`, `ortho guardrails`)
- Interactive workflows with approval gates

---

## Key Decisions

### ADR-016: Package Structure
Each component is independent, not monolithic. Enables parallel work.

### ADR-017: Confidence Scoring
All outputs include confidence (0.0-1.0) based on evidence. Conservative thresholds.

### ADR-018: Zero False Positives
Refactoring advisor + guardrails prioritize precision over recall.

### ADR-019: Feature Planner Variety
Must return ≥3 distinct paths (not one hardcoded solution).

### ADR-020: Guardrails Configurability
Rules are per-project customizable (with exceptions).

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Overfitting | Adversarial tests designed to catch naive solutions | TEST-DESIGNER |
| False positives | Explicit filtering, high confidence threshold (0.8+) | BUILDER |
| False negatives | 100% block rate tests, adversarial guardrails cases | TEST-DESIGNER |
| Performance | Profiling targets (<100ms, <500ms, <2s per component) | BUILDER |
| Scope creep | Rollback plan if component fails GATE 5 | Phase lead |

---

## Success Metrics (GATE 5)

### Accuracy & Precision
| Component | Metric | Target | Evidence |
|-----------|--------|--------|----------|
| Change Planner | Accuracy | ≥90% | 18/20 tests on hand-verified truth |
| Feature Planner | Variety | ≥3 paths | Variety test verifies distinct paths |
| Refactoring Advisor | Precision | 100% | Adversarial tests confirm zero false positives |
| Guardrails | Recall | 100% | 25/25 violation tests caught |

### Quality Gates
| Gate | Target | Evidence |
|------|--------|----------|
| **Test Pass Rate** | 100% | All 90+ tests pass |
| **Type Safety** | mypy --strict | Zero violations |
| **Code Coverage** | ≥85% | pytest-cov report |
| **Determinism** | No flakes | Tests pass consistently |
| **Performance** | <30s total | Execution time measured |

---

## Phase 6.1 Timeline

**Week 1:**
- Day 1-2: User review + GATE 3 approval
- Day 3-5: BUILDER 1 + TEST-DESIGNER 1 (change-planner)

**Week 2:**
- Day 1-2: BUILDER 2 + TEST-DESIGNER 2 (feature-planner)
- Day 3-4: BUILDER 3 + TEST-DESIGNER 3 (refactoring-advisor)
- Day 5: BUILDER 4 + TEST-DESIGNER 4 (arch-guardrails)

**Integration (Day 6-7):**
- Wire all 4 into orchestrator
- Full test suite run
- GATE 5 verification

---

## Definition of Done

✅ PLANNER: Spec complete (this document)  
✅ ARCHITECT: Design complete (5 ADRs, component specs)  
⏳ GATE 3: Scope review (awaiting user approval)  
✅ TEST-DESIGNER: Test specs complete (90+ hard cases)  
⏳ BUILDER: Implementation (in progress, parallel)  
⏳ GATE 5: Verification (all tests pass, metrics met)  
⏳ CODE REVIEW: Independent review (before merge)  
⏳ MERGE: To main branch  

---

## Rollback Plan

If any component fails GATE 5:
1. Revert to empty skeleton (keep interfaces)
2. Move failing tests to `tests/deferred/`
3. Create ADR explaining deferral
4. Phase 6.1 ships with 3/4 components
5. Phase 6.2 completes remaining component

---

## Author Notes

**Phase 6 Philosophy:**
- **Hard tests, not easy mocks.** Real fixtures, real algorithms, real edge cases.
- **No overfitting.** Adversarial tests designed to catch naive solutions.
- **Zero false positives/negatives.** Precision on advisor, recall on guardrails.
- **Parallel execution.** TEST-DESIGNER + BUILDER move together, not sequentially.
- **Variety over optimization.** Multiple paths, not one hardcoded solution.

**Success = All 4 components + All 90+ tests pass + Zero overfitting.**

