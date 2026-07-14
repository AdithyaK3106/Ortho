task: task-018-layer-boundaries-noise
title: Exclude non-production directories from LayerDetector layer assignment
owner: Solo Developer
created: 2026-07-15
status: DRAFT
architecture_impact: NONE (additive filter within existing LayerDetector class, no new modules, no API contract change to extract_layers signature)

objective: LayerDetector.extract_layers() must exclude files under test/example/vendor directories from layer assignment, so ortho guardrails stops reporting test-files-importing-the-library-they-test as layer_boundaries violations.

files_create:
  - packages/arch-intelligence/tests/test_layer_detector_exclusions.py

files_modify:
  - packages/arch-intelligence/src/arch_intelligence/layer_detector.py

files_forbid:
  - packages/arch-intelligence/src/arch_intelligence/arch_detector.py (do not touch — separate style-detection heuristic, not this task's concern)
  - packages/arch-intelligence/src/arch_intelligence/types.py (Layer dataclass unchanged)
  - packages/cli-commands/src/cli_commands/repo_scanner.py (no change needed — fix belongs in LayerDetector itself since it has no other internal consumers, confirmed by grep)

contract_in: list[ImportEdge] (importer_file_id/imported_file_id), list[File] (id/rel_path) — unchanged from current signature
contract_out: list[Layer] — unchanged shape, but excludes non-production files entirely

---

## Behavior

### Current (buggy) behavior
`extract_layers()` topologically sorts ALL files in the input, including
test files and example scripts, assigning them layer numbers purely by
import depth. A test file importing production code lands one layer above
it, then gets labeled with a generic depth-based name ("Data"/"Business"/
"Presentation" for layers 0/1/2), producing meaningless "Business cannot
import Data" violations when `ArchitectureEnforcer` later checks boundaries.

**Measured impact:** 83/83 (100%) of `layer_boundaries` violations on
`repos/click` are test/example files importing `src/click/*`.

### Required behavior

1. Before building the topological sort, filter `files` (and the
   `import_graph` edges referencing filtered-out files) to exclude any
   `File` whose `rel_path` contains a path segment (not substring) exactly
   matching one of: `tests`, `test`, `examples`, `example`, `__tests__`,
   `vendor`, `node_modules`.
   - Segment match means: split `rel_path` on `/` and `\`, check each
     resulting segment for exact (case-insensitive) equality — NOT
     `"test" in rel_path`. A file at `src/test_utils.py` (filename
     contains "test" but no directory segment named "test") must NOT be
     excluded. A file at `tests/test_core.py` (directory segment `tests`)
     MUST be excluded.
2. Excluded files:
   - Do not appear in any `Layer.file_ids`.
   - Do not participate in the topological sort (their import edges to/from
     production files are dropped before sorting).
3. Everything else about `extract_layers()`'s algorithm (topological sort,
   layer numbering, semantic naming via `SEMANTIC_KEYWORDS`) is unchanged.
4. If ALL files in the input are excluded (edge case: a repo scan that
   only contains test files), return `[]` — same as the existing
   `if not files: return []` early-exit behavior.

### Test Coverage (12+ cases)

| Case | Input | Expected | Notes |
|---|---|---|---|
| File under `tests/` excluded | `File(rel_path="tests/test_core.py")` | not in any Layer.file_ids | Core case |
| File under `test/` (singular) excluded | `File(rel_path="test/test_x.py")` | not in any Layer.file_ids | Click uses `tests/`, some projects use `test/` |
| File under `examples/` excluded | `File(rel_path="examples/demo.py")` | not in any Layer.file_ids | Matches click's actual structure |
| File under nested `pkg/tests/x.py` excluded | `File(rel_path="pkg/tests/test_x.py")` | not in any Layer.file_ids | Segment match works at any depth |
| Production file named `test_utils.py` at top level NOT excluded | `File(rel_path="test_utils.py")` | present in some Layer.file_ids | Filename substring "test" must not trigger exclusion |
| Production file in `testing_helpers/` dir NOT excluded | `File(rel_path="testing_helpers/x.py")` | present in some Layer.file_ids | Segment must be exact match "test"/"tests", not "testing_helpers" |
| All files excluded | all files under `tests/` | `[]` returned | Edge case |
| Mixed production + test files | 2 production files (layered), 3 test files | Layers built only from the 2 production files; test files absent from file_ids | Core integration case |
| Import edge between excluded and included file dropped | test file imports production file | edge does not affect production file's layer number | Verifies edges are filtered, not just files |
| Case insensitivity | `File(rel_path="Tests/test_x.py")` | excluded | Some platforms/conventions capitalize |
| `__tests__` directory (JS-style convention, defensive) | `File(rel_path="__tests__/x.py")` | excluded | Included per spec even though this is a Python-focused tool, cheap to support |
| Real-repo regression: `repos/click` full scan | real `repos/click` scan via existing `cli-commands` pipeline | `layer_boundaries` violation count == 0 (down from 83) | Mandatory real-repo verification |
| Existing 8 `test_layer_detector.py` tests | unchanged | still pass, 0 modifications needed | Regression guard |

## Notes for BUILDER

- Implement exclusion as a filter step at the START of `extract_layers()`,
  before `file_map`/`imports` dict construction — cleanest place, avoids
  touching the topological sort algorithm itself.
- Directory segment set should be a module-level constant (e.g.
  `_EXCLUDED_SEGMENTS`), not inlined, so it can be referenced by tests.
- Do not attempt to also fix `arch_detector.py`'s separate style-detection
  signals in this task — out of scope, different code path, not exhibiting
  the measured bug.
