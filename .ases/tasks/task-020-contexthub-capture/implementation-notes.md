# Implementation Notes — task-020-contexthub-capture

## What Was Built
- `packages/cli-commands/src/cli_commands/workflow_capture.py` (new):
  `capture_workflow_run(scan_root, command, argument, report)` — builds an
  `ArtifactIngestionRequest(type="workflow_run", ...)`, opens
  `OrthoDatabase(resolved_root)` + `ArtifactStore(db,
  repo_id=mint_repo_id(resolved_root))`, calls `ingest_artifact()`.
  Wrapped entirely in `try/except Exception: logging.warning(...)` —
  never raises, never touches `report.success`.
- `commands.py`: all 4 methods (`guardrails`, `decide`, `plan`,
  `refactor`) now call `capture_workflow_run` on every return path,
  including early-return failure paths (empty/non-str intent, nonexistent
  scan path) — refactored each method to build the `CliReport` first,
  capture, then return, so no return path can be missed by a future edit.

## Real Bug Found and Fixed During BUILDER's Own Manual Verification
Before running any tests, I manually smoke-tested all 4 commands against
a real copy of `repos/click` and confirmed 4 real `workflow_run` rows
landed in `.ortho/ortho.db` (correct). Then, running the full pytest
suite surfaced 4 test failures where nonexistent-path tests
(`guardrails("/definitely/not/a/real/path/xyz")`, etc.) unexpectedly
returned `success=True`. Root cause: `OrthoDatabase.__init__` (pre-
existing code, `shared/storage/src/storage/database.py:13`) does
`self.db_path.parent.mkdir(parents=True, exist_ok=True)` **unconditionally
in its constructor**. My first draft of `capture_workflow_run` constructed
`OrthoDatabase(resolved_root)` for every call, including calls where
`scan_root` was a bogus/nonexistent path passed straight from a failed
`scan_repository()` call (e.g. `/definitely/not/a/real/path/xyz`) — this
silently created the entire directory tree `C:\definitely\not\a\real\
path\xyz\.ortho\` on disk as a side effect of a *failed* command, and
because the directory then genuinely existed, every subsequent test run
against that same "nonexistent" path saw it as real and scanned it
successfully — a self-perpetuating environment-contamination bug that
would get worse on every CI run.

**Fixed** by adding an explicit `if not resolved_root.is_dir(): return`
guard at the top of `capture_workflow_run`, before `OrthoDatabase` is ever
constructed. Verified the fix directly: ran `capture_workflow_run` against
a bogus path, confirmed no directory was created on disk (`ls` before/
after), then re-ran the full test suite and confirmed all 4 previously-
failing tests passed with the fix in place.

Cleaned up the contamination this bug had already caused during
development: `C:\definitely\...` (from a direct capture_workflow_run call)
and a stray `src/module.py/.ortho/` + `src/.ortho/` at the ortho repo root
itself (from `test_edge_cases_exhaustive.py`'s pre-existing
`refactor("src/module.py")`/`test_commands.py`'s `refactor("src/service.py")`
calls, which — before this fix — also silently created real directories).
Both cleanups were of untracked, non-git paths (confirmed via `git status`
before removal).

## mypy --strict
Whole-`src/` check: 27 errors vs. 23 on the clean `5e1ca78` baseline
(confirmed via `git stash -u`/`git stash pop` comparison). The 4 new
errors are exactly `workflow_capture.py`'s own 4 lazy imports
(`repo_intelligence.index_store`, `storage`, `context_hub.ingestion`,
`context_hub.store`), all `import-untyped` — same "sibling package lacks
py.typed marker" class as every other cross-package import in this file.
Zero new type-correctness errors. (Note: mypy's own incremental cache
`.mypy_cache/` was corrupted mid-session — `sqlite3.DatabaseError:
database disk image is malformed`, an internal mypy crash unrelated to
any code in this task — cleared with `rm -rf .mypy_cache` before
re-running; this is mypy's own tool state, not a project file.)

## Manual Verification (real repo, post-fix)
Re-ran all 4 commands against a real copy of `repos/click`; confirmed via
direct sqlite3 query against the real `.ortho/ortho.db` (bypassing
`ArtifactStore`, reading the raw table) that exactly 4 `workflow_run` rows
exist with correct `type`, `title`, `tags`, `source` values. No mocking
anywhere in this verification.
