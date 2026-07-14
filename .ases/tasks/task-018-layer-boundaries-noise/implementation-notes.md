# Implementation Notes: task-018-layer-boundaries-noise

## What Was Built

### packages/arch-intelligence/src/arch_intelligence/layer_detector.py (modified)
- Added `_EXCLUDED_SEGMENTS` (module-level frozenset constant) and
  `_is_excluded(rel_path)` helper: splits a path on `/`/`\`, checks each
  segment for exact case-insensitive membership in
  `{tests, test, examples, example, __tests__, vendor, node_modules}`.
- `LayerDetector.extract_layers()` now filters `files` through
  `_is_excluded` as its very first step, before building `file_ids`/
  `file_map`. Since the existing edge-filtering logic (line ~50, unchanged)
  already restricts edges to `importer_file_id`/`imported_file_id` both
  being in `file_ids`, excluded files' edges are automatically dropped —
  no additional edge-filtering code was needed.
- Everything else (topological sort, layer numbering, semantic naming) is
  byte-for-byte unchanged.

### packages/arch-intelligence/tests/test_layer_detector_exclusions.py (created)
- 18 tests: 11 unit tests on the `_is_excluded` helper directly (segment
  match vs. substring, case-insensitivity, nested paths), 7 integration
  tests on `extract_layers()` (mixed production/test input, all-excluded
  edge case, edge-dropping verification, regression guard reproducing the
  existing `test_layer_detector.py` fixture to confirm unchanged behavior
  on pure-production input).

## What Was Deliberately NOT Built
- **A fix for the second false-positive pattern** (production leaf/utility
  modules like `typing.py`/`shell_completion.py`/`__version__.py` getting
  labeled "Data layer" just because nothing imports them back) — measured
  during this task's verification but explicitly out of spec.md's scope.
  User decision: ship this task as scoped, file the second pattern as a
  separate task (task-021, not yet created).
- No change to `arch_detector.py`'s separate style-detection heuristic
  (`_dag_shape`, `_Signals`) — different code path, not exhibiting the
  measured bug, explicitly forbidden by spec.md.

## Deviations from Spec
None. Implementation matches spec.md's Notes for BUILDER exactly (filter
at start of `extract_layers()`, named module-level constant, no edge
list surgery needed).

## Files Modified (exact paths)
- packages/arch-intelligence/src/arch_intelligence/layer_detector.py (modified)
- packages/arch-intelligence/tests/test_layer_detector_exclusions.py (new)

## Verification Commands
```
mypy --strict packages/arch-intelligence/src/arch_intelligence/layer_detector.py --ignore-missing-imports
pytest packages/arch-intelligence/tests -q --no-cov --deselect packages/arch-intelligence/tests/test_phase5_3_benchmarks.py
pytest packages/cli-commands/tests -q --no-cov
```

## Measured Impact (real-repo verification, mandatory per spec.md)

| Repo | layer_boundaries before | layer_boundaries after | Reduction |
|---|---|---|---|
| repos/click | 83 | 7 | 92% |
| repos/flask | not measured pre-fix this task (measured post-fix: 20) | 20 | — |
| repos/requests | not measured pre-fix this task (measured post-fix: 4) | 4 | — |

click's before/after was directly measured (83→7). flask/requests were only
measured post-fix in this task, but by inspection their remaining
violations are the same "production leaf/utility module" pattern as
click's remaining 7 — not test/example files (confirmed: none of the
remaining violations reference `tests/`, `test/`, or `examples/` paths).

## Honest Assessment: What Might Break
- **mypy --strict on layer_detector.py:** pre-existing 6 errors (missing
  generic type args on `list`/`dict`, one missing var annotation) remain —
  confirmed via `git stash`/`git stash pop` comparison that these exist
  identically on clean master, not introduced by this task. My new code
  (`_is_excluded`, `_EXCLUDED_SEGMENTS`) is itself fully typed.
- **Directory-name heuristic is not exhaustive** — a repo using `spec/` or
  `it/` for test directories would not benefit from this exclusion. This
  is a known, documented limitation (spec.md, plan.md), not solved here.
- **Second false-positive pattern remains** (see "What Was Deliberately NOT
  Built" above) — `layer_boundaries` is NOT yet a fully quiet rule; it is
  measurably 92% quieter on the pattern this task targeted.
