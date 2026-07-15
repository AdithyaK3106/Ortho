# Evidence Package — task-020-contexthub-capture

## Gates Checklist
| Gate | Status | Evidence |
|---|---|---|
| GATE 1: Plan Approval | APPROVED | plan.md, spec.md, rollback-plan.md |
| GATE 2: Architecture Approval | APPROVED | architecture-review.md |
| GATE 3: Scope Review | APPROVED | implementation-notes.md |
| GATE 4: Test Coverage Review | APPROVED | test-plan.md |
| API Contract Gate | Contract Valid | contract-report.md |
| GATE 5: Evidence Review | PENDING — this package | verification-report.md, logs below |
| REVIEWER | PENDING | to follow GATE 5 |

## Evidence Log Files
- `.ases/evidence/task-020-contexthub-capture/tests_final_*.log` — first clean full-suite pass post-fix, 100 passed / 1 skipped
- `.ases/evidence/task-020-contexthub-capture/verify_tests_20260715_153144.log` — final fresh verification run, EXIT:0
- `.ases/evidence/task-020-contexthub-capture/verify_backing_20260715_153144.log` — context-hub + shared/storage, 91 passed, EXIT:0
- `.ases/evidence/task-020-contexthub-capture/verify_mypy_20260715_153144.log` — whole-src/ mypy, 27 errors (net +4 vs 23 baseline, all import-untyped)

## Measured Real-World Impact
All 4 `CliCommands` methods now persist a real, queryable `workflow_run`
artifact into `<scanned_root>/.ortho/ortho.db` on every call — ortho
begins accumulating genuine engineering memory across runs, the explicit
goal of this task per the vNext strategy.

## Bug Found and Fixed This Task
`capture_workflow_run`'s first draft silently created full directory
trees on disk for nonexistent scan_root paths (via `OrthoDatabase`'s
unconditional `mkdir`), which then made subsequent "nonexistent path"
tests see those paths as real — a self-perpetuating environment-
contamination bug. Fixed with an `is_dir()` existence guard before any
filesystem object is constructed. Caught by TEST-DESIGNER's shadow-
parallel hard-edge-case suite combined with the pre-existing
`test_edge_cases_exhaustive.py` suite's nonexistent-path assumptions.

## Human Verification Instructions (GATE 5)
See verification-report.md's "Human Verification Instructions" section.
