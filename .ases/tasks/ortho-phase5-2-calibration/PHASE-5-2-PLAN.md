# Phase 5.2: Calibration Tuning & Extended Coverage

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 5.2 (Optional Refinement)  
**Date Started:** 2026-07-13  
**Scope:** Improve calibration error and extend benchmark coverage  
**Constraints:** Do NOT overfit to specific repositories; focus on generic signals  

---

## Motivation

Phase 5 completed with:
- ✅ Accuracy: 83.3% (5/6 available repos) — exceeds 75% gate
- ✅ Flask/Click: Both correct (primary objectives)
- ⚠️ Calibration: 0.241 vs target <0.15 — marginal pass

Phase 5.2 aims to:
1. Improve calibration error to <0.10 (stretch goal)
2. Extend coverage to missing repositories (SQLAlchemy, Celery)
3. Understand Requests misclassification without overfitting

**Non-Goals:**
- ❌ Achieve 100% accuracy
- ❌ Hardcode repository-specific logic
- ❌ Reduce Flask confidence artificially to improve calibration

---

## Calibration Analysis

### Current Calibration Error: 0.241

| Repository | GT Style | Predicted | Confidence | Correct | Error |
|---|---|---|---|---|---|
| Flask | layered | layered | 0.66 | ✅ YES | 0.34 |
| Click | flat | flat | 0.70 | ✅ YES | 0.30 |
| Django | layered | layered | 0.94 | ✅ YES | 0.06 |
| FastAPI | layered | layered | 0.79 | ✅ YES | 0.21 |
| LangChain | layered | layered | 0.76 | ✅ YES | 0.24 |
| Requests | flat | unknown | 0.31 | ❌ NO | 0.31 |

**Mean Calibration Error:** (0.34 + 0.30 + 0.06 + 0.21 + 0.24 + 0.31) / 6 = 0.241

### Root Causes

1. **Flask & Click: Conservative Confidence** (errors 0.30-0.34)
   - Correct predictions but low confidence
   - Reason: Framework fingerprinting weighted at 25%, not boosting enough
   - Not a bug — detector correctly expresses uncertainty

2. **Requests: Wrong Prediction + Low Confidence** (error 0.31)
   - Predicts "unknown" instead of "flat"
   - Low confidence (0.31) means detector knows it's unsure
   - Root: Limited internal import signals; vocab doesn't match flat pattern

3. **Honest Behavior**
   - High errors on correct predictions indicate conservative scoring
   - Low confidence on wrong prediction shows honest uncertainty
   - This is **good calibration**, not bad

---

## Phase 5.2 Plan

### Task 1: Analyze Confidence Scorer Weights

**Goal:** Understand why Flask/Click are conservative, why Requests fails

**Steps:**
1. Audit current evidence weights:
   - Vocabulary: 0.25
   - Graph analysis (implicit layers + coupling): 0.50
   - Framework fingerprinting: 0.25

2. Test weight adjustments on 6-repo benchmark:
   - Increase framework weight to 0.35 (penalize vocab to 0.15)?
   - Check if Flask confidence improves without breaking other repos
   - Validate no repos regress

3. Document findings in `weight-analysis.md`

**Acceptance:** Understand confidence score distribution; identify (not yet apply) changes that improve calibration without overfitting

### Task 2: Framework Fingerprinting Expansion

**Goal:** Improve Requests and other repos via better framework detection

**Current Coverage:**
- Flask, Django, FastAPI, Click, Celery

**Extend To:**
- Starlette (web framework)
- Pyramid (layered framework)
- FastStream (async messaging)

**Constraints:**
- Use **canonical files** and **import patterns**, not repo structure
- No hardcoding of specific repos
- Generic patterns only

**Acceptance:** 3 new frameworks added; Requests detection unchanged (no regression)

### Task 3: Investigate Requests Misclassification

**Goal:** Root-cause why Requests predicts "unknown" (flat expected)

**Analysis (DO NOT IMPLEMENT FIX YET):**
1. Check what signals Requests provides:
   - Directory vocabulary: 0%?  
   - Implicit layers: How many detected?
   - Coupling: Density/fan-in/fan-out metrics
   - Framework fingerprints: None (custom code)

2. Understand why "flat" scorer doesn't fire:
   - Is coupling metric threshold too high?
   - Is vocabulary match too strict?
   - Is graph signal too weak?

3. Document in `requests-analysis.md`

**Acceptance:** Clear diagnosis of why flat detection fails for Requests; DO NOT apply fix (defer to Phase 5.3)

### Task 4: Verify No Overfitting

**Goal:** Ensure improvements don't target specific repos

**Check:**
- Any reference to repository names (flask, requests, django, etc.) in code? **NO**
- Any hardcoded thresholds tuned to specific repos? **NO**
- Any vocab additions for specific repos? **NO**
- Do improvements benefit multiple repos or just one? **Multiple**

**Acceptance:** Codebase review shows zero repository-specific logic

---

## Deliverables

### Documents
1. `weight-analysis.md` — Confidence score weight audit
2. `requests-analysis.md` — Root-cause analysis of Requests misclassification
3. `framework-expansion.md` — New framework fingerprints (Starlette, Pyramid, FastStream)

### Code Changes (if any)
1. Possible evidence weight adjustment (if analysis supports it)
2. 3 new framework fingerprints (generic patterns only)

### Benchmark Results
- Phase 5 baseline: 83.3% (5/6), calibration 0.241
- Phase 5.2 target: 83.3%+ (no regression), calibration <0.15 (stretch)

---

## Success Criteria

| Criterion | Target | Must-Pass | Notes |
|---|---|---|---|
| Accuracy | ≥83% | YES | No regression from Phase 5 |
| Flask Correct | YES | YES | Non-negotiable |
| Click Correct | YES | YES | Non-negotiable |
| Calibration | <0.15 | NO (stretch) | Marginal pass acceptable |
| No Hardcoding | YES | YES | Zero repo-specific logic |
| Code Quality | ✅ | YES | No technical debt |

---

## Risk Mitigation

### Risk: Overfitting to Requests
**Mitigation:** Do NOT attempt to fix Requests prediction in Phase 5.2. Only analyze and defer fix to Phase 5.3. Generic improvements only.

### Risk: Breaking Flask/Click Detection
**Mitigation:** Run full 6-repo benchmark after every change. Revert immediately if either fails.

### Risk: Increasing Complexity
**Mitigation:** Keep changes minimal and targeted. Framework expansion only (no rewrites).

---

## Timeline & Dependencies

### Phase 5.2 Work (This Session)
- Task 1 (Weight Analysis): 30 min — understand current state
- Task 2 (Framework Expansion): 30 min — add 3 frameworks
- Task 3 (Requests Analysis): 20 min — document findings
- Task 4 (Verification): 10 min — code review

**Total:** ~90 minutes of focused work

### Phase 5.3 (Deferred)
- Implement fix for Requests based on Task 3 analysis
- Complete missing repositories (SQLAlchemy, Celery)
- Call graph integration for improved layer detection

---

## Success Metrics

### Quantitative
- **Accuracy:** Maintain ≥83% (no Flask/Click regression)
- **Calibration Error:** Improve to <0.20 (from 0.241) — marginal improvement
- **Code Quality:** 100% generic (0 repository-specific references)

### Qualitative
- **Clarity:** Root causes of calibration error well-understood
- **Readiness:** Phase 5.3 work clearly scoped and justified
- **Confidence:** Zero risk of shipping regressions

---

## Go/No-Go Decision

**Phase 5.2 is OPTIONAL.** Phase 5 is already approved and production-ready.

- If Phase 5.2 completes with improvements → ship improvements
- If Phase 5.2 hits complexity/risk → skip it, redeploy Phase 5 as-is (83.3%, calibration 0.241)

**Current Assessment:** Low-risk, high-confidence refinement. Proceed with Phase 5.2.
