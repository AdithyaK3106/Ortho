---
task_id: task-004
title: Rollback Plan
status: APPROVED
created: 2026-06-30
owner: PLANNER
---

# Task-004 Rollback Plan

## Overview

This document specifies how to safely roll back task-004 if implementation, testing, or verification fails. All rollback procedures use audit-friendly `git revert` (not destructive `reset --hard`).

---

## Scenarios and Procedures

### Scenario 1: Design Rejection (pre-implementation)

**Trigger:** ARCHITECT review identifies architectural flaw before BUILDER starts

**Decision Authority:** ARCHITECT

**Action:**
1. No code committed — safe to redesign
2. PLANNER + ARCHITECT rewrite affected spec sections
3. Return to GATE-2 for second review
4. Proceed only after approval

**Rollback Procedure:** Not needed (no code to revert)

**Impact:** Zero

---

### Scenario 2: Implementation Blocked (during BUILDER)

**Trigger:** Code complexity, unforeseen dependencies, library incompatibility

**Decision Authority:** ARCHITECT (with BUILDER input)

**Examples:**
- FTS5 trigger syntax errors (non-standard SQL)
- EmbeddingProvider interface too complex (refactor needed)
- sqlite-vec integration failures
- GitPython incompatibility with Python version

**Evaluation:**
1. **Workaround feasible?** → Preferred. BUILDER implements fix, reruns tests.
2. **Design change needed?** → Return to GATE-1 (spec revision), then GATE-2
3. **Defer feature to Phase 2?** → Reduce scope, update plan, document in ADR

**Rollback Procedure (if partial revert needed):**

Use `git revert` to remove specific commits:

```bash
# Identify failing commit(s)
git log --oneline task-004/   # find which commit broke something

# Revert cleanly (creates new commit with audit trail)
git revert --no-edit <commit-hash>

# Verify
git status                     # clean
git log --oneline -1           # should show "Revert: ..."
```

**Cleanup (if abandoning feature entirely):**

```bash
# Remove all task-004 code (create clean revert)
git revert --no-commit <all-task-004-commits>
rm -rf packages/context-hub/src/*
git add packages/context-hub/
git commit -m "[task-004] ROLLBACK: Feature incomplete, deferred to [reason]"
```

**Impact:** Clear audit trail. No lost history. Next task starts from known good state.

---

### Scenario 3: Test Failures (VERIFIER phase)

**Trigger:** >10% of tests fail; verification discovers critical bug

**Decision Authority:** VERIFIER (with BUILDER)

**Examples:**
- Versioning logic creates duplicate versions
- FTS5 triggers not firing correctly
- Staleness detector has false negatives
- Search results malformed

**Triage:**
1. **Bug in single module?** → BUILDER fixes, reruns tests
2. **Bug in architecture?** → Escalate to ARCHITECT
3. **Unfixable in time?** → Full rollback

**Rollback Procedure (surgical fix):**

```bash
# Revert one problematic commit
git revert --no-edit <buggy-commit>

# Or: remove one feature entirely
git revert --no-commit <feature-commits...>
rm -rf packages/context-hub/src/feature_file.py
git commit -m "[task-004] ROLLBACK: Remove [feature] due to test failure"
```

**Rollback Procedure (full revert):**

```bash
# Revert entire task-004
git log --oneline task-004/ | head -20  # list all task-004 commits

# Create single clean revert commit
git revert --no-edit <oldest-task-004-commit>^..<newest-task-004-commit>
git commit --amend -m "[task-004] ROLLBACK: Entire task due to fundamental issue"

# Verify
git log --oneline -5
git status                    # clean
```

**Impact:** Clear. No lost work (commits still in history). Repo ready for retry.

---

### Scenario 4: External Library Unavailable

**Trigger:** Dependency fails to build or is incompatible

**Decision Authority:** BUILDER (escalate if blocking multiple features)

| Failure | Impact | Mitigation |
|---------|--------|-----------|
| `sqlite-vec` build fails | No semantic search | Use FTS5 only; mark semantic deferred |
| `gitpython` import error | No git history | Skip git metadata; core features work |
| `anthropic` SDK missing | No Anthropic embeddings | Use `NullEmbedding`; config switches providers |

**Rollback Procedure (feature flag degradation):**

No code rollback needed. Update config:

```toml
# .ortho/config.toml
[context_hub]
semantic_search_enabled = false       # if sqlite-vec unavailable
git_history_enabled = false           # if gitpython unavailable
embedding_provider = "null"           # if anthropic unavailable
```

**Code change (if feature entirely unavailable):**

```python
# conditional import
try:
    from semantic_search import SemanticSearch
except ImportError:
    SemanticSearch = None  # graceful skip
```

**Commit:**
```bash
git commit -m "[task-004] DEGRADE: Disable [feature] (library unavailable in Phase 1)"
```

**Impact:** Minimal. Core features unaffected. Phase 2 can add back.

---

### Scenario 5: Performance Regression (Benchmark)

**Trigger:** Search latency exceeds 500ms on 5k artifacts

**Decision Authority:** VERIFIER (with BUILDER)

**Diagnosis:**
1. Identify bottleneck: FTS5 query plan? Vector search? Python loop?
2. Profile with benchmark suite
3. ARCHITECT evaluates: optimize or defer?

**Optimization Procedure:**

```bash
# Option 1: Revert slow commit, reimplement
git revert --no-edit <slow-commit>

# Option 2: Fix in place
# (edit the file, rerun benchmark)
git add packages/context-hub/
git commit -m "[task-004] PERF: Optimize [search] latency"

# Verify
./benchmarks/bench_search.py          # should show improvement
```

**Deferral Procedure:**

If optimization infeasible:

```bash
# Mark feature as Phase 4 (Token Optimizer)
git revert --no-commit <perf-critical-feature>
git commit -m "[task-004] DEFER: [Feature] optimization deferred to Phase 4"
```

**Impact:** Localized. Phase 4 handles caching/optimization.

---

### Scenario 6: Concurrent Modification Conflict

**Trigger:** Multiple tasks/PRs conflict during merge (unlikely in solo dev)

**Decision Authority:** REVIEWER

**Procedure (if merging with another branch):**

```bash
# Identify conflict
git status                    # shows CONFLICT

# Option 1: Ours (task-004 version)
git checkout --ours .
git add .
git commit -m "[task-004] MERGE: Resolved conflict (task-004 version preferred)"

# Option 2: Theirs (other task)
git checkout --theirs .
git add .
git commit -m "[task-004] MERGE: Resolved conflict (reverted to [other-task])"

# Option 3: Manual merge
# (edit conflicted files, resolve, commit)
```

**Impact:** Minimal. Clear commit message documents decision.

---

## Schema Rollback (if applied)

**If migrations committed but task rolled back:**

```python
# In migrations/down.py
def down():
    db = OrthoDatabase(project_root)
    db.execute("DROP TABLE IF EXISTS git_history")
    db.execute("DROP TABLE IF EXISTS artifacts_fts")
    db.execute("DROP TABLE IF EXISTS artifacts")
    db.execute("DROP TABLE IF EXISTS artifact_embeddings")
    db.execute("DROP TABLE IF EXISTS project_memory")
    db.commit()
```

**Run during rollback:**

```bash
python migrations/down.py
git add migrations/
git commit -m "[task-004] ROLLBACK: Undo schema migrations"
```

**Verify:**

```bash
# Schema should match task-003 baseline
sqlite3 .ortho/ortho.db ".schema artifacts"   # should be empty
```

---

## Contingency Decisions

| Issue | Decision |
|-------|----------|
| Semantic search slow | Defer to Phase 4 (search caching) |
| Embedding model unavailable | Use NullEmbedding (config-driven) |
| FTS5 triggers complex | Simplify: manual sync in Python (acceptable trade-off) |
| Git history parsing fails | Skip git metadata (non-blocking, Phase 2 scope) |
| Project memory schema conflict | Use simple key/value store (compatible) |
| Staleness detection unreliable | Disable on-retrieval checks; Phase 4 adds scheduled verification |

---

## Prevention Checklist

To avoid rollback, verify before committing:

- ✓ All validation rules tested (edge cases: empty strings, special chars, large content)
- ✓ FTS5 triggers firing (insert, update, delete all tested)
- ✓ Embedding provider abstraction used (no Anthropic-specific code in ArtifactStore)
- ✓ Versioning creates expected versions (no duplicates, latest retrieved correctly)
- ✓ Search results normalized (same SearchResult contract across methods)
- ✓ Git history gracefully degrades (no crash if .git missing)
- ✓ Staleness never throws (hash comparison robust, file I/O error-safe)
- ✓ Search performance acceptable (<200ms for 5k artifacts)

---

## After Rollback

1. **Log incident** — Document what failed and why in GATE-5 verification report
2. **Update plan** — Record contingency decision if scope reduced
3. **Write ADR** — If architectural change made, document in `docs/adr/`
4. **Retry or defer** — Start next iteration or move feature to Phase 2

---

## Owner and Authority

| Phase | Owner | Escalation |
|-------|-------|-----------|
| Design rejection | ARCHITECT | (none — decision final) |
| Implementation blocked | ARCHITECT | (none — decision final) |
| Test failures | VERIFIER + BUILDER | ARCHITECT if architecture issue |
| Library unavailable | BUILDER | ARCHITECT if cascading impact |
| Performance issue | VERIFIER | ARCHITECT if requires redesign |
| Merge conflict | REVIEWER | (none — document decision) |

---

*Created: 2026-06-30 by PLANNER*
*Revised: 2026-06-30 by PLANNER (audit-friendly procedures)*
*Status: Ready for GATE-1 approval*
