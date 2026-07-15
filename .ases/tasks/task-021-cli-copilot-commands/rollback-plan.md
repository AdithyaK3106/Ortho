# Rollback Plan — task-021-cli-copilot-commands

## Blast Radius
- New files: `apps/cli/src/commands/copilot.py`, `apps/cli/src/commands/copilot.ts`.
- Modified: `apps/cli/src/index.ts` (import + addCommand lines only).
- Zero changes to any `packages/*` Python package or `shared/*`.
- The four new CLI commands are purely additive; none of the 10 existing
  `ortho` commands are touched.

## Rollback Procedure
`git revert <task-021 commit>` — fully self-contained. The Python
packages remain usable via their API exactly as before this task; only
the CLI registration disappears. No data, schema, or `.ortho/` format
changes (memory capture behavior is unchanged — it ships with
`CliCommands` itself, task-020).

## Risk Assessment
Low. Same additive-command pattern as the existing `context`/`history`
commands. The one real risk — a copilot command accidentally scanning an
unbounded directory — is structurally prevented by the bridge requiring
an explicit path (TS always passes cwd), per spec.md.
