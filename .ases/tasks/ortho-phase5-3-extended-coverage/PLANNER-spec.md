# Phase 5.3: Extended Coverage & Refinement — PLANNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 5.3 (Extended Coverage & Refinement)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 with parallel BUILDER + TEST-DESIGNER  

---

## Executive Summary

Phase 5.3 completes the optional refinement work deferred from Phase 5.2:

1. **Complete 8-Repository Benchmark** — Add SQLAlchemy & Celery (currently 6/8)
2. **Fix Requests Misclassification** — Currently flat → unknown (0.31 conf); diagnose and fix
3. **Call Graph Integration** — Leverage unused call graph data for layer detection
4. **Extended Framework Coverage** — Add missing frameworks for better detection

**Success Criteria:**
- ✅ All 8 repositories benchmarked (100% coverage)
- ✅ Accuracy ≥85% or maintain 83.3% minimum
- ✅ Requests correctly detected as flat (>0.75 confidence)
- ✅ Tests identify and expose edge cases
- ✅ Zero regressions (453+ tests passing)

---

## Current State (Phase 5.2)

### Working Metrics
```
Accuracy:         83.3% (5/6 available repos)
  Flask:          layered (0.81) ✅
  Click:          flat (0.70) ✅
  Django:         layered (0.94) ✅
  FastAPI:        layered (0.79) ✅
  LangChain:      layered (0.91) ✅
  Requests:       unknown (0.31) ❌

Calibration:      0.150 (target <0.15 met)
Tests:            453/453 passing
Regressions:      Zero
Frameworks:       8 (Flask, Django, FastAPI, Click, Celery, 
                     Starlette, Pyramid, FastStream)
```

### Known Gaps
1. **Missing 2 Repos:** SQLAlchemy, Celery not cloned in Phase 5 testing
2. **Requests Failing:** Detected as "unknown" instead of "flat"
   - Root cause identified: File `api.py` triggers false layer vocabulary
   - Fix needed: Separate file stems from directory tokens
3. **Unused Call Graph:** Call patterns available but not integrated
4. **Framework Gaps:** Some Python frameworks not in fingerprints

---

## Phase 5.3 Objectives

### AC1: Complete 8-Repository Benchmark ✅

**Acceptance Criteria:**
- ✅ SQLAlchemy cloned and indexed
- ✅ Celery cloned and indexed
- ✅ Predictions made for both
- ✅ Ground truth classified for both
- ✅ Results documented

**Definition of Done:**
- All 8 repos in benchmark results
- Metrics computed for all (accuracy, calibration, etc.)
- No failures in indexing or detection

### AC2: Fix Requests Misclassification ✅

**Current State:**
- Prediction: unknown (0.31 confidence)
- Expected: flat (>0.75 confidence)
- Root cause: File stem "api" in PRESENTATION_TOKENS causes 50% penalty

**Acceptance Criteria:**
- ✅ Requests detected as flat
- ✅ Confidence >0.75
- ✅ No regression on other repos
- ✅ Fix verified with tests

**Definition of Done:**
- Code change: Separate file stems from directory tokens
- Tests verify Requests detection
- Full benchmark re-run shows no regressions

### AC3: Call Graph Integration ✅

**Current State:**
- Call graph extracted but not used in architecture detection
- Opportunity: Call patterns reveal implicit layering

**Acceptance Criteria:**
- ✅ Call graph data fed into detector
- ✅ Improves layer detection accuracy
- ✅ Tested on all 8 repos
- ✅ Maintains or improves accuracy

**Definition of Done:**
- ArchitectureDetector uses call graph
- Metrics show improvement (or neutral)
- Tests validate call graph signals

### AC4: Extended Framework Coverage ✅

**Current Frameworks (8):**
- Flask, Django, FastAPI, Click, Celery, Starlette, Pyramid, FastStream

**Candidates to Add:**
- Tornado, Aiohttp, Falcon, Bottle, CherryPy (web frameworks)
- APScheduler, Huey (task queues)
- Others based on gap analysis

**Acceptance Criteria:**
- ✅ 2-3 new frameworks added
- ✅ Fingerprints tested on real repos
- ✅ No false positives
- ✅ Framework detection verified

**Definition of Done:**
- New frameworks in FRAMEWORK_FINGERPRINTS
- Tests validate detection
- Benchmark shows coverage improvement

---

## ASES Workflow — Parallel BUILDER + TEST-DESIGNER

### Phase Structure

```
PLANNER (This phase)
    ↓
ARCHITECT ← Design review + validation strategy
    ↓
BUILDER (Parallel with TEST-DESIGNER)
├── AC1: Clone & index 2 repos
├── AC2: Fix Requests classification
├── AC3: Integrate call graph
└── AC4: Add framework coverage
    ↓
TEST-DESIGNER (Parallel with BUILDER)
├── Hard edge case tests
├── Call graph validation
├── Framework fingerprinting tests
└── Regression test suite
    ↓
VERIFIER
├── Full 8-repo benchmark
├── Metric validation
└── Gate checks
    ↓
REVIEWER
├── Code quality
├── No hardcoding
└── Approval
```

### Key Differences from Phase 5

**Parallel Execution:**
- TEST-DESIGNER writes tests WHILE BUILDER implements
- Tests drive implementation decisions
- Edge cases discovered early and fixed immediately

**Hard Tests:**
- Not just happy path (Flask → layered)
- Test edge cases: symlinks, namespace packages, mixed layouts
- Test framework detection false positives
- Test call graph signal strength

**Bug Discovery:**
- Tests identify regressions before benchmark
- Edge cases expose in TDD flow
- Quick iteration: test → implement → test

---

## Detailed Plan

### PLANNER Phase Deliverables ✅

- [x] Phase goals and acceptance criteria (this file)
- [x] Current state analysis
- [x] ASES workflow design
- [x] Risk assessment
- [x] Success metrics

### ARCHITECT Phase (Next)

- [ ] Ground truth classification (SQLAlchemy, Celery)
- [ ] Call graph integration design
- [ ] Framework fingerprint gaps
- [ ] Test strategy (edge cases, hard tests)
- [ ] Architecture review document

### BUILDER Phase (Parallel with TEST-DESIGNER)

**Task 1: Repository Coverage**
- Clone SQLAlchemy and Celery
- Run indexer, verify data completeness
- Classify ground truth
- ~1-2 hours

**Task 2: Requests Fix**
- Separate file stems from directory tokens
- Test with Requests specifically
- Verify no regression on other repos
- ~2-3 hours

**Task 3: Call Graph Integration**
- Modify ArchitectureDetector to use call graph
- Implement call pattern signals
- Weight call graph evidence (suggested: 0.15)
- ~3-4 hours

**Task 4: Framework Coverage**
- Add 2-3 new frameworks
- Test fingerprints on real repos
- Verify detection accuracy
- ~2 hours

**Estimated Total:** 8-12 hours

### TEST-DESIGNER Phase (Parallel with BUILDER)

**Test 1: Edge Cases — Repository Layouts**
- Symlinked packages
- Namespace packages (PEP-420)
- Mixed layouts (src/ + top-level)
- Deep nesting
- Single-file modules

**Test 2: Framework Fingerprinting**
- False positive detection (Flask in non-web code)
- Multiple frameworks (FastAPI + Celery)
- Framework not installed (imports only)
- Version edge cases

**Test 3: Call Graph Signals**
- Pure hierarchy (no cycles)
- Circular calls (should dampen signal)
- High fan-in files (hub patterns)
- Isolated call islands

**Test 4: Repository Benchmarks**
- SQLAlchemy: Expect flat
- Celery: Expect microservices
- All 8 repos: Full accuracy/calibration metrics

**Test 5: Regression Suite**
- All Phase 5 tests still pass
- Flask, Click, Django, FastAPI, LangChain: No degradation
- Requests: Fix verified (flat, >0.75)

**Estimated Test Count:** 40-50 new tests

---

## Success Metrics

### Phase 5.3 Complete When:

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Repository Coverage** | 8/8 | 6/8 | ❌ Needs: SQLAlchemy, Celery |
| **Overall Accuracy** | ≥85% or maintain 83.3% | 83.3% | ⏳ TBD (after 8-repo bench) |
| **Requests Detection** | flat, >0.75 conf | unknown, 0.31 conf | ❌ Needs fix |
| **Tests Passing** | 500+ (parallel adds) | 453 | ⏳ TBD (after parallel tests) |
| **Regressions** | Zero | Zero | ✅ Must maintain |
| **Call Graph Used** | Yes, in detection | No, unused | ❌ Needs integration |
| **Frameworks** | 10-12 | 8 | ❌ Needs 2-3 added |

---

## Risk Assessment

### Low Risk ✅
- Adding frameworks (additive, no changes to core logic)
- Cloning new repositories (standard indexing)
- Writing tests (non-breaking)

### Medium Risk ⚠️
- Separating file stems from directory tokens (touches core logic)
- Integrating call graph (new signal, needs careful weighting)
- Fixing Requests (may affect other flat repos)

### Mitigation
- Parallel tests catch issues immediately
- Regression suite prevents breaking changes
- 8-repo benchmark validates all changes
- Hard tests identify edge cases early

---

## Timeline

**Estimated Duration:** 5-7 days

| Day | Phase | Deliverable |
|-----|-------|-------------|
| 1 | ARCHITECT | Ground truth, design docs |
| 2-3 | BUILDER + TEST-DESIGNER | Parallel implementation & hard tests |
| 4 | BUILDER + TEST-DESIGNER | Edge case fixes, regression validation |
| 5 | VERIFIER | Full 8-repo benchmark, metrics |
| 6 | REVIEWER | Code quality, approval |
| 7 | Deployment | Push to master, update README |

---

## Next: ARCHITECT Phase

Ready to proceed to ARCHITECT phase:
- Ground truth classification (SQLAlchemy, Celery)
- Call graph integration design
- Test strategy document
- Framework fingerprint audit

**Approve to continue?** → ARCHITECT phase next
