---
task_id: task-004
title: ContextHub (Week 7–8)
phase: 1
week: 7-8
workflow: feature
status: GATE-1-APPROVAL-PENDING
created: 2026-06-30
owner: PLANNER
---

# Task-004 Plan: ContextHub (Pillar 2)

## Objective

Implement the artifact store and retrieval layer for Ortho. ContextHub is the knowledge engine — it ingests, persists, and retrieves all engineering artifacts (FRDs, ADRs, docs, code evidence, git metadata, project facts).

**Success Criteria:** Artifact storage with versioning, hybrid search (BM25 + semantic), git metadata, project memory, and staleness detection fully functional.

---

## Scope

### Core Features (FRD §7, Table: Features)

1. **Artifact Store** — Ingest typed artifacts with validation contract
   - Table: `artifacts` (id, repo_id, type, title, content, source, created_at, last_modified, relevance_scope, tags, related_symbols, estimated_tokens, content_hash, version)
   - FTS5 virtual table: `artifacts_fts` with automatic trigger synchronization
   - Validation: type, title, content, source, relevance_scope all required
   - Versioning: immutable versions, latest retrieved by default

2. **Ingestion Contract** — Reject invalid artifacts before storage
   - Interface: `ArtifactIngestionRequest` (type, title, content, source, relevance_scope, tags, related_symbols)
   - Validator: `validate_ingestion()` returns ValidationResult (pass/fail with reason)
   - No silent failures; all validation errors enumerated

3. **BM25 Full-Text Search** — SQLite FTS5 keyword search
   - Method: `bm25_search(query: str, limit: int, type_filter, scope_filter) → list[SearchResult]`
   - Filters: artifact type, relevance scope (AND logic)
   - Synchronization: automatic via database triggers (insert, update, delete)

4. **Semantic Search** — sqlite-vec KNN similarity search
   - Method: `semantic_search(query_embedding: list[float], k: int, filters) → list[SearchResult]`
   - Requires: embeddings pre-computed by configurable EmbeddingProvider
   - Graceful fallback: if embeddings unavailable, returns empty results (no error)

5. **Hybrid Search (RRF)** — Merge BM25 + semantic with Reciprocal Rank Fusion
   - Formula: `score(doc) = sum(1/(k + rank(doc)))` per result list, k=60
   - Method: `hybrid_search(query, query_embedding, limit, type_filter, scope_filter) → list[SearchResult]`
   - Fallback: if semantic unavailable, degrades to BM25 only

6. **Git Metadata Store** — Persist commit history and file churn
   - Tables: `git_history` (file_id, commit_hash, author, date, message, diff_lines_added/removed)
   - Integration: GitPython to read git log on-demand (non-blocking)
   - Used by: Arch Intelligence (technical debt scoring) in Phase 2

7. **Project Memory** — Structured key/value store for project facts
   - Table: `project_memory` (key, repo_id, value, source, updated_at)
   - Examples: primary_language, test_framework, api_style, auth_approach
   - Interface: `set(key, value, source)`, `get(key)`, `list_all()`

8. **Staleness Detector** — Flag artifacts whose source has changed
   - Logic: Compare `artifact.content_hash` against live file content (hash-based, not timestamp)
   - Non-file artifacts (manual, generated) are never stale
   - Mark: staleness_flag, last_verified_at
   - Integration: Run on retrieval (optional), on schedule (Phase 4)

**Deferred to Phase 2:**
- Conversation Store (schema prepared, full implementation deferred)
- Diff detection (full diff parsing, showing line-by-line changes)
- Search caching (Phase 4)

---

## Acceptance Criteria (20 total)

### Artifact Store (4)
- [ ] 1. Artifacts can be ingested via `ingest_artifact(req: ArtifactIngestionRequest) → str` (returns artifact_id)
- [ ] 2. Invalid artifacts rejected before storage (validation contract enforced)
- [ ] 3. Artifacts queryable by type, scope, tags, and related_symbols
- [ ] 4. Artifact versioning: immutable versions, latest retrieved by `get_artifact()`, history via `get_artifact_history()`

### BM25 Search (3)
- [ ] 5. `bm25_search(query, limit=10, type_filter=None, scope_filter=None) → list[SearchResult]`
- [ ] 6. Search returns results ranked by keyword relevance (FTS5 BM25 algorithm)
- [ ] 7. Filters by type and scope work correctly (AND logic)

### Semantic Search (3)
- [ ] 8. `semantic_search(query_embedding, k=10, type_filter, scope_filter) → list[SearchResult]`
- [ ] 9. KNN search returns nearest embeddings by distance
- [ ] 10. Graceful fallback if embeddings unavailable (returns empty, not error)

### Hybrid Search (3)
- [ ] 11. `hybrid_search(query, query_embedding, limit=10, filters) → list[SearchResult]`
- [ ] 12. RRF correctly merges BM25 + semantic results using formula: sum(1/(k+rank))
- [ ] 13. Hybrid search fallback to BM25 if semantic unavailable

### Git Metadata (2)
- [ ] 14. Git history queryable: `get_file_churn(file_id) → FileChurnMetadata`
- [ ] 15. Commit message and author accessible per file

### Project Memory (2)
- [ ] 16. `set(key, value, source)` stores project facts
- [ ] 17. `get(key)` and `list_all()` retrieve facts

### Staleness (2)
- [ ] 18. Artifacts tagged stale if source content changed (hash-based comparison)
- [ ] 19. Staleness check API: `check_staleness(artifact_id) → StalenessReport`
- [ ] 20. Staleness metadata persisted (last_verified_at)

---

## Implementation Tasks (Atomic, Ordered)

1. **Artifact schema migration** — Create `artifacts` table with versioning, `artifacts_fts` virtual table, indexes
2. **FTS5 trigger synchronization** — Implement insert/update/delete triggers for automatic FTS5 sync
3. **Embedding provider abstraction** — Define `EmbeddingProvider` interface, implement `NullEmbedding` (no-op), inject into ArtifactStore
4. **Ingestion validator** — `ArtifactIngestionRequest` + validation logic, comprehensive error reporting
5. **Artifact store API** — `ingest_artifact()`, `get_artifact()`, `get_artifact_version()`, `get_artifact_history()` methods
6. **Artifact versioning** — Hash-based version detection, immutable version creation, latest retrieval
7. **BM25 search** — `BM25Search` class, FTS5 query builder, ranking, filter logic
8. **Semantic search setup** — `SemanticSearch` class, sqlite-vec integration, KNN queries
9. **Hybrid search (RRF)** — `HybridSearch` class, RRF algorithm (sum of reciprocal ranks), fallback to BM25
10. **Git metadata** — `GitMetadataStore` class, GitPython integration, `get_file_churn()` API
11. **Project memory** — `ProjectMemory` class, CRUD API, cross-repo isolation
12. **Staleness detector** — `StalenessDetector` class, hash comparison, file existence check, non-blocking errors
13. **SearchResult contract** — Unified `SearchResult` dataclass for all search methods, normalized relevance scoring
14. **Integration tests** — End-to-end tests for ingest → search → retrieve flows

---

## Dependencies (Build Order)

```
task-001 (shared types, storage.py) ✓
task-002 (symbols, import graph) ✓
task-003 (call graph, incremental) ✓
    ↓
task-004 (ContextHub — requires shared types + storage layer)
    ↓
task-005 (Architectural Intelligence — requires ContextHub for artifact storage)
```

**No blocking external work** — all input from prior tasks available.

---

## Effort Estimate

- **Planning:** 1h
- **Architecture review:** 1h
- **Implementation:** 10h (14 atomic tasks × ~45 min avg, some serialized)
- **Testing:** 4h (design + run 50+ tests)
- **Verification:** 1h (run suite, check gates)
- **Review:** 1h (code + design review)
- **Total:** ~18 hours

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Embedding API rate limit | Low | Medium | Use NullEmbedding in Phase 1; Anthropic config deferred |
| FTS5 performance degradation | Low | Medium | Benchmark with 5k artifacts; add pagination if needed |
| Staleness detection false positives | Low | Low | Hash-based comparison (binary), file existence check |
| Git history parsing errors | Low | Low | Non-blocking: log warning, continue; graceful degradation |
| EmbeddingProvider injection complexity | Low | Low | Simple dependency injection; single responsibility per provider |
| SearchResult contract mismatch | Medium | High | Define once in spec, all methods return same type |

---

## Rollback Plan

### Scenario 1: Design Rejected (pre-implementation)

**Trigger:** ARCHITECT review identifies architectural flaw

**Action:**
1. No code committed yet
2. PLANNER + ARCHITECT rewrite spec sections
3. Return to GATE-2 for second review
4. Proceed only after approval

**Impact:** Zero. Nothing to rollback.

---

### Scenario 2: Implementation Blocked (during BUILDER phase)

**Trigger:** Implementation discovers unforeseen complexity (e.g., FTS5 trigger syntax)

**Action:**
1. Halt work on blocking task
2. Escalate to ARCHITECT for design decision
3. ARCHITECT evaluates:
   - Workaround feasible? (preferred)
   - Design change needed? (return to GATE-1)
   - Defer feature to Phase 2? (scope reduction)

**Procedure (if code rollback needed):**

```bash
# Identify last good commit (task-003)
git log --oneline | grep "task-003"  # e.g., 286dd23

# Revert task-004 commits cleanly
git revert --no-commit <commit-004-1>..<commit-004-N>
git commit -m "[task-004] ROLLBACK: Revert implementation due to [reason]"

# Clean up artifacts
rm -rf packages/context-hub/src/* 
git add packages/context-hub/src/
git commit -m "[task-004] ROLLBACK: Remove incomplete implementation"
```

**Impact:** All task-004 code discarded. Repo clean. No data loss (no migrations applied yet).

---

### Scenario 3: Test Failures (VERIFIER phase)

**Trigger:** >10% of tests fail; verification discovers critical bug

**Action:**
1. VERIFIER reports failure details
2. BUILDER investigates root cause
3. Fix and retest (iterate within task-004)
4. If unfixable: escalate to ARCHITECT

**Procedure (if full revert needed):**

```bash
# Use git revert (audit-friendly, creates new commits)
git revert --no-edit <buggy-commit>

# Verify clean state
git status                  # should be clean
git log --oneline -5        # should show revert commit
```

**Impact:** Clear audit trail. No lost history.

---

### Scenario 4: External Library Unavailable

**Trigger:** sqlite-vec fails to build, gitpython incompatible, etc.

**Action:**

| Library | Failure | Mitigation |
|---------|---------|-----------|
| sqlite-vec | Build fails | Use pure SQL FTS5 only; mark semantic as deferred |
| gitpython | Import error | Defer git metadata to Phase 2; proceed with core features |
| Both | Critical | Reduce scope; complete BM25 + versioning only |

**Configuration (degraded mode):**

```toml
[context_hub]
semantic_search_enabled = false
git_history_enabled = false
# BM25 + versioning + project memory still work
```

**No code rollback needed** — feature flags handle degradation.

---

### Scenario 5: Performance Regression (Benchmark phase)

**Trigger:** Search latency exceeds 500ms on 5k artifacts

**Action:**
1. Identify bottleneck (FTS5 query plan, vector search, etc.)
2. ARCHITECT evaluates:
   - Indexing strategy change?
   - Query optimization?
   - Defer to Phase 4?
3. Rebuild search modules if needed

**Procedure (if localized fix needed):**

```bash
# Revert one module only (surgical)
git revert --no-edit <slow-commit>
git commit -m "[task-004] FIX: Optimize search latency"
```

**Impact:** Minimal. One module fixed.

---

## Success Criteria (Prevent Rollback)

- ✓ All 20 acceptance criteria pass
- ✓ 50+ tests run with 0 failures
- ✓ Coverage >85%
- ✓ No breaking changes to tasks 1-3 or shared types
- ✓ Schema migrations clean (no orphaned columns)
- ✓ Embedding provider abstraction fully decoupled
- ✓ Synchronous ingestion API (no async in ArtifactStore)
- ✓ FTS5 triggers working (no manual sync)
- ✓ Search latency <200ms (5k artifacts, benchmarked)
- ✓ Code review APPROVED (no major issues)

---

## Owner Decisions

- **ARCHITECT:** Approves design (Gates 1–2)
- **BUILDER:** Implements code, manages complexity during execution
- **VERIFIER:** Decides if tests pass (Gate 5)
- **REVIEWER:** Final code review (Gate 6)
- **Escalation:** Any scenario → ARCHITECT for decision

---

## Next Steps (After GATE-1 Approval)

1. **ARCHITECT:** Review spec, write architecture-review.md, document any ADRs, produce GATE-2 verdict
2. **BUILDER:** After GATE-2 approval, implement 14 atomic tasks in order (test as you go)
3. **TEST-DESIGNER:** Design 50+ tests (35 unit + 15 integration), produce test-plan.md
4. **VERIFIER:** Run tests, produce verification-report.md
5. **REVIEWER:** Code + design review, produce review.md
6. **HUMAN:** Final approval, merge to main

---

*Created: 2026-06-30 by PLANNER*
*Revised: 2026-06-30 by PLANNER (GATE-1 consistency improvements)*
*Status: Awaiting GATE-1 human approval*
