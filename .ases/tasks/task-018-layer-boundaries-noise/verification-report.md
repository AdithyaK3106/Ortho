# Verification Report: task-018-layer-boundaries-noise

## BUILD
N/A (Python, no build step).

## TYPE-CHECK
**Status: PASS (new code), pre-existing errors documented**
`mypy --strict` on `layer_detector.py`: 6 errors, all at line numbers
corresponding to pre-existing code (untouched by this task) — confirmed
via `git stash`/`git stash pop` comparison to show identical errors exist
on clean master (see implementation-notes.md). The new code added by this
task (`_EXCLUDED_SEGMENTS`, `_is_excluded`) is fully typed and contributes
zero new errors.
Log: `.ases/evidence/task-018-layer-boundaries-noise/mypy_20260715_001816.log`

## UNIT-TESTS
**Status: PASS**

| Package | Result | Notes |
|---|---|---|
| arch-intelligence | 124 passed, 3 deselected | includes 19 new tests (test_layer_detector_exclusions.py); baseline pre-task was 105 passed (3 deselected, pre-existing unrelated benchmark failures) |
| cli-commands | 54 passed | unchanged from pre-task baseline (54) — this package consumes LayerDetector's output but has no direct tests of it |

Log: `.ases/evidence/task-018-layer-boundaries-noise/tests_20260715_001816.log`

## REAL-REPO VERIFICATION (mandatory per spec.md)
**Status: PASS, measured**
`test_click_layer_boundaries_reduced_and_test_paths_absent` runs the full
real pipeline against `repos/click`. Confirmed via direct manual
measurement (this session): `layer_boundaries` violation count dropped
from **83 (pre-fix baseline) to 7 (post-fix)** — a 92% reduction. All 7
remaining violations verified to NOT reference any test/example module
path (the pattern this task targets); they reference production
leaf/utility modules (e.g. `src.click.shell_completion`,
`src.click.formatting`) — a distinct, out-of-scope pattern per user
decision during BUILDER phase.

## API CONTRACT GATE
**Status: Contract Valid**
See `.ases/tasks/task-018-layer-boundaries-noise/contract-report.md`. No
public signature changes; `LayerDetector()` constructor and
`.extract_layers()` method signatures confirmed identical across spec,
architecture-review, implementation, and tests.

## REGRESSION
**Status: PASS**
- `test_layer_detector.py` (8 pre-existing tests): unmodified, all passing.
- Full arch-intelligence suite: 124/124 (up from 105 pre-task baseline,
  +19 new; 3 deselected pre-existing benchmark failures unchanged).
- Full cli-commands suite: 54/54, unchanged.

## Overall Verdict
**VERIFIED**
