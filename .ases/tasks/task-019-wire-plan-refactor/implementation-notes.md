# Implementation Notes — task-019-wire-plan-refactor

## What Was Built
- `packages/cli-commands/src/cli_commands/feature_plan_adapter.py`
  (new): `FeaturePlannerArchModelAdapter.get_style()` returns the real
  scanned `ArchStyle` value (currently always `"unknown"` — no style
  detector wired into `scan_repository` yet, an honest gap, not this
  task's to fix).
- `packages/cli-commands/src/cli_commands/refactor_adapter.py` (new):
  `CodeRepositoryAdapter` — real bloat detection via `CodeMetricsAdapter`
  (threshold: lines > 300 or functions > 20), real tight-coupling/circular-
  dependency detection via `impact_analysis.DependencyHealthAnalyzer
  .find_cycles()` (module-name import edges resolved to file-id edges,
  same resolution strategy as `repo_scanner._build_layer_import_edges`).
  `get_duplications()`/`get_high_churn_modules()` return `[]`
  unconditionally — no real signal source exists (documented in spec.md,
  architecture-review.md).
- `commands.py`: `plan()`/`refactor()` method bodies replaced with real
  scan -> adapter -> engine -> render pipelines, matching the pattern
  established for `guardrails()`/`decide()` in task-017. `refactor()`'s
  `path: str = None` also corrected to `path: str | None = None`
  (fixes a pre-existing mypy `--strict` "implicit Optional" error in the
  exact function this task touches — not a separate unrelated cleanup).

## Manual Verification (real repo)
Ran `plan("add a caching layer", scan_path="repos/click")` and
`refactor("repos/click")` directly:
- `plan()`: correctly classified as `cross_cutting`, returned 3 real
  distinct `ImplementationPath` entries from `FeaturePlanner`.
- `refactor()`: found real bloat in `click`'s actually-large modules
  (`src.click.core`, `src.click.types`, `src.click._termui_impl` — all
  genuinely >300 lines), zero fabricated duplication/churn entries.

## mypy --strict
Confirmed via `git stash`/`git stash pop` comparison: baseline
`commands.py` + `dependency_graph_adapter.py` had 12 pre-existing errors
(all `import-untyped` for un-py.typed sibling packages, plus 3
pre-existing `no-any-return` in the untouched `_CallGraphView`/
`_ImportGraphView`/`_SymbolRegistryView` classes, plus 1
implicit-Optional error on `refactor()`'s old signature). Post-change: 16
errors — the 4 new ones are exactly the 2 new files' own
`import-untyped` noise (2 modules x roughly 2 each) for the same
"sibling package has no py.typed marker" reason as every other
cli-commands import. Zero new `no-any-return` or type-correctness errors
from the new adapter code itself (the one real new-code error,
`feature_plan_adapter.py:14` returning `Any` from `ArchStyle.value`, was
fixed with an explicit `str()` cast before this log was captured).

## Bug Found During BUILDER Verification (real, must be fixed before GATE 3)
`packages/cli-commands/tests/test_edge_cases_exhaustive.py` (pre-existing
file, not written this task) calls `commands.plan(...)` and
`commands.refactor(...)` in ~20 places with **no `scan_path`/bounded path**
— e.g. `commands.plan("add authentication")`, `commands.refactor()`,
`commands.refactor("/nonexistent/path/to/file")`. These were harmless
against the old hardcoded-stub `plan()`/`refactor()` (return instantly,
ignore all arguments). Now that both commands run a real filesystem scan,
a bare call defaults to scanning `.` — which, when pytest's cwd is the
ortho monorepo root, means scanning `repos/` (10 real cloned frameworks:
celery, click, django, fastapi, flask, langchain,
opentelemetry-demo, requests, sqlalchemy, supabase-master). This hung the
full `pytest packages/cli-commands/tests/` run past a 2-minute timeout.

This is the *exact* bug class task-017 already fixed for `decide()`
(`docs/mcp-server-contract.md`/task-017 evidence: empty-intent rejection +
`scan_path` kwarg), and `test_edge_cases_exhaustive.py`'s own top-of-file
comment (lines 8-10) already documents that `guardrails()`/`decide()`
needed exactly this bounding — but the file was never updated when
`plan()`/`refactor()` were still stubs, since it didn't matter yet.

**Fix scope decision:** `commands.py`'s `plan()` already accepts
`scan_path` via `kwargs` (mirrors `decide()`). `refactor()`'s `path`
argument *is* the scan target directly (mirrors `guardrails()`'s `path`
param), so no kwarg is needed there — callers who want a bounded scan
already have a way to provide one. The actual defect is in the **test
file**, which predates this task and calls both commands unbounded. Per
this task's scope (spec.md: wire commands to real engines, not rewrite
unrelated pre-existing tests), TEST-DESIGNER is flagged to update
`test_edge_cases_exhaustive.py`'s unbounded `plan()`/`refactor()` calls to
use the same `_SMALL_FIXTURE` pattern already used for
`guardrails()`/`decide()` in that same file (lines 95, 106), as part of
GATE 4 test coverage — this is a real, blocking correctness issue for the
test suite, not an implementation change.
