# Traceability Matrix — task-018-layer-boundaries-noise

| Requirement | Architecture | Code | Tests | Evidence | Status |
|---|---|---|---|---|---|
| Exclude test/example/vendor dirs from layer assignment (spec.md Behavior §1-2) | architecture-review.md: additive filter, no API change | layer_detector.py:6-18,38 | test_layer_detector_exclusions.py::TestIsExcludedHelper (11 tests), TestExtractLayersExclusion (7 tests) | tests_20260715_001816.log (arch-intelligence: 124 passed) | Complete |
| Segment-match not substring-match (production `test_utils.py` not excluded) | architecture-review.md: same contract | layer_detector.py:16-18 | test_production_file_named_test_utils_not_excluded, test_production_dir_testing_helpers_not_excluded, test_production_file_named_test_utils_not_excluded_integration | tests_20260715_001816.log | Complete |
| Import edges to/from excluded files dropped (spec.md Behavior §2) | architecture-review.md: data flow section | layer_detector.py:38,46,50 (existing edge filter, automatically applies to rebuilt file_ids) | test_import_edge_between_excluded_and_included_dropped | tests_20260715_001816.log | Complete |
| All-files-excluded edge case returns [] (spec.md Behavior §4) | N/A | layer_detector.py:40-41 (existing early-exit, now reachable via new filter) | test_all_files_excluded_returns_empty | tests_20260715_001816.log | Complete |
| Existing 8 test_layer_detector.py tests unmodified (spec.md acceptance criteria) | N/A | N/A (regression guard, not new code) | test_layer_detector.py (8 tests, 0 modifications) | tests_20260715_001816.log | Complete |
| Real-repo verification: layer_boundaries reduction on repos/click (spec.md line 77, corrected during TEST-DESIGNER pass) | N/A | N/A | test_click_layer_boundaries_reduced_and_test_paths_absent | tests_20260715_001816.log; manually measured 83->7 this session | Complete |
| mypy --strict on new code | N/A | layer_detector.py:6-18 (new code only) | N/A (type-check, not a test) | mypy_20260715_001816.log | Complete |
| No regression in cli-commands (sole consumer) | architecture-review.md: dependency analysis | N/A | packages/cli-commands/tests (54 tests, unmodified) | tests_20260715_001816.log (cli-commands: 54 passed) | Complete |

## Automatically Detected Gaps

- **Missing implementation:** None.
- **Missing tests:** Minor — 4 adversarial edge cases (leading-slash path, empty string, trailing slash, dotted-substring-but-not-segment) were probed manually during REVIEWER's adversarial pass and confirmed to behave correctly, but are not codified as explicit test assertions in the test suite. Not blocking (behavior verified correct), but a gap in the written test suite itself.
- **Missing verification:** None.
- **Missing review:** None — review.md addresses all requirement rows.
- **Orphaned code:** None — `_EXCLUDED_SEGMENTS`/`_is_excluded` trace directly to spec.md's Behavior section.
- **Untested implementation:** None at the requirement level (see "Missing tests" for the sub-case gap).
- **Acceptance criteria without evidence:** None.
- **Evidence without originating requirement:** None.

## Coverage Summary

- Requirements implemented: 8 / 8
- Requirements tested: 8 / 8 (with 1 minor sub-case gap noted above, not requirement-level)
- Requirements verified: 8 / 8
- Requirements reviewed: 8 / 8
