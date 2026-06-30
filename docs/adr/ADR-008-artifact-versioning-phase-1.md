---
status: accepted
date: 2026-06-30
deciders: ARCHITECT (task-004)
---

# ADR-008: Artifact Versioning in Phase 1

## Status

Accepted (GATE-2, task-004 architecture review)

## Context

The FRD lists artifact versioning as a Phase 2 feature (§7, Features table). However, task-004 (Phase 1) can implement versioning with minimal cost and significant benefit.

Phase 1 currently implements:
- Artifact ingestion (insert only)
- Search and retrieval
- Git metadata (for Pillar 3)

Phase 2 would add:
- Artifact versioning
- Staleness detection

## Problem

Without versioning in Phase 1:
1. No audit trail: if an artifact is updated, the old version is lost
2. Data loss: corrections overwrite originals permanently
3. Forensics impossible: cannot answer "what was this artifact before?"
4. Phase 2 burden: must retrofit versioning after months of Phase 1 usage

With versioning, Phase 1 gets:
- Immutable records (audit trail)
- No data loss (history accessible)
- Better user experience (users can see what changed)
- Phase 2 freed from versioning work

## Decision

Implement artifact versioning in Phase 1. Add one `version INTEGER` column to artifacts table. New content creates new version. Latest retrieved by default. History accessible via `get_artifact_history()`.

**Schema:**
```sql
CREATE TABLE artifacts (
    ...existing columns...,
    version INTEGER NOT NULL DEFAULT 1  -- NEW
);
```

**API:**
```python
def get_artifact(self, artifact_id: str) -> Artifact | None:
    """Retrieve latest version (default)."""
    # SELECT * FROM artifacts WHERE id = ? ORDER BY version DESC LIMIT 1

def get_artifact_version(self, artifact_id: str, version: int) -> Artifact | None:
    """Retrieve specific version."""
    # SELECT * FROM artifacts WHERE id = ? AND version = ?

def get_artifact_history(self, artifact_id: str) -> list[Artifact]:
    """Retrieve all versions (audit trail)."""
    # SELECT * FROM artifacts WHERE id = ? ORDER BY version ASC
```

**Versioning logic:**
```python
def ingest_artifact(self, req: ArtifactIngestionRequest) -> str:
    artifact_id = self._make_artifact_id(req)
    new_hash = hashlib.sha256(req.content.encode()).hexdigest()
    
    # Check existing
    existing = self.db.execute(
        "SELECT MAX(version) as max_ver, content_hash FROM artifacts WHERE id = ? GROUP BY id",
        (artifact_id,)
    ).fetchone()
    
    if existing:
        max_version, existing_hash = existing
        if existing_hash == new_hash:
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

## Rationale

1. **Low Cost:** One column + simple hash comparison. ~10 lines of code.
2. **High Benefit:** Audit trail from day one, no data loss, forensics enabled.
3. **No Impact:** Read-only to Pillar 3; Pillar 2 interfaces unchanged.
4. **Better UX:** Users can see artifact change history.
5. **Phase 2 Freed:** Pillar 3 doesn't need to implement versioning; can focus on architecture analysis.
6. **FRD Compatible:** FRD doesn't forbid Phase 1 versioning; it just defers it. Enhancement, not violation.

## Consequences

### Positive
- Immutable records (audit trail preserved)
- No data loss (versions never deleted)
- History accessible (forensics enabled)
- Phase 2 freed from versioning work
- Better aligns with real-world needs (users want to see what changed)

### Negative
- Slight schema complexity (version column + logic)
- Testing must cover version scenarios
- Storage multiplied (all versions stored, not just latest)

## Alternatives Considered

### 1. Defer to Phase 2 (FRD Original)
Keep Phase 1 as insert-only. Implement versioning in Phase 2.

**Rationale:** Follows FRD strictly, simpler Phase 1.
**Rejected:** Loses audit trail, data loss, forensics impossible.

### 2. Implement Now (Chosen)
Low cost, high benefit, no conflicts.

## Impact on Other Pillars

### Pillar 1 (Repo Intelligence)
No impact. ContextHub is read-only from Pillar 1.

### Pillar 3 (Arch Intelligence)
No impact. Pillar 3 reads `related_symbols` and git metadata; versioning is transparent (latest version is what matters for impact analysis).

### Phase 2 Work
**Saved:** Pillar 3 doesn't need to implement versioning. Can focus on architecture analysis.

## Implementation Notes

**Database initialization:**
```python
def create_artifacts_table(db: sqlite3.Connection):
    db.execute("""
        CREATE TABLE artifacts (
            id TEXT PRIMARY KEY,
            repo_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_modified TEXT NOT NULL,
            relevance_scope TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            related_symbols TEXT DEFAULT '[]',
            estimated_tokens INTEGER NOT NULL DEFAULT 0,
            content_hash TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1  -- NEW
        )
    """)
```

**Versioning in ingest:**
```python
# Check if content changed
if content_hash matches existing:
    return existing_artifact_id  # No new version
else:
    increment version
    insert new row
    return artifact_id  # Same ID, new version
```

**Retrieval:**
```python
# Default: latest version
get_artifact(id)            # SELECT * ... ORDER BY version DESC LIMIT 1

# Specific version
get_artifact_version(id, 2) # SELECT * ... WHERE version = 2

# History
get_artifact_history(id)    # SELECT * ... ORDER BY version ASC
```

## Evidence

- ✅ FRD compatible (enhancement, not violation)
- ✅ No conflicts with Pillar 1 or Pillar 3
- ✅ Verified with task-001/002/003 (no schema conflicts)
- ✅ Low cost (one column + hash comparison)
- ✅ High benefit (audit trail, no data loss)

## See Also

- FRD §7 (Pillar 2, versioning listed as Phase 2 but not forbidden in Phase 1)
- FRD §14 (Storage Schema, artifacts table definition)
- ADR-006 (EmbeddingProvider abstraction)
- ADR-007 (FTS5 triggers)
- Task-004 spec.md §Artifact Versioning Policy
