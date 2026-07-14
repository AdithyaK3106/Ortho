# Rollback Plan: task-018-layer-boundaries-noise

## Triggers
1. Any existing `LayerDetector` test (8 tests, `test_layer_detector.py`) fails.
2. Any existing `ArchitectureDetector`/integration test fails.
3. False-positive rate does not measurably improve on `repos/click`,
   `repos/flask`, or `repos/requests` after the fix.
4. `cli-commands` regression suite (54 tests) fails.

## Procedure
1. `git status` to confirm no unrelated uncommitted work.
2. `git diff packages/arch-intelligence/src/arch_intelligence/layer_detector.py`
   — save patch if partial work is salvageable.
3. `git checkout -- packages/arch-intelligence/src/arch_intelligence/layer_detector.py`
4. Remove any new test file additions.
5. Re-run full arch-intelligence + cli-commands suites to confirm return
   to task-017's committed baseline (105 + 54 passing).

## Verification After Rollback
```
pytest packages/arch-intelligence/tests -q --no-cov --deselect packages/arch-intelligence/tests/test_phase5_3_benchmarks.py
pytest packages/cli-commands/tests -q --no-cov
```
Expect: 105 passed (arch-intelligence, 3 deselected), 54 passed (cli-commands).

## What Is NOT Rolled Back
Task planning artifacts — kept for future re-attempt with revised scope.
