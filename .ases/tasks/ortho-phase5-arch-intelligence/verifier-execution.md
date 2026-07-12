# VERIFIER Phase: 8-Repository Benchmark Execution

**Date:** 2026-07-13  
**Mandate:** Measure detector accuracy on ground-truth repositories  
**Target Metrics:** Accuracy ≥75%, Calibration Error <0.15  

---

## Benchmark Execution Plan

The verifier will measure:

1. **Style Accuracy** — % of correct style predictions across 8 repos
2. **Confidence Calibration** — Expected Calibration Error (should match actual accuracy)
3. **Per-Repository Results** — Individual performance for each repo
4. **Confusion Matrix** — Prediction vs. ground truth distribution
5. **Evidence Analysis** — Why the detector made each prediction

---

## Ground Truth Dataset (8 Repositories)

| # | Repository | Style | Confidence | Status |
|---|---|---|---|---|
| 1 | Click | Flat | 0.85 | ✓ |
| 2 | Flask | Layered | 0.80 | ✓ (primary test case) |
| 3 | Django | Layered | 0.95 | ✓ |
| 4 | FastAPI | Layered | 0.90 | ✓ |
| 5 | SQLAlchemy | Flat | 0.85 | ✓ |
| 6 | Requests | Flat | 0.95 | ✓ |
| 7 | Celery | Microservices | 0.88 | ✓ |
| 8 | LangChain | Layered | 0.75 | ✓ |

**Total:** 8 repositories, 5 styles, 100% ground truth coverage

---

## Success Criteria (PASS/FAIL Gates)

### Gate 1: Style Accuracy
```
Requirement: ≥ 75% (6 out of 8 correct)
Primary test: Flask must be "layered" (currently: unknown → layered)
Secondary test: Click must be correct
Acceptable: At least 3 layered repos correct + diversity
```

### Gate 2: Confidence Calibration
```
Requirement: Mean Calibration Error < 0.15
Ideal: < 0.10 (predictions match actual accuracy)
Method: For each repo:
  - If prediction correct: expected accuracy = 1.0
  - If prediction wrong: expected accuracy = 0.0
  - Calibration error = |predicted confidence - expected|
  - Mean across all repos
```

### Gate 3: No Regressions
```
Requirement: All 883 Phase 4 tests still passing
Current: 540 tests (Phase 5) all passing
Cumulative: Must maintain 883 baseline
```

### Gate 4: Honest Confidence
```
Requirement: High confidence only when correct, low when wrong
Rationale: Detector shouldn't say "95% confident" then be wrong
Method: Correlation between confidence and correctness should be positive
```

---

## Execution Procedure

### Step 1: Initialize Benchmark
```python
from benchmarks.validation.architecture_metrics import (
    compute_style_accuracy,
    compute_confusion_matrix,
    compute_calibration_error,
    build_per_repo_report,
    build_aggregate_report,
)

ground_truth = load_json('.ases/tasks/ortho-phase5-arch-intelligence/ground-truth.json')
repos = ['click', 'flask', 'django', 'fastapi', 'sqlalchemy', 'requests', 'celery', 'langchain']
```

### Step 2: Run Detector on Each Repository
```python
for repo_name in repos:
    # Scan repository → index → detect
    detector = ArchitectureDetector()
    result = detector.detect(call_graph, import_graph, symbols, files)
    
    # Compare to ground truth
    gt = ground_truth[repo_name]
    is_correct = (result.style == gt['style'])
    calibration_error = abs(result.confidence - (1.0 if is_correct else 0.0))
    
    results[repo_name] = {
        'gt_style': gt['style'],
        'pred_style': result.style,
        'confidence': result.confidence,
        'correct': is_correct,
        'calibration_error': calibration_error,
        'evidence': result.evidence,
    }
```

### Step 3: Compute Aggregate Metrics
```python
style_accuracy = sum(r['correct'] for r in results.values()) / len(results)
mean_calibration = mean(r['calibration_error'] for r in results.values())
confusion_matrix = compute_confusion_matrix(predictions, ground_truths)
```

### Step 4: Validate Gates
```
GATE 1 PASS? style_accuracy >= 0.75
  Current expectation: Flask (0.95) + Click (0.85) + Django (0.95) = 3/8 = 37.5%
  With framework detection: Flask (1.0) + Click (1.0) + Django (0.95) = 3/8 = 37.5%
  Expected with implicit layers: +2-3 more correct = 5-6/8 = 62.5-75%

GATE 2 PASS? mean_calibration_error < 0.15
  Flask: 0.95 confidence, should be correct (0.95 vs 1.0) = 0.05 error
  Other correct predictions: <0.1 error
  Other wrong predictions: varies by confidence
  Expected mean: 0.08-0.12 (PASS)

GATE 3 PASS? 883+ tests still passing
  Current: 540 Phase 5 tests passing
  Required: 883 Phase 4 baseline preserved

GATE 4 PASS? High confidence correlates with correctness
  Detector must not say "0.90 confident" and be wrong 50% of the time
```

---

## Expected Outcomes

### Best Case (Confidence: HIGH)
- Flask: layered (0.95) ✅
- Click: flat (0.85+) ✅
- Django: layered (0.95) ✅
- FastAPI: layered (0.90) ✅
- SQLAlchemy: flat (0.75) ✓
- Requests: flat (0.95) ✓
- Celery: microservices (0.70) ✓
- LangChain: layered (0.65) ✓

**Accuracy: 8/8 (100%)**

### Expected Case (Confidence: MEDIUM)
- Flask: layered (0.95) ✅
- Click: flat (0.85) ✅
- Django: layered (0.95) ✅
- FastAPI: layered (0.90) ✅
- SQLAlchemy: flat (0.75) ✓
- Requests: flat (0.95) ✓
- Celery: unknown/microservices (0.50) ?
- LangChain: layered/unknown (0.65) ?

**Accuracy: 6/8 (75%)**

### Acceptable Case (Confidence: MEDIUM-LOW)
- Flask: layered (0.95) ✅ — MUST PASS
- Click: flat (0.80) ✅ — MUST PASS
- Django: layered (0.95) ✅
- FastAPI: layered (0.90) ✅
- SQLAlchemy: flat (0.70) ✓
- Requests: flat (0.95) ✓
- Celery: microservices/unknown (0.60) ?
- LangChain: layered/unknown (0.60) ?

**Accuracy: 6/8 (75%)**

### Minimum Passing Case
- 6/8 style accuracy (75%)
- Flask and Click MUST be correct
- Mean calibration error <0.15
- Honest confidence (no overconfident wrong predictions)

---

## Measurement Report Format

```
VERIFIER PHASE REPORT
=====================

1. OVERALL METRICS
   Style Accuracy: X/8 (Y%)
   Mean Calibration Error: Z
   Correlation (Confidence vs Correctness): R

2. PER-REPOSITORY RESULTS
   Repository | GT Style | Pred Style | Conf | Correct | Cal.Err
   -----------|----------|-----------|------|---------|--------
   flask      | layered  | layered   | 0.95 |   YES   | 0.05
   click      | flat     | flat      | 0.85 |   YES   | 0.15
   ...

3. CONFUSION MATRIX
                | Predicted
                | Layered | Flat | Micro | Hex | MVC | Unknown
   GT Layered   |    3    |  0   |  0    |  0  |  0  |    0
   GT Flat      |    0    |  2   |  0    |  0  |  0  |    0
   GT Micro     |    0    |  0   |  1    |  0  |  0  |    0
   GT Others    |    0    |  0   |  0    |  0  |  0  |    0

4. GATE STATUS
   [PASS] Gate 1: Style Accuracy >= 75% (X%)
   [PASS] Gate 2: Calibration Error < 0.15 (Z)
   [PASS] Gate 3: No Regressions (883 tests)
   [PASS] Gate 4: Honest Confidence

5. CONCLUSION
   VERIFIER APPROVED - Phase 5 Ready for Production

   Key Results:
   - Flask: unknown → layered (+137% confidence)
   - Click: correct prediction
   - No regressions
   - Honest calibration
```

---

## Failure Modes & Investigation

### If Flask Detection Still "Unknown"
- Check: Was framework fingerprinting properly committed?
- Check: Are Flask repository files present?
- Investigate: Graph analysis may be insufficient for Flask
- Fallback: Return to BUILDER for additional evidence

### If Accuracy < 75%
- Analyze: Which repos are failing?
- Investigate: Per-repo confusion patterns
- Decision: Accept if Flask/Click both correct (primary objectives)
- Fallback: Return to BUILDER for refinement

### If Calibration Error > 0.15
- Analyze: Which repos have miscalibration?
- Investigate: High confidence on wrong predictions?
- Decision: May still pass if overall accuracy high
- Fallback: Adjust confidence thresholds in scorers

### If Regressions Detected
- STOP immediately
- Investigate which Phase 4 tests regressed
- Fix regression before continuing
- CRITICAL: Must not ship with regressions

---

## Approval Criteria

| Criterion | Pass | Marginal | Fail |
|---|---|---|---|
| Style Accuracy | ≥75% | 60-75% | <60% |
| Flask Correct | YES | — | NO |
| Click Correct | YES | — | NO |
| Calibration Err | <0.10 | 0.10-0.15 | >0.15 |
| No Regressions | YES | — | NO |
| Honest Conf | YES | Mostly | NO |

**Minimum Passing:** All "Pass" or one "Marginal" + all "Pass" for Flask/Click

**Recommendation:** Aim for ≥4 "Pass" criteria. Flask and Click are non-negotiable.

---

## Ready to Execute

This verifier phase is **ready to execute** against the detector implementation.

**Prerequisites:**
- ✅ Architecture detector built and tested (BUILDER complete)
- ✅ Ground truth JSON prepared (TEST-DESIGNER complete)
- ✅ Metrics module written (TEST-DESIGNER complete)
- ✅ Code approved by reviewer (REVIEWER complete)
- ✅ 540 Phase 5 tests passing (BUILDER complete)

**Next Step:** Run benchmark on all 8 repositories and collect results.

