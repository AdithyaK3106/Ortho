# Evidence Package: task-005 Verification Run

**Generated:** 2026-07-01  
**Role:** VERIFIER (fresh session)  
**Task:** Architecture Intelligence (task-005)  
**Test Suite:** 72 tests across 4 modules

---

## Evidence Summary

This package documents the complete test verification run for task-005. All test output, diagnostics, and failure analysis are included.

**Status:** GATE-5 BLOCKED ❌  
**Pass Rate:** 63/72 (87.5%)  
**Critical Issues:** 9 failing tests indicate fundamental algorithm issues

---

## Test Execution Log

**Framework:** pytest 9.0.3  
**Python:** 3.12.3  
**Platform:** Windows 11  
**Execution Time:** 3.88 seconds

### Full Test Output

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0

collected 72 items

packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_fixture_detects_as_layered FAILED [  1%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_confidence_breakdown_shows_layered_highest FAILED [  2%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_evidence_mentions_layers_and_upward_deps PASSED [  4%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorHexagonalPattern::test_hexagonal_fixture_detects_as_hexagonal PASSED [  5%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorHexagonalPattern::test_hexagonal_confidence_breakdown_shows_hexagonal_highest PASSED [  6%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorMVCPattern::test_mvc_fixture_detects_as_mvc PASSED [  8%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorMVCPattern::test_mvc_evidence_mentions_three_layers PASSED [  9%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorMicroservicesPattern::test_microservices_fixture_detects_as_microservices FAILED [ 11%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorMicroservicesPattern::test_microservices_evidence_mentions_modularity PASSED [ 12%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorFlatPattern::test_flat_fixture_detects_as_flat FAILED [ 13%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorFlatPattern::test_flat_evidence_mentions_interconnection PASSED [ 15%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLowConfidenceHandling::test_ambiguous_fixture_returns_alternative FAILED [ 16%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLowConfidenceHandling::test_confidence_always_in_range PASSED [ 18%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorEvidenceQuality::test_evidence_not_empty_list PASSED [ 19%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorEvidenceQuality::test_evidence_contains_meaningful_strings FAILED [ 20%]
packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorEvidenceQuality::test_evidence_describes_detection_not_just_metrics PASSED [ 22%]
packages\arch-intelligence\tests\test_detector.py::TestConfidenceBreakdown::test_breakdown_includes_all_five_styles PASSED [ 23%]
packages\arch-intelligence\tests\test_detector.py::TestConfidenceBreakdown::test_breakdown_scores_sum_meaningfully PASSED [ 25%]
packages\arch-intelligence\tests\test_detector.py::TestDeterminism::test_detect_twice_gives_identical_result PASSED [ 26%]
packages\arch-intelligence\tests\test_integration.py::TestEndToEndDetectionFlow::test_full_detection_produces_valid_results PASSED [ 27%]
packages\arch-intelligence\tests\test_integration.py::TestEndToEndDetectionFlow::test_layered_fixture_end_to_end FAILED [ 29%]
packages\arch-intelligence\tests\test_integration.py::TestEvidenceQuality::test_evidence_describes_detection_rationale PASSED [ 30%]
packages\arch-intelligence\tests\test_integration.py::TestEvidenceQuality::test_evidence_list_not_empty PASSED [ 31%]
packages\arch-intelligence\tests\test_integration.py::TestEvidenceQuality::test_all_evidence_items_strings PASSED [ 33%]
packages\arch-intelligence\tests\test_integration.py::TestEvidenceQuality::test_confidence_breakdown_complete PASSED [ 34%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_model_store_initialized PASSED [ 36%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_save_and_load_model PASSED [ 37%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_load_latest_returns_model PASSED [ 38%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_persistence_data_integrity PASSED [ 40%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_multiple_saves_overwrites PASSED [ 41%]
packages\arch-intelligence\tests\test_integration.py::TestArchitectureModelPersistence::test_load_by_model_id PASSED [ 43%]
packages\arch-intelligence\tests\test_integration.py::TestPerformanceBasics::test_detector_completes_quickly PASSED [ 44%]
packages\arch-intelligence\tests\test_integration.py::TestPerformanceBasics::test_layer_detector_completes PASSED [ 47%]
packages\arch-intelligence\tests\test_integration.py::TestPerformanceBasics::test_subsystem_detector_completes PASSED [ 47%]
packages\arch-intelligence\tests\test_integration.py::TestLayerDetectorIntegration::test_layers_consistent_with_style PASSED [ 48%]
packages\arch-intelligence\tests\test_integration.py::TestLayerDetectorIntegration::test_violations_detected_when_present PASSED [ 50%]
packages\arch-intelligence\tests\test_integration.py::TestSubsystemDetectorIntegration::test_subsystems_reflect_architecture_style PASSED [ 51%]
packages\arch-intelligence\tests\test_integration.py::TestSubsystemDetectorIntegration::test_coupling_scores_meaningful PASSED [ 52%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerDetectionBasics::test_detect_layers_returns_list_not_empty PASSED [ 54%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerDetectionBasics::test_layered_fixture_detects_three_layers PASSED [ 55%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerFieldContent::test_layer_id_is_string PASSED [ 56%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerFieldContent::test_layer_name_is_semantic PASSED [ 58%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerFieldContent::test_layer_file_ids_are_nonempty_list PASSED [ 59%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerFieldContent::test_layer_confidence_in_range PASSED [ 61%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerFieldContent::test_layer_depends_on_is_list PASSED [ 62%]
packages\arch-intelligence\tests\test_layer_detector.py::TestSemanticNaming::test_layered_fixture_has_presentation_business_data FAILED [ 63%]
packages\arch-intelligence\tests\test_layer_detector.py::TestSemanticNaming::test_mvc_fixture_has_view_controller_model PASSED [ 65%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerViolationDetection::test_violations_returns_list_of_strings PASSED [ 66%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerViolationDetection::test_layered_fixture_has_minimal_violations FAILED [ 68%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerHierarchyValidity::test_all_dependencies_reference_valid_layers PASSED [ 69%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerHierarchyValidity::test_no_self_dependencies PASSED [ 70%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerHierarchyValidity::test_files_in_single_layer PASSED [ 72%]
packages\arch-intelligence\tests\test_layer_detector.py::TestDeterminism::test_detect_layers_twice_identical PASSED [ 73%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerConfidenceLogic::test_all_layers_have_confidence PASSED [ 75%]
packages\arch-intelligence\tests\test_layer_detector.py::TestLayerConfidenceLogic::test_layered_fixture_layers_have_high_confidence PASSED [ 76%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemDetectionBasics::test_detect_subsystems_returns_nonempty_list PASSED [ 77%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemDetectionBasics::test_layered_fixture_detects_subsystems PASSED [ 79%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemDetectionBasics::test_microservices_fixture_detects_services PASSED [ 80%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemFieldContent::test_subsystem_id_is_string PASSED [ 81%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemFieldContent::test_subsystem_name_is_meaningful PASSED [ 83%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemFieldContent::test_subsystem_file_ids_nonempty PASSED [ 84%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemFieldContent::test_coupling_score_is_float_in_range PASSED [ 86%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestCouplingCalculation::test_tightly_coupled_has_high_score PASSED [ 87%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestCouplingCalculation::test_layered_fixture_has_varied_coupling PASSED [ 88%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestCouplingCalculation::test_microservices_has_low_intercoupling PASSED [ 90%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestCouplingCalculation::test_flat_fixture_high_coupling PASSED [ 91%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemNaming::test_names_derived_from_structure PASSED [ 93%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemNaming::test_microservices_names_reflect_services PASSED [ 94%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemOrganization::test_no_file_duplicates_across_subsystems PASSED [ 95%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemOrganization::test_all_files_in_subsystems PASSED [ 97%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestDeterminism::test_detect_twice_identical PASSED [ 98%]
packages\arch-intelligence\tests\test_subsystem_detector.py::TestSubsystemSorting::test_subsystems_sorted_descending_by_coupling PASSED [100%]

================================== FAILURES ===================================
_ TestArchitectureDetectorLayeredPattern.test_layered_fixture_detects_as_layered _
packages\arch-intelligence\tests\test_detector.py:26: in test_layered_fixture_detects_as_layered
    assert result.style == "layered", f"Expected 'layered', got '{result.style}'"
E   AssertionError: Expected 'layered', got 'mvc'
E   assert 'mvc' == 'layered'
E     
E     - layered
E     + mvc

_ TestArchitectureDetectorLayeredPattern.test_layered_confidence_breakdown_shows_layered_highest _
packages\arch-intelligence\tests\test_detector.py:40: in test_layered_confidence_breakdown_shows_layered_highest
    AssertionError: Layered (0.5411851851851851) should beat hex/mvc/micro/flat
E   assert (0.5411851851851851 >= 0.1 and 0.5411851851851851 >= 0.891179012345679)

_ TestArchitectureDetectorMicroservicesPattern.test_microservices_fixture_detects_as_microservices _
packages\arch-intelligence\tests\test_detector.py:115: in test_microservices_fixture_detects_as_microservices
    AssertionError: Expected 'microservices', got 'layered'
E   assert 'layered' == 'microservices'
E     
E     - microservices
E     + layered

____ TestArchitectureDetectorFlatPattern.test_flat_fixture_detects_as_flat ____
packages\arch-intelligence\tests\test_detector.py:140: in test_flat_fixture_detects_as_flat
    AssertionError: Expected 'flat', got 'layered'
E   assert 'layered' == 'flat'
E     
E     - flat
E     + layered

_ TestArchitectureDetectorLowConfidenceHandling.test_ambiguous_fixture_returns_alternative _
packages\arch-intelligence\tests\test_detector.py:166: in test_ambiguous_fixture_returns_alternative
    AssertionError: Ambiguous fixture must suggest alternative
E   assert None is not None
E    +  where None = DetectionResult(style='mvc', confidence=0.9212777777777778, alternative=None, alternative_confidence=None)

_ TestArchitectureDetectorEvidenceQuality.test_evidence_contains_meaningful_strings _
packages\arch-intelligence\tests\test_detector.py:212: in test_evidence_contains_meaningful_strings
    AssertionError: Evidence item lacks meaningful content: 'Clear tier separation (presentation → business → data)'
E   assert False

_ TestEndToEndDetectionFlow.test_layered_fixture_end_to_end _
packages\arch-intelligence\tests\test_integration.py:58: in test_layered_fixture_end_to_end
    AssertionError: Expected layered, got mvc
E   assert 'layered' == 'mvc'
E     
E     - layered
E     + mvc

___ TestSemanticNaming.test_layered_fixture_has_presentation_business_data ____
packages\arch-intelligence\tests\test_layer_detector.py:138: in test_layered_fixture_has_presentation_business_data
    AssertionError: Expected presentation/business/data, got {'business', 'data'}
E   assert (False)

___ TestLayerViolationDetection.test_layered_fixture_has_minimal_violations ___
packages\arch-intelligence\tests\test_layer_detector.py:173: in test_layered_fixture_has_minimal_violations
    AssertionError: Strict layered should have ≤1 violations, got 9
E   assert 9 <= 1
E    +  where 9 = len(['data imports business (cross-layer)', 'data imports business (cross-layer)', ...])

================================ short test summary info =========================
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_fixture_detects_as_layered
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_confidence_breakdown_shows_layered_highest
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorMicroservicesPattern::test_microservices_fixture_detects_as_microservices
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorFlatPattern::test_flat_fixture_detects_as_flat
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorLowConfidenceHandling::test_ambiguous_fixture_returns_alternative
FAILED packages\arch-intelligence\tests\test_detector.py::TestArchitectureDetectorEvidenceQuality::test_evidence_contains_meaningful_strings
FAILED packages\arch-intelligence\tests\test_integration.py::TestEndToEndDetectionFlow::test_layered_fixture_end_to_end
FAILED packages\arch-intelligence\tests\test_layer_detector.py::TestSemanticNaming::test_layered_fixture_has_presentation_business_data
FAILED packages\arch-intelligence\tests\test_layer_detector.py::TestLayerViolationDetection::test_layered_fixture_has_minimal_violations
======================== 9 failed, 63 passed in 3.88s =========================
```

---

## Diagnostic Run Output

A separate diagnostic script was run to understand the metrics for the layered fixture:

```
Layering score: 1.0
Cohesion score: 0.26666666666666666
Modularity score: 0.5324074074074074
Topological levels: {'l8': 0, 'l9': 0, 'l10': 0, 'l4': 1, 'l5': 1, 'l6': 1, 'l7': 1, 'l1': 2, 'l2': 2, 'l3': 2}
Tier count: 3
Files per tier: 3.3333333333333335
Hub score: 0.4166666666666667
Confidence breakdown:
  layered: 0.5460555555555555
  hexagonal: 0.1
  mvc: 0.9125995370370369
  microservices: 0.34958333333333336
  flat: 0.18703703703703703
Detected style: mvc
Confidence: 0.9125995370370369
```

**Key Finding:** The canonical "layered" fixture with:
- Perfect layering (1.0)
- Exactly 3 tiers
- ~3.3 files per tier

...is being detected as **MVC (0.912)** instead of **Layered (0.546)**.

---

## Test Files Location

All test files are in: `packages/arch-intelligence/tests/`

- `test_detector.py` — Architecture style detection tests
- `test_integration.py` — End-to-end integration tests
- `test_layer_detector.py` — Layer detection and violation tests
- `test_subsystem_detector.py` — Subsystem detection tests
- `conftest.py` — Pytest fixtures and test DB setup

---

## Implementation Files Under Test

- `packages/arch-intelligence/src/detector.py` — Style detection scoring
- `packages/arch-intelligence/src/layer_detector.py` — Layer extraction
- `packages/arch-intelligence/src/subsystem_detector.py` — Subsystem clustering
- `packages/arch-intelligence/src/graph_utils.py` — Metrics computation
- `packages/arch-intelligence/src/detection_types.py` — Data structures

---

## Critical Code Sections Identified

### Issue 1: Layered/MVC Threshold Bug
**File:** `packages/arch-intelligence/src/detector.py` (lines 131–154)

```python
def _score_layered(self, metrics: DetectionMetrics) -> float:
    """Score layered architecture (most common pattern)."""
    layered_base = (
        metrics.layering_score * 0.85
        + (1.0 - metrics.modularity_score) * 0.10
        + metrics.cohesion_score * 0.05
    )

    # PROBLEM: This penalty triggers for valid layered architectures
    files_per_tier = self._files_per_tier()
    tier_count = self._tier_count()
    if tier_count == 3 and files_per_tier < 3.5:
        layered_base *= 0.6  # Likely MVC, not layered ← WRONG
    
    # ... more code ...
    return layered_base

def _score_mvc(self, metrics: DetectionMetrics) -> float:
    """Score MVC architecture."""
    tier_count = self._tier_count()
    
    # ... validation ...
    
    mvc_base = (
        metrics.layering_score * 0.65
        + (1.0 - metrics.modularity_score) * 0.25
        + metrics.cohesion_score * 0.10
    )

    # PROBLEM: This bonus makes MVC win even with perfect layering
    if tier_count == 3:
        mvc_base *= 1.15  # ← ALWAYS triggers for 3-tier
    
    return min(1.0, mvc_base)
```

**Impact:** Layered gets penalized to 0.546, MVC boosted to 0.912. MVC wins despite layering_score being 1.0.

---

### Issue 2: Inverted Violation Logic
**File:** `packages/arch-intelligence/src/layer_detector.py`

The `detect_violations()` function treats upward dependencies as violations, when they should be flagged for downward/cross-layer edges only.

---

### Issue 3: Layer Naming Gap
**File:** `packages/arch-intelligence/src/layer_detector.py`

The layer naming heuristics fail to detect "presentation" layer in 3-tier structures, returning only {'business', 'data'}.

---

### Issue 4: Evidence String Validation
**File:** `packages/arch-intelligence/src/detector.py` (line 242)

```python
evidence.append("Clear tier separation (presentation → business → data)")
```

The Unicode arrow (→) may fail the test's meaningful content check.

---

## Test Design Assessment

All tests are well-designed and correctly specify the expected behavior:

1. **Detector tests** correctly expect canonical fixtures to detect as their pattern type
2. **Layer detector tests** correctly expect valid layer hierarchies with minimal violations
3. **Integration tests** correctly verify end-to-end flows
4. **Evidence tests** correctly validate that detection has meaningful justification

**Conclusion:** Tests are CORRECT. The implementation has bugs, not the tests.

---

## Recommendations for BUILDER

1. **Primary fix:** Adjust the layered/MVC decision boundary
   - Option A: Remove or raise the `files_per_tier < 3.5` threshold
   - Option B: Add a secondary check: if `layering_score > 0.9`, always prefer layered
   - Option C: Change the bonus/penalty magnitudes (use 1.05x vs 0.6x)

2. **Secondary fix:** Invert violation detection logic
   - Violations should be downward edges only

3. **Tertiary fix:** Debug layer naming heuristics
   - Ensure "presentation" layer is detected

4. **Quality fix:** Use ASCII in evidence strings
   - Replace `→` with `->`

---

## Checklist for Re-verification

After BUILDER applies fixes:

- [ ] Run `pytest packages/arch-intelligence/tests/ -v`
- [ ] Expect 72/72 passing
- [ ] Re-run diagnostics on layered fixture (should get 1.0 for layered score)
- [ ] Verify all 5 architecture styles detect correctly
- [ ] Check layer names include presentation/business/data
- [ ] Confirm violations count ≤ 1 for strict layered architecture
- [ ] Validate evidence strings pass meaningful content check
- [ ] Re-run determinism tests (ensure reproducibility)

---

**Package Generated:** 2026-07-01  
**Verification Complete:** No approval given — GATE-5 BLOCKED  
**Status:** Awaiting BUILDER fixes and re-verification
