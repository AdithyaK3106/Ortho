# task-005: Architecture Detection — Verification Report

**Verifier Role:** Independent test execution and evidence capture  
**Test Date:** 2026-07-01  
**Status:** BLOCKED (21 failures, 51 passes, 5 errors)

---

## Executive Summary

Test suite execution completed with **21 FAILED**, **51 PASSED**, **5 ERRORS** out of 72 tests.

**Verdict:** GATE 5 BLOCKED — Critical failures prevent verification approval.

Key blockers:
1. **Scoring Logic Misclassification** — Detector returns wrong architecture style for canonical fixtures (layered → microservices, hexagonal → flat, mvc → microservices)
2. **Incomplete Confidence Breakdown** — Detector only returns single style in breakdown instead of all 5 styles
3. **Model Persistence Type Mismatch** — `DetectionResult` missing `repo_id` attribute required by `ArchitectureModelStore.save()`
4. **Database Cleanup Errors** — SQLite temp files locked on Windows during fixture teardown (5 tests)
5. **Evidence Quality Issues** — Generated evidence strings lack semantic meaning for pattern description

---

## Test Results Summary

| Category | Count | Status |
|----------|-------|--------|
| **Passed** | 51 | ✅ |
| **Failed** | 21 | ❌ |
| **Errors** | 5 | ⚠️ |
| **Total** | 77 | - |

**Note:** Two tests appear in both FAILED and ERROR counts (cleanup failures after assertion failures).

---

## Passing Tests (51 ✅)

### Microservices Detection (2/2)
- ✅ test_microservices_fixture_detects_as_microservices
- ✅ test_microservices_evidence_mentions_modularity

### Low Confidence Handling (2/2)
- ✅ test_ambiguous_fixture_returns_alternative
- ✅ test_confidence_always_in_range

### Evidence Quality Basics (2/3)
- ✅ test_evidence_not_empty_list
- ✅ test_evidence_describes_detection_not_just_metrics
- ❌ test_evidence_contains_meaningful_strings (FAILED)

### Determinism (1/1)
- ✅ test_detect_twice_gives_identical_result

### Integration — Full Detection Flow (1/2)
- ✅ test_full_detection_produces_valid_results
- ❌ test_layered_fixture_end_to_end (FAILED)

### Integration — Evidence Quality (3/4)
- ✅ test_evidence_describes_detection_rationale
- ✅ test_evidence_list_not_empty
- ✅ test_all_evidence_items_strings
- ❌ test_confidence_breakdown_complete (FAILED)

### Integration — Model Persistence (1/7)
- ✅ test_model_store_initialized
- ❌ test_save_and_load_model (FAILED + ERROR)
- ❌ test_load_latest_returns_model (FAILED + ERROR)
- ❌ test_persistence_data_integrity (FAILED + ERROR)
- ❌ test_multiple_saves_overwrites (FAILED + ERROR)
- ❌ test_load_by_model_id (FAILED + ERROR)

### Integration — Performance (3/3)
- ✅ test_detector_completes_quickly
- ✅ test_layer_detector_completes
- ✅ test_subsystem_detector_completes

### Integration — Layer/Subsystem Consistency (4/4)
- ✅ test_layers_consistent_with_style
- ✅ test_violations_detected_when_present
- ✅ test_subsystems_reflect_architecture_style
- ✅ test_coupling_scores_meaningful

### Layer Detector Basics (1/2)
- ✅ test_detect_layers_returns_list_not_empty
- ❌ test_layered_fixture_detects_three_layers (FAILED)

### Layer Field Content (5/5)
- ✅ test_layer_id_is_string
- ✅ test_layer_name_is_semantic
- ✅ test_layer_file_ids_are_nonempty_list
- ✅ test_layer_confidence_in_range
- ✅ test_layer_depends_on_is_list

### Layer Semantic Naming (1/2)
- ✅ test_mvc_fixture_has_view_controller_model
- ❌ test_layered_fixture_has_presentation_business_data (FAILED)

### Layer Violation Detection (2/2)
- ✅ test_violations_returns_list_of_strings
- ✅ test_layered_fixture_has_minimal_violations

### Layer Hierarchy Validity (3/3)
- ✅ test_all_dependencies_reference_valid_layers
- ✅ test_no_self_dependencies
- ✅ test_files_in_single_layer

### Layer Determinism (1/1)
- ✅ test_detect_layers_twice_identical

### Layer Confidence Logic (2/2)
- ✅ test_all_layers_have_confidence
- ✅ test_layered_fixture_layers_have_high_confidence

### Subsystem Detection (3/3)
- ✅ test_detect_subsystems_returns_nonempty_list
- ✅ test_layered_fixture_detects_subsystems
- ✅ test_microservices_fixture_detects_services

### Subsystem Field Content (4/4)
- ✅ test_subsystem_id_is_string
- ✅ test_subsystem_name_is_meaningful
- ✅ test_subsystem_file_ids_nonempty
- ✅ test_coupling_score_is_float_in_range

### Subsystem Coupling Calculation (4/4)
- ✅ test_tightly_coupled_has_high_score
- ✅ test_layered_fixture_has_varied_coupling
- ✅ test_microservices_has_low_intercoupling
- ✅ test_flat_fixture_high_coupling

### Subsystem Naming (2/2)
- ✅ test_names_derived_from_structure
- ✅ test_microservices_names_reflect_services

### Subsystem Organization (2/2)
- ✅ test_no_file_duplicates_across_subsystems
- ✅ test_all_files_in_subsystems

### Subsystem Determinism (1/1)
- ✅ test_detect_twice_identical

### Subsystem Sorting (1/1)
- ✅ test_subsystems_sorted_descending_by_coupling

---

## Failed Tests (21 ❌)

### Category 1: Architecture Style Misclassification (5 failures)

**Symptom:** Detector incorrectly identifies architecture style for canonical fixtures.

#### test_layered_fixture_detects_as_layered
- **Location:** `test_detector.py::TestArchitectureDetectorLayeredPattern`
- **Root Cause:** Detector returns "microservices" instead of "layered"
- **Evidence:** 
  - Fixture has clear 3-tier layering: presentation → business → data
  - All 9 edges are upward (presentation imports business, business imports data)
  - Expected high `layering_score`, but detector scoring logic places microservices higher
- **Expected:** style == "layered"
- **Actual:** style == "microservices"

#### test_hexagonal_fixture_detects_as_hexagonal
- **Location:** `test_detector.py::TestArchitectureDetectorHexagonalPattern`
- **Root Cause:** Detector returns "flat" instead of "hexagonal"
- **Evidence:**
  - Fixture has core (domain + service) + 4 adapters
  - All adapters depend only on core, no cross-adapter dependencies (8 edges total)
  - Detector incorrectly classifies as flat
- **Expected:** style == "hexagonal"
- **Actual:** style == "flat"

#### test_mvc_fixture_detects_as_mvc
- **Location:** `test_detector.py::TestArchitectureDetectorMVCPattern`
- **Root Cause:** Detector returns "microservices" instead of "mvc"
- **Evidence:**
  - Fixture has classic MVC structure: 3 models, 2 controllers, 2 views
  - Views import controllers, controllers import models (6 edges, all upward)
  - Detector misclassifies as microservices
- **Expected:** style == "mvc"
- **Actual:** style == "microservices"

#### test_flat_fixture_detects_as_flat
- **Location:** `test_detector.py::TestArchitectureDetectorFlatPattern`
- **Root Cause:** Detector returns "hexagonal" instead of "flat"
- **Evidence:**
  - Fixture is intentionally flat: 6 files with 13 edges (dense connectivity)
  - Each file imports 2-3 others, no layer structure
  - Detector incorrectly classifies as hexagonal (high cohesion mistaken for adapter pattern)
- **Expected:** style == "flat"
- **Actual:** style == "hexagonal"

#### test_layered_fixture_end_to_end
- **Location:** `test_integration.py::TestEndToEndDetectionFlow`
- **Root Cause:** Same as test_layered_fixture_detects_as_layered
- **Evidence:** Detector returns "microservices" for canonical layered fixture
- **Expected:** style == "layered"
- **Actual:** style == "microservices"

**Analysis:** The detector's scoring formulas are weighting modularity too heavily relative to layering. For layered architecture:
```python
_score_layered = layering_score * 0.7 + (1.0 - modularity_score) * 0.2 + cohesion_score * 0.1
_score_microservices = modularity_score * 0.7 + (1.0 - cohesion_score) * 0.3
```
When layering_score is high but modularity is also moderate (due to 3 distinct groups), microservices score can win. Similar issues affect other patterns.

---

### Category 2: Confidence Breakdown Incomplete (2 failures)

**Symptom:** `detect_confidence_breakdown()` returns only the top style instead of all 5 styles.

#### test_breakdown_includes_all_five_styles
- **Location:** `test_detector.py::TestConfidenceBreakdown`
- **Root Cause:** Implementation returns `{result.style: result.confidence, result.alternative: ...}` instead of all 5 styles
- **Code Issue:** detector.py line 159-167:
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
- **Expected:** Dict with keys {'layered', 'hexagonal', 'mvc', 'microservices', 'flat'}
- **Actual:** Dict with single key {result.style: result.confidence}

#### test_breakdown_scores_sum_meaningfully
- **Location:** `test_detector.py::TestConfidenceBreakdown`
- **Root Cause:** Same as above — only 1-2 styles in breakdown instead of all 5
- **Expected:** All 5 scores present to show differentiation
- **Actual:** Only top 1-2 styles

#### test_confidence_breakdown_complete (integration)
- **Location:** `test_integration.py::TestEvidenceQuality`
- **Root Cause:** Same as above
- **Expected:** All 5 styles in breakdown
- **Actual:** Only top style

**Fix Required:** Return the full `scores` dict (which has all 5 styles) instead of filtered result:
```python
def detect_confidence_breakdown(self) -> Dict[ArchStyle, float]:
    metrics = self._compute_metrics()
    return {
        "layered": self._score_layered(metrics),
        "hexagonal": self._score_hexagonal(metrics),
        "mvc": self._score_mvc(metrics),
        "microservices": self._score_microservices(metrics),
        "flat": self._score_flat(metrics),
    }
```

---

### Category 3: Model Persistence Type Mismatch (6 failures + 5 errors)

**Symptom:** Tests call `store.save(detection_result)` but method expects `ArchitectureModel`.

#### test_save_and_load_model
- **Location:** `test_integration.py::TestArchitectureModelPersistence`
- **Root Cause:** Type mismatch — detector returns `DetectionResult` (has style, confidence, evidence), but store expects `ArchitectureModel` (has repo_id, style, layers, subsystems, etc.)
- **Code Issue:** models.py line 110 accesses `model.repo_id` which doesn't exist on DetectionResult
- **Error:**
  ```
  AttributeError: 'DetectionResult' object has no attribute 'repo_id'
  ```
- **Impact:** 6 tests fail with this error + 5 additional errors during fixture cleanup (database locked on Windows)

#### All Persistence Tests Affected:
- ❌ test_save_and_load_model
- ❌ test_load_latest_returns_model
- ❌ test_persistence_data_integrity
- ❌ test_multiple_saves_overwrites
- ❌ test_load_by_model_id

**Root Cause Analysis:**

`DetectionResult` dataclass (detection_types.py):
```python
@dataclass
class DetectionResult:
    style: ArchStyle
    confidence: float
    evidence: list[str]
    alternative: ArchStyle | None = None
    alternative_confidence: float | None = None
```

`ArchitectureModelStore.save()` expects (models.py):
```python
def save(self, model: "ArchitectureModel") -> str:
    # Tries to serialize model.repo_id, model.layers, model.subsystems
    # DetectionResult doesn't have these fields
```

**Design Breach:** Detector and Store are out of sync. The detector produces a minimal DetectionResult, but tests (and Store) expect a full ArchitectureModel that includes layers, subsystems, and repo_id.

**Fix Options:**
1. Make detector return ArchitectureModel instead of DetectionResult
2. Make store.save() convert DetectionResult → ArchitectureModel internally
3. Split: detector.detect() → DetectionResult, then separate .to_model(repo_id) → ArchitectureModel

---

### Category 4: Layer Detection Accuracy (2 failures)

#### test_layered_fixture_detects_three_layers
- **Location:** `test_layer_detector.py::TestLayerDetectionBasics`
- **Root Cause:** Layer detector returns 2 layers instead of 3
- **Evidence:**
  - Layered fixture has 10 files across 3 logical tiers: presentation (3), business (4), data (3)
  - Detector returns only 2 layers: business (l4, l5) and business again (l8, l9, l10, l1, l2, l3, l6, l7)
  - Both layers named "business" — semantic naming failure
- **Expected:** 3 layers with names ['presentation', 'business', 'data']
- **Actual:** 2 layers both named 'business'

#### test_layered_fixture_has_presentation_business_data
- **Location:** `test_layer_detector.py::TestSemanticNaming`
- **Root Cause:** Layer detector doesn't produce all three semantic layer names
- **Expected:** Layer names include 'presentation', 'business', 'data'
- **Actual:** Only {'business'} found in layer names

**Analysis:** Layer detection logic likely groups files incorrectly based on directory structure or import patterns, missing the presentation tier entirely.

---

### Category 5: Evidence Quality (2 failures)

#### test_evidence_contains_meaningful_strings
- **Location:** `test_detector.py::TestArchitectureDetectorEvidenceQuality`
- **Root Cause:** Evidence strings are too generic/metric-focused, lack semantic meaning
- **Example Failure:** `'High modularity (59%)'` marked as lacking meaningful content
- **Issue:** Evidence should explain WHY the pattern was detected (e.g., "adapters depend only on core" for hexagonal), not just report metrics
- **Expected:** Semantic descriptions of architectural patterns
- **Actual:** Generic metric reporting

#### test_mvc_evidence_mentions_three_layers
- **Location:** `test_detector.py::TestArchitectureDetectorMVCPattern`
- **Root Cause:** Evidence list doesn't mention MVC-specific terms
- **Evidence:** `['High modularity (56%)', 'Multiple independent subsystems detected', 'Architecture score: 0.60 (confidence: 60%)']`
- **Expected:** Evidence includes terms like "model", "view", "controller", "three-tier", or "MVC"
- **Actual:** Generic modularity/subsystems language

---

### Category 6: Windows SQLite Cleanup Issues (5 errors during teardown)

**Symptom:** PermissionError during fixture cleanup on Windows.

#### Error Pattern:
```
PermissionError: [WinError 32] The process cannot access the file because 
it is being used by another process: 'C:\...\ortho.db'
```

**Root Cause:** SQLite database connections not properly closed before tempfile.TemporaryDirectory() cleanup attempts to delete the directory.

**Affected Tests:**
- ERROR: TestArchitectureModelPersistence.test_save_and_load_model (teardown)
- ERROR: TestArchitectureModelPersistence.test_load_latest_returns_model (teardown)
- ERROR: TestArchitectureModelPersistence.test_persistence_data_integrity (teardown)
- ERROR: TestArchitectureModelPersistence.test_multiple_saves_overwrites (teardown)
- ERROR: TestArchitectureModelPersistence.test_load_by_model_id (teardown)

**Fix Required:** conftest.py temp_db fixture must explicitly close database connections:
```python
@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        db = OrthoDatabase(project_root)
        db.migrate()
        yield db
        # Add explicit close
        db.close()  # OR close all open connections
```

---

## Root Cause Summary

| Issue | Severity | Root Cause | Impact |
|-------|----------|-----------|--------|
| Style Misclassification | CRITICAL | Scoring formula weights modularity over layering incorrectly | 5 tests fail, patterns not detected correctly |
| Incomplete Breakdown | HIGH | Method returns filtered results instead of all 5 styles | 3 tests fail, test expectations violated |
| Type Mismatch (repo_id) | CRITICAL | DetectionResult vs ArchitectureModel design mismatch | 6 failures + 5 cleanup errors = 11 test issues |
| Layer Detection (2 vs 3) | MEDIUM | Layer detector algorithm misses presentation tier | 2 tests fail |
| Evidence Quality | MEDIUM | Evidence generation lacks semantic pattern descriptions | 2 tests fail, user experience poor |
| SQLite Cleanup (Windows) | MEDIUM | Database connections not closed before fixture teardown | 5 teardown errors |

---

## Gate 5 Verdict

**STATUS: BLOCKED**

### Blocking Issues (must fix before GATE 5 approval):
1. **Type Mismatch** — Cannot save results to database (repo_id missing)
2. **Style Misclassification** — Core detector logic produces wrong results for canonical fixtures
3. **Incomplete Breakdown** — Violates contract to return all 5 style scores

### Non-Blocking but High Priority:
4. **Layer Detection** — Accuracy issues in layering subsystem
5. **Evidence Quality** — Needs semantic pattern descriptions
6. **Database Cleanup** — Windows-specific fixture issue

### Recommendation:
Return implementation to BUILDER for critical fixes:
1. Resolve DetectionResult vs ArchitectureModel design mismatch
2. Reweight scoring formulas to correctly identify layered architectures
3. Fix detect_confidence_breakdown() to return all 5 styles
4. Improve evidence generation with pattern-specific descriptions
5. Fix layer detector to identify all semantic tiers

Do not approve GATE 5 until all style misclassifications are resolved and model persistence works end-to-end.

---

## Evidence Artifacts Location

Test output log: (captured in session)
- Total tests: 72
- Test files: 4 (test_detector.py, test_integration.py, test_layer_detector.py, test_subsystem_detector.py)
- Passed: 51 (70.8%)
- Failed: 21 (29.2%)
- Errors: 5 (teardown only)

---

*Verification Report Generated: 2026-07-01*
*Verifier: Claude Haiku 4.5 (independent test execution)*
*Status: GATE 5 BLOCKED*
