# Feature Specification

**Task ID:** task-025
**Task Title:** Git History as an Architecture Evidence Source
**Owner:** Solo Developer
**Created:** 2026-07-22
**Status:** DRAFT

---

## Objective

`GitMetadataStore` (context-hub) already defines a `git_history` table with
per-commit `message`, `author`, `commit_date` — but `load_git_history()` is
never called from `ortho scan`/`ortho index`, so the table is always empty
today. This task wires it in, then uses the data three ways requested by the
user: (1) commit messages as decision-engine evidence, (2) churn weighting
for arch-intelligence/refactoring-advisor findings, (3) a branch-diff check
for pre-merge architecture drift. No new subsystem — three small additive
uses of data the schema already models.

**ponytail note:** GitMetadataStore already exists and is fully built; this
is a wiring + consumption task, not a new store. Resist the urge to build a
generic "git intelligence" package — bolt onto the three existing consumers
(scan_cli, decision-engine sources dict, a new `guardrails --against-branch`
flag) instead.

---

## Part 1 — Wire `GitMetadataStore` into `ortho scan`

**File:** `packages/repo-intelligence/src/repo_intelligence/scan_cli.py`

After `indexer.index_repository()` succeeds, call
`GitMetadataStore(db.conn, repo_root, repo_id).load_git_history(file_id, rel_path)`
for every scanned file (loop over `store`'s known files — reuse whatever the
indexer already returns, do not re-query the filesystem).

Non-blocking per existing docstring contract ("failures logged but not
raised") — a repo scan must not fail because git history query failed.

**Edge case:** not a git repo → `GitMetadataStore._init_git_repo` already
returns `None` and `load_git_history` already no-ops. No new handling needed.

---

## Part 2 — Commit messages as decision-engine evidence

**New file:** `packages/context-hub/src/context_hub/commit_evidence.py`

```python
@dataclass
class CommitEvidence:
    title: str          # first line of commit message
    description: str    # full message
    source: str = "git_history"
    commit_hash: str
    author: str
    commit_date: str
    confidence: float   # keyword-match strength, 0.0-1.0

def find_relevant_commits(
    db: sqlite3.Connection, repo_id: str, query: str, limit: int = 5
) -> list[CommitEvidence]:
    """Search git_history.message for query words (reuse the same word-tokenize
    approach as decision_engine._words — split on non-alnum, lowercase,
    Jaccard-style overlap against query). Return top `limit` by overlap,
    ties broken by most recent commit_date."""
```

**Wire into decision-engine:** `DecisionEngine.decide()` already accepts
`sources: dict[str, list[Any]]` and dispatches on source name in
`_convert_to_recommendation`. Add a `git_history` branch:

```python
elif source == "git_history":
    return Recommendation(
        title=f"Prior commit: {item.title}",
        description=item.description,
        source="git_history",
        effort="low",
        risk="low",
        confidence=item.confidence,
        suggested_fix="Review this commit for prior context before proceeding.",
        evidence=[f"{item.commit_hash[:8]} by {item.author} on {item.commit_date}"],
    )
```

Caller (`CliCommands.decide`) passes `sources["git_history"] =
find_relevant_commits(db.conn, repo_id, intent)` alongside the existing
change_planner/feature_planner/refactoring_advisor/arch_guardrails sources.

**Edge case:** no commits match query words → empty list, `decide()`'s
existing "no options" path already handles zero sources gracefully.

---

## Part 3 — Churn weighting for arch-intelligence / refactoring-advisor

**File:** `packages/refactoring-advisor` (wherever confidence is currently a
constant — grep `confidence=` in refactoring_advisor's finding builder).

Add an optional churn multiplier: a file with `commit_count > 20` (from
`GitMetadataStore.get_file_churn`) bumps a finding's confidence by a fixed
+0.1 (capped at 1.0), reflecting that frequently-changed files are
higher-risk targets for the bloat/coupling/cycle issues this package already
detects. This is a weighting on existing findings, not a new finding type.

**ponytail note:** a flat +0.1 threshold bump is the lazy version — skip
building a decay curve or configurable weighting scheme until a pilot shows
the flat bump is wrong.

**Edge case:** no git history available (empty repo, git not installed) →
`get_file_churn` already returns `commit_count=0`, multiplier does not apply,
confidence unchanged.

---

## Part 4 — Branch drift check (pre-merge)

**File:** `packages/cli-commands/src/cli_commands/commands.py`,
`guardrails()` method.

Add `--against-branch <name>` kwarg. When set: use GitPython to diff current
HEAD against `<name>`, get the list of changed files
(`repo.git.diff("--name-only", against_branch)`), and restrict
`ArchitectureEnforcer.check_violations()` to only those files (it already
takes a `path` filter — reuse that, do not build a new enforcer).

Output: same `CliReport` shape as `guardrails` today, but title becomes
`"Guardrails (vs {against_branch}): {repo}"` and content is prefixed with
the changed-file count, so it reads as a pre-merge check rather than a
whole-repo scan.

**Edge case:** `against_branch` doesn't exist locally → catch
`git.GitCommandError`, return `CliReport(success=False, content=f"Branch
'{against_branch}' not found locally. Fetch it first.")`.

---

## Files to Create or Modify

### Create
- `packages/context-hub/src/context_hub/commit_evidence.py`
- `packages/context-hub/tests/test_commit_evidence.py`
- `packages/cli-commands/tests/test_guardrails_branch_diff.py`

### Modify
- `packages/repo-intelligence/src/repo_intelligence/scan_cli.py` — call `load_git_history` per file after indexing
- `packages/decision-engine/src/decision_engine/engine.py` — add `git_history` source branch
- `packages/cli-commands/src/cli_commands/commands.py` — `decide()` passes git_history source; `guardrails()` gains `--against-branch`
- `packages/refactoring-advisor/src/refactoring_advisor/*.py` — churn confidence bump (exact file TBD at BUILDER time, grep for finding-confidence constant)
- `apps/cli/src/commands/copilot.ts` — expose `--against-branch` flag on `guardrails` command

---

## Test Plan (must run, real pytest, no simulated logs — per CLAUDE.md §3)

- `pytest packages/context-hub/tests/test_commit_evidence.py -v` — keyword match, ranking, empty-query, no-match cases
- `pytest packages/repo-intelligence/tests/ -v` — scan still succeeds on a repo with no git and a repo with git; git_history table populated after scan on a real fixture repo
- `pytest packages/decision-engine/tests/ -v` — `decide()` includes git_history recommendations when sources contain matching commits, degrades gracefully when empty
- `pytest packages/refactoring-advisor/tests/ -v` — confidence bump applies only when churn > 20, capped at 1.0
- `pytest packages/cli-commands/tests/test_guardrails_branch_diff.py -v` — restricts violations to changed-file set, handles missing branch

---

## Explicitly Out of Scope (do not build)

- A generic "git intelligence" package/subsystem — this bolts onto three existing consumers.
- Full diff/patch parsing (`diff_lines_added`/`removed` stay 0 as already documented "deferred to Phase 2" in git_metadata.py — not this task's problem).
- Configurable churn-weighting curves, decay functions, or a scoring DSL.
- Remote branch fetching — `--against-branch` only diffs local refs.
