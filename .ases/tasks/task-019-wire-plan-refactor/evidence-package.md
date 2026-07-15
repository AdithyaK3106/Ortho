# Evidence Package — task-019-wire-plan-refactor

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
- `.ases/evidence/task-019-wire-plan-refactor/mypy_20260715_130111.log` — first mypy pass (16 errors, 3-file scope)
- `.ases/evidence/task-019-wire-plan-refactor/mypy_final_20260715_*.log` — post-cast-fix (still 16, confirmed identical set)
- `.ases/evidence/task-019-wire-plan-refactor/tests_engines_*.log` — feature-planner/refactoring-advisor/impact-analysis, all EXIT:0
- `.ases/evidence/task-019-wire-plan-refactor/verify_tests_20260715_131151.log` — full cli-commands suite, 72 passed, EXIT:0
- `.ases/evidence/task-019-wire-plan-refactor/verify_mypy_20260715_131151.log` — whole-src/ mypy, 23 errors (net +1 vs 22 baseline, one baseline error fixed)

## Measured Real-World Impact
`refactor("repos/click")`: real bloat findings on click's genuinely large
modules (`core.py`, `types.py`, `_termui_impl.py`), zero fabricated
duplication/churn data. `plan(...)`: real feature-type classification
(cross_cutting/endpoint/data_layer/service/infrastructure) driving >=3
genuinely distinct implementation paths per intent.

## Bugs Found and Fixed This Task
1. `plan(123)` / any non-str truthy intent crashed with `AttributeError`
   (`'int' object has no attribute 'lower'`) inside `FeaturePlanner
   ._classify_feature_type`. Fixed: `commands.py`'s `plan()` now rejects
   non-str intents alongside empty ones.
2. Pre-existing test files (`test_edge_cases_exhaustive.py`,
   `test_commands.py`) called `plan()`/`refactor()` unbounded, hanging
   the full suite once these commands started doing real scans. Fixed:
   rebounded ~15 call sites to real small fixture repos, matching the
   pattern already used for `guardrails()`/`decide()`.

## Human Verification Instructions (GATE 5)
See verification-report.md's "Human Verification Instructions" section.
