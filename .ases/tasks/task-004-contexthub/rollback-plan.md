---
task_id: task-004
title: Rollback Plan
status: APPROVED
created: 2026-06-30
owner: PLANNER
---

# Task-004 Rollback Plan

## Scenarios

### Scenario 1: Test/Verification Failures

**Trigger:** >10% of tests fail or verification discovers critical bug

**Action:**
1. Stop all work
2. Identify failing tests/evidence
3. Revert commits to last passing state: `git reset --hard origin/main`
4. If root cause in design: ARCHITECT rejects spec, restart at GATE-2
5. If root cause in code: BUILDER debugs and reworks implementation

**No permanent impact** — all work discarded, repo clean.

---

### Scenario 2: Architecture Rejection

**Trigger:** ARCHITECT review rejects spec or identifies design flaw

**Action:**
1. No code committed yet (still in review phase)
2. PLANNER + ARCHITECT rewrite spec
3. Return to GATE-2 for second review
4. Proceed only after approval

**No rollback needed** — nothing to undo.

---

### Scenario 3: Scope Creep / Integration Issue

**Trigger:** Implementation discovers ContextHub conflicts with Pillar 3 (Arch Intelligence) or requires changes to shared types

**Action:**
1. Halt atomic task causing conflict
2. Escalate to ARCHITECT for design decision
3. If requires spec change: replan (return to GATE-1)
4. If requires shared types change: defer to task-005 (Arch Intelligence depends on ContextHub anyway)

**Partial rollback:** Revert commits since last good state, keep working tasks.

---

### Scenario 4: External Library Unavailable

**Trigger:** sqlite-vec fails to build, anthropic API unavailable, gitpython incompatible

**Action:**

**If sqlite-vec fails to build:**
- Switch to pure SQL FTS5 (fallback: no semantic search)
- Mark semantic as deferred to Phase 2
- Update spec: `semantic_enabled = false` in config
- Proceed with BM25 + git metadata + project memory only

**If anthropic API unavailable:**
- Use local embedding model (HuggingFace `.gguf`)
- If .gguf fails: disable embeddings entirely
- Hybrid search degrades to BM25 only (acceptable for Phase 1)
- Update config: `embedding_enabled = false`

**If gitpython fails:**
- Git history becomes manual (skip git metadata in Phase 1)
- Update spec: `git_history_enabled = false`
- Proceed without churn metrics (non-blocking)

**No code rollback** — feature flags handle degradation.

---

### Scenario 5: Performance Issue (Search Timeouts)

**Trigger:** BM25/semantic search exceeds 500ms on 10k artifacts

**Action:**
1. Halt implementation
2. Add indexing/pagination strategy
3. ARCHITECT reviews and approves
4. BUILDER reimplement search with limits
5. Benchmark: verify <200ms per query
6. Proceed after performance verified

**Partial code revert** — rebuild search modules only.

---

## Rollback Procedure (by Phase)

### If Rollback Needed Before GATE-3 (Before BUILDER commits)

```bash
git status                          # Check what's staged
git reset --hard origin/main        # Discard all local changes
rm -rf packages/context-hub/src/*   # Clean implementation dir (keep schema.py skeleton)
```

**Impact:** Zero — nothing merged yet.

---

### If Rollback Needed After GATE-3 (After BUILDER commits)

```bash
# Find last good commit (task-003)
git log --oneline | grep "task-003"  # e.g., 286dd23

# Revert to it
git reset --hard 286dd23

# Verify
git status                          # should show clean
git log --oneline -1               # should be task-003
```

**Impact:** All task-004 commits removed. ContextHub package code discarded.

---

### Database Schema Rollback

**If migrations applied before rollback:**

```python
# In migration script (migrations/down.py)
def down():
    db = OrthoDatabase(project_root)
    db.execute("DROP TABLE IF EXISTS artifacts_fts")
    db.execute("DROP TABLE IF EXISTS artifacts")
    db.execute("DROP TABLE IF EXISTS artifact_embeddings")
    db.execute("DROP TABLE IF EXISTS git_history")
    db.execute("DROP TABLE IF EXISTS project_memory")
    db.commit()
```

**When to run:** Only if reverting after GATE-3 (after migrations committed).

---

## Contingency Decisions

| Issue | Decision |
|-------|----------|
| Embedding model slow | Defer to Phase 4, use BM25 only |
| FTS5 insufficient | Add pagination, limits (no full table scans) |
| sqlite-vec build fail | No semantic search in Phase 1 (acceptable) |
| Git history complex | Skip git metadata (Phase 1 doesn't require it) |
| Staleness FP rate high | Increase hash comparison tolerance |

---

## Success Criteria (Prevent Rollback)

- ✓ All 20 acceptance criteria pass
- ✓ 50+ tests run with 0 failures
- ✓ Coverage >85%
- ✓ No breaking changes to tasks 1-3 or shared types
- ✓ Schema migrations clean (no orphaned columns)
- ✓ Search latency <200ms per query
- ✓ Code review APPROVED (no major issues)

---

## Owner

- **ARCHITECT:** Decides if design rollback needed
- **BUILDER:** Decides if partial rollback needed
- **VERIFIER:** Decides if full rollback needed
- **REVIEWER:** Final sign-off after rollback (if any)

---

*Created: 2026-06-30 by PLANNER*
*Approved: Ready for GATE-1 human review*
