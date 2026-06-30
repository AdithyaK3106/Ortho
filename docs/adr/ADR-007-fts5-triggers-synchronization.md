---
status: accepted
date: 2026-06-30
deciders: ARCHITECT (task-004)
---

# ADR-007: FTS5 Triggers for Automatic Synchronization

## Status

Accepted (GATE-2, task-004 architecture review)

## Context

ContextHub maintains two representations of artifacts:
1. `artifacts` table — canonical record (id, type, title, content, etc.)
2. `artifacts_fts` virtual table — FTS5 index (for BM25 keyword search)

These must stay synchronized at all times. If they diverge, search results become stale or incorrect.

## Problem

If synchronization is manual (Python code managing both tables):
1. Easy to forget sync when updating/deleting (bugs)
2. Non-atomic (artifact stored, then FTS5 sync fails → inconsistency)
3. Race conditions (concurrent ingestions)
4. Complex error handling (rollback on partial failure)

## Decision

Use **database triggers** to automatically synchronize FTS5 on every modification:

```sql
CREATE TRIGGER artifacts_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_fts(rowid, title, content) 
    VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER artifacts_au AFTER UPDATE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
    INSERT INTO artifacts_fts(rowid, title, content) 
    VALUES (NEW.rowid, NEW.title, NEW.content);
END;

CREATE TRIGGER artifacts_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_fts WHERE rowid = OLD.rowid;
END;
```

**Python code:** Only executes `INSERT INTO artifacts (...)` or `UPDATE artifacts ...`. Triggers handle FTS5 automatically.

## Rationale

1. **Atomic:** Trigger fires within same transaction as artifacts table modification.
2. **Automatic:** No Python code needed to manage synchronization.
3. **Consistent:** Impossible to have artifacts without FTS5 entry (or vice versa).
4. **Portable:** Standard SQLite (no extensions beyond FTS5, which we already use).
5. **Tested:** SQLite triggers are well-understood and robust.

## Consequences

### Positive
- Bulletproof consistency (triggers enforce invariant)
- Simpler Python code (no manual sync logic)
- No divergence possible (even under edge cases)
- Self-healing (triggers apply on every transaction)
- Transaction-safe (trigger part of same transaction)

### Negative
- Triggers add complexity to schema (must be defined at initialization)
- Testing must verify trigger firing (not always obvious)
- Limited to what SQL can express (complex transformations would need Python)

## Alternatives Considered

### 1. Manual Sync in Python
```python
def ingest_artifact(self, req):
    # Insert artifact
    self.db.execute("INSERT INTO artifacts (...) VALUES (...)")
    
    # Manually sync FTS5
    self.db.execute("INSERT INTO artifacts_fts (...) VALUES (...)")
```

**Rejected:** Error-prone, non-atomic, race conditions.

### 2. Periodic Re-sync Job
```python
def sync_fts_background():
    # Run every 5 minutes to re-sync FTS5 from artifacts
    ...
```

**Rejected:** Eventual consistency only, races possible, overhead.

### 3. Database Triggers (Chosen)
Atomic, automatic, consistent. No downsides for FTS5 sync.

## Implementation

**Schema creation:**
```python
def create_fts5_triggers(db: sqlite3.Connection):
    db.execute("""
        CREATE TRIGGER artifacts_ai AFTER INSERT ON artifacts BEGIN
            INSERT INTO artifacts_fts(rowid, title, content) 
            VALUES (NEW.rowid, NEW.title, NEW.content);
        END;
    """)
    # ... (update and delete triggers)
```

**Verification (unit test):**
```python
def test_fts5_trigger_on_insert():
    store.ingest_artifact(req)
    
    # Verify FTS5 has entry
    result = store.bm25_search("keyword")
    assert len(result) > 0
```

## Evidence

- ✅ Standard SQLite best practice
- ✅ No portability issues (FTS5 + triggers are standard)
- ✅ Verified with FRD (no schema conflicts)
- ✅ Compatible with task-001/002/003 schema

## See Also

- SQLite Documentation: CREATE TRIGGER
- SQLite FTS5 Documentation
- ADR-006 (EmbeddingProvider abstraction)
- Task-004 spec.md §FTS5 Virtual Table
