# Plan: task-018-layer-boundaries-noise

**Owner:** Solo Developer
**Created:** 2026-07-15

## Feature Summary

`ortho guardrails` currently produces massive false-positive noise on the
`layer_boundaries` rule. Measured on `repos/click`: **83/83 (100%)** of
`layer_boundaries` violations are test files or example scripts importing
the library they test/demonstrate — not real architectural problems. Root
cause: `LayerDetector.extract_layers()` (`packages/arch-intelligence/src/arch_intelligence/layer_detector.py`)
does a pure topological sort with no concept of test/example/vendor code,
so `tests/test_core.py` importing `src/click/core.py` gets misclassified
as "Business layer importing Data layer" — a meaningless violation.

This task excludes non-production directories (tests, examples, vendored
code) from layer assignment, so `LayerDetector` only evaluates real
production source when building layers.

## Why

Per the vNext strategy's north-star guardrail: false-positive rate must
stay under 20% or the review tool is noise, not signal. Current measured
rate on this rule is 100% on the one real repo tested. A pilot's first
`ortho guardrails` run would be dominated by meaningless violations,
destroying trust before any real finding gets noticed.

## Atomic Tasks

1. **Add non-production directory detection to `LayerDetector`** — a
   constant set of directory-name patterns (`tests`, `test`, `examples`,
   `example`, `__tests__`, `vendor`, `node_modules`) checked against each
   `File.rel_path`'s path segments; files matching are excluded from layer
   assignment entirely (never assigned a layer, never appear in
   `Layer.file_ids`). ~45-60 min.
2. **Verify existing `LayerDetector` tests still pass** — confirm no
   existing test relies on test/example files being included in layer
   output (checked: existing tests use plain fixture paths like `a.py`,
   `data/db.py`, none use `tests/`-prefixed paths, so this should be
   additive-only). ~15 min.
3. **Re-measure false-positive rate on `repos/click`, `repos/flask`,
   `repos/requests`** — confirm layer_boundaries violation count drops to
   0 (or to genuinely real violations only) on all 3 fixture repos. ~20 min.

## Dependencies

None. Builds on task-017's `ArchModelAdapter`/`repo_scanner.py` (already
committed) but only modifies `layer_detector.py` (pre-existing,
untouched by task-017) plus adds test coverage.

## Risks

| Risk | Mitigation |
|---|---|
| Excluding test dirs changes `Layer.file_ids` counts, could affect any future consumer of `LayerDetector` beyond cli-commands | Verified: `LayerDetector` has zero internal consumers within arch-intelligence itself (grep confirmed) — only `cli-commands/repo_scanner.py` uses it. Low blast radius. |
| Directory-name heuristic could false-negative on repos using non-standard test dir names (e.g. `spec/`, `it/`) | Documented as a known limitation, not solved in this task — covers the common cases (`tests`, `test`, `examples`, `example`) verified against the 3 fixture repos' actual conventions. |
| Excluding too aggressively could hide a genuine violation that happens to live under a matched directory name (e.g. a real subsystem literally named `test_utils/` as production code, not a test dir) | Match on exact directory *segment* name (`tests`, not substring `test` anywhere), keeping false-exclusion risk low; documented in implementation-notes.md. |

## Acceptance Criteria (binary, testable)

- `layer_boundaries` violation count on `repos/click` drops from 83 to a
  number reflecting only genuine production-code layer violations (target:
  0, since click's own `src/click/` has no internal layer violations by
  inspection — to be confirmed after fix).
- Existing `LayerDetector` test suite (8 tests) still passes unmodified.
- New tests added covering: files under `tests/`, `test/`, `examples/`,
  `example/` are excluded from all layers; a file legitimately named
  `test_utils.py` at production top-level (not inside a `tests/` dir) is
  NOT excluded (segment-match, not substring-match).
- No regression in `arch-intelligence`, `cli-commands` full suites.

## Rollback Trigger

If exclusion logic causes any existing `LayerDetector` or `ArchitectureDetector`
test to fail, or if the false-positive rate on any of the 3 fixture repos
does not measurably improve, revert `layer_detector.py` changes.
