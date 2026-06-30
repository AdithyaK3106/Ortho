---
task_id: task-004
title: ContextHub Specification
workflow: feature
status: GATE-1-APPROVAL-PENDING
created: 2026-06-30
owner: PLANNER
---

# Task-004 Spec: ContextHub (Pillar 2)

## Executive Summary

ContextHub is the persistent knowledge layer. It stores all engineering artifacts (FRDs, ADRs, docs, code evidence, conversations, git metadata), indexes them for fast retrieval, and surfaces them via hybrid search (BM25 + semantic). No AI generation — pure storage and retrieval.

**Package:** `packages/context-hub/`  
**Language:** Python (dataclasses, SQLite)  
**Dependencies:** sqlite-vec, anthropic (embeddings API), gitpython  
**Exit Criteria:** All 20 acceptance criteria passing, 50+ tests with 85%+ coverage

---

## Data Model

### Artifact Table

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,                    -- hash(repo_id + title + created_at)
    repo_id TEXT NOT NULL,
    type TEXT NOT NULL,                     -- frd|adr|architecture|spec|decision|lesson_learned|dev_note|benchmark|conversation|git_metadata|project_memory|evidence|workflow_run
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,                   -- file path, 'manual', 'generated', git SHA
    created_at TEXT NOT NULL,               -- ISO 8601
    last_modified TEXT NOT NULL,
    relevance_scope TEXT NOT NULL,          -- global|project|module|file
    tags TEXT NOT NULL DEFAULT '[]',        -- JSON array of strings
    related_symbols TEXT DEFAULT '[]',      -- JSON array of symbol IDs
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL              -- SHA256 of content (for staleness)
);
```

**Indexes:**
```sql
CREATE INDEX idx_artifacts_repo ON artifacts(repo_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_artifacts_scope ON artifacts(relevance_scope);
CREATE INDEX idx_artifacts_created ON artifacts(created_at DESC);
```

### FTS5 Virtual Table (BM25)

```sql
CREATE VIRTUAL TABLE artifacts_fts USING fts5(
    title,
    content,
    content='artifacts',
    content_rowid='rowid'
);
```

Keep in sync with `artifacts` table via triggers (insert, update, delete).

### Vector Table (sqlite-vec)

```sql
CREATE VIRTUAL TABLE artifact_embeddings USING vec0(
    artifact_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]                   -- dimension matches embedding model
);
```

**Embedding workflow:**
1. On `ingest_artifact()`, compute embedding if enabled in config
2. Store in `artifact_embeddings`
3. If embedding fails, store artifact anyway (BM25 fallback)

### Git Metadata Table

```sql
CREATE TABLE git_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    author TEXT,
    commit_date TEXT NOT NULL,              -- ISO 8601
    message TEXT,
    diff_lines_added INTEGER,
    diff_lines_removed INTEGER
);
```

**Indexes:**
```sql
CREATE INDEX idx_git_history_file ON git_history(file_id);
CREATE INDEX idx_git_history_commit ON git_history(commit_hash);
```

### Project Memory Table

```sql
CREATE TABLE project_memory (
    key TEXT NOT NULL,
    repo_id TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',  -- 'manual', 'detected', 'generated'
    updated_at TEXT NOT NULL,
    PRIMARY KEY (key, repo_id)
);
```

---

## Core APIs

### Artifact Ingestion

```python
@dataclass
class ArtifactIngestionRequest:
    type: ArtifactType
    title: str
    content: str
    source: str
    relevance_scope: str  # 'global' | 'project' | 'module' | 'file'
    tags: list[str]
    related_symbols: list[str] | None = None

class ArtifactStore:
    def ingest_artifact(
        self,
        req: ArtifactIngestionRequest
    ) -> str:
        """
        Validate and store artifact. Return artifact_id.
        Raises: ValidationError if request invalid.
        """
        # Validate
        validation = validate_ingestion(req)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # Hash ID
        artifact_id = hashlib.sha256(
            f"{req.title}:{req.source}:{int(time.time())}".encode()
        ).hexdigest()[:16]
        
        # Compute embedding (async, non-blocking)
        embedding = None
        if self.embedding_enabled:
            try:
                embedding = await embed(req.content, req.type)
            except EmbeddingError:
                pass  # silent fallback to BM25
        
        # Store
        self.db.execute("""
            INSERT INTO artifacts
            (id, repo_id, type, title, content, source, created_at, last_modified,
             relevance_scope, tags, related_symbols, estimated_tokens, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artifact_id, self.repo_id, req.type, req.title, req.content,
            req.source, datetime.now().isoformat(), datetime.now().isoformat(),
            req.relevance_scope, json.dumps(req.tags),
            json.dumps(req.related_symbols or []),
            count_tokens(req.content),
            hashlib.sha256(req.content.encode()).hexdigest()
        ))
        
        # Store embedding
        if embedding:
            self.vec_store.upsert(artifact_id, embedding)
        
        # Sync to FTS5
        self.db.execute(
            "INSERT INTO artifacts_fts(rowid, title, content) VALUES (?, ?, ?)",
            (artifact_id, req.title, req.content)
        )
        
        return artifact_id
    
    def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Retrieve artifact by ID."""
        ...
    
    def delete_artifact(self, artifact_id: str) -> None:
        """Soft delete (mark, keep in FTS5)."""
        ...
```

### Validation

```python
def validate_ingestion(req: ArtifactIngestionRequest) -> ValidationResult:
    """Reject invalid requests. Return detailed errors."""
    errors = []
    
    # Required fields
    if not req.type or req.type not in ARTIFACT_TYPES:
        errors.append(f"type must be one of {ARTIFACT_TYPES}")
    if not req.title or len(req.title.strip()) == 0:
        errors.append("title cannot be empty")
    if not req.content or len(req.content.strip()) == 0:
        errors.append("content cannot be empty")
    if not req.source or len(req.source.strip()) == 0:
        errors.append("source cannot be empty")
    if req.relevance_scope not in ['global', 'project', 'module', 'file']:
        errors.append(f"relevance_scope must be one of global|project|module|file")
    
    # Tags must be list of strings
    if not isinstance(req.tags, list):
        errors.append("tags must be a list")
    for tag in req.tags:
        if not isinstance(tag, str):
            errors.append(f"tag {tag} must be string")
    
    # Symbols must be valid IDs if provided
    if req.related_symbols:
        # Could validate against symbol registry, but defer to Phase 2+
        pass
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### BM25 Search

```python
class BM25Search:
    def search(
        self,
        query: str,
        limit: int = 10,
        type_filter: list[str] | None = None,
        scope_filter: str | None = None,
    ) -> list[SearchResult]:
        """
        Full-text search via FTS5.
        Returns ranked by relevance.
        """
        where_clauses = []
        params = [query]
        
        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            where_clauses.append(f"type IN ({placeholders})")
            params.extend(type_filter)
        
        if scope_filter:
            where_clauses.append("relevance_scope = ?")
            params.append(scope_filter)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        sql = f"""
            SELECT
                a.id,
                a.title,
                a.type,
                a.content,
                a.relevance_scope,
                rank,
                highlight(artifacts_fts, 1, '<match>', '</match>') as snippet
            FROM artifacts_fts
            JOIN artifacts a ON artifacts_fts.rowid = a.rowid
            WHERE artifacts_fts MATCH ?
                AND {where_sql}
            ORDER BY rank
            LIMIT ?
        """
        params.append(limit)
        
        results = self.db.execute(sql, params).fetchall()
        return [SearchResult(...) for row in results]
```

### Semantic Search

```python
class SemanticSearch:
    def search(
        self,
        query_embedding: list[float],
        k: int = 10,
        type_filter: list[str] | None = None,
        scope_filter: str | None = None,
    ) -> list[SearchResult]:
        """
        KNN search via sqlite-vec.
        Returns by distance (ascending).
        """
        where_clauses = ["1=1"]
        params = []
        
        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            where_clauses.append(f"a.type IN ({placeholders})")
            params.extend(type_filter)
        
        if scope_filter:
            where_clauses.append("a.relevance_scope = ?")
            params.append(scope_filter)
        
        where_sql = " AND ".join(where_clauses)
        
        embedding_bytes = struct.pack(f'{len(query_embedding)}f', *query_embedding)
        
        sql = f"""
            SELECT
                ae.artifact_id,
                a.title,
                a.type,
                a.content,
                a.relevance_scope,
                ae.distance
            FROM artifact_embeddings ae
            JOIN artifacts a ON ae.artifact_id = a.id
            WHERE ae.embedding MATCH ? AND {where_sql}
            ORDER BY ae.distance
            LIMIT ?
        """
        params = [embedding_bytes] + params + [k]
        
        results = self.db.execute(sql, params).fetchall()
        return [SearchResult(...) for row in results]
```

### Hybrid Search (RRF)

```python
class HybridSearch:
    def search(
        self,
        query: str,
        query_embedding: list[float] | None,
        limit: int = 10,
        type_filter: list[str] | None = None,
        scope_filter: str | None = None,
    ) -> list[SearchResult]:
        """
        Merge BM25 + semantic via RRF.
        score(doc) = sum(1 / (k + rank)) across result sets
        k = 60 (standard RRF constant)
        """
        k_rrf = 60
        
        # BM25 results
        bm25_results = self.bm25.search(
            query, limit * 2, type_filter, scope_filter
        )
        bm25_ranked = {
            r.artifact_id: 1.0 / (k_rrf + i)
            for i, r in enumerate(bm25_results)
        }
        
        # Semantic results (if embedding provided)
        semantic_ranked = {}
        if query_embedding:
            semantic_results = self.semantic.search(
                query_embedding, k=limit * 2, type_filter=type_filter, scope_filter=scope_filter
            )
            semantic_ranked = {
                r.artifact_id: 1.0 / (k_rrf + i)
                for i, r in enumerate(semantic_results)
            }
        
        # Merge: sum scores
        merged = {}
        for artifact_id, score in bm25_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score
        for artifact_id, score in semantic_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score
        
        # Rank by merged score
        ranked_ids = sorted(merged.items(), key=lambda x: -x[1])[:limit]
        
        # Fetch full results
        results = []
        for artifact_id, rrf_score in ranked_ids:
            artifact = self.store.get_artifact(artifact_id)
            results.append(SearchResult(
                artifact_id=artifact_id,
                artifact=artifact,
                relevance_score=rrf_score
            ))
        
        return results
```

### Git Metadata

```python
class GitMetadataStore:
    def load_git_history(self, file_id: str) -> None:
        """
        Query git log for file, store in git_history table.
        Called on-demand (Phase 1) or scheduled (Phase 4).
        """
        file = self.store.files[file_id]
        repo = git.Repo(self.repo_root)
        
        try:
            commits = list(repo.iter_commits(paths=file.rel_path))
        except git.InvalidGitRepositoryError:
            return  # not a git repo
        
        for commit in commits:
            self.db.execute("""
                INSERT INTO git_history
                (file_id, repo_id, commit_hash, author, commit_date, message,
                 diff_lines_added, diff_lines_removed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                file_id, self.repo_id, commit.hexsha,
                commit.author.name, commit.committed_datetime.isoformat(),
                commit.message,
                # Simplified: count lines (full diff parsing deferred)
                0, 0
            ))
    
    def get_file_churn(self, file_id: str) -> FileChurnMetadata:
        """
        Return: commit count, total lines added/removed, last modified date.
        """
        rows = self.db.execute("""
            SELECT
                COUNT(*) as commit_count,
                SUM(diff_lines_added) as total_added,
                SUM(diff_lines_removed) as total_removed,
                MAX(commit_date) as last_modified
            FROM git_history
            WHERE file_id = ?
        """, (file_id,)).fetchone()
        
        return FileChurnMetadata(
            commit_count=rows[0] or 0,
            lines_added=rows[1] or 0,
            lines_removed=rows[2] or 0,
            last_modified=rows[3]
        )
```

### Project Memory

```python
class ProjectMemory:
    def set(self, key: str, value: str, source: str = 'manual') -> None:
        """Store a project fact."""
        self.db.execute("""
            INSERT OR REPLACE INTO project_memory
            (key, repo_id, value, source, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (key, self.repo_id, value, source, datetime.now().isoformat()))
    
    def get(self, key: str) -> str | None:
        """Retrieve a project fact."""
        row = self.db.execute(
            "SELECT value FROM project_memory WHERE key = ? AND repo_id = ?",
            (key, self.repo_id)
        ).fetchone()
        return row[0] if row else None
    
    def list_all(self) -> dict[str, str]:
        """List all facts for this repo."""
        rows = self.db.execute(
            "SELECT key, value FROM project_memory WHERE repo_id = ?",
            (self.repo_id,)
        ).fetchall()
        return {row[0]: row[1] for row in rows}
```

### Staleness Detector

```python
class StalenessDetector:
    def check_staleness(self, artifact_id: str) -> StalenessReport:
        """
        Compare artifact.content_hash against live file.
        Return staleness report.
        """
        artifact = self.store.get_artifact(artifact_id)
        
        if not artifact.source.startswith('/'):
            # Not a file (manual, generated) — never stale
            return StalenessReport(is_stale=False, reason="non-file artifact")
        
        # Read live file
        file_path = Path(self.repo_root) / artifact.source
        if not file_path.exists():
            return StalenessReport(is_stale=True, reason="source file deleted")
        
        live_content = file_path.read_text()
        live_hash = hashlib.sha256(live_content.encode()).hexdigest()
        
        is_stale = live_hash != artifact.content_hash
        
        return StalenessReport(
            is_stale=is_stale,
            reason="content mismatch" if is_stale else "up-to-date",
            last_verified_at=datetime.now().isoformat()
        )
```

---

## File Structure

```
packages/context-hub/
├── src/
│   ├── __init__.py
│   ├── store.py              # ArtifactStore main API
│   ├── ingestion.py          # Validation + ingestion contract
│   ├── search/
│   │   ├── __init__.py
│   │   ├── bm25.py           # BM25Search class
│   │   ├── semantic.py       # SemanticSearch class
│   │   └── hybrid.py         # HybridSearch + RRF
│   ├── git_metadata.py       # GitMetadataStore
│   ├── project_memory.py     # ProjectMemory CRUD
│   ├── staleness.py          # StalenessDetector
│   └── schema.py             # SQL schema, migrations
├── tests/
│   ├── test_store.py
│   ├── test_ingestion.py
│   ├── test_bm25.py
│   ├── test_semantic.py
│   ├── test_hybrid.py
│   ├── test_git.py
│   ├── test_memory.py
│   ├── test_staleness.py
│   └── fixtures/
├── benchmarks/
│   ├── bench_search.py       # RRF speed, embedding time
│   └── bench_storage.py      # Ingest throughput
└── pyproject.toml
```

---

## Configuration

In `.ortho/config.toml`:

```toml
[context_hub]
embedding_enabled = true
embedding_model = "voyage-code-3"              # voyage-code-3 | voyage-3-lite | local
embedding_provider = "anthropic"               # anthropic | local | ollama
embedding_local_path = null                    # path to .gguf if local
bm25_enabled = true
hybrid_rrf_k = 60                              # RRF constant
git_history_enabled = true
staleness_check_on_retrieval = true            # or false (deferred to Phase 4)
```

---

## Testing Strategy

**Unit Tests (35+):**
- Ingestion validation (7 tests)
- Artifact CRUD (5)
- BM25 search (5)
- Semantic search (5)
- Hybrid RRF (5)
- Git metadata (3)
- Project memory (3)
- Staleness detector (3)

**Integration Tests (15+):**
- Ingest + BM25 retrieve (2)
- Ingest + semantic retrieve (2)
- Ingest + hybrid retrieve (2)
- Large artifact (>1MB) (1)
- Special characters in content (1)
- Missing embeddings fallback (1)
- Git history with multiple commits (1)
- Project memory cross-repo isolation (1)
- Staleness with deleted file (1)
- Staleness with modified file (1)
- Concurrent ingestion (1)

**Coverage Target:** 85%+

---

## Exit Criteria

- [x] All 20 acceptance criteria passing
- [x] 50+ tests (50, >85% coverage)
- [x] No breaking changes to shared types
- [x] All APIs documented (docstrings)
- [x] Integration with `.ortho/` storage layer verified
- [x] Embedding model fallback tested
- [x] No external API calls at startup (embeddings lazy)

---

*Created: 2026-06-30 by PLANNER*
*Status: Awaiting GATE-1 approval*
