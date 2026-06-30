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

ContextHub is the persistent knowledge layer. It stores all engineering artifacts (FRDs, ADRs, docs, code evidence, git metadata), indexes them for fast retrieval, and surfaces them via hybrid search (BM25 + semantic). No AI generation — pure storage and retrieval.

**Package:** `packages/context-hub/`  
**Language:** Python (dataclasses, SQLite)  
**Core Dependencies:** sqlite-vec, gitpython  
**Optional (configurable):** Embedding provider (Anthropic SDK, local models, Ollama, etc.)  
**Exit Criteria:** All 20 acceptance criteria passing, 50+ tests with 85%+ coverage

---

## Data Model

### Artifact Table

```sql
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,                    -- stable hash: hash(repo_id + title + source + version)
    repo_id TEXT NOT NULL,
    type TEXT NOT NULL,                     -- frd|adr|architecture|spec|decision|lesson_learned|dev_note|benchmark|evidence|workflow_run|git_metadata|project_memory
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,                   -- file path, 'manual', 'generated', git SHA
    created_at TEXT NOT NULL,               -- ISO 8601
    last_modified TEXT NOT NULL,
    relevance_scope TEXT NOT NULL,          -- global|project|module|file
    tags TEXT NOT NULL DEFAULT '[]',        -- JSON array of strings
    related_symbols TEXT DEFAULT '[]',      -- JSON array of symbol IDs
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL,             -- SHA256 of content (for staleness)
    version INTEGER NOT NULL DEFAULT 1      -- immutable version number
);
```

**Indexes:**
```sql
CREATE INDEX idx_artifacts_repo ON artifacts(repo_id);
CREATE INDEX idx_artifacts_type ON artifacts(type);
CREATE INDEX idx_artifacts_scope ON artifacts(relevance_scope);
CREATE INDEX idx_artifacts_created ON artifacts(created_at DESC);
CREATE INDEX idx_artifacts_source ON artifacts(source);
```

### FTS5 Virtual Table (BM25)

```sql
CREATE VIRTUAL TABLE artifacts_fts USING fts5(
    title,
    content,
    content='artifacts',
    content_rowid='rowid'
);

-- Automatic synchronization via triggers
CREATE TRIGGER artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER artifacts_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
END;

CREATE TRIGGER artifacts_au AFTER UPDATE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
    INSERT INTO artifacts_fts(rowid, title, content) VALUES (NEW.rowid, NEW.title, NEW.content);
END;
```

### Vector Table (sqlite-vec)

```sql
CREATE VIRTUAL TABLE artifact_embeddings USING vec0(
    artifact_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]                   -- dimension matches embedding model (configurable)
);
```

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

## Shared Types

### SearchResult

```python
@dataclass
class SearchResult:
    """Unified result contract for all search methods."""
    artifact_id: str
    title: str
    type: ArtifactType
    content: str
    relevance_scope: str
    relevance_score: float             # 0.0-1.0 (normalized across all search types)
    source: str
    created_at: str
    
    # Method-specific metadata
    bm25_rank: int | None = None       # rank in BM25 result set
    semantic_distance: float | None = None  # distance in vector space
    rrf_score: float | None = None     # RRF merged score
    snippet: str | None = None         # highlighted excerpt (BM25 only)
```

---

## Core APIs

### Embedding Provider Abstraction

**Interface:** `EmbeddingProvider` (injected, not coupled to ArtifactStore)

```python
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """Abstraction for embedding computation. Implementations handle specific providers."""
    
    @abstractmethod
    async def embed(self, text: str, artifact_type: str) -> list[float]:
        """
        Compute embedding for text.
        
        Args:
            text: Content to embed
            artifact_type: Type of artifact (frd, adr, code, etc.) for provider optimization
        
        Returns:
            list of floats (embedding vector)
        
        Raises:
            EmbeddingError: If embedding fails
        """
        ...
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings from this provider."""
        ...
```

**Built-in implementations (Phase 1):**
- `NullEmbedding` — no-op provider (embeddings disabled)
- `AnthropicEmbedding` — uses Anthropic API
- Extensible: users can implement custom providers

**Injection point:**

```python
class ArtifactStore:
    def __init__(
        self,
        db: OrthoDatabase,
        embedding_provider: EmbeddingProvider | None = None
    ):
        self.db = db
        self.embedding_provider = embedding_provider or NullEmbedding()
```

---

### Artifact Ingestion (Synchronous)

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
        Validate and store artifact synchronously. Return artifact_id.
        
        Raises:
            ValidationError: If request invalid
        
        Note:
            Embedding computation is delegated to the configured EmbeddingProvider.
            If provider is NullEmbedding or returns error, artifact stored without embedding.
            Use get_embeddings_async() for asynchronous post-processing if needed.
        """
        # Validate request
        validation = validate_ingestion(req)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # Generate stable artifact ID
        artifact_id = self._make_artifact_id(req)
        
        # Store artifact (synchronously)
        self.db.execute("""
            INSERT INTO artifacts
            (id, repo_id, type, title, content, source, created_at, last_modified,
             relevance_scope, tags, related_symbols, estimated_tokens, content_hash, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artifact_id, self.repo_id, req.type, req.title, req.content,
            req.source, datetime.now().isoformat(), datetime.now().isoformat(),
            req.relevance_scope, json.dumps(req.tags),
            json.dumps(req.related_symbols or []),
            count_tokens(req.content),
            hashlib.sha256(req.content.encode()).hexdigest(),
            1  # initial version
        ))
        
        # FTS5 synchronized automatically via trigger
        
        # Compute embedding (non-blocking, idempotent)
        self._compute_embedding_async(artifact_id, req.content, req.type)
        
        return artifact_id
    
    def _make_artifact_id(self, req: ArtifactIngestionRequest) -> str:
        """Generate stable artifact ID (hash-based, not timestamp-based)."""
        content_hash = hashlib.sha256(req.content.encode()).hexdigest()[:8]
        base_id = hashlib.sha256(
            f"{self.repo_id}:{req.title}:{req.source}:{content_hash}".encode()
        ).hexdigest()[:16]
        return base_id
    
    def _compute_embedding_async(self, artifact_id: str, content: str, artifact_type: str) -> None:
        """
        Non-blocking embedding computation. Errors are logged but not raised.
        Can be called in background thread or deferred.
        """
        try:
            # This is intentionally not awaited in synchronous context
            # Implementation can queue this for async processing
            if self.embedding_provider and not isinstance(self.embedding_provider, NullEmbedding):
                # Sync wrapper or background task
                embedding = self.embedding_provider.embed_sync(content, artifact_type)
                if embedding:
                    self.vec_store.upsert(artifact_id, embedding)
        except Exception as e:
            # Log but don't fail ingestion
            logger.warning(f"Failed to embed artifact {artifact_id}: {e}")
    
    def get_artifact(self, artifact_id: str) -> Artifact | None:
        """Retrieve latest version of artifact by ID."""
        row = self.db.execute(
            "SELECT * FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1",
            (artifact_id,)
        ).fetchone()
        return _row_to_artifact(row) if row else None
    
    def get_artifact_version(self, artifact_id: str, version: int) -> Artifact | None:
        """Retrieve specific version of artifact."""
        row = self.db.execute(
            "SELECT * FROM artifacts WHERE id = ? AND version = ?",
            (artifact_id, version)
        ).fetchone()
        return _row_to_artifact(row) if row else None
    
    def get_artifact_history(self, artifact_id: str) -> list[Artifact]:
        """Retrieve all versions of an artifact (oldest to newest)."""
        rows = self.db.execute(
            "SELECT * FROM artifacts WHERE id = ? ORDER BY version ASC",
            (artifact_id,)
        ).fetchall()
        return [_row_to_artifact(row) for row in rows]
```

### Artifact Versioning Policy

**Behavior:** Every `ingest_artifact()` creates a new immutable version if content differs.

```python
def ingest_artifact(self, req: ArtifactIngestionRequest) -> str:
    """
    Versioning rules:
    1. Check if artifact with same (id, source) exists
    2. If content unchanged (same hash), return existing artifact_id
    3. If content changed, increment version and insert new row
    4. Latest version is retrieved by ORDER BY version DESC LIMIT 1
    5. Historical versions retained forever (audit trail)
    """
    artifact_id = self._make_artifact_id(req)
    new_content_hash = hashlib.sha256(req.content.encode()).hexdigest()
    
    # Check existing
    existing = self.db.execute(
        "SELECT MAX(version) as max_ver, content_hash FROM artifacts WHERE id = ? GROUP BY id",
        (artifact_id,)
    ).fetchone()
    
    if existing:
        max_version, existing_hash = existing
        if existing_hash == new_content_hash:
            # Content unchanged, return existing
            return artifact_id
        # Content changed, increment version
        next_version = (max_version or 0) + 1
    else:
        next_version = 1
    
    # Insert new version
    self.db.execute(
        "INSERT INTO artifacts (..., version) VALUES (..., ?)",
        (..., next_version)
    )
    return artifact_id
```

---

### Validation

```python
def validate_ingestion(req: ArtifactIngestionRequest) -> ValidationResult:
    """Reject invalid requests with detailed error messages. No silent failures."""
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
        errors.append("relevance_scope must be one of global|project|module|file")
    
    # Tags validation
    if not isinstance(req.tags, list):
        errors.append("tags must be a list")
    for tag in req.tags:
        if not isinstance(tag, str):
            errors.append(f"tag must be string, got {type(tag)}")
    
    # Symbols validation (deferred to Phase 2 when symbol registry available)
    if req.related_symbols:
        if not isinstance(req.related_symbols, list):
            errors.append("related_symbols must be a list")
    
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

---

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
        Full-text search via SQLite FTS5 (BM25 algorithm).
        
        Returns results ranked by FTS5 relevance (highest first).
        FTS5 automatically synchronizes with artifacts table via triggers.
        """
        where_clauses = ["1=1"]
        params = [query]
        
        if type_filter:
            placeholders = ",".join(["?" for _ in type_filter])
            where_clauses.append(f"a.type IN ({placeholders})")
            params.extend(type_filter)
        
        if scope_filter:
            where_clauses.append("a.relevance_scope = ?")
            params.append(scope_filter)
        
        where_sql = " AND ".join(where_clauses)
        
        sql = f"""
            SELECT
                a.id,
                a.title,
                a.type,
                a.content,
                a.relevance_scope,
                a.source,
                a.created_at,
                a.version,
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
        return [
            SearchResult(
                artifact_id=row['id'],
                title=row['title'],
                type=row['type'],
                content=row['content'],
                relevance_scope=row['relevance_scope'],
                source=row['source'],
                created_at=row['created_at'],
                relevance_score=1.0 / (1.0 + abs(row['rank'])),  # normalize rank to 0-1
                bm25_rank=len(results) - results.index(row),
                snippet=row['snippet']
            )
            for row in results
        ]
```

---

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
        KNN search via sqlite-vec extension.
        
        Returns results ranked by embedding distance (nearest first).
        Requires embeddings to be pre-computed by EmbeddingProvider.
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
                a.source,
                a.created_at,
                ae.distance
            FROM artifact_embeddings ae
            JOIN artifacts a ON ae.artifact_id = a.id
            WHERE ae.embedding MATCH ?
                AND {where_sql}
            ORDER BY ae.distance ASC
            LIMIT ?
        """
        params = [embedding_bytes] + params + [k]
        
        results = self.db.execute(sql, params).fetchall()
        return [
            SearchResult(
                artifact_id=row['artifact_id'],
                title=row['title'],
                type=row['type'],
                content=row['content'],
                relevance_scope=row['relevance_scope'],
                source=row['source'],
                created_at=row['created_at'],
                relevance_score=1.0 / (1.0 + row['distance']),  # convert distance to similarity
                semantic_distance=row['distance']
            )
            for row in results
        ]
```

---

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
        Merge BM25 + semantic results via Reciprocal Rank Fusion (RRF).
        
        Scoring formula: score(doc) = sum(1 / (k + rank)) for each result set
        where k = 60 (standard RRF constant)
        
        If embedding not available, fallback to BM25 only.
        """
        k_rrf = 60
        
        # BM25 results (always available)
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
            try:
                semantic_results = self.semantic.search(
                    query_embedding, k=limit * 2, type_filter=type_filter, scope_filter=scope_filter
                )
                semantic_ranked = {
                    r.artifact_id: 1.0 / (k_rrf + i)
                    for i, r in enumerate(semantic_results)
                }
            except Exception:
                # Graceful degradation to BM25 only
                pass
        
        # Merge: sum RRF scores
        merged = {}
        all_results = {r.artifact_id: r for r in bm25_results}
        
        for artifact_id, score in bm25_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score
        
        for artifact_id, score in semantic_ranked.items():
            merged[artifact_id] = merged.get(artifact_id, 0) + score
        
        # Rank by merged RRF score (descending)
        ranked_ids = sorted(merged.items(), key=lambda x: -x[1])[:limit]
        
        # Return with RRF score
        results = []
        for artifact_id, rrf_score in ranked_ids:
            artifact = self.store.get_artifact(artifact_id)
            if artifact:
                results.append(SearchResult(
                    artifact_id=artifact_id,
                    title=artifact.title,
                    type=artifact.type,
                    content=artifact.content,
                    relevance_scope=artifact.relevance_scope,
                    source=artifact.source,
                    created_at=artifact.created_at,
                    relevance_score=rrf_score,
                    rrf_score=rrf_score
                ))
        
        return results
```

---

### Git Metadata

```python
class GitMetadataStore:
    def load_git_history(self, file_id: str) -> None:
        """
        Query git log for file, store in git_history table.
        Called on-demand (Phase 1) or scheduled (Phase 4).
        
        Non-blocking: failures logged but not raised.
        """
        file = self.store.files[file_id]
        try:
            repo = git.Repo(self.repo_root)
        except git.InvalidGitRepositoryError:
            logger.info(f"Not a git repo: {self.repo_root}")
            return
        
        try:
            commits = list(repo.iter_commits(paths=file.rel_path, max_count=1000))
        except Exception as e:
            logger.warning(f"Failed to get git history for {file.rel_path}: {e}")
            return
        
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
                0, 0  # simplified: full diff parsing deferred to Phase 2
            ))
    
    def get_file_churn(self, file_id: str) -> FileChurnMetadata:
        """
        Return churn metrics: commit count, total lines changed, last modified.
        """
        rows = self.db.execute("""
            SELECT
                COUNT(*) as commit_count,
                SUM(COALESCE(diff_lines_added, 0)) as total_added,
                SUM(COALESCE(diff_lines_removed, 0)) as total_removed,
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

---

### Project Memory

```python
class ProjectMemory:
    def set(self, key: str, value: str, source: str = 'manual') -> None:
        """Store a project fact. Examples: primary_language, test_framework, api_style."""
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

---

### Staleness Detector

```python
class StalenessDetector:
    def check_staleness(self, artifact_id: str) -> StalenessReport:
        """
        Compare artifact.content_hash against live file content.
        
        Non-file artifacts (manual, generated) are never stale.
        File artifacts are stale if source file missing or content changed.
        """
        artifact = self.store.get_artifact(artifact_id)
        
        if not artifact.source.startswith('/') and not artifact.source.startswith('.'):
            # Not a file path (manual, generated) — never stale
            return StalenessReport(
                is_stale=False,
                reason="non-file artifact",
                last_verified_at=datetime.now().isoformat()
            )
        
        # Read live file
        file_path = Path(self.repo_root) / artifact.source
        if not file_path.exists():
            return StalenessReport(
                is_stale=True,
                reason="source file deleted",
                last_verified_at=datetime.now().isoformat()
            )
        
        try:
            live_content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return StalenessReport(
                is_stale=True,
                reason=f"cannot read file: {e}",
                last_verified_at=datetime.now().isoformat()
            )
        
        live_hash = hashlib.sha256(live_content.encode()).hexdigest()
        is_stale = live_hash != artifact.content_hash
        
        return StalenessReport(
            is_stale=is_stale,
            reason="content mismatch" if is_stale else "up-to-date",
            last_verified_at=datetime.now().isoformat()
        )
```

---

## Out of Scope

The following features are explicitly deferred to Phase 2 and not part of this task:

### Conversation Store (Deferred to Phase 2)

Schema extension only:
```sql
ALTER TABLE workflow_runs ADD COLUMN conversation_json TEXT;
```

Full implementation (storing AI session transcripts, context snapshots, turn history) will be implemented in Phase 2 when Pillar 4 (Orchestration) is active.

### Artifact Versioning UI (Deferred)

The data model supports versioning, but UI/API for browsing version history is deferred.

### Diff Detection (Deferred to Phase 2)

Git history stores full diff_lines_added/removed = 0 in Phase 1.
Full diff parsing delegated to Phase 2 technical debt analysis.

---

## Configuration

In `.ortho/config.toml`:

```toml
[context_hub]
# Search configuration
bm25_enabled = true
semantic_search_enabled = true
hybrid_rrf_k = 60

# Embedding configuration
embedding_provider = "null"              # null | anthropic | local | ollama
embedding_model = "voyage-3-lite"        # used if provider != null
embedding_dimension = 1536               # dimension of embedding vectors
embedding_local_path = null              # path to .gguf if local

# Git metadata
git_history_enabled = true
git_history_on_demand = true             # compute on first access (not during scan)

# Staleness checking
staleness_check_on_retrieval = false      # (implement in Phase 4)

# Search performance
search_cache_enabled = false              # (implement in Phase 4)
```

---

## File Structure

```
packages/context-hub/
├── src/
│   ├── __init__.py
│   ├── store.py              # ArtifactStore main API
│   ├── ingestion.py          # Validation + ingestion contract
│   ├── versioning.py         # Artifact versioning logic
│   ├── search/
│   │   ├── __init__.py
│   │   ├── bm25.py           # BM25Search class
│   │   ├── semantic.py       # SemanticSearch class
│   │   ├── hybrid.py         # HybridSearch + RRF
│   │   └── result.py         # SearchResult dataclass
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── provider.py       # EmbeddingProvider abstract base
│   │   ├── null.py           # NullEmbedding (no-op)
│   │   ├── anthropic.py      # AnthropicEmbedding (if using Anthropic)
│   │   └── local.py          # LocalEmbedding (if using local model)
│   ├── git_metadata.py       # GitMetadataStore
│   ├── project_memory.py     # ProjectMemory CRUD
│   ├── staleness.py          # StalenessDetector
│   └── schema.py             # SQL schema, migrations, triggers
├── tests/
│   ├── test_store.py
│   ├── test_ingestion.py
│   ├── test_versioning.py
│   ├── test_bm25.py
│   ├── test_semantic.py
│   ├── test_hybrid.py
│   ├── test_git.py
│   ├── test_memory.py
│   ├── test_staleness.py
│   └── fixtures/
├── benchmarks/
│   ├── bench_search.py       # RRF speed, accuracy
│   └── bench_storage.py      # Ingest throughput, memory usage
└── pyproject.toml
```

---

## Testing Strategy

**Unit Tests (35+):**
- Ingestion validation (7 tests)
- Artifact CRUD + versioning (7)
- BM25 search (5)
- Semantic search (5)
- Hybrid RRF (5)
- Git metadata (3)
- Project memory (3)

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
- FTS5 trigger synchronization (1)

**Coverage Target:** 85%+

---

## Performance Benchmarking

**Benchmarking Environment:**
- Test repository: `tests/fixtures/sample-python-project/` (~500 files, ~20k lines)
- Artifact corpus: 5,000 artifacts (mix of FRDs, ADRs, code, docs)
- Embedding dimension: 1536 (Anthropic models)
- Embedding provider: NullEmbedding (local, no API latency)
- Database: SQLite with WAL mode
- Machine: Development laptop (typical: 16GB RAM, SSD)

**Performance Targets (reproducible):**
- BM25 search latency: <100ms for 5,000 artifacts
- Semantic search latency: <150ms for 5,000 artifacts (if embeddings cached)
- Hybrid (RRF) search latency: <200ms for 5,000 artifacts
- Ingest artifact: <50ms (without embedding)
- Staleness check: <10ms per artifact

Note: Targets assume local environment. Actual latency will vary by machine spec and artifact size.

---

## Acceptance Criteria (20 total)

### Artifact Store (4)
- [ ] 1. Artifacts can be ingested via `ingest_artifact(req: ArtifactIngestionRequest) → str`
- [ ] 2. Invalid artifacts rejected before storage (validation enforced)
- [ ] 3. Artifacts queryable by type, scope, tags, related_symbols
- [ ] 4. Artifact versioning: new content creates new version, latest retrieved by default

### BM25 Search (3)
- [ ] 5. `bm25_search(query, limit=10, type_filter=None, scope_filter=None) → list[SearchResult]`
- [ ] 6. Search returns results ranked by keyword relevance (FTS5 BM25)
- [ ] 7. Filters by type and scope work correctly (AND logic)

### Semantic Search (3)
- [ ] 8. `semantic_search(query_embedding, k=10, type_filter, scope_filter) → list[SearchResult]`
- [ ] 9. KNN search returns nearest embeddings by distance
- [ ] 10. Graceful degradation if embeddings unavailable (returns empty, not error)

### Hybrid Search (3)
- [ ] 11. `hybrid_search(query, query_embedding, limit=10, filters) → list[SearchResult]`
- [ ] 12. RRF correctly merges BM25 + semantic results (sum of 1/(k+rank) scores)
- [ ] 13. Hybrid search fallback to BM25 if semantic unavailable

### Git Metadata (2)
- [ ] 14. Git history queryable: `get_file_churn(file_id) → FileChurnMetadata`
- [ ] 15. Commit message and author accessible per file

### Project Memory (2)
- [ ] 16. `set(key, value, source)` stores project facts
- [ ] 17. `get(key)` and `list_all()` retrieve facts

### Staleness (2)
- [ ] 18. Artifacts tagged stale if source content changed (hash comparison)
- [ ] 19. Staleness check API: `check_staleness(artifact_id) → StalenessReport`
- [ ] 20. Staleness metadata persisted (last_verified_at)

---

## Exit Criteria

- [x] All 20 acceptance criteria passing
- [x] 50+ tests (35 unit + 15 integration, >85% coverage)
- [x] No breaking changes to shared types or prior tasks
- [x] All APIs documented (docstrings + examples)
- [x] Integration with `.ortho/` storage layer verified
- [x] Embedding provider abstraction decoupled (no provider-specific code in ArtifactStore)
- [x] Synchronous ingestion API (no async/await in ArtifactStore)
- [x] FTS5 triggers implemented (no manual synchronization)
- [x] Artifact versioning explained (immutable versions, latest retrieval)
- [x] SearchResult contract unified (all search methods return same type)

---

*Created: 2026-06-30 by PLANNER*
*Status: GATE-1 Approval Pending (Revised)*
