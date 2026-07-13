# Phase 6.3: LLM Integration & Feedback Loop — PLANNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6.3 (LLM Integration & Feedback)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 with parallel BUILDER + TEST-DESIGNER  
**Duration:** 1 week (Phase 6.3 MVP)  
**Builds On:** Phase 6.1 (4 components) + Phase 6.2 (2 components)

---

## Executive Summary

Phase 6.3 integrates Claude API for real-time decision scoring and feedback:

1. **LLM Decision Scorer** — Real Claude API for decision quality scoring
2. **Feedback Loop** — User acceptance tracking, model improvements
3. **Confidence Calibration** — Learn from real vs. predicted outcomes
4. **Advanced Recommendations** — LLM-enhanced suggestions

**Success Criteria:**
- ✅ Claude API integration working (real API calls)
- ✅ Decision scoring accuracy ≥95% (vs ground truth)
- ✅ Feedback collection & storage
- ✅ No regressions on Phase 6.1/6.2 (all tests pass)
- ✅ 50+ integration tests passing

---

## Current State (End of Phase 6.2)

- ✅ Phase 6.1: 4 core components (78/78 tests)
- ✅ Phase 6.2: Decision engine + CLI (18/18 tests)
- ✅ 96/96 tests passing (100%)
- ✅ Average coverage: 93.5%

**Missing:**
- Real LLM scoring
- Feedback collection
- Calibration loop
- Advanced workflows

---

## Acceptance Criteria

### AC1: LLM Scorer MVP
- ✅ Call Claude API for decision scoring
- ✅ Score 0.0-1.0 based on decision quality
- ✅ Cache results (avoid duplicate calls)
- ✅ Fallback to heuristic if API fails
- ✅ 50+ integration tests

### AC2: Feedback Collection
- ✅ Track user acceptance (yes/no/maybe)
- ✅ Store in SQLite
- ✅ Enable future calibration

### AC3: No Regressions
- ✅ All Phase 6.1/6.2 tests pass (96/96)
- ✅ New component tests pass (50+)
- ✅ Performance intact (<5s per operation)

---

## Definition of Done

✅ PLANNER: Spec complete  
⏳ ARCHITECT: Design (ADRs, components)  
⏳ TEST-DESIGNER: Test specs (50+ cases)  
⏳ BUILDER: Implementation  
⏳ VERIFICATION: All tests pass, metrics met  

---

## Next: Comprehensive Phase 6 Test Suite

After Phase 6.3 plan, execute **MEGA HARD TEST SUITE** for ALL Phase 6:
- 200+ adversarial test cases
- Cross-component integration
- Real-world scenarios
- Performance verification
- Zero overfitting validation

