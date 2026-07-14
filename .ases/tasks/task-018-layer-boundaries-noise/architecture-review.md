# Architecture Review: task-018-layer-boundaries-noise

## Module Boundary Evaluation
No new modules. Change is entirely within `LayerDetector`
(`packages/arch-intelligence/src/arch_intelligence/layer_detector.py`), an
existing class in an existing package. `extract_layers()`'s public
signature (`list[ImportEdge], list[File] -> list[Layer]`) is unchanged —
only internal filtering logic is added before the existing topological
sort runs. Cohesion is preserved: the class's single responsibility
("extract architectural layers from import DAG") is unchanged; the fix
narrows *what counts as part of the architecture* (production code only),
which is squarely within that responsibility, not scope creep into it.

## Dependency Analysis
```
cli-commands/repo_scanner.py -> arch-intelligence/LayerDetector.extract_layers()
(no other internal callers of LayerDetector within arch-intelligence — verified via grep)
```
No new dependencies. No circular dependencies introduced or possible (the
change adds a pure filter, no new imports of other packages).

## API Contract Definitions
`extract_layers(import_graph: list[ImportEdge], files: list[File]) -> list[Layer]`
— signature unchanged from current implementation. Output `Layer` objects
now simply exclude non-production `file_ids`; the `Layer` dataclass shape
itself is untouched (`types.py` is in `files_forbid`).

## Data Flow Review
```
files (all scanned files, incl. tests/examples)
  -> [NEW] filter: exclude files with a path segment in {tests, test,
     examples, example, __tests__, vendor, node_modules}
  -> existing topological sort (production files + production-file-only edges)
  -> existing layer numbering + semantic naming
  -> Layer objects (file_ids now production-only)
```
Filtering happens at the earliest point (before the sort), which is the
correct layer for this kind of "which inputs count" decision — no
validation/business logic is split across layers.

## Risk Flags
- **Security:** N/A — no new I/O, no new inputs beyond what's already passed in.
- **Scalability:** Filtering is O(n) over files/edges, strictly cheaper than the existing O(V+E) topological sort it precedes. No new scalability concern.
- **Extensibility:** The excluded-segment set is a named module-level constant per spec.md's Notes for BUILDER, making future additions (e.g. a project using `spec/` instead of `tests/`) a one-line change, not a rewrite. Documented as a known limitation in plan.md rather than solved exhaustively now — reasonable scope boundary.
- **Data Integrity:** N/A — stateless, deterministic, no persistence.
- **Breaking Changes:** None for existing callers — `cli-commands`'s `repo_scanner.py` will simply receive cleaner `Layer.file_ids` sets; nothing depends on test/example files currently being included (no test asserts on that inclusion — confirmed by reading `test_layer_detector.py`'s 8 existing tests, all use non-test-named fixture paths).

## ADR References
- ADR-015 (Layer Boundaries & Import Rules): not implicated — this task doesn't touch package-to-package import rules, only within-repo architectural layer detection (a different, unrelated meaning of "layer" — ADR-015's "layers" are ortho's own package layers; this task's "layers" are a detected property of a *scanned target* repo). No conflict.
- ADR-016 (Engineering Copilot layer): not implicated — no change to package classification.
- No new ADR required: this is a bug fix within existing module boundaries, not a new module/dependency/API/schema/security decision (per architect.md's "Do NOT create ADRs for: bug fixes that don't change design").

## Verdict
**APPROVED** — No red flags. Single-package, additive-filter fix with unchanged public contract, zero circular-dependency risk, no new ADR required.
