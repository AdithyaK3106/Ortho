# Plan — task-024-memory-search

## Goal
Pilots want to ask "What have we learned about this codebase?" — search the 
accumulated engineering memory (workflow_run artifacts captured by task-020) 
to see patterns, recommendations, and past decisions. Enable querying the 
ContextHub memory store by keyword/intent.

## Current State
- Every `guardrails/decide/plan/refactor` call writes a `workflow_run` artifact 
  to `<repo>/.ortho/ortho.db` (task-020).
- No way to read that memory back — no search, no query interface.
- `ortho context` command exists for manual add/search of user-created artifacts, 
  but `workflow_run` capture is "write-only" from pilot perspective.

## Scope

### New Python API: CliCommands.search_memory()
```python
def search_memory(self, repo_path: str, query: str) -> CliReport:
    """Search workflow_run artifacts in repo's ContextHub."""
    # Returns structured results + human-readable summary
```

Returns `CliReport` with:
- `title`: "Memory Search: <repo>"
- `content`: Human-readable summary of results (e.g., "Found 3 guardrails runs, 2 decide runs recommending refactoring")
- `success`: True if query succeeded
- Structured field (from task-022): `search_results: Optional[list[WorkflowRunResult]]` 
  where `WorkflowRunResult` contains: `command`, `timestamp`, `intent/path`, 
  `success`, `artifact_id`

### New CLI command: ortho memory search
```
ortho memory search <query> [--repo-path <path>]
```

- Searches for keyword in workflow_run artifacts (title, content, tags)
- Default repo-path: current directory
- Output: human-readable list of matching runs with summaries
- Real implementation: uses ContextHub's BM25 search (FTS5) that already exists

### Implementation Plan
1. **CliCommands.search_memory()**: query ArtifactStore.search() filtered to 
   `type=="workflow_run"`, return results
2. **CLI bridge**: `memory_search.py` argparse wrapper (mirrors context.py pattern)
3. **CLI registration**: `ortho memory search` command in copilot.ts

## Acceptance Criteria
1. `search_memory(repo_path, "guardrails")` returns all workflow_run artifacts 
   with "guardrails" in title/content/tags.
2. `search_memory(repo_path, "refactor")` returns refactoring-related runs.
3. Text content summarizes results: "Found N workflow_run artifacts matching '<query>'" 
   with breakdown by command (e.g., "2 guardrails runs, 1 plan run, 1 decide run").
4. Structured results include artifact_id for later inspection if needed.
5. CLI `ortho memory search "guardrails" --repo-path repos/click` works end-to-end.
6. Empty query or no matches returns success=True with "No artifacts found" message.
7. All existing 170 tests still pass (no regressions).
8. New tests verify search against real captured workflow_run artifacts.

## Out of Scope
- Updating/deleting artifacts (read-only memory search)
- Complex query syntax (simple keyword matching, BM25 ranking)
- Exporting memory (future task)

## Non-Goals
- Machine learning on accumulated memory
- Recommendation synthesis from memory (future, Phase 7.2+)
