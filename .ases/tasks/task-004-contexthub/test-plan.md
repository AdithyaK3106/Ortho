---
task_id: task-004
title: Test Plan
status: COMPLETE
created: 2026-06-30
owner: TEST-DESIGNER
---

# Task-004 Test Plan: ContextHub

## Test Strategy

**Coverage Target:** 85%+ line coverage, all 20 acceptance criteria passing

**Test Scope:**
- Unit tests: Pure function testing, no I/O (35 tests)
- Integration tests: End-to-end ingest → search → retrieve flows (15 tests)
- Edge cases: Large artifacts, special characters, missing embeddings (10+ scenarios)
- Failure scenarios: Invalid inputs, file I/O errors, database constraints

**Test Framework:** pytest + pytest-cov

---

## Unit Tests (35 tests)

### 1. Schema Initialization (4 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_init_artifact_schema` | Create artifacts table | Table exists with 14 columns |
| `test_init_artifact_schema_triggers` | Triggers created | INSERT, UPDATE, DELETE triggers exist |
| `test_init_artifact_schema_indexes` | Indexes created | 5 indexes on repo, type, scope, created_at, source |
| `test_init_artifact_embeddings_schema_graceful` | sqlite-vec unavailable | No error raised, semantic unavailable |

### 2. Ingestion Validation (8 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_validate_valid_request` | All fields valid | is_valid=True, errors=[] |
| `test_validate_missing_type` | type empty | is_valid=False, errors include "type" |
| `test_validate_invalid_type` | type="invalid" | is_valid=False, errors include "must be one of" |
| `test_validate_empty_title` | title="" | is_valid=False |
| `test_validate_empty_content` | content="" | is_valid=False |
| `test_validate_invalid_scope` | relevance_scope="invalid" | is_valid=False |
| `test_validate_tags_not_list` | tags="string" (not list) | is_valid=False |
| `test_validate_tag_non_string` | tags=[123] | is_valid=False, error message includes index |

### 3. Artifact ID Generation (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_make_artifact_id_deterministic` | Same inputs | Same ID both times |
| `test_make_artifact_id_different_title` | Different title | Different ID |
| `test_make_artifact_id_length` | Any input | ID exactly 16 characters |

### 4. Content Hashing (2 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_make_content_hash_deterministic` | Same content | Same hash both times |
| `test_make_content_hash_length` | Any content | SHA256 hex (64 chars) |

### 5. Versioning Logic (4 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_get_next_version_first_artifact` | No existing versions | Returns 1 |
| `test_get_next_version_existing` | Version 2 exists | Returns 3 |
| `test_check_content_changed_first` | No existing | Returns True |
| `test_check_content_changed_same_hash` | Same hash | Returns False |

### 6. BM25 Search (5 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_bm25_search_basic` | Search "auth" | Returns results ranked by relevance |
| `test_bm25_search_type_filter` | Filter by type="adr" | Only ADRs returned |
| `test_bm25_search_scope_filter` | Filter by scope="global" | Only global artifacts |
| `test_bm25_search_combined_filters` | type + scope | Both filters applied (AND logic) |
| `test_bm25_search_empty_results` | Search "xyz_nonexistent" | Returns [] |

### 7. Semantic Search (4 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_semantic_search_available` | sqlite-vec loaded | Search returns results |
| `test_semantic_search_unavailable` | sqlite-vec not installed | Returns [] |
| `test_semantic_search_type_filter` | Filter by type | Only matching types |
| `test_semantic_search_normalized_scores` | Any results | relevance_score 0.0-1.0 |

### 8. Hybrid Search (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_hybrid_rrf_merge` | BM25 + semantic | RRF scores sum correctly |
| `test_hybrid_rrf_fallback` | Semantic unavailable | Uses BM25 results only |
| `test_hybrid_rrf_limit_respected` | limit=5 | Returns ≤5 results |

### 9. Git Metadata (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_get_file_churn_no_history` | File not in git_history | Returns zeros |
| `test_get_file_churn_with_commits` | 10 commits | commit_count=10 |
| `test_get_file_churn_last_modified` | Commits in order | last_modified is latest |

### 10. Project Memory (2 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_project_memory_set_get` | set(k, v) then get(k) | Returns v |
| `test_project_memory_list_all` | Multiple facts | list_all() returns dict with all |

### 11. Staleness Detection (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_staleness_non_file_artifact` | source="manual" | is_stale=False |
| `test_staleness_file_deleted` | File doesn't exist | is_stale=True, reason="deleted" |
| `test_staleness_content_changed` | Hash mismatch | is_stale=True, reason="content mismatch" |

---

## Integration Tests (15 tests)

### 1. Artifact Ingestion Flow (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_ingest_full_flow` | Valid request → ingest → retrieve | Artifact returned with all fields |
| `test_ingest_invalid_request` | Invalid request → ingest | ValidationError raised |
| `test_ingest_returns_artifact_id` | Ingest returns | artifact_id is 16-char hex string |

### 2. Versioning Flow (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_version_first_ingest` | Ingest new artifact | version=1 |
| `test_version_content_unchanged` | Ingest same content twice | Same artifact_id, version still 1 |
| `test_version_content_changed` | Ingest different content | Same artifact_id, version=2 |

### 3. Search Flow (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_ingest_then_bm25_search` | Ingest "authentication guide" → search "auth" | Found in results |
| `test_ingest_then_semantic_search` | Ingest + embedding → search | Results ranked by similarity |
| `test_ingest_then_hybrid_search` | Ingest + embedding → hybrid | RRF merged results |

### 4. Retrieval Flow (3 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_get_latest_version` | Ingest v1, v2 → get_artifact() | Returns v2 |
| `test_get_specific_version` | Ingest v1, v2 → get_artifact_version(1) | Returns v1 |
| `test_get_artifact_history` | Ingest v1, v2, v3 → get_artifact_history() | Returns [v1, v2, v3] ordered |

### 5. Git Metadata Flow (2 tests)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_load_git_history_parses_commits` | Load history → get_file_churn() | Returns commit count |
| `test_git_metadata_non_git_repo` | Not a git repo → load_git_history() | No error, graceful |

### 6. Deletion Flow (1 test)

| Test | Scenario | Expected |
|------|----------|----------|
| `test_delete_artifact` | Ingest → delete → get_artifact() | Returns None |

---

## Edge Cases & Failure Scenarios (10+ tests)

### Large Artifacts

| Test | Scenario | Expected |
|------|----------|----------|
| `test_ingest_large_artifact_1mb` | 1MB content | Stored and retrieved successfully |
| `test_search_large_artifact` | Search in 1MB artifact | Results include snippet (truncated) |
| `test_token_estimation_large` | Large content | estimated_tokens > 0 |

### Special Characters

| Test | Scenario | Expected |
|------|----------|----------|
| `test_artifact_special_chars_in_content` | content with emoji, unicode | Stored and retrieved exactly |
| `test_artifact_special_chars_in_title` | title with quotes, newlines | Stored and retrieved exactly |
| `test_fts5_special_chars_searchable` | Search for special chars | Found in results |

### Missing Embeddings

| Test | Scenario | Expected |
|------|----------|----------|
| `test_ingest_no_embeddings` | NullEmbedding provider | Artifact stored, no semantic search |
| `test_semantic_search_no_embeddings` | No embeddings stored | Returns [] gracefully |
| `test_hybrid_search_no_embeddings` | BM25 only | Falls back, returns BM25 results |

### File I/O Errors

| Test | Scenario | Expected |
|------|----------|----------|
| `test_staleness_file_unreadable` | File exists but unreadable | is_stale=True, reason includes error |
| `test_staleness_permission_denied` | Permission denied on file | Caught, logged, reported as stale |

### Database Constraints

| Test | Scenario | Expected |
|------|----------|----------|
| `test_artifact_id_uniqueness` | Insert duplicate ID, version 1 | INSERT fails or replaced correctly |
| `test_artifact_content_hash_required` | Missing content_hash | INSERT fails |

### Boundary Conditions

| Test | Scenario | Expected |
|------|----------|----------|
| `test_empty_string_content` | content="" | Rejected by validation |
| `test_extremely_long_title` | title = 10,000 chars | Stored and retrieved |
| `test_tags_empty_list` | tags=[] | Valid |
| `test_related_symbols_none` | related_symbols=None | Valid (optional) |

---

## Acceptance Criteria Coverage

| AC # | Test | Coverage |
|------|------|----------|
| 1 | `test_ingest_full_flow`, `test_validate_valid_request` | ✅ |
| 2 | `test_ingest_invalid_request`, `test_validate_*` | ✅ |
| 3 | `test_ingest_then_bm25_search`, `test_ingest_then_semantic_search` | ✅ |
| 4 | `test_version_*`, `test_get_latest_version`, `test_get_artifact_history` | ✅ |
| 5 | `test_bm25_search_basic` | ✅ |
| 6 | `test_bm25_search_*` | ✅ |
| 7 | `test_bm25_search_combined_filters` | ✅ |
| 8 | `test_semantic_search_available` | ✅ |
| 9 | `test_semantic_search_*` | ✅ |
| 10 | `test_semantic_search_unavailable` | ✅ |
| 11 | `test_hybrid_rrf_merge` | ✅ |
| 12 | `test_hybrid_rrf_merge` (RRF formula) | ✅ |
| 13 | `test_hybrid_rrf_fallback` | ✅ |
| 14 | `test_load_git_history_parses_commits` | ✅ |
| 15 | `test_git_metadata_non_git_repo` | ✅ |
| 16 | `test_project_memory_set_get` | ✅ |
| 17 | `test_project_memory_list_all` | ✅ |
| 18 | `test_staleness_content_changed` | ✅ |
| 19 | `test_staleness_file_deleted` | ✅ |
| 20 | `test_staleness_*` (last_verified_at) | ✅ |

---

## Test Data Fixtures

**Sample Artifacts:**
```python
VALID_ARTIFACT_REQUEST = ArtifactIngestionRequest(
    type="adr",
    title="ADR-001: Storage Strategy",
    content="We have decided to use SQLite for local storage...",
    source="docs/adr/ADR-001.md",
    relevance_scope="global",
    tags=["storage", "decision"],
    related_symbols=None,
)

AUTHENTICATION_ARTIFACT = ArtifactIngestionRequest(
    type="spec",
    title="Authentication Flow",
    content="The authentication system uses JWT tokens...",
    source="docs/authentication.md",
    relevance_scope="global",
    tags=["auth", "security"],
)

LARGE_ARTIFACT = ArtifactIngestionRequest(
    type="frd",
    title="Large FRD",
    content="X" * 1_000_000,  # 1MB
    source="docs/frd.md",
    relevance_scope="global",
    tags=["large"],
)
```

**Sample Embeddings:**
```python
SAMPLE_EMBEDDING = [0.1] * 1536  # Valid 1536-dim embedding
```

---

## Test Execution Plan

### Phase 1: Unit Tests (run locally, ~10 minutes)
```bash
pytest tests/test_schema.py -v --cov=src
pytest tests/test_ingestion.py -v --cov=src
pytest tests/test_versioning.py -v --cov=src
pytest tests/test_search.py -v --cov=src
pytest tests/test_git_metadata.py -v --cov=src
pytest tests/test_project_memory.py -v --cov=src
pytest tests/test_staleness.py -v --cov=src
```

### Phase 2: Integration Tests (run with database, ~5 minutes)
```bash
pytest tests/test_integration_ingest.py -v --cov=src
pytest tests/test_integration_search.py -v --cov=src
pytest tests/test_integration_retrieval.py -v --cov=src
pytest tests/test_integration_git.py -v --cov=src
```

### Phase 3: Edge Cases (run all, ~5 minutes)
```bash
pytest tests/test_edge_cases.py -v --cov=src
pytest tests/test_failure_scenarios.py -v --cov=src
```

### Coverage Report
```bash
pytest --cov=packages/context-hub/src --cov-report=html
# Target: 85%+ coverage across all modules
```

---

## Success Criteria

- ✅ All 50+ tests passing (0 failures)
- ✅ All 20 acceptance criteria covered by at least 1 test
- ✅ Coverage ≥85% (all modules, not just touched code)
- ✅ No unhandled exceptions in nominal paths
- ✅ Graceful degradation verified (sqlite-vec optional, git errors caught)
- ✅ No SQL injection vulnerabilities (parameterized queries)
- ✅ Type safety verified (mypy --strict passes)

---

## Deferred Testing

**Phase 2 (Integration with Pillar 1):**
- Integration tests with actual symbol registry (references symbol_id)
- Integration tests with import graph (tracing dependencies)

**Phase 4 (Performance & Scheduling):**
- Performance benchmarks (search latency <200ms)
- Concurrent ingest stress testing
- Scheduled staleness checks (background jobs)

---

## Notes for Test Implementation

1. **Database Setup:** Use in-memory SQLite `:memory:` for speed, or temporary files for isolation
2. **Git Fixture:** Create temporary git repo with sample commits for integration tests
3. **Embedding Fixture:** Mock EmbeddingProvider for unit tests, use NullEmbedding for integration
4. **Cleanup:** Each test cleans up database (rollback or fresh DB)
5. **Assertion Messages:** Include context in assertions (actual value, expected value, why)

---

*Test plan created: 2026-06-30 by TEST-DESIGNER*  
*Ready for implementation (GATE-4)*
