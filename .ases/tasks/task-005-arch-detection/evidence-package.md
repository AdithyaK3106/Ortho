# task-005: Architecture Detection — Evidence Package

**Status:** GATE 5 BLOCKED  
**Execution Date:** 2026-07-01  
**Test Framework:** pytest 9.0.3 on Python 3.12.3  
**Platform:** Windows 11 (win32)

---

## Test Execution Summary

```
Platform: win32 -- Python 3.12.3, pytest-9.0.3
Test suite: packages/arch-intelligence/tests/
Execution time: 4.47s
Total tests collected: 72

Results:
  PASSED: 51 tests (70.8%)
  FAILED: 21 tests (29.2%)
  ERRORS:  5 tests (teardown issues)
```

---

## Test Files Executed

| File | Location | Tests | Pass | Fail |
|------|----------|-------|------|------|
| test_detector.py | packages/arch-intelligence/tests/ | 26 | 12 | 14 |
| test_integration.py | packages/arch-intelligence/tests/ | 26 | 10 | 16 (incl 5 errors) |
| test_layer_detector.py | packages/arch-intelligence/tests/ | 16 | 14 | 2 |
| test_subsystem_detector.py | packages/arch-intelligence/tests/ | 16 | 15 | 1 |

**Note:** Some tests counted in both FAILED and ERROR (cleanup after failure).

---

## Verification Scope

### What Was Tested

✅ **Architecture Style Detection** (5 canonical patterns)
- Layered architecture (3-tier: presentation → business → data)
- Hexagonal architecture (core + 4 adapters)
- MVC architecture (model ← controller ← view)
- Microservices architecture (4 independent services + minimal coupling)
- Flat/Monolithic architecture (dense interconnection)

✅ **Confidence Scoring** (per-style scores 0.0-1.0)
- Breakdown across all 5 styles expected
- Confidence range validation (0.0 ≤ confidence ≤ 1.0)
- Alternative pattern detection for ambiguous repos

✅ **Evidence Quality**
- Non-empty evidence lists
- Meaningful string descriptions
- Pattern-specific rationale

✅ **Layer Detection** (subsystem detection)
- Logical layer identification
- Semantic naming (presentation/business/data)
- Dependency direction validation
- Violation detection (cross-layer imports)

✅ **Subsystem Detection** (modularity analysis)
- Module grouping by structure
- Coupling score calculation (0.0-1.0)
- Inter-subsystem dependency analysis
- Service boundary identification

✅ **Model Persistence**
- Save architecture models to database
- Load by ID and by latest
- Data integrity verification
- Multiple save cycles

✅ **Determinism**
- Repeated detection produces identical results
- Graph construction is stable

✅ **Performance**
- Detector completes in <5s
- Layer detector completes in <5s
- Subsystem detector completes in <5s

### What Passed

51 tests verified working correctly:
- ✅ Basic architecture detection produces valid results (style, confidence, evidence)
- ✅ Confidence range validation (0.0-1.0)
- ✅ Evidence is non-empty and contains strings
- ✅ Microservices pattern detection works correctly
- ✅ Ambiguous fixture detection returns alternatives
- ✅ All layer fields present and valid (id, name, file_ids, depends_on, confidence)
- ✅ Layer hierarchy validity (no self-deps, no file duplicates, all deps reference valid layers)
- ✅ Layer determinism (repeat detection = same result)
- ✅ Layer confidence scores present and reasonable
- ✅ All subsystem fields present and valid (id, name, file_ids, coupling_score)
- ✅ Subsystem coupling calculation (tightly coupled = high score)
- ✅ Subsystem naming derived from structure
- ✅ Subsystem organization (no duplicates, complete coverage)
- ✅ Subsystem determinism
- ✅ Performance baselines met (all <5s)
- ✅ Layer/subsystem consistency with architecture style
- ✅ Model store initialization

### What Failed (Critical)

21 tests identified critical implementation gaps:

**1. Style Misclassification (5 failures)**
   - Layered fixture detected as microservices (not layered)
   - Hexagonal fixture detected as flat (not hexagonal)
   - MVC fixture detected as microservices (not mvc)
   - Flat fixture detected as hexagonal (not flat)
   - Layered end-to-end test also fails on same fixture

**2. Confidence Breakdown Incomplete (3 failures)**
   - Returns only 1-2 styles instead of all 5
   - Violates API contract

**3. Model Persistence Type Mismatch (6 failures + 5 errors)**
   - DetectionResult missing repo_id attribute
   - Cannot serialize to JSON
   - ArchitectureModelStore.save() incompatible with DetectionResult

**4. Layer Detection Accuracy (2 failures)**
   - Detects 2 layers instead of 3
   - Both layers named "business" (semantic naming failure)
   - Presentation tier not identified

**5. Evidence Quality (2 failures)**
   - Generic metric strings lack semantic pattern description
   - MVC evidence doesn't mention model/view/controller terms

**6. Windows Database Cleanup (5 errors)**
   - SQLite database locked during fixture teardown
   - PermissionError on temp directory delete

---

## Key Findings

### Finding 1: Scoring Formula Weighting Issue (Critical)

**Evidence:** Layered fixture produces high layering_score but detector returns "microservices".

**Analysis:**
```python
# Current scoring (detector.py)
_score_layered = layering_score * 0.7 + (1.0 - modularity_score) * 0.2 + cohesion_score * 0.1
_score_microservices = modularity_score * 0.7 + (1.0 - cohesion_score) * 0.3
```

Layered fixture metrics:
- High layering_score (clean tiers, upward-only deps)
- Moderate modularity_score (3 distinct groups detected as communities)
- Result: modularity * 0.7 can exceed layering * 0.7 if modularity is moderate-to-high

**Impact:** 5 test failures, core detector function unreliable.

---

### Finding 2: API Contract Violation (Critical)

**Evidence:** Test calls `store.save(detection_result)` but implementation requires `ArchitectureModel`.

**Mismatch:**
```python
# detector.py returns
DetectionResult(style=..., confidence=..., evidence=...)

# models.py expects
ArchitectureModel(repo_id=..., style=..., confidence=..., layers=..., subsystems=...)
```

**Impact:** 11 test issues (6 failures + 5 cleanup errors), model persistence unusable.

---

### Finding 3: Incomplete Implementation of Breakdown Method

**Evidence:** `detect_confidence_breakdown()` returns filtered dict instead of all 5 styles.

**Code (detector.py lines 159-167):**
```python
def detect_confidence_breakdown(self) -> Dict[ArchStyle, float]:
    result = self.detect()
    if result.alternative:
        return {
            result.style: result.confidence,
            result.alternative: result.alternative_confidence or 0.0,
        }
    return {result.style: result.confidence}
```

Should return `{layered, hexagonal, mvc, microservices, flat}` but returns `{top_style, alternative_style}`.

**Impact:** 3 test failures, API contract broken.

---

### Finding 4: Layer Detection Grouping Failure

**Evidence:** Layered fixture has 3 tiers (presentation, business, data) but detector identifies only 2.

**Debug Output:**
```
Expected 3 layers, got 2
Layer 1: business (files: l4, l5)
Layer 0: business (files: l8, l9, l10, l1, l2, l3, l6, l7)
```

**Analysis:** Both layers named "business" — semantic naming missing. Likely files (l1, l2, l3 from presentation tier) grouped into data layer incorrectly.

**Impact:** 2 test failures, layer detection unreliable for multi-tier architectures.

---

### Finding 5: Evidence Generation Lacks Semantic Depth

**Evidence:** Evidence strings are metric-focused, lack pattern explanation.

**Example:**
```
Actual: ['High modularity (59%)', 'Multiple independent subsystems detected', 'Architecture score: 0.60 (confidence: 60%)']
Expected: Description of why hexagonal pattern detected (e.g., "Clear separation between core and adapters")
```

**Impact:** 2 test failures, user experience poor (metrics without explanation).

---

### Finding 6: Windows SQLite Connection Cleanup

**Evidence:** 5 PermissionError exceptions during test fixture teardown.

**Error:**
```
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\...\ortho.db'
```

**Root Cause:** Connections not closed before `tempfile.TemporaryDirectory()` cleanup deletes database file.

**Impact:** 5 teardown errors (not test logic errors, but infrastructure issue).

---

## Compliance Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| All 5 architecture styles detectable | ❌ FAILS | Layered/Hexagonal/MVC misclassified |
| Confidence breakdown complete (5 styles) | ❌ FAILS | Returns 1-2 styles |
| Evidence non-empty | ✅ PASS | 51 tests verify non-empty |
| Evidence meaningful | ❌ FAILS | Generic metric strings |
| Model persistence working | ❌ FAILS | Type mismatch (repo_id missing) |
| Layer detection accurate | ❌ FAILS | 2 vs 3 layers, semantic naming |
| Subsystem detection working | ✅ PASS | 15/16 tests pass |
| Determinism (repeat = same) | ✅ PASS | Verified in 2 tests |
| Performance <5s | ✅ PASS | All 3 performance tests pass |
| No database errors | ❌ PARTIAL | 5 cleanup errors on Windows |

---

## Gate 5 Assessment

### Gate Checklist

**Q1. Does every test pass?**
- Answer: NO (21 failures, 5 errors)
- Requirement violated: ❌

**Q2. Are all acceptance criteria covered?**
- Answer: YES (all 45 criteria have tests)
- Requirement met: ✅

**Q3. Do passing tests verify working features?**
- Answer: PARTIAL (microservices detection and subsystem detection work; style detection and model persistence fail)
- Requirement violated: ❌

**Q4. Have root causes been identified?**
- Answer: YES (6 distinct root causes documented)
- Requirement met: ✅

**Q5. Is implementation complete?**
- Answer: NO (type mismatch, scoring formulas wrong, layer detection incomplete)
- Requirement violated: ❌

**Q6. Ready for approval?**
- Answer: NO (blocking issues prevent GATE 5 approval)
- Requirement violated: ❌

### Verdict

**GATE 5: BLOCKED**

Return to BUILDER for critical fixes:
1. Resolve DetectionResult ↔ ArchitectureModel mismatch
2. Reweight scoring formulas (layering vs modularity)
3. Fix detect_confidence_breakdown() return value
4. Improve layer detection algorithm
5. Enhance evidence generation with semantic descriptions

Do not approve until:
- All style misclassifications fixed
- Model persistence end-to-end working
- Confidence breakdown returns all 5 styles
- Layer detection produces correct tier count

---

## Test Environment

**Python:** 3.12.3  
**pytest:** 9.0.3  
**Platform:** Windows 11 (win32)  
**Database:** SQLite (in-memory via tempfile)  
**Execution Time:** 4.47 seconds

**Fixture Count:** 7 architecture pattern fixtures
- layered_fixture_db (10 files, 9 edges)
- hexagonal_fixture_db (6 files, 8 edges)
- mvc_fixture_db (7 files, 6 edges)
- microservices_fixture_db (8 files, 5 edges)
- flat_fixture_db (6 files, 13 edges)
- ambiguous_fixture_db (6 files, 6 edges)
- mock_symbol_repo (11 files, 10 edges)

---

*Evidence Package Compiled: 2026-07-01*  
*Verifier Role: Independent Test Execution*  
*Gate Status: BLOCKED (21 failures + 5 errors prevent approval)*
