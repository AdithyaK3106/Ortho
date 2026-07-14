# Evidence Package: task-017-repo-graph-queries

## Gates Checklist

| Gate | Status | Evidence |
|---|---|---|
| GATE 1: Plan Approval | ✓ APPROVED | plan.md, spec.md, rollback-plan.md — approved by user |
| GATE 2: Architecture Approval | ✓ APPROVED | architecture-review.md (conditional, corrections applied to spec.md), ADR-016 (ACCEPTED) — approved by user |
| GATE 3: Scope Review | ✓ APPROVED | implementation-notes.md — approved by user |
| GATE 4: Test Coverage Review | ✓ APPROVED | test-plan.md, contract-report.md (Contract Valid) — approved by user |
| GATE 5: Evidence Review | PENDING — this package | verification-report.md, logs below |
| REVIEWER | PENDING | to follow GATE 5 |

## Evidence Log Files

- `.ases/evidence/task-017-repo-graph-queries/mypy_20260714_231609.log` — mypy --strict, exit 0, "Success: no issues found in 5 source files"
- `.ases/evidence/task-017-repo-graph-queries/tests_20260714_231609.log` — full pytest run across 6 packages, all exit 0

## Real Bug Found and Fixed (during BUILDER phase, before handoff)
`decide('')` and default-path calls silently scanned an unbounded cwd
(this monorepo's `repos/` directory contains 7,882 vendored Python files
across 5 cloned frameworks), causing 60+ second hangs. Fixed by rejecting
empty intent explicitly and adding a `scan_path` kwarg. Documented in
implementation-notes.md's "Real Bug Found and Fixed" section.

## Regression Baseline Confirmation
Pre-existing `test_phase5_3_benchmarks.py` failures (3 tests, arch-intelligence)
confirmed via `git stash`/`git stash pop` to exist identically on clean
master before this task — not a regression.

## Human Verification Instructions (GATE 5)
1. Open `.ases/evidence/task-017-repo-graph-queries/mypy_20260714_231609.log` directly — confirm "Success: no issues found in 5 source files".
2. Open `.ases/evidence/task-017-repo-graph-queries/tests_20260714_231609.log` directly — spot-check at least one `EXIT_<package>:0` line and one real test name per package.
3. Confirm `verification-report.md`'s per-package counts match the log.
