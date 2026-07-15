# Rollback Plan — task-020-contexthub-capture

## Blast Radius
- New file: `cli_commands/workflow_capture.py`.
- Modified: `cli_commands/commands.py` (one new call added at the end of
  each of the 4 existing methods; no changes to existing logic/return
  values).
- No changes to `context-hub`, `shared/storage`, or `repo-intelligence`
  (all consumed as-is, already real and tested).
- Side effect (new): running any of the 4 commands now creates/appends to
  `<scanned_root>/.ortho/ortho.db`. This is a real filesystem write that
  did not happen before this task. Directly relevant to rollback: if a
  pilot user's repo unexpectedly gains a `.ortho/` directory, that is
  this task's doing.

## Rollback Procedure
1. `git revert <task-020 commit>` — self-contained, restores the
   stateless-call behavior.
2. Any `.ortho/ortho.db` files already created by capture in the interim
   are not automatically cleaned up by a code revert (they are user-repo
   filesystem artifacts, not tracked by ortho's own git history) — if a
   full rollback of capture side effects is needed, affected repos'
   `.ortho/` directories would need manual removal. This is called out
   explicitly because it's the one part of this task's blast radius that
   isn't "just a code change."

## Risk Assessment
Low-to-moderate. The code change itself is small and additive (matches
task-017/018/019's precedent), but this is the first task in the session
that writes to the *scanned target's* filesystem rather than only reading
it — `guardrails`/`decide`/`plan`/`refactor` were previously pure reads.
Mitigated by: capture is wrapped in try/except and can never fail the
calling command (spec.md failure-modes table), and `.ortho/` as a
convention already exists project-wide (used by `scan_cli.py`,
`workflow_cli.py`, `context.py` today) — this task does not invent a new
side-effect location, it reuses the one ortho already writes to
elsewhere.
