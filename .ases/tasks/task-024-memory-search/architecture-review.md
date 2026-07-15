# Architecture Review — task-024-memory-search

**Verdict:** APPROVED

## Design Analysis

### API Extension Pattern
Adding `search_memory()` to `CliCommands` follows the established pattern: 
a new orchestration method that wraps lower-level components (ArtifactStore.search) 
and returns a `CliReport`. No new layers, no new dependencies. Purely additive 
to the Apps layer (CliCommands).

### Read-Only Memory Access
This task only *reads* from ContextHub, never mutates. Reuses the existing 
`ArtifactStore.search()` method (which uses SQLite FTS5 BM25 ranking) that 
is already tested in `packages/context-hub/tests/`. No new storage layer, 
no new indexing logic. Safe by design.

### CLI Bridge Pattern
`memory_search.py` follows the exact established pattern: argparse bridge 
(`context.py` precedent), sys.path bootstrap, call to CliCommands, UTF-8 
output buffer write, exit-code mapping. No new abstraction, no new framework.

`memoryCommand` in `copilot.ts` follows the same pattern as guardrails/decide: 
Commander registration, option parsing, TS-side validation (non-empty query 
via `requireIntent`), spawn Python bridge. Consistent with task-021/023.

### Structured Output (task-022 Extension)
The new `search_results: Optional[list[WorkflowRunResult]]` field on CliReport 
extends the pattern established in task-022. `WorkflowRunResult` is a simple 
data class (id, command, timestamp, intent, success) — mirrors the 
`GuardrailViolation` / `Recommendation` pattern. Backward-compatible (defaults 
to None).

### Integration with Existing Subsystems
- **ContextHub (task-020):** Reads workflow_run artifacts that task-020 captures. 
  No schema changes, no new artifact types.
- **CLI (task-021):** New CLI command added to the existing copilot registration 
  pattern.
- **Filtering (task-023):** Search results can be filtered by pilots at the CLI 
  level (e.g., grep the output). No feature interaction needed.

## Correctness Checks

1. **What if repo has no .ortho/ortho.db yet?**
   `success=True, content="No memory artifacts in this repo yet"` — correct, 
   non-error state.

2. **What if query is empty?**
   `requireIntent()` catches it at the TS layer (exit 1 before spawn). Python 
   side can also validate. Correct.

3. **What if ArtifactStore.search() throws?**
   Wrapped in try/except (same pattern as task-020 capture) → 
   `success=False, content="Search failed: <error>"`. Never raises.

4. **Performance: searching a repo with 1000 workflow_run artifacts?**
   SQLite FTS5 with BM25 ranking handles this efficiently. Limit=50 keeps 
   output reasonable. Safe.

5. **Does this expose any security concerns?**
   No — it only reads from the local repo's own .ortho/ directory, no network, 
   no credential exposure.

## Verdict
**APPROVED** — read-only memory search, reuses existing ArtifactStore.search, 
follows all established patterns (CLI bridge, CliReport, structured output). 
No new architecture, no new risk. Low blast radius, high pilot value.
