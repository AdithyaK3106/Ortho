# Test Plan — task-019-wire-plan-refactor

## Method
Shadow-parallel, blind, per session-standing decision: tests were derived
from `spec.md`'s behavior tables and adapter method signatures, not from
`implementation-notes.md`'s narrative of what BUILDER actually wrote. Real
product code (`feature_plan_adapter.py`, `refactor_adapter.py`,
`commands.py`) was read only to confirm import paths/attribute names
after tests were drafted from the spec, never to shape expected values.
No overfitting: all assertions on `refactor()`'s bloat output are bounded
("at least N found", "every entry exceeds threshold X") against a real
scan of `repos/click`, never a hardcoded exact module list or exact line
count — click's source will drift over time and the test must still hold.

## New Test File
`packages/cli-commands/tests/test_plan_refactor_wiring.py` — 17 tests:
- `TestPlanCommand` (6): empty/non-str rejection, >=3-path guarantee,
  feature-type variance (endpoint vs. data_layer intents produce
  different output — not a fixed string), nonexistent scan_path failure,
  title reflects the real intent.
- `TestRefactorCommand` (4): fast-fail on nonexistent path, real bloat
  detection on click, absence of fabricated duplication/churn data, clean
  small repo returns `success=True` with an empty-findings message (not
  treated as an error).
- `TestFeaturePlannerArchModelAdapter` (1): `get_style()` returns the
  actual scanned `ArchStyle.value`, not a fixed string.
- `TestCodeRepositoryAdapter` (7): duplications/churn always `[]`;
  bloated-modules entries individually verified against the documented
  threshold (not a hardcoded list); tight-coupling pairs deduplicated
  (A,B) != (A,B)+(B,A); circular-dep chains are genuinely closed loops of
  >2 nodes; no cycle double-counted as both tight-coupling and circular.
- `TestRealRepoRegressionPlanRefactor` (1): mandatory real-repo check —
  both commands succeed end-to-end against `repos/click`.

## Gap Found and Fixed (during this pass)
While writing `test_numeric_intent`/`test_none_input_handling` against
spec.md's "empty intent rejected" behavior row, I traced what `not intent`
actually guards: `not 123` is `False` (a non-empty int is truthy), so a
non-str, non-empty intent like `123` was **not** caught by the empty-
string guard and reached `FeaturePlanner._classify_feature_type()`, which
unconditionally calls `.lower()` on it — a genuine `AttributeError` crash,
reproduced directly against the real code before writing the assertion
(see implementation-notes.md's mypy/manual-verification section for the
traceback). This is exactly the kind of gap shadow-parallel TEST-DESIGNER
exists to catch: the spec said "reject empty intent" but the actual
crash surface was "reject empty-or-non-string intent." Reported back to
BUILDER; fixed with `if not intent or not isinstance(intent, str)` in
`commands.py`'s `plan()`. Verified the fix directly (manual repro) before
encoding it as `test_numeric_intent`'s assertion.

## Pre-Existing Defect Fixed (flagged in implementation-notes.md, not new code)
`test_edge_cases_exhaustive.py` and `test_commands.py` (both pre-existing,
not written this task) called `plan()`/`refactor()` unbounded (no
`scan_path`, default `.`) in ~15 places. These were harmless against the
old 100%-fake stubs but hang for minutes against the now-real scan
pipeline when pytest's cwd is the ortho monorepo root (`repos/` holds 10
real cloned frameworks). Updated every such call to use the same bounded
`_SMALL_FIXTURE`/`_FIXTURE_REPO` pattern the file already used for
`guardrails()`/`decide()` (an identical bug task-017 had already fixed for
those two commands). This is a test-file correctness fix, not a change to
product behavior — confirmed by reproducing the hang risk directly
(`timeout 15 python -c "...plan('...')..."` genuinely walking the full
`apps/`+`packages/` tree) before touching the test file.

Also updated `test_no_stub_literals_remain` (pre-existing, previously
documented `plan()`/`refactor()` stubs as "explicitly out of scope") to
assert the old stub strings are gone and the real engines
(`FeaturePlanner`, `RefactoringAdvisor`) are now called — this assertion
was stale the moment this task's scope was approved at GATE 1.

## Real-Repo Verification
`repos/click` (already used for task-017/018) and `repos/requests`
(adapter unit tests) — both real, non-trivial Python codebases already
present in this monorepo's fixture set.

## Results
- New file: 17/17 passed.
- Full `packages/cli-commands/tests/`: 72/72 passed, 45.75s (no hang).
- `feature-planner`, `refactoring-advisor`, `impact-analysis` regression
  suites: 0 modified, all passing (evidence: tests_engines_*.log).
