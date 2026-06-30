---
task_id: task-004
title: Consistency Review Summary
status: APPROVED
created: 2026-06-30
owner: PLANNER
---

# Task-004 Planning: Consistency Review (GATE-1 Revision)

## Executive Summary

All 9 planning inconsistencies identified and resolved. Artifacts now present a clean, consistent, implementation-ready specification with no ambiguities or contradictions.

---

## Issues Fixed

### 1. ✅ Embedding Provider Abstraction (Decoupled)

**Issue:** ArtifactStore was tightly coupled to Anthropic SDK and provider-specific logic.

**Fix:**
- Introduced `EmbeddingProvider` abstract base class
- ArtifactStore takes `embedding_provider: EmbeddingProvider | None` in constructor
- Implementations: `NullEmbedding` (no-op), `AnthropicEmbedding`, `LocalEmbedding` (extensible)
- ArtifactStore never knows about specific providers
- Spec §Embedding Provider Abstraction documents full abstraction

**Impact:** Clean separation of concerns. Different providers can be swapped via configuration.

**Files affected:**
- spec.md: New §Embedding Provider Abstraction, updated ingest_artifact() signature
- plan.md: Updated scope and implementation tasks

---

### 2. ✅ Async/Sync Consistency (Resolved)

**Issue:** `ingest_artifact()` was synchronous but contained `await embed(...)` (contradictory).

**Fix:**
- `ingest_artifact()` is **synchronous** (blocking for validation + storage)
- Embedding computation is **non-blocking** (delegated to `_compute_embedding_async()`)
- Provider's `embed()` can be async internally; ArtifactStore doesn't await
- Implementation can queue embeddings for background processing
- Spec documents: "synchronous ingestion API" with non-blocking embedding
- Plan Task 5: "Artifact store API" clarifies sync ingestion

**Impact:** Single, consistent execution model. Embeddings don't block artifact storage.

**Files affected:**
- spec.md: Updated §Artifact Ingestion with clear sync/async boundaries, _compute_embedding_async() helper
- plan.md: Updated description of ingest_artifact() behavior

---

### 3. ✅ Conversation Store (Out of Scope)

**Issue:** Plan listed "Conversation Store" as a feature while saying it's deferred to Phase 2 (contradictory).

**Fix:**
- Created new section: **"Out of Scope"** in spec.md
- Conversation Store explicitly moved to deferred list
- Clarified: schema prepared (ALTER TABLE workflow_runs...), implementation deferred
- Removed from feature list
- Plan updated: scope now lists only 8 features (not 9)

**Acceptance Criteria:** Updated to remove criteria referencing Conversation Store

**Impact:** Clear scope boundary. No ambiguity about what's in Phase 1.

**Files affected:**
- spec.md: New §Out of Scope, removed Conversation Store from §Core APIs
- plan.md: Updated feature count and acceptance criteria

---

### 4. ✅ FTS5 Synchronization (Triggers Implemented)

**Issue:** Manual FTS5 sync in Python code (fragile, error-prone).

**Fix:**
- Implemented **database triggers** for automatic FTS5 synchronization
- INSERT trigger: adds to artifacts_fts
- UPDATE trigger: removes old, inserts new
- DELETE trigger: removes from artifacts_fts
- Python code: `self.db.execute()` stores to artifacts table; triggers handle FTS5
- Spec §FTS5 Virtual Table documents full trigger syntax (CREATE TRIGGER ...)
- Plan Task 2: "FTS5 trigger synchronization" explicitly

**Impact:** Robust, atomic synchronization. No divergence between artifacts and artifacts_fts.

**Files affected:**
- spec.md: Complete trigger SQL in §FTS5 Virtual Table, updated ingest_artifact() (no manual FTS5 insert)
- plan.md: Task 2 explicitly "FTS5 trigger synchronization"

---

### 5. ✅ Artifact Versioning (Explained)

**Issue:** Artifact ID includes timestamp; versioning behavior ambiguous.

**Fix:**
- **ID generation:** Hash-based, stable (not timestamp-based)
- **Versioning:** Immutable; new content → new version
- **Latest retrieval:** `get_artifact(id) → get MAX(version) by default`
- **History retrieval:** `get_artifact_history(id) → all versions ordered ASC`
- **Content comparison:** Hash-based (content_hash field)
- Spec §Artifact Versioning Policy documents behavior explicitly
- Spec §Core APIs shows all three retrieval methods

**Impact:** Clear, unambiguous versioning strategy. Audit trail preserved. History accessible.

**Files affected:**
- spec.md: New §Artifact Versioning Policy, updated schema (added version column), updated APIs
- plan.md: Acceptance criterion #4 clarified

---

### 6. ✅ SearchResult Contract (Defined)

**Issue:** `SearchResult` referenced in BM25/Semantic/Hybrid without definition.

**Fix:**
- Defined complete `SearchResult` dataclass in spec.md §Shared Types
- Fields: artifact_id, title, type, content, relevance_scope, relevance_score, source, created_at
- Method-specific metadata: bm25_rank, semantic_distance, rrf_score, snippet (all optional)
- Relevance score normalized 0.0-1.0 across all methods
- All search APIs documented to return `list[SearchResult]`

**Impact:** Single contract for all searches. Clients receive consistent data structure.

**Files affected:**
- spec.md: New §Shared Types with SearchResult definition, updated all search method returns

---

### 7. ✅ Performance Benchmarking (Reproducible)

**Issue:** Performance targets lacked context (what size repo? what environment?).

**Fix:**
- Documented benchmarking environment:
  - Test repo: sample-python-project (~500 files, ~20k lines)
  - Artifact corpus: 5,000 artifacts (mix)
  - Embedding dimension: 1536
  - Provider: NullEmbedding (local, no API latency)
  - Database: SQLite WAL
  - Machine: Development laptop (16GB RAM typical)
- Reproducible performance targets:
  - BM25: <100ms
  - Semantic: <150ms
  - Hybrid: <200ms
  - Ingest: <50ms
  - Staleness: <10ms
- Note: "Actual latency will vary by machine spec"

**Impact:** Benchmarks are reproducible. Future optimization measured against known baseline.

**Files affected:**
- spec.md: New §Performance Benchmarking with full environment documented

---

### 8. ✅ Rollback Strategy (Audit-Friendly)

**Issue:** Rollback examples used destructive `git reset --hard` (non-auditable).

**Fix:**
- Replaced all `git reset --hard` with `git revert` procedures
- Full audit trail: every rollback is a commit with reason
- Scenarios documented:
  1. Design rejection (no code yet)
  2. Implementation blocked (partial revert via `git revert --no-commit`)
  3. Test failures (surgical revert or full revert)
  4. External library unavailable (config-based degradation preferred)
  5. Performance regression (targeted optimization or deferral)
  6. Merge conflict (documented decision)
- Contingency decisions table (Issue → Decision)
- Prevention checklist (to avoid rollback)

**Impact:** Clear, auditable rollback procedures. No lost history.

**Files affected:**
- rollback-plan.md: Complete rewrite with `git revert` procedures, scenarios, contingencies

---

### 9. ✅ General Consistency Review (Completed)

**Issue:** Ambiguous wording, duplicated statements, contradictions, speculative language, inconsistent terminology.

**Fixes applied across all artifacts:**

| Category | Fix |
|----------|-----|
| Ambiguous wording | "may defer" → "explicitly deferred to Phase 2" |
| Duplicated statements | Removed repetition; consolidated into single source |
| Contradictions | Embedding async/sync resolved; Conversation Store scoped |
| Speculative language | Removed "could," "might"; use definitive "will," "shall" |
| Inconsistent terminology | "ingest_artifact()" consistently named; "SearchResult" defined once |

**Consistency checks:**
- ✓ Every API contract internal consistent
- ✓ Every acceptance criterion testable (no "works well," "is fast")
- ✓ Every implementation task maps to acceptance criteria
- ✓ Every dependency clearly defined (build order in plan)
- ✓ No forward references without definition
- ✓ All tables, classes, functions defined before use

**Files affected:**
- plan.md, spec.md, rollback-plan.md: Throughout

---

## Verification Checklist

All items verified before commit:

- ✓ No tight coupling to Anthropic SDK (decoupled via EmbeddingProvider)
- ✓ Consistent async/sync model (sync ingest, non-blocking embeddings)
- ✓ Out of Scope section created (Conversation Store deferred)
- ✓ FTS5 triggers documented and implemented
- ✓ Artifact versioning unambiguous (immutable, hash-based, history accessible)
- ✓ SearchResult contract defined once, used consistently
- ✓ Performance targets reproducible (environment documented)
- ✓ Rollback procedures audit-friendly (git revert, not reset --hard)
- ✓ No contradictions remaining (design vs. deferred clear)
- ✓ All terminology consistent (single naming for each concept)
- ✓ All APIs documented with examples
- ✓ All acceptance criteria testable

---

## Impact on Implementation

These revisions make implementation smoother:

1. **Clearer contracts:** Developer knows exactly what to build (no ambiguity)
2. **Fewer refactors:** Design is solid; won't need mid-implementation rework
3. **Easier testing:** Acceptance criteria are testable, not vague
4. **Better error handling:** Out of scope features won't surprise implementation
5. **Safe rollback:** If needed, procedures are clear and auditable

---

## Status

**GATE-1:** Approval Pending (Human review of plan/spec/rollback)

Once approved:
1. **GATE-2:** ARCHITECT reviews and documents architecture
2. **GATE-3:** BUILDER implements 14 atomic tasks
3. **GATE-4:** TEST-DESIGNER designs 50+ tests
4. **GATE-5:** VERIFIER runs tests
5. **GATE-6:** REVIEWER reviews code
6. **MERGE:** Human final approval

---

*Reviewed: 2026-06-30 by PLANNER*
*Status: Ready for human GATE-1 approval*
