# Rollback Plan — task-023-filtering

## Blast Radius
- Modified: `packages/cli-commands/src/cli_commands/commands.py` 
  (guardrails and decide method signatures, +filtering logic)
- Modified: `apps/cli/src/commands/copilot.py` (argparse, +2 optional arguments)
- Modified: `apps/cli/src/commands/copilot.ts` (commander options, +TS-side 
  validation)
- New tests: filtering test cases in 
  `packages/cli-commands/tests/test_filtering.py`
- Zero changes to any other package, type definitions, or infrastructure.

## Rollback Procedure
`git revert <task-023 commit>`

All Python API changes are backward-compatible (new optional parameters, 
default to None/no-filtering). CLI flag additions are optional and 
backward-compatible (existing commands without flags work unchanged). 
No data schema changes, no `.ortho/` format changes.

## Risk Assessment
Low. Purely additive CLI flags, backward-compatible Python API changes. 
The only risk is a typo in the filtering logic (e.g., wrong comparison 
operator) but that would be caught by new tests immediately. Filter logic 
is simple (list comprehension, float comparison) and well-tested.
