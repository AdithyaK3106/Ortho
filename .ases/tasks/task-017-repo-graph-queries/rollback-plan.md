# Rollback Plan: task-017-repo-graph-queries

## Triggers

1. Any of the 3 fixture repo scans (`repos/click`, `repos/flask`,
   `repos/requests`) crashes the CLI (unhandled exception, not a graceful
   "0 violations found because scan failed").
2. `mypy --strict` cannot pass on new adapter modules within the task's
   time-box.
3. Regression: any of the existing 303 tests (Phase 5+6) starts failing.
4. `find_cycles` or `find_callers` implementations show pathological
   performance (>30s) on any fixture repo.

## Procedure

1. `git status` to confirm no other uncommitted work is present before
   touching anything.
2. If mid-task and uncommitted: `git diff` the new/modified files, save a
   patch (`git diff > .ases/evidence/task-017-repo-graph-queries/rollback.patch`)
   before discarding, in case the partial work is salvageable later.
3. Revert new adapter files (delete): expected new files only (see spec.md
   `files_create`).
4. Revert modified files via `git checkout -- <file>` for anything listed
   in spec.md `files_modify` (currently only
   `packages/cli-commands/src/cli_commands/commands.py`).
5. Re-run full test suite to confirm return to 303/303 passing baseline.
6. Document rollback reason in CLAUDE.md under Known Limitations.

## Verification After Rollback

```
pytest packages/ -v --tb=short
```
Expect: same pass count as pre-task baseline (303 passed).

## What Is NOT Rolled Back

- Task planning artifacts (`plan.md`, `spec.md`, this file) — kept for
  future re-attempt with revised scope.
