# Evidence Package: task-018-layer-boundaries-noise

## Gates Checklist

| Gate | Status | Evidence |
|---|---|---|
| GATE 1: Plan Approval | ✓ APPROVED | plan.md, spec.md, rollback-plan.md — approved by user |
| GATE 2: Architecture Approval | ✓ APPROVED | architecture-review.md — approved by user |
| GATE 3: Scope Review | ✓ APPROVED | implementation-notes.md — approved by user |
| GATE 4: Test Coverage Review | ✓ APPROVED | test-plan.md (documents a real bug caught in the test itself) — approved by user |
| API Contract Gate | ✓ Contract Valid | contract-report.md |
| GATE 5: Evidence Review | PENDING — this package | verification-report.md, logs below |
| REVIEWER | PENDING | to follow GATE 5 |

## Evidence Log Files
- `.ases/evidence/task-018-layer-boundaries-noise/mypy_20260715_001816.log` — exit 1, 6 pre-existing errors (confirmed pre-existing via git stash), 0 new errors from this task's code
- `.ases/evidence/task-018-layer-boundaries-noise/tests_20260715_001816.log` — arch-intelligence exit 0 (124 passed, 3 deselected), cli-commands exit 0 (54 passed)

## Measured Real-World Impact
`repos/click` `layer_boundaries` violations: 83 → 7 (92% reduction), zero
remaining violations reference test/example paths (the targeted pattern).

## Human Verification Instructions (GATE 5)
1. Open `.ases/evidence/task-018-layer-boundaries-noise/mypy_20260715_001816.log` — confirm the 6 errors are at lines 30/47/71/77/108 (pre-existing code, not the new `_is_excluded`/`_EXCLUDED_SEGMENTS` at lines 6-18).
2. Open `.ases/evidence/task-018-layer-boundaries-noise/tests_20260715_001816.log` — confirm `EXIT_arch-intelligence:0` and `EXIT_cli-commands:0`, spot-check `test_click_layer_boundaries_reduced_and_test_paths_absent PASSED`.
