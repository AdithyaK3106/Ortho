# Rollback Plan

**Task ID:** task-001  
**Feature:** Phase 1 Week 1–2 — Shared Foundation  
**Created:** 2026-06-30

---

## Rollback Trigger

Rollback is required if any of these occur:

- Type checking fails: `tsc --noEmit` or `mypy --strict` return non-zero exit code
- Linting fails: `eslint` returns non-zero exit code
- Monorepo structure breaks: `poetry show` fails
- Schema validation fails: SQL syntax errors in 001_initial_schema.sql
- CLI `ortho init` command fails to create `.ortho/` structure
- FastAPI server fails to start or `/health` endpoint returns non-200
- Test failures during verification (not applicable to Phase 1 Week 1–2, but included for completeness)
- Critical issues found in architecture review
- Database migration cannot be applied (SQL errors)
- Dependency conflicts between packages (circular dependencies)

---

## Rollback Procedure

[Exact git commands. Repeatable.]

### Step 1: Identify the commit to revert

```bash
# Find recent commits related to task-001
git log --oneline --grep="task-001" | head -5

# Or find all commits since feature started
git log --oneline | head -10

# Note the commit hash(es): [commit-hash]
# If multiple commits, revert the earliest one first
```

### Step 2: Revert all commits for this task

```bash
# If task-001 was a single commit:
git revert [commit-hash]

# If task-001 spans multiple commits, revert each in reverse order:
git revert [latest-commit]
git revert [middle-commit]
git revert [earliest-commit]

# Or use git reset if commits have not been pushed:
git reset --hard [previous-commit-hash]
```

### Step 3: Delete task-001 folders (if reset was used)

```bash
# If reset --hard was used, folders may still exist locally
rm -rf .ases/tasks/task-001-shared-foundation
rm -rf .ases/architecture/adrs/ADR-001-*
rm -rf .ases/architecture/adrs/ADR-002-*

# Re-run git status to verify working directory is clean
git status
```

### Step 4: Verify git history is clean

```bash
# Check log shows revert commits or no task-001 commits
git log --oneline | head -20

# Check status is clean
git status
# Should show "On branch main, nothing to commit, working tree clean"
```

---

## Affected Components

If rollback occurs:

- Monorepo structure: back to state before task-001 (possibly no packages/ or shared/ folders)
- Shared types: removed or reverted to previous version
- Storage layer: removed
- CLI: removed or reverted
- API server: removed or reverted
- Database: not yet initialized (no `.ortho/` directory)
- ADRs: ADR-001 and ADR-002 removed

**Business Impact:**
- Cannot run `ortho init` (CLI doesn't exist or is broken)
- Cannot proceed to Phase 1 Week 3–4 (Repo Intelligence)
- No infrastructure foundation for subsequent weeks

---

## Verification After Rollback

### Git/Code Verification

```bash
# Type checking passes
tsc --noEmit
# Exit code should be 0 (or no TypeScript files to check if fully rolled back)

# Python linting passes
mypy --strict .
# Exit code should be 0 (or no Python files to check if fully rolled back)

# Git status is clean
git status
# Should show "nothing to commit, working tree clean"

# Verify task-001 folders are gone
ls -la .ases/tasks/ | grep task-001
# Should return nothing (no task-001 folder)
```

### Functional Verification

```bash
# If CLI still exists from before rollback
ortho --help
# Should show help (or error "command not found" if fully rolled back)

# If .ortho/ directory was created
ls -la .ortho/
# Should not exist (rolled back)

# Check previous state is restored
git log --oneline | head -1
# Should not mention "task-001"
```

### Archive Verification

```bash
# Check CLAUDE.md for rollback note
cat CLAUDE.md | grep -i rollback
# Should show rollback was recorded

# Check status.md is updated
cat status.md | grep -i "task-001" | grep -i "ROLLED-BACK"
```

---

## Known Rollback Limitations

**What cannot be automatically rolled back:**

1. **Files created outside git:** If CLI or build artifacts were created but not committed, `git revert` won't delete them.
   - **Mitigation:** Manually delete `packages/`, `shared/`, `apps/` folders if they persist after rollback

2. **Package manager lock files:** `poetry.lock` and `package-lock.json` may be out of sync after rollback.
   - **Mitigation:** Re-run `poetry lock` and `npm install` after rollback

3. **Local database files:** If `.ortho/ortho.db` was created locally during testing, rollback won't delete it.
   - **Mitigation:** Manually delete `.ortho/` folder if it exists

4. **Uncommitted changes:** If you made local changes not yet committed, `git revert` won't affect them.
   - **Mitigation:** `git restore .` to discard uncommitted changes before rolling back

5. **Memory/Context:** Notes in status.md, CLAUDE.md about task-001 progress won't be automatically removed.
   - **Mitigation:** Manually update CLAUDE.md and status.md to reflect rollback

---

## Rollback Checklist

Before declaring rollback complete, verify all of these:

- [ ] `git log --oneline` shows revert commit or no task-001 commits
- [ ] `git status` shows "working tree clean"
- [ ] `tsc --noEmit` passes (exit 0) or no TypeScript files
- [ ] `mypy --strict .` passes (exit 0) or no Python files
- [ ] `.ases/tasks/task-001-*` folder does not exist
- [ ] `.ases/architecture/adrs/ADR-001-*` does not exist
- [ ] `.ases/architecture/adrs/ADR-002-*` does not exist
- [ ] `packages/`, `shared/`, `apps/` folders either don't exist or are in clean state
- [ ] `.ortho/` folder does not exist (or is empty)
- [ ] `CLAUDE.md` updated with rollback reason
- [ ] `status.md` updated to reflect rolled-back state
- [ ] Team notified (if applicable)

---

## Rollback Owner

- **Trigger authority:** Human developer (after reviewing verification failures or code review issues)
- **Executor:** Human (runs git revert or reset commands)
- **Verifier:** Human (runs verification commands to confirm rollback succeeded)

---

## Post-Rollback Action

After successful rollback:

1. **Analyze root cause:** Why did task-001 fail?
   - Type errors in shared types?
   - Schema design issue?
   - CLI/API integration problem?
   - Configuration structure wrong?

2. **Document findings:** Update CLAUDE.md with:
   - Rollback timestamp
   - Root cause
   - What went wrong
   - What to fix in next attempt

3. **Update task plan:** PLANNER creates revised plan addressing the root cause
   - If types were wrong: what types need fixing?
   - If schema wrong: what schema needs changing?
   - If CLI wrong: what CLI approach should be different?

4. **Create new task:** task-002-shared-foundation-retry (if needed)
   - OR task-001-v2 (if iterating on same scope)
   - Repeat ASES workflow with revised plan

5. **Return to PLANNER:** Start over with updated understanding

---

## Example Rollback Scenario

**Scenario:** Type checking fails because TypeScript types don't match Python expectations.

```
1. Rollback trigger detected: tsc --noEmit returns exit 5 (type errors)

2. VERIFIER reports: "Type errors in shared/types/artifact.ts"

3. Rollback procedure:
   git log --oneline | head -5
   # Output: abc123 task-001: shared foundation complete
   
   git revert abc123
   # Creates revert commit

4. Verification:
   tsc --noEmit
   # Exit 0 (no more type errors because task-001 is rolled back)

5. Root cause analysis:
   - Artifact type used union types that Python couldn't deserialize
   - JSON serialization didn't match TypeScript interfaces
   - Need to redesign types for Python/JS interop

6. Update CLAUDE.md:
   Rollback: task-001 (2026-06-30 14:30 UTC)
   Reason: Type errors in shared/types/artifact.ts
   Root cause: JSON serialization mismatch between TypeScript and Python
   Next action: PLANNER designs type schema for language interop before implementation

7. PLANNER creates task-001-v2 with revised type design
```

---

## Prevention

To avoid rollback:

1. **Type Safety First:** Before BUILDER writes code, TEST-DESIGNER creates type validation tests
2. **Schema Review:** ARCHITECT reviews schema line-by-line against FRD before BUILDER applies migrations
3. **Integration Tests:** VERIFIER tests CLI → API → Storage flow before marking complete
4. **Incremental Commits:** Commit each subtask (monorepo, types, storage) separately so rollback can be granular
5. **Type Checking on Every Change:** Run `tsc --noEmit` and `mypy --strict` after each commit

---

*End of rollback-plan.md*
