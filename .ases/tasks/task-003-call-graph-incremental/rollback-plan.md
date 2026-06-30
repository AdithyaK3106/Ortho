# Task-003 Rollback Plan

**Status:** DRAFT  
**Trigger Conditions:** See spec.md rollback triggers

---

## Overview

If task-003 implementation fails or violates scope, this plan restores the repo to a known good state (task-002 HEAD commit).

All implementation is atomic: each of the 5 tasks commits separately, allowing surgical rollback if needed.

---

## Rollback Triggers

When ANY of these occur, execute rollback immediately:

1. **Build fails** — `npm run build` exits with error, or `mypy` fails
2. **Lint fails** — `npm run lint` exits with error
3. **Tests fail** — > 3 test failures (not easily fixed)
4. **Call graph confidence drops below 0.5** — > 50% of calls marked unreliable
5. **Incremental indexer misses files** — re-index misses > 10% of actual changes
6. **Watch mode CPU spike** — Idle CPU usage > 20%
7. **Git integration broken** — `git diff` fails when it shouldn't
8. **Scope violation** — files modified outside spec, or new dependencies added without approval

---

## Rollback Procedure

**Estimated time:** 3 minutes (full rollback), 30 seconds (partial rollback of last task)

### Full Rollback (to task-002 HEAD)

```bash
# Step 1: Verify current state
git status
git log --oneline -n 10

# Step 2: Identify task-002 commit (example: 5b8f8a2)
# From CLAUDE.md, task-002 commit: 5b8f8a2

# Step 3: Reset working tree to task-002 HEAD
git reset --hard 5b8f8a2

# Step 4: Verify rollback successful
git status       # should show "On branch main, nothing to commit"
npm run build    # should succeed
npm run lint     # should succeed
npm run test     # should pass

# Step 5: Update CLAUDE.md
# - Mark task-003 as FAILED
# - Document reason in notes
# - Set next step: return to PLANNER with feedback
```

### Partial Rollback (last atomic task only)

If only task 5 (watch mode / CLI) failed, and tasks 1–4 are solid:

```bash
# Step 1: Identify the most recent task-003-task-N commit
git log --oneline | grep -i "task-003"

# Step 2: Find the commit BEFORE the failing task
# Example: if task-5 failed, find task-4 commit

# Step 3: Reset to that commit
git reset --hard <task-4-commit-hash>

# Step 4: Verify build/lint/tests pass
npm run build
npm run lint
npm run test

# Step 5: Update CLAUDE.md
# - Move task state back (IMPLEMENTED → BUILDER can fix task 5 in new session)
# - Document what failed (specific line, error message)
```

### Verify Rollback Success

After rollback, confirm:

```bash
# 1. Database is clean (only task-001 + task-002 data)
sqlite3 .ortho/ortho.db ".tables"
sqlite3 .ortho/ortho.db "SELECT COUNT(*) FROM symbols;"
# Should match task-002 symbol count (~1,245)

# 2. Code builds and lints
npm run build    # Exit 0
npm run lint     # Exit 0

# 3. Tests pass (no regressions from task-002)
npm run test     # All tests pass
npm run test -- --coverage  # Coverage ≥ 80%

# 4. Git log clean (no task-003 commits)
git log --oneline -n 5
# Should show task-002 as HEAD, no task-003- prefixed commits
```

---

## Partial Rollback Decision Matrix

| Failing Task | Action | Why |
|--------------|--------|-----|
| Task 1 (CallGraphBuilder) | Full rollback | Core dependency for tasks 2–5 |
| Task 2 (DependencyGraphBuilder) | Full rollback | Tasks 4–5 depend on working modules |
| Task 3 (ModuleDetector) | Full rollback | Task 4 depends on it |
| Task 4 (IncrementalIndexer) | Partial + fix | Task 5 can proceed with full-index only |
| Task 5 (Watch mode / CLI) | Partial + fix | Tasks 1–4 standalone, CLI optional (for now) |

---

## Data Recovery (if needed)

If rollback is performed AFTER implementation-notes.md is written:

1. Save implementation-notes.md to external location (backup)
2. Execute rollback (git reset --hard)
3. BUILDER examines backup to understand what failed
4. BUILDER fixes issues and resubmits (new session, fresh context)

---

## Prevention

To minimize rollback risk:

1. **Commit each atomic task separately** — don't batch all 5 together
2. **Test as you go** — after each task, run full build/lint/test suite
3. **No feature-gating** — all code committed is live (no flags)
4. **Binary acceptance criteria** — if criteria not met, BUILDER knows immediately
5. **ARCHITECT validates design before implementation** — prevents major rework

---

## Post-Rollback Steps

If rollback is executed:

1. **BUILDER logs root cause** in rollback-event.md:
   - What failed (specific line, error, test)
   - Why it failed (design flaw, environment, scope violation)
   - What would fix it

2. **ARCHITECT (if needed) revises design** in architecture-review.md:
   - Update failed module boundaries
   - Clarify API contracts that were misunderstood
   - Identify circular dependencies or coupling issues

3. **PLANNER (if needed) revises spec** in spec.md:
   - Clarify acceptance criteria
   - Simplify scope if needed
   - Document lessons learned

4. **BUILDER session 2** implements fixes (fresh session, zero context from failed attempt)

---

## Emergency Contacts (for solo developer)

If rollback is unclear or repo is in inconsistent state:

1. Check git log for task-002 commit hash
2. Verify task-002 passes all tests (`npm run test`)
3. Use that as safe fallback (git reset --hard <commit>)
4. Document state in CLAUDE.md
5. Restart BUILDER session from scratch with clearer spec

---

## Verification Checklist (After Rollback)

- [ ] `git status` shows clean working tree
- [ ] `git log` shows task-002 as most recent task commit
- [ ] No task-003- prefixed commits in log
- [ ] `npm run build` exits with 0
- [ ] `npm run lint` exits with 0
- [ ] `npm run test` passes (all existing tests)
- [ ] Database has only task-001 + task-002 data
- [ ] `.ortho/config.json` unchanged
- [ ] CLAUDE.md updated with rollback reason

---

*End of rollback-plan.md. PLANNER complete.*
