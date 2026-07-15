# Rollback Plan — task-022-structured-json-output

## Blast Radius
- Modified: `packages/cli-commands/src/cli_commands/types.py` (CliReport 
  dataclass, +2 optional fields)
- Modified: `packages/cli-commands/src/cli_commands/commands.py` 
  (guardrails() and decide() now assign violations/recommendations)
- Updated: `docs/mcp-server-contract.md` (appendix only, no breaking changes 
  to existing prose)
- New tests: `packages/cli-commands/tests/test_structured_output.py`
- Zero changes to any other package or to CLI/bridge code.

## Rollback Procedure
1. `git revert <task-022 commit>`
2. All Python packages remain fully functional — the new fields are optional 
   and default to `None`, so any code not expecting them will simply see 
   `None` and continue.
3. CLI output is identical (`content` field unchanged), so `ortho guardrails` 
   / `ortho decide` CLI commands are unaffected.
4. No data loss — `.ortho/ortho.db` format is unchanged (workflow_run 
   artifacts are unaffected).

## Risk Assessment
Low. The changes are purely additive (new optional fields), backward-
compatible (existing callers unaffected), and purely internal to the 
Python API (no CLI/schema changes). The only risk is an accidental 
change to the `content` text format during implementation, but that 
would be caught by existing tests (acceptance criterion #6).
