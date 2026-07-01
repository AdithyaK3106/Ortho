# task-006: Rollback Plan
## CallGraphBuilder + Adapter Completion

**Task ID:** task-006  
**Rollback Owner:** HUMAN (decides when to invoke)  
**Estimated Rollback Time:** 5 minutes (git revert)

---

## Rollback Triggers

Rollback is invoked ONLY if one of these occurs:

| Trigger | Severity | Action |
|---------|----------|--------|
| VERIFIER reports test failures (exit ≠ 0) that BUILDER cannot fix in 1 session | CRITICAL | Rollback immediately |
| REVIEWER finds breaking security flaw | CRITICAL | Rollback immediately |
| Regressions in other packages (context-hub, arch-intelligence) from these changes | CRITICAL | Rollback immediately |
| Code introduces circular dependency | CRITICAL | Rollback immediately |
| Performance regression >2x on `ortho scan` benchmarks | MEDIUM | Rollback unless BUILDER agrees to optimize |
| Type checking fails (mypy strict) and cannot be fixed in 1 session | HIGH | Rollback |
| Lint errors and cannot be fixed in 1 session | HIGH | Rollback |

**Do NOT rollback for:**
- ✓ Legitimate xfail markers with documented reasons (these are acceptable)
- ✓ Regressions BUILDER can fix in same session
- ✓ Test failures BUILDER can fix in same session

---

## Pre-Rollback Checklist

Before invoking rollback:

1. [ ] Confirm trigger is one of the above
2. [ ] Attempt to fix in current BUILDER session (max 30 min)
3. [ ] If unfixable in 30 min → proceed to rollback
4. [ ] Document which trigger was hit in CLAUDE.md

---

## Rollback Procedure

### Step 1: Identify Commits to Revert

```bash
cd /path/to/ortho
git log --oneline -10 | grep -i task-006
```

Identify all commits labeled `task-006` or related to CallGraphBuilder/adapter changes.

### Step 2: Create Rollback Commit

```bash
# Find the commit before task-006 started
git log --oneline | grep task-005
# This is the last known-good commit

# Revert all task-006 commits
git revert <first-task-006-commit>..<last-task-006-commit> --no-edit
# OR simple cherry-pick revert if single commit
git revert <task-006-commit> --no-edit
```

### Step 3: Verify Rollback

```bash
# Confirm files are back to task-005 state
git status
git diff HEAD~1 packages/repo-intelligence/src/call_graph.py

# Run tests to verify we're back to baseline
pytest packages/repo-intelligence/tests/ -v --tb=short
# Should see: 31 PASSED, 28 XFAILED, 29 XPASSED (task-005 baseline)
```

### Step 4: Document Rollback

Update CLAUDE.md:

```markdown
## Rollback Event: task-006

**Date:** YYYY-MM-DD HH:MM UTC  
**Trigger:** [CRITICAL | HIGH | MEDIUM]  
**Reason:** [specific description]  
**Commit reverted:** [git hash]  
**Tests after rollback:** 31 PASSED, 28 XFAILED, 29 XPASSED  
**Status:** ROLLED-BACK → [Next action: rethink approach, restart PLANNER, etc.]
```

### Step 5: Notify Human

Rollback is complete when:
- [ ] All task-006 code removed
- [ ] Tests back to baseline (31 PASSED, 28 XFAILED, 29 XPASSED)
- [ ] CLAUDE.md updated with rollback event
- [ ] Git history shows revert commit
- [ ] No uncommitted changes

---

## Data Impact

**What gets rolled back:**
- All changes to `packages/repo-intelligence/src/call_graph.py`
- All changes to `packages/repo-intelligence/src/module_detector.py`
- All changes to `packages/repo-intelligence/src/import_graph.py`
- All changes to `packages/repo-intelligence/src/symbol_extractor.py`

**What stays intact:**
- `.ortho/` databases (no schema changes)
- Other packages (context-hub, arch-intelligence, cli)
- Test files (tests are only read, not modified)
- shared/types and shared/storage

**No data loss:** SQLite databases are unaffected. Rollback is code-only.

---

## Recovery Path (After Rollback)

1. **Analyze failure:** Human examines BUILDER session output to identify root cause
2. **Decision:** 
   - A) Restart PLANNER → revise spec with lessons learned
   - B) Restart BUILDER → try different implementation approach
   - C) Defer task → mark as blocked, move to next task
3. **CLAUDE.md update:** Document decision and next steps
4. **Restart if continuing:** Start fresh PLANNER or BUILDER session (new session context)

---

## Rollback Success Criteria

Rollback is successful when:

- ✓ `git log` shows revert commit
- ✓ `pytest packages/repo-intelligence/tests/ -v` exits 0 with baseline results
- ✓ No uncommitted changes
- ✓ No merge conflicts
- ✓ `.ortho/` databases intact
- ✓ Other test suites pass (context-hub, arch-intelligence)

---

## If Rollback Itself Fails

**Scenario:** `git revert` encounters conflicts or data corruption

**Recovery:**
1. `git reset --hard <last-good-commit>` (use task-005 commit hash)
2. Verify: `pytest packages/repo-intelligence/tests/ -v`
3. Document in CLAUDE.md with timestamp
4. Contact human — this is a critical state

---

*Created by PLANNER*  
*Reviewed before GATE 1 approval*  
*Status: DRAFT*
