# ADR-004: Storage Strategy — SQLite + sqlite-vec, Local-First

**Status:** PROPOSED  
**Date:** 2026-06-30  
**Author:** ARCHITECT  
**Approved by:** [Pending human approval]

---

## Context

Ortho must persist three types of data:
1. **Repository metadata** (files, symbols, dependencies, call graphs)
2. **Engineering artifacts** (FRD, ADRs, specs, conversation history)
3. **Embeddings** (for semantic search of artifacts)

The system must:
- Work offline (no cloud services required)
- Require no authentication
- Support single-developer local development
- Enable future team/multi-user deployment without core design changes

This decision affects all of Phases 1–4 and potentially Phase 5+ as Ortho scales.

---

## Problem Statement

**What database backend should Ortho use?**

Constraints from FRD:
- Principle 6: "Local-first whenever practical"
- Section 5: "Storage: Local-first — SQLite + sqlite-vec"
- Section 8: "No cloud, no account required"

Options:
1. PostgreSQL (heavyweight, mature, requires setup)
2. SQLite + sqlite-vec (lightweight, zero setup, purely local)
3. Cloud database (Firestore, DynamoDB, RDS — requires credentials, network-dependent)

---

## Alternatives Considered

### Option A: PostgreSQL

**Description:** Deploy PostgreSQL locally or cloud-hosted. Use pg_trgm for full-text search, pgvector for embeddings, concurrent write handling.

**Pros:**
- Mature, battle-tested, highly scalable
- Excellent full-text search (pg_trgm) and vector search (pgvector)
- Supports concurrent writers (multi-user future)
- Well-understood migration path

**Cons:**
- Requires server setup and management (local or cloud)
- Not inherently portable (would need Docker for deployment)
- Network-dependent (cannot work offline)
- Contradicts FRD Principle 6 (local-first)
- Adds operational burden (backups, administration)

**Verdict:** ❌ **Rejected** — Violates FRD local-first principle, adds complexity for solo developer phase.

---

### Option C: Cloud Database (Firestore, DynamoDB, RDS)

**Description:** Use managed cloud databases with API access.

**Pros:**
- Highly scalable from day one
- Managed backups and disaster recovery
- Supports multi-user/team access

**Cons:**
- Requires API credentials and authentication
- Network-dependent (cannot work offline)
- Locks Ortho into cloud provider
- Directly contradicts FRD: "Storage: Local-first" and "zero cloud"
- Costs money at scale
- Adds privacy concerns (data not user-controlled)

**Verdict:** ❌ **Rejected** — Directly contradicts FRD principles 6 and 8.

---

### Option B: SQLite + sqlite-vec (Chosen)

**Description:** Use SQLite for structured data (repositories, files, symbols), sqlite-vec extension for embedding storage and KNN search. All data persists in `.ortho/` directory.

**Pros:**
- Zero setup required — no server, no authentication, no configuration
- Purely local — single `.db` file in project directory
- Offline-capable — no network calls needed for core functionality
- Portable — entire database fits in version control or backup as single file
- Developer-friendly — inspect data with `sqlite3` CLI, no tools needed
- Full-text search via FTS5 (SQLite built-in)
- Vector search via sqlite-vec (local extension)
- Aligns with FRD Principle 6 and Section 5

**Cons:**
- Single-writer concurrency model (not suitable for multi-user server)
- Query performance optimization needed for large tables (1M+ rows)
- No built-in horizontal scaling
- Requires migration to PostgreSQL if team-based deployment becomes requirement

**Verdict:** ✅ **Selected** — Best fit for Phase 1 solo developer constraints, clear upgrade path.

---

## Decision

**Ortho stores all data in SQLite with local-first architecture.**

### Storage Layout

```
.ortho/
├── config.toml              # Configuration (TOML)
├── ortho.db                 # Main database (repositories, files, symbols, artifacts)
│   ├── repositories
│   ├── files
│   ├── symbols
│   ├── call_edges
│   ├── import_edges
│   ├── artifacts
│   ├── project_memory
│   ├── architecture_models
│   ├── workflow_runs
│   ├── agent_manifests
│   ├── skill_manifests
│   └── artifacts_fts (virtual table, FTS5)
│
└── vectors.db               # Embedding vectors (sqlite-vec extension)
    └── artifact_embeddings (virtual table, vec0)
    └── symbol_embeddings (virtual table, vec0)
```

### Data Persistence

- **Metadata:** SQLite `ortho.db` with all tables from FRD Section 14
- **Embeddings:** sqlite-vec in `vectors.db` for KNN similarity search
- **Configuration:** `.ortho/config.toml` (TOML format from FRD Section 5)
- **Schema Versioning:** Migrations in `shared/storage/src/migrations/` (001_initial_schema.sql, 002_*.sql, etc.)

### Guarantees

- ✅ Zero setup (no server installation)
- ✅ No authentication required
- ✅ Works offline
- ✅ Portable (move `.ortho/` to another machine, it works)
- ✅ Debuggable (direct SQL access via `sqlite3` CLI)
- ✅ Versioned data (schema migrations tracked in git)

---

## Rationale

1. **Alignment with FRD:**
   - Principle 6: "Local-first whenever practical" — SQLite is purely local
   - Section 5: "Storage: Local-first — SQLite + sqlite-vec"
   - Section 8: "No cloud, no account required" — SQLite satisfies both

2. **Phase 1 Appropriateness:**
   - Solo developer, single process, no concurrency needs
   - Fast to prototype, fast to verify
   - No infrastructure setup delays development

3. **Developer Experience:**
   - Single `.ortho/` directory contains all state
   - No configuration to manage
   - Works offline (critical for development environment)
   - Inspectable with `sqlite3` CLI

4. **Clear Upgrade Path:**
   - Well-understood migration: SQLite → PostgreSQL
   - Schema is standard SQL (minimal PostgreSQL-specific syntax)
   - No application logic rewrite needed (both use relational tables)
   - Can migrate when team collaboration becomes required (Phase 3+)

5. **Cost and Sustainability:**
   - No cloud costs during development
   - No vendor lock-in
   - Sustainable for solo developer indefinitely

---

## Consequences

### Positive

- **Developer Velocity:** No database setup, fast iteration
- **Offline Capability:** Essential for laptop-based development
- **Debuggability:** Direct SQL access makes issues transparent
- **Portability:** `.ortho/` is self-contained; backup/sync straightforward
- **Zero Credentials:** No API keys to manage or expose
- **Embedding Support:** sqlite-vec provides KNN search without external service

### Negative

- **Concurrency Limitations:** Single-writer model (WAL mode improves read concurrency, but writes still serialized)
  - *Acceptable in Phase 1* (solo developer)
  - *Mitigation in Phase 2+*: If multi-user needed, migrate to PostgreSQL
- **Query Performance:** Optimization needed for large tables (1M+ symbols in Phase 3+)
  - *Acceptable in Phase 1* (repo data small initially)
  - *Mitigation in Phase 4*: Add indexing strategy, possibly sharding
- **Migration Burden:** Switching to PostgreSQL requires migration process
  - *Acceptable* (well-understood process, clear trigger conditions)

### Neutral

- **Embedding Dimensions:** Fixed at 1536 (matches Voyage embeddings)
  - If model changes (e.g., to 512-dim), schema update needed (one-time)
- **Schema Versioning:** Manual migration bumps required
  - *Acceptable* (only ARCHITECT+BUILDER manage schema)

---

## Future Considerations

### When Might This Decision Be Revisited?

1. **Team Collaboration (Phase 3+):** If Ortho becomes a team tool (not solo developer only), multi-writer concurrency needed → PostgreSQL migration
2. **Scale (1M+ rows in Phase 4+):** If symbol/artifact tables exceed SQLite's comfortable range, performance analysis may trigger migration
3. **Expense App Divergence:** Expense App (Phase 3) may need separate PostgreSQL for multi-user scenarios; Ortho remains solo SQLite unless requirements change

### Migration Strategy (If Needed)

If evidence shows PostgreSQL needed:

1. **Export:** `SELECT * FROM ortho.db → CSV files`
2. **Import:** `COPY FROM CSV → PostgreSQL`
3. **Update Connection:** Change connection string in `shared/storage/src/database.py`
4. **Test:** Run full verification suite
5. **Deploy:** Switch connection, archive old `.db` file

Estimated effort: 2–3 days (low risk).

---

## Related Tasks

- **task-001:** Phase 1 Week 1–2 Shared Foundation (implements this ADR)

---

## Related ADRs

- **ADR-001:** ASES Multi-Agent Orchestration — Independent of storage choice; works with any backend
- **ADR-003:** Evidence Capture Strategy — Uses terminal tools, not database queries; storage-agnostic
- **ADR-005:** Language Adapter Plugin Model — Depends on storage for symbol persistence; compatible with SQLite

---

*End of ADR-004*
