# Task-014: Rollback Plan

**Rollback Triggers:**
- BUILD fails: compilation errors in token-optimizer or orchestration modifications
- REGRESSION: existing orchestration/context-hub tests fail after integration changes
- CRITICAL ISSUE: circular import detected between orchestration → token-optimizer → context-hub
- SCOPE VIOLATION: feature creep attempts to add semantic reranking/embeddings before infrastructure ready

---

## Local Rollback (Uncommitted Changes)

**Condition:** Task-014 implementation not yet committed to git

**Steps:**
```bash
# Discard all local changes and return to pre-task-014 state (commit 3f2a59e)
git reset --hard 3f2a59e
git clean -fd                          # Remove untracked files (new token-optimizer/ directory)
```

**Verification:**
```bash
# Confirm no token-optimizer directory exists
ls -d packages/token-optimizer/src/ 2>&1 && echo "FAILED: directory still exists" || echo "OK: cleaned"

# Confirm imports resolve (no broken TaskBudget import)
python -c "from packages.orchestration.src.selector.engine import SelectorEngine; print('OK')" 2>&1

# Confirm orchestration tests still pass
pytest packages/orchestration/tests/ -q 2>&1 | tail -1
```

---

## Published Rollback (Committed to main)

**Condition:** Task-014 commit(s) already pushed to remote/main

**Steps:**
```bash
# Create revert commit(s) — one per task-014 commit
# (BUILDER will have made granular commits per atomic task; revert each in reverse order)

# Identify task-014 commits (should start with "task-014:" prefix per feature.md Commit Message Format)
git log --oneline --grep="task-014" main

# Revert in reverse chronological order (latest first)
# Example: if 5 commits for the 5 atomic tasks, revert the 5th, then 4th, ... then 1st
git revert -n <commit-hash-5>          # -n = no-commit; batch them
git revert -n <commit-hash-4>
git revert -n <commit-hash-3>
git revert -n <commit-hash-2>
git revert -n <commit-hash-1>

# Create single rollback commit
git commit -m "Rollback task-014: Token Optimizer (reason: [specify trigger])"
```

**Why revert instead of reset --hard:**
- Reset would lose the commits from the history; revert creates a new commit that undoes them
- Revert is safe for shared branches (doesn't rewrite history)
- Evidence of the rollback remains in the git log for analysis

**Verification After Revert:**
```bash
# Confirm revert is clean (no merge conflicts)
git status | grep "nothing to commit" && echo "OK: no conflicts" || echo "CONFLICT: resolve manually"

# Confirm workflow_executor.py reverted to stub
grep "context_package=None" packages/orchestration/src/executor/workflow_executor.py && echo "OK: stub restored" || echo "FAILED"

# Confirm broken import is back (expected)
python -c "from apps.api_server.src.routers.orchestration import TokenBudget" 2>&1 | grep "ModuleNotFoundError" && echo "OK: expected import error restored"

# Regression check
pytest packages/orchestration/tests/ -q 2>&1
```

---

## Clean-Up After Rollback

**Remove task-014 evidence and artifacts:**
```bash
# If rolling back before first VERIFIER run, delete evidence directory
rm -rf .ases/evidence/task-014/

# Delete task-014 plan/spec artifacts (optional; keep for post-mortem)
# rm -rf .ases/tasks/task-014-token-optimizer/
```

**Update CLAUDE.md:**
```markdown
## Rollback Record

**Task:** task-014 (Token Optimizer, Pillar 5)  
**Date:** [YYYY-MM-DD]  
**Trigger:** [BUILD | REGRESSION | CIRCULAR-IMPORT | SCOPE-VIOLATION]  
**Commits Reverted:** [list hash(es)]  
**Reason:** [specific details]  
**Status:** ROLLED-BACK → Ready for rework or reassessment

The feature is deferred to a later phase or iteration. Root cause analysis:
- [If BUILD: compilation errors, missing imports, type issues]
- [If REGRESSION: which tests broke, why existing code now incompatible]
- [If CIRCULAR-IMPORT: dependency chain that created cycle]
- [If SCOPE-VIOLATION: what creep occurred and why it was rejected]
```

---

## Decision Tree for Rollback vs. Fix-Forward

**When to rollback:**
- Circular dependency between packages (architecture violation, hard to fix)
- Regression affecting more than 5 existing tests (suggests deep integration bug)
- BUILD failure in a different package (token-optimizer broke orchestration API)
- Critical design conflict discovered (e.g., TokenBudget needs to be mutable but shared, causing state issues)

**When to fix-forward (BUILDER continues):**
- Single failing test in token-optimizer's own suite (fix the test or code)
- Import error due to missing __init__.py (simple fix)
- Type mismatch in local code (localized to token-optimizer)
- Minor regression (1-2 tests, easy cause identified)

---

## Rollback Success Criteria

After executing rollback:

- [ ] `git status` shows clean working tree (no uncommitted changes)
- [ ] `git log --oneline -5` does not include task-014 commits
- [ ] `ls packages/token-optimizer/src/` fails (directory deleted or never created)
- [ ] `python -c "from packages.token_optimizer import TokenBudget"` fails with ModuleNotFoundError
- [ ] `workflow_executor.py:118` contains `context_package=None,  # Stubbed; token optimizer (task-014) provides this`
- [ ] All orchestration/context-hub regression tests pass (0 failures)
- [ ] CLAUDE.md updated with rollback record and reason

---

*End of rollback-plan.md*
