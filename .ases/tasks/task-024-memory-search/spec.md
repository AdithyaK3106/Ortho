# Spec — task-024-memory-search

## Python API: CliCommands.search_memory()

```python
def search_memory(self, repo_path: str, query: str) -> CliReport:
    """Search workflow_run artifacts in the repo's ContextHub.
    
    Args:
        repo_path: Path to the repository
        query: Search keyword (e.g., "guardrails", "refactor", "layer_boundaries")
    
    Returns:
        CliReport with:
        - title: "Memory Search: <repo>"
        - content: Human-readable summary + artifact list
        - success: True if search succeeded (even if no results)
        - search_results: list[WorkflowRunResult] with id/command/timestamp/intent/success
    """
```

**Implementation:**
1. Open `OrthoDatabase(repo_path)` and `ArtifactStore(db)` (same as task-020)
2. Call `ArtifactStore.search(query, artifact_type="workflow_run", limit=50)`
3. Format results to text:
   ```
   Memory Search: repos/click
   
   Found 5 workflow_run artifacts matching "guardrails":
   - guardrails: No violations found (success=True)
   - guardrails: 7 violations found (success=True)
   - guardrails: Scan failed (success=False)
   - plan: add caching (success=True)
   - decide: improve code quality (success=True)
   
   Breakdown: 3 guardrails runs, 1 plan run, 1 decide run
   ```
4. Build `search_results` list with parsed `WorkflowRunResult` objects

**Edge cases:**
- Empty query: return all workflow_run artifacts (or reject with error)
- No results: `success=True, content="No artifacts found matching '<query>'"`
- Nonexistent repo: `success=False, content="Repo path does not exist: <path>"`
- No .ortho/ortho.db: `success=True, content="No memory artifacts in this repo yet"`

## CLI Bridge: memory_search.py

```python
# apps/cli/src/commands/memory_search.py
def _main():
    parser = argparse.ArgumentParser(description="Search workflow memory")
    parser.add_argument("query", help="Search keyword")
    parser.add_argument("--repo-path", default=".", help="Repository path")
    args = parser.parse_args()
    
    from cli_commands.commands import CliCommands
    commands = CliCommands()
    report = commands.search_memory(args.repo_path, args.query)
    
    output = report.title + "\n\n" + report.content + "\n"
    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.exit(0 if report.success else 1)
```

## CLI Registration: copilot.ts

```typescript
export const memoryCommand = new Command()
  .command("memory <query>")
  .description("Search workflow_run artifacts in ContextHub")
  .option("--repo-path <dir>", "Repository path (default: current directory)")
  .action(async (query: string, options?: { repoPath?: string }) => {
    requireIntent(query, "memory");  // Validate non-empty query
    const args = ["search", query, "--repo-path", options?.repoPath || process.cwd()];
    await runPython("apps/cli/src/commands/memory_search.py", args);
  });
```

Register in `index.ts`:
```typescript
import { memoryCommand } from "./commands/copilot";
program.addCommand(memoryCommand);
```

## Real-Repo Verification

After task-020/021/022/023 have run against a repo (e.g., repos/click), that repo 
will have accumulated workflow_run artifacts. Example queries:

```bash
ortho memory search "guardrails"
# Returns: all guardrails runs, count, summary

ortho memory search "refactor"
# Returns: all refactor runs showing recommendations

ortho memory search "layer_boundaries"
# Returns: guardrails runs that detected layer violations

ortho memory search "high confidence"
# Returns: decide runs with high-confidence recommendations (keyword in content)
```
