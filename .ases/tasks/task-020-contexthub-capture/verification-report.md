# Verification Report — task-020-contexthub-capture

## Tests
`packages/cli-commands/tests/` full suite: **100 passed, 1 skipped**
(the documented Windows-permission-simulation limitation), 55.66s.
Evidence: `verify_tests_20260715_153144.log`, `EXIT_cli-commands:0`.

## Backing Packages (context-hub, shared/storage)
**91 passed**, 0 files modified in either package. Evidence:
`verify_backing_20260715_153144.log`, `EXIT_backing:0`.

## mypy --strict
Whole-`src/` check: 27 errors (clean-master baseline on commit `5e1ca78`
is 23, confirmed via `git stash -u`/`git stash pop` comparison in
implementation-notes.md). Net +4, all four are `workflow_capture.py`'s
own lazy cross-package imports (`repo_intelligence.index_store`,
`storage`, `context_hub.ingestion`, `context_hub.store`) — same
`import-untyped` class as every other cross-package import in this file
tree (no `py.typed` markers anywhere in this monorepo yet). Zero new
type-correctness errors. Evidence: `verify_mypy_20260715_153144.log`.

Note: `.mypy_cache/` was found corrupted mid-session (`sqlite3
.DatabaseError: database disk image is malformed`, an mypy-internal
crash) and cleared with `rm -rf .mypy_cache` before this run — this is
mypy's own tool cache, not a project artifact, and clearing it does not
affect correctness of the comparison (both before/after runs used a
freshly rebuilt cache).

## Real Bug Found, Fixed, and Verified
`capture_workflow_run`'s first draft silently created full directory
trees on disk (via `OrthoDatabase.__init__`'s unconditional
`mkdir(parents=True, exist_ok=True)`) when called against a nonexistent
`scan_root` — reproduced directly (`ls` before/after showed a real
`C:\definitely\not\a\real\path\xyz\.ortho\` appear from a single call).
Fixed with an `is_dir()` guard before any filesystem object is
constructed. Re-verified post-fix: same repro command creates nothing on
disk; full test suite (including the 4 tests that had been failing due
to this exact contamination) now passes.

## Filesystem Contamination Cleanup (confirmed complete)
All stray untracked paths created during development (`C:\definitely\...`,
`<ortho-root>/src/module.py/.ortho/`, `<ortho-root>/src/.ortho/`) were
removed and confirmed absent in this final verification pass (`git
status --short` shows no unexpected untracked paths beyond this task's
own intended new files; `ls /c/definitely` confirms absence).

## Manual Real-Repo Verification
All 4 commands run against a real copy of `repos/click`; confirmed via
direct sqlite3 query (bypassing `ArtifactStore`) that exactly 4
`workflow_run` rows exist with correct `type`/`title`/`tags`/`source`.

## Human Verification Instructions (GATE 5)
1. Open `verify_tests_20260715_153144.log` — confirm `100 passed, 1
   skipped`, `EXIT_cli-commands:0`.
2. Open `verify_mypy_20260715_153144.log` — confirm 27 errors, all
   `import-untyped`/pre-existing-class, none inside `workflow_capture.py`'s
   actual logic (only its import lines).
3. Spot-check `test_workflow_capture.py::TestNeverRaisesNeverFlipsSuccess
   ::test_corrupt_existing_db_does_not_raise` — confirms the "never
   raises" contract against a genuinely malformed sqlite file, not a mock.
4. Confirm no stray filesystem paths remain: `git status --short` at
   repo root should show only this task's own new/modified files.
