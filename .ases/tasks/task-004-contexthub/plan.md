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

Implement the artifact store and retrieval layer for Ortho. ContextHub is the knowledge engine — it ingests, persists, and retrieves all engineering artifacts (FRDs, ADRs, docs, conversations, evidence).

**Success Criteria:** Artifact storage, hybrid search (BM25 + semantic), git metadata, project memory, and staleness detection fully functional.

---

## Scope

### Core Features (FRD §7, Table: Features)

1. **Artifact Store** — Ingest typed artifacts with validation contract
   - Table: `artifacts` (id, repo_id, type, title, content, source, created_at, last_modified, relevance_scope, tags, related_symbols, estimated_tokens, content_hash)
   - FTS5 virtual table: `artifacts_fts` for full-text search
   - Validation: type, title, content, source, relevance_scope all required

2. **Ingestion Contract** — Reject invalid artifacts before storage
   - Interface: `ArtifactIngestionRequest` (type, title, content, source, relevance_scope, tags, related_symbols)
   - Validator: `validate_ingestion()` returns ValidationResult (pass/fail with reason)
   - No silent failures

3. **BM25 Full-Text Search** — SQLite FTS5 keyword search
   - Method: `bm25_search(query: str, limit: int, type_filter, scope_filter) → list[SearchResult]`
   - Filters: artifact type, relevance scope
   - Integration point: ContextHub retrieval layer

4. **Semantic Search** — sqlite-vec KNN similarity search
   - Method: `semantic_search(query_embedding: list[float], k: int, filters) → list[SearchResult]`
   - Requires: embeddings pre-computed and stored in sqlite-vec
   - Embedding model: Anthropic `voyage-code-3` (code) or `voyage-3-lite` (docs) or local `.gguf`

5. **Hybrid Search (RRF)** — Merge BM25 + semantic with Reciprocal Rank Fusion
   - Formula: `score(doc) = sum(1/(k + rank(doc)))` per result list, k=60
   - Method: `hybrid_search(query, query_embedding, limit, type_filter, scope_filter) → list[SearchResult]`
   - Preference: semantic preferred, BM25 fallback if embedding unavailable

6. **Git Metadata Store** — Persist commit history and file churn
   - Tables: `git_history` (file_id, commit_hash, author, date, message, diff_lines_added/removed)
   - Integration: GitPython to read git log on demand
   - Used by: Arch Intelligence (technical debt scorer)

7. **Project Memory** — Structured key/value store for project facts
   - Table: `project_memory` (key, repo_id, value, source, updated_at)
   - Examples: primary_language, test_framework, api_style, auth_approach
   - Interface: `set(key, value, source)`, `get(key)`, `list_all()`

8. **Conversation Store** — Persist AI sessions with context snapshots
   - Table: `workflow_runs` (already exists from Pillar 4 design)
   - Extension: Add `conversation_json` column for session transcripts
   - Not full build — defer implementation to Phase 2

9. **Staleness Detector** — Flag artifacts whose source has changed
   - Logic: Compare `artifact.content_hash` against live file content
   - Mark: staleness_flag, last_verified_at
   - Integration: Run on retrieval (optional), on schedule (Phase 4)

---

## Acceptance Criteria (20 total)

### Artifact Store (4)
- [ ] 1. Artifacts can be ingested via `ingest_artifact(req: ArtifactIngestionRequest) → str` (returns artifact_id)
- [ ] 2. Invalid artifacts rejected before storage (validation contract enforced)
- [ ] 3. Artifacts queryable by type, scope, tags, and related_symbols
- [ ] 4. Artifact versioning: old versions preserved, latest accessible via `get_artifact(id) → Artifact`

### BM25 Search (3)
- [ ] 5. `bm25_search(query, limit=10, type_filter=None, scope_filter=None) → list[SearchResult]`
- [ ] 6. Search returns results ranked by keyword relevance
- [ ] 7. Filters by type and scope work correctly (AND logic)

### Semantic Search (3)
- [ ] 8. `semantic_search(query_embedding, k=10, type_filter, scope_filter) → list[SearchResult]`
- [ ] 9. KNN search returns nearest embeddings by distance
- [ ] 10. Embedding model configurable (Anthropic API or local)

### Hybrid Search (3)
- [ ] 11. `hybrid_search(query, query_embedding, limit=10, filters) → list[SearchResult]`
- [ ] 12. RRF correctly merges BM25 + semantic results
- [ ] 13. Hybrid search prefers semantic results when available

### Git Metadata (2)
- [ ] 14. Git history queryable: `get_file_churn(file_id) → FileChurnMetadata`
- [ ] 15. Commit message and author accessible per file

### Project Memory (2)
- [ ] 16. `set(key, value, source)` stores project facts
- [ ] 17. `get(key)` and `list_all()` retrieve facts

### Staleness (2)
- [ ] 18. Artifacts tagged as stale if source content changed
- [ ] 19. Staleness check API: `get_staleness(artifact_id) → StalenessReport`
- [ ] 20. Staleness metadata (last_verified_at) persisted

### Edge Cases (1 meta)
- [ ] Handles: large artifacts (>1MB), special characters in content, missing embeddings gracefully

---

## Implementation Tasks (Atomic)

1. **Artifact schema migration** — Add `artifacts` table + `artifacts_fts` FTS5 virtual table
2. **Ingestion validator** — `ArtifactIngestionRequest` + validation logic
3. **Artifact store API** — `ingest()`, `get()`, `update()`, `delete()` methods
4. **BM25 search** — FTS5 query builder + ranking
5. **Semantic search setup** — sqlite-vec integration, embedding storage
6. **Semantic search API** — KNN query builder
7. **Hybrid search (RRF)** — Merge BM25 + semantic with RRF algorithm
8. **Git metadata** — Table schema + GitPython integration
9. **Project memory** — Table + CRUD API
10. **Staleness detector** — Hash-based change detection + API

---

## Dependencies (Build Order)

```
task-001 (shared types, storage.py) ✓
task-002 (symbols, import graph) ✓
task-003 (call graph, incremental) ✓
    ↓
task-004 (ContextHub — requires shared types + storage layer)
    ↓
task-005 (Architectural Intelligence — requires ContextHub)
```

**No blocking external work** — all input from prior tasks available.

---

## Estimated Effort

- **Planning:** 1h
- **Architecture review:** 1h
- **Implementation:** 8h (10 atomic tasks × 45 min avg)
- **Testing:** 4h (design + run 50+ tests)
- **Verification:** 1h (run suite, check gates)
- **Review:** 1h (code + design review)
- **Total:** ~16 hours

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Embedding model API unavailable | Low | High | Use local `.gguf` model fallback, defer embedding to Phase 4 |
| FTS5 performance on large corpus | Low | Medium | Benchmark with 10k artifacts; add pagination if needed |
| Staleness detection false positives | Medium | Low | Compare content hashes, not timestamps; allow grace period |
| Circular refs (artifact → symbol → artifact) | Low | Medium | Enforce one-way refs: artifacts reference symbols, not vice versa |

---

## Rollback Plan

If implementation blocked or verification fails:
1. Keep `shared/types/` intact (no breaking changes)
2. Revert `packages/context-hub/` to empty package (code removed, dir preserved)
3. Revert schema migrations (down to task-003 baseline)
4. No impact to Pillar 1 (repo-intelligence) — clean interface boundary

---

## Gate 1 Checklist

- [ ] **Clarity:** Acceptance criteria unambiguous, each testable
- [ ] **Completeness:** All 9 features from FRD §7 covered
- [ ] **Feasibility:** No unknown tech, all libraries approved (sqlite-vec, anthropic API, gitpython)
- [ ] **Dependencies:** Clear build order, no circular deps
- [ ] **Scope:** Fits 8-hour window (token optimizer deferred to Phase 4)
- [ ] **Owner:** Assigned to ARCHITECT after human approval

---

## Next Steps

1. **HUMAN:** Review and approve plan
2. **ARCHITECT:** Review spec, write ADR, produce architecture-review.md
3. **BUILDER:** Implement 10 atomic tasks in order
4. **TEST-DESIGNER:** Design 50+ tests
5. **VERIFIER:** Run tests, produce verification report
6. **REVIEWER:** Code + design review
7. **HUMAN:** Final approval, merge to main

---

*Created: 2026-06-30 by PLANNER*
*Status: Awaiting GATE-1 approval (human review)*
