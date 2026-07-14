# Test Plan: task-018-layer-boundaries-noise

## Unit Tests Per Acceptance Criterion (spec.md's 12+ case table)

All 12 cases from spec.md's table are covered, plus the mandatory real-repo
verification (added during TEST-DESIGNER review — see "Gap Found and Fixed"
below):

- test_tests_dir_excluded
- test_test_dir_singular_excluded
- test_examples_dir_excluded
- test_example_dir_singular_excluded
- test_nested_tests_dir_excluded
- test_production_file_named_test_utils_not_excluded
- test_production_dir_testing_helpers_not_excluded
- test_case_insensitive_match
- test_dunder_tests_dir_excluded
- test_vendor_dir_excluded (bonus, beyond spec table's explicit list but named in spec's exclusion set)
- test_production_file_no_match
- test_test_file_excluded_from_layers (integration)
- test_example_file_excluded_from_layers (integration)
- test_all_files_excluded_returns_empty (edge case)
- test_mixed_production_and_test_files (core integration case)
- test_import_edge_between_excluded_and_included_dropped (edge-filtering verification)
- test_production_file_named_test_utils_not_excluded_integration
- test_existing_behavior_unchanged_for_pure_production_input (regression guard)
- **test_click_layer_boundaries_reduced_and_test_paths_absent (real-repo, mandatory)**

## Gap Found and Fixed (genuine TEST-DESIGNER value)

spec.md's real-repo test row (line 77) asserted the expected count as
`layer_boundaries == 0`, written before the fix was actually measured. The
existing test file (written during BUILDER's own verification pass) did
not include this mandatory real-repo test at all — a real coverage gap.

Adding it exposed a second bug, this time in the **test itself**: an
initial naive `"test" in v.location.lower()` substring check incorrectly
flagged `src.click.testing` (a real production module — `click`'s
`CliRunner` testing utilities, shipped as part of the library, not a test
file) as a false-positive-pattern violation, because the module's *name*
happens to contain "test". This would have made the test lie about what
it verifies. Fixed by matching spec.md's actual rule precisely: check the
first dotted segment of the module path against the exclusion set
(`tests`, `test`, `examples`, `example`), not a bare substring search.

This is exactly the kind of assumption-testing TEST-DESIGNER exists to
catch — the fix code was correct; a naive verification test would have
been wrong in a way that happened to still pass on this data.

## Real-Repo Scan Test (mandatory)

`test_click_layer_boundaries_reduced_and_test_paths_absent` runs the full
real `guardrails` pipeline (`scan_repository` → `ArchModelAdapter` →
`DependencyGraphAdapter` → `CodeMetricsAdapter` → `ArchitectureEnforcer`)
against `repos/click`, asserting:
1. Zero `layer_boundaries` violations reference a module rooted at
   `tests`/`test`/`examples`/`example` (the exact pattern this task fixes).
2. Total `layer_boundaries` count is bounded well below the pre-fix
   baseline of 83 (confirms the fix is active, not a silent no-op).

Deliberately does NOT assert `== 0` (spec.md's pre-measurement expectation)
since the actual, human-approved-as-out-of-scope remaining pattern
(leaf/utility module mislabeling) means 0 is not the correct current
target — asserting it would make the test fail for a reason unrelated to
this task's fix.

## Edge Cases Covered
Empty exclusion set membership check, nested paths, case sensitivity,
all-files-excluded, mixed production/test/example input, edge-dropping
between excluded/included files, filename-vs-directory-segment distinction
(the core precision requirement of this task).

## Regression Candidates
- `packages/arch-intelligence/tests/test_layer_detector.py` (8 pre-existing
  tests) — verified still passing, 0 modifications.
- `packages/arch-intelligence` full suite — 124/124 passing (105 pre-task
  baseline + 19 new).
- `packages/cli-commands` full suite — 54/54 passing, unchanged (this
  package only consumes `LayerDetector`'s output, doesn't test it directly).

## Deferred
None for this task's approved scope. The second false-positive pattern
(production leaf/utility modules) is explicitly deferred to a future task
per user decision during BUILDER verification — not a TEST-DESIGNER gap,
an explicit scope boundary.
