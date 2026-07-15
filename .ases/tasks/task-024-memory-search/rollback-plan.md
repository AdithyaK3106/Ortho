# Rollback Plan — task-024-memory-search

## Blast Radius
- New file: `apps/cli/src/commands/memory_search.py` (argparse bridge)
- New file: `packages/cli-commands/src/cli_commands/search_memory.py` (optional refactor)
- Modified: `packages/cli-commands/src/cli_commands/commands.py` (add search_memory method)
- Modified: `apps/cli/src/commands/copilot.ts` (register memoryCommand)
- Modified: `apps/cli/src/index.ts` (import memoryCommand)
- New tests: `packages/cli-commands/tests/test_memory_search.py`
- Zero changes to any other package or infrastructure.

## Rollback Procedure
`git revert <task-024 commit>` — fully self-contained. The memory store 
(workflow_run artifacts) remains untouched; only the query interface disappears.

## Risk Assessment
Low. Read-only memory search, no mutation. CLI command follows established 
context.py/memory_search.py bridge pattern. Reuses existing ArtifactStore.search() 
which is already tested in context-hub test suite.
