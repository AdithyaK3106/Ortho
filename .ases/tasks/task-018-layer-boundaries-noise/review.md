# Code Review — task-018-layer-boundaries-noise

**Verdict:** APPROVED

## Summary
Excludes test/example/vendor directories from `LayerDetector`'s layer
assignment, fixing a measured 100% false-positive rate on the
`layer_boundaries` guardrail rule (test files importing the library they
test were being flagged as architectural violations). Measured real-repo
result: 83 → 7 violations on `repos/click` (92% reduction), zero of the
remaining 7 reference test/example paths.

## Specification Compliance
✓ `LayerDetector.extract_layers()` signature unchanged.
✓ Exclusion is segment-based (not substring) — verified `test_utils.py` and `testing_helpers/` are correctly NOT excluded, while `tests/`, `test/`, `examples/`, `example/`, `__tests__/`, `vendor/` are.
✓ Excluded files absent from `Layer.file_ids`; their import edges are dropped (verified — the existing `file_ids in file_ids` edge filter at line 50 automatically excludes edges touching filtered files, no separate edge-filtering code was needed or added).
✓ All-files-excluded edge case returns `[]`.
✓ `files_forbid` respected: `arch_detector.py` and `types.py` untouched (confirmed via reading the diff — only `layer_detector.py` modified, one new test file added).

No deviations from spec.

## Code Quality Assessment
- Small, clean diff. `_EXCLUDED_SEGMENTS` is a named module-level constant per spec.md's explicit guidance, not inlined.
- The comment on `_EXCLUDED_SEGMENTS` (lines 6-10) explains *why* (test files importing production code get misclassified), which is the right kind of comment — non-obvious rationale, not restating what the code does.
- Adversarial probing (this review): tested 4 cases not in the existing suite — leading slash, empty string, trailing slash, dotted-substring-but-not-segment. All behave correctly. This is a minor test-coverage gap (not a defect) worth noting for a future pass, not blocking.

## Security Assessment
No new input surface. `rel_path` strings originate from the same source (repo file scan) as before this change; no new trust boundary crossed, no new I/O, no secrets.

## Architecture Compliance
✓ No ADR implicated — this task's "layers" (detected architectural layers within a *scanned target* repo) is unrelated to ADR-015/016's meaning of "layers" (ortho's own package structure). No conflict.
✓ Independently verified (not just cited from architecture-review.md): `grep -rln "LayerDetector\|extract_layers" packages/` confirms exactly one internal consumer (`cli-commands/repo_scanner.py`) besides the definition itself — architecture-review.md's blast-radius claim holds.

## Evidence Completeness
✓ Opened `.ases/evidence/task-018-layer-boundaries-noise/mypy_20260715_001816.log` directly: 6 errors, all at lines 30/47/71/77/108 — pre-existing code, confirmed via the task's own `git stash` comparison (documented in implementation-notes.md) to be identical on clean master. Zero new errors from lines 6-18 (this task's new code).
✓ Opened `.ases/evidence/task-018-layer-boundaries-noise/tests_20260715_001816.log` directly: confirmed `EXIT_arch-intelligence:0` (124 passed, 3 deselected) and `EXIT_cli-commands:0` (54 passed) — matches verification-report.md exactly.
✓ API Contract Gate: Contract Valid, re-verified independently — `LayerDetector()` zero-arg constructor and `.extract_layers(edges, files)` two-positional-arg call pattern match in both implementation and tests.

## Test Authenticity Audit (MANDATORY)
1. **Product imports:** `test_layer_detector_exclusions.py` imports `arch_intelligence.layer_detector.{LayerDetector, _is_excluded}` and `arch_intelligence.arch_detector.File` — real product code, confirmed via direct read (not grep alone).
2. **Pass-body / tautology check:** Read all 19 test bodies directly. Every assertion depends on the return value of `_is_excluded(...)` or `LayerDetector().extract_layers(...)` — none are hardcoded-data tautologies. `test_click_layer_boundaries_reduced_and_test_paths_absent` runs a genuine end-to-end scan against real files on disk (`repos/click`), not mocked.
3. **`pytest.raises`:** Zero occurrences — correctly, since neither `_is_excluded` nor `extract_layers` is specified to raise.
4. **Claimed vs. executed counts:** test-plan.md claims 19 tests; evidence log confirms 124 total arch-intelligence tests passed (105 pre-task baseline + 19 new) — arithmetic checks out exactly, no discrepancy this time (unlike task-017's minor count issue).

## Seven Adversarial Questions

1. **What would make this break in production?** Probed adversarially (this review): leading-slash paths, empty strings, trailing slashes, dotted-substring-but-not-segment names. All behave correctly — no crash, no false exclusion/inclusion. No production break found.
2. **What did TEST-DESIGNER not test?** The four adversarial cases above were not in the existing 19-test suite. Minor gap, not a defect — behavior is correct, just unverified by an explicit test. Not blocking, but worth adding in a future pass if this file is touched again.
3. **What assumption is unverified?** "LayerDetector has no other internal consumers" — independently re-verified via grep in this review, holds true.
4. **Dependencies failing?** N/A — pure function, no I/O, no external calls.
5. **Security surface?** None new.
6. **ADR violations?** None — verified independently.
7. **Evidence complete?** Yes — both log files opened and spot-checked directly in this review, not taken on faith from prior summaries.

## Confidence Level
EVIDENCE-BACKED

## Approval
**Verdict:** APPROVED

**Reason:** Fix is correctly scoped, matches spec.md exactly, measured 92% real-world reduction in the targeted false-positive pattern, zero regressions, and independently re-verified architecture/security/evidence claims rather than trusting prior session summaries. The one minor gap (untested edge cases for `_is_excluded`, all of which behave correctly when probed) does not rise to a blocking issue — it's a coverage nice-to-have, not a defect.

**Approved by:** REVIEWER
**Date:** 2026-07-15
