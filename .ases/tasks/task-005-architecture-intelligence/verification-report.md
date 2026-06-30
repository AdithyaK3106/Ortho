# Verification Report: task-005 (Architecture Intelligence)

**Task:** Detect architecture patterns (layered, hexagonal, MVC, microservices, flat)  
**Date:** 2026-07-01  
**Role:** VERIFIER (fresh context)  
**Test Framework:** pytest 9.0.3 on Python 3.12.3

---

## Executive Summary

**GATE-5: BLOCKED** ❌

**Overall Result:** 63 passing, 9 failing out of 72 tests (87.5% pass rate)

**Critical Issue:** Scoring algorithm incorrectly penalizes valid layered architectures when they have 3 tiers with ~3 files per tier, causing them to be misclassified as MVC instead.

---

## Test Results Summary

| Category | Count | Status |
|----------|-------|--------|
| **Passing** | 63 | ✅ |
| **Failing** | 9 | ❌ |
| **Total** | 72 | |

**Pass Rate:** 87.5%  
**Execution Time:** 3.88 seconds

---

## Detailed Test Results

### Passing Tests (63) ✅

**Core Functionality:**
- ✅ test_layered_evidence_mentions_layers_and_upward_deps
- ✅ test_hexagonal_fixture_detects_as_hexagonal
- ✅ test_hexagonal_confidence_breakdown_shows_hexagonal_highest
- ✅ test_mvc_fixture_detects_as_mvc
- ✅ test_mvc_evidence_mentions_three_layers
- ✅ test_microservices_evidence_mentions_modularity
- ✅ test_flat_evidence_mentions_interconnection
- ✅ test_confidence_always_in_range
- ✅ test_evidence_not_empty_list
- ✅ test_evidence_describes_detection_not_just_metrics
- ✅ test_breakdown_includes_all_five_styles
- ✅ test_breakdown_scores_sum_meaningfully
- ✅ test_detect_twice_gives_identical_result

**Integration Tests:**
- ✅ test_full_detection_produces_valid_results
- ✅ test_evidence_describes_detection_rationale
- ✅ test_evidence_list_not_empty
- ✅ test_all_evidence_items_strings
- ✅ test_confidence_breakdown_complete
- ✅ test_model_store_initialized
- ✅ test_save_and_load_model
- ✅ test_load_latest_returns_model
- ✅ test_persistence_data_integrity
- ✅ test_multiple_saves_overwrites
- ✅ test_load_by_model_id
- ✅ test_detector_completes_quickly
- ✅ test_layer_detector_completes
- ✅ test_subsystem_detector_completes
- ✅ test_layers_consistent_with_style
- ✅ test_violations_detected_when_present
- ✅ test_subsystems_reflect_architecture_style
- ✅ test_coupling_scores_meaningful

**Layer Detector:**
- ✅ test_detect_layers_returns_list_not_empty
- ✅ test_layered_fixture_detects_three_layers
- ✅ test_layer_id_is_string
- ✅ test_layer_name_is_semantic
- ✅ test_layer_file_ids_are_nonempty_list
- ✅ test_layer_confidence_in_range
- ✅ test_layer_depends_on_is_list
- ✅ test_mvc_fixture_has_view_controller_model
- ✅ test_violations_returns_list_of_strings
- ✅ test_all_dependencies_reference_valid_layers
- ✅ test_no_self_dependencies
- ✅ test_files_in_single_layer
- ✅ test_detect_layers_twice_identical
- ✅ test_all_layers_have_confidence
- ✅ test_layered_fixture_layers_have_high_confidence

**Subsystem Detector:**
- ✅ test_detect_subsystems_returns_nonempty_list
- ✅ test_layered_fixture_detects_subsystems
- ✅ test_microservices_fixture_detects_services
- ✅ test_subsystem_id_is_string
- ✅ test_subsystem_name_is_meaningful
- ✅ test_subsystem_file_ids_nonempty
- ✅ test_coupling_score_is_float_in_range
- ✅ test_tightly_coupled_has_high_score
- ✅ test_layered_fixture_has_varied_coupling
- ✅ test_microservices_has_low_intercoupling
- ✅ test_flat_fixture_high_coupling
- ✅ test_names_derived_from_structure
- ✅ test_microservices_names_reflect_services
- ✅ test_no_file_duplicates_across_subsystems
- ✅ test_all_files_in_subsystems
- ✅ test_detect_twice_identical
- ✅ test_subsystems_sorted_descending_by_coupling

---

### Failing Tests (9) ❌

#### CRITICAL: Pattern Detection Misclassification

**1. test_layered_fixture_detects_as_layered**
```
FAILED: Expected 'layered', got 'mvc'
File: packages/arch-intelligence/tests/test_detector.py:26
```
**Root Cause:** Layered fixture has:
- Layering score: 1.0 (perfect)
- Tier count: 3
- Files per tier: 3.33

The `_score_layered()` function (detector.py:144) applies a 0.6x penalty when `tier_count == 3 AND files_per_tier < 3.5`, treating this as "too small to be layered". However, 3.33 files/tier IS valid for layered architecture.

Meanwhile, `_score_mvc()` gets a 1.15x bonus for exactly 3 tiers, pushing it to 0.912 > 0.546.

**Severity:** BLOCKING - Fundamental misclassification

---

**2. test_layered_confidence_breakdown_shows_layered_highest**
```
FAILED: Layered (0.541) should beat mvc/hex/micro/flat
Expected: layered_score >= all others
Got: layered_score (0.541) < mvc_score (0.912)
File: packages/arch-intelligence/tests/test_detector.py:40
```
**Root Cause:** Same as #1 — layered is penalized, MVC is boosted.

**Severity:** BLOCKING - Confidence ordering broken

---

**3. test_microservices_fixture_detects_as_microservices**
```
FAILED: Expected 'microservices', got 'layered'
File: packages/arch-intelligence/tests/test_detector.py:115
```
**Root Cause:** Microservices fixture has high modularity but also high layering_score. The penalty in `_score_microservices()` at line 223 (`if metrics.layering_score > 0.6: microservices_base *= 0.6`) is too aggressive, causing it to lose to layered even when it should win on modularity.

**Severity:** BLOCKING - Misclassification

---

**4. test_flat_fixture_detects_as_flat**
```
FAILED: Expected 'flat', got 'layered'
File: packages/arch-intelligence/tests/test_detector.py:140
```
**Root Cause:** Flat architecture (heavily interconnected) is incorrectly detected as layered. Layering score calculation is not distinguishing flat from layered properly.

**Severity:** BLOCKING - Misclassification

---

**5. test_ambiguous_fixture_returns_alternative**
```
FAILED: Ambiguous fixture must suggest alternative
Expected: alternative is not None
Got: alternative = None
File: packages/arch-intelligence/tests/test_detector.py:166
```
**Root Cause:** The ambiguous fixture (0.92 MVC, 0.89 hexagonal) has a gap of only 0.03, which SHOULD trigger the alternative suggestion (threshold is 0.15 at line 59 of detector.py). However, the result shows MVC won cleanly without alternative. The fixture scoring is not close enough to trigger ambiguity.

**Severity:** BLOCKING - Edge case handling broken

---

**6. test_evidence_contains_meaningful_strings**
```
FAILED: Evidence item lacks meaningful content
Evidence: 'Clear tier separation (presentation → business → data)'
File: packages/arch-intelligence/tests/test_detector.py:212
```
**Root Cause:** The test checks evidence strings for "meaningful content" (non-empty, no newlines, etc.). The Unicode arrow (→) in the evidence string may be failing the validation check in the test's `_is_meaningful()` helper. This is a TEST issue, not necessarily a CODE issue, but it indicates the evidence generation needs refinement.

**Severity:** MEDIUM - Non-blocking but indicates poor evidence quality

---

**7. test_layered_fixture_end_to_end**
```
FAILED: Expected layered, got mvc
File: packages/arch-intelligence/tests/test_integration.py:58
```
**Root Cause:** Same as #1 — end-to-end flow includes the broken layered vs. MVC scoring.

**Severity:** BLOCKING - Integration test failure

---

**8. test_layered_fixture_has_presentation_business_data**
```
FAILED: Expected presentation/business/data, got {'business', 'data'}
Expected: 3 layers with those names
Got: Only 2 layer names detected
File: packages/arch-intelligence/tests/test_layer_detector.py:138
```
**Root Cause:** The layer detector is missing the "presentation" layer or mislabeling it. This could be a naming/detection issue in `detect_layers()` logic.

**Severity:** BLOCKING - Layer detection incomplete

---

**9. test_layered_fixture_has_minimal_violations**
```
FAILED: Expected ≤1 violations, got 9
Violations: 9 cross-layer imports detected
File: packages/arch-intelligence/tests/test_layer_detector.py:173
```
**Root Cause:** The violation detector is seeing 9 upward dependencies (business→data, data→business) as violations, even though these are CORRECT layered dependencies. The `detect_violations()` logic is too strict — it's treating ALL upward dependencies as violations instead of only flagging DOWNWARD (reverse) dependencies.

**Severity:** BLOCKING - Violation detection logic inverted

---

## Root Cause Analysis

### Problem 1: Layered vs. MVC Confusion (5 failures)
**Files:** `packages/arch-intelligence/src/detector.py` (lines 131–154)

The problem: When a repository has exactly 3 tiers with ~3-4 files per tier, it triggers the "likely MVC" penalty (0.6x) in `_score_layered()`, while `_score_mvc()` gets a 1.15x bonus for exactly 3 tiers. This causes valid layered architectures to be misclassified as MVC.

**Current logic (line 144):**
```python
if tier_count == 3 and files_per_tier < 3.5:
    layered_base *= 0.6  # Likely MVC, not layered
```

**Why it's wrong:** MVC also has 3 tiers AND can have ~2-4 files per tier. The threshold is arbitrary and doesn't account for the fact that layered architecture OFTEN has 3 tiers (presentation/business/data).

**Diagnostic metrics from actual fixture:**
- Layering score: 1.0 (perfect upward deps)
- Files per tier: 3.33 (well within layered range)
- But penalized to 0.546, while MVC boosted to 0.912

---

### Problem 2: Violation Detection Inverted (1 failure)
**Files:** `packages/arch-intelligence/src/layer_detector.py`

The `detect_violations()` function is treating upward dependencies (correct behavior) as violations. It should only flag:
- Downward edges (lower tier importing higher tier)
- Cross-layer edges that skip tiers

Instead, it's flagging ALL layer transitions as violations.

---

### Problem 3: Evidence Quality (1 failure)
**Files:** `packages/arch-intelligence/src/detector.py` (line 242)

The evidence string contains a Unicode arrow (→) that may fail regex validation in the test. Simple fix: use ASCII representation.

---

### Problem 4: Layer Naming (1 failure)
**Files:** `packages/arch-intelligence/src/layer_detector.py`

The layer naming logic is not detecting "presentation" layer correctly. The fixture clearly has presentation/business/data layers, but only business/data are being named.

---

## Verdict

**GATE-5: BLOCKED** ❌

**Reason:** 9 failing tests represent fundamental issues in the architecture detection algorithm:
1. **Core scoring breaks layered/MVC distinction** (5 failures)
2. **Violation detection logic is inverted** (1 failure)
3. **Layer naming incomplete** (1 failure)
4. **Evidence quality issue** (1 failure)
5. **Edge case handling broken** (1 failure)

These are not edge cases or fine-tuning issues — they break the core functionality of the detector. A layered architecture should detect as "layered", not "mvc".

---

## Failing Tests Summary

```
FAILED test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_fixture_detects_as_layered
FAILED test_detector.py::TestArchitectureDetectorLayeredPattern::test_layered_confidence_breakdown_shows_layered_highest
FAILED test_detector.py::TestArchitectureDetectorMicroservicesPattern::test_microservices_fixture_detects_as_microservices
FAILED test_detector.py::TestArchitectureDetectorFlatPattern::test_flat_fixture_detects_as_flat
FAILED test_detector.py::TestArchitectureDetectorLowConfidenceHandling::test_ambiguous_fixture_returns_alternative
FAILED test_detector.py::TestArchitectureDetectorEvidenceQuality::test_evidence_contains_meaningful_strings
FAILED test_integration.py::TestEndToEndDetectionFlow::test_layered_fixture_end_to_end
FAILED test_layer_detector.py::TestSemanticNaming::test_layered_fixture_has_presentation_business_data
FAILED test_layer_detector.py::TestLayerViolationDetection::test_layered_fixture_has_minimal_violations
```

---

## Required Fixes

### High Priority (Blocking)

1. **Adjust layered/MVC threshold** (detector.py:144)
   - Change `files_per_tier < 3.5` to `files_per_tier < 2.5` or remove the penalty entirely
   - Reduce MVC bonus from 1.15x to 1.05x to avoid over-boosting
   - Consider layering_score as primary differentiator (layered = 1.0, MVC ≤ 0.9)

2. **Fix violation detection** (layer_detector.py)
   - Invert logic: only flag DOWNWARD edges as violations, not upward
   - A violation = edge from lower tier to higher tier (wrong direction)

3. **Fix layer naming** (layer_detector.py)
   - Ensure "presentation" layer is detected in 3-tier structures
   - Check the layer naming heuristics for all tiers

4. **Fix microservices penalty** (detector.py:223)
   - Reduce penalty from 0.6x to 0.85x, or make it conditional on other factors
   - Microservices with high layering should still be detectable if modularity is strong

### Medium Priority (Quality)

5. **Fix evidence formatting** (detector.py:242)
   - Replace Unicode arrow (→) with ASCII (->)
   - Ensure all evidence strings pass meaningful content validation

6. **Fix ambiguity detection** (detector.py)
   - Review ambiguous fixture scoring
   - Ensure close calls (gap < 0.15) trigger alternative suggestions

---

## Next Steps for BUILDER

1. **Do NOT proceed** until GATE-5 is APPROVED
2. Apply fixes in this order: violations → layer naming → layered/MVC scoring
3. Re-run full test suite after each fix
4. Verify all 72 tests pass before requesting re-verification
5. Ensure evidence quality passes validation

---

**Report Generated:** 2026-07-01  
**Verifier:** VERIFIER (fresh context, task-005)  
**Evidence Location:** Test output logged in pytest-output.log  
**Recommendation:** BLOCKED — Return to BUILDER for critical fixes
