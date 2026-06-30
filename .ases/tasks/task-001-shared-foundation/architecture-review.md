# Architecture Review

**Task ID:** task-001  
**Task Title:** Phase 1 Week 1–2 — Shared Foundation  
**Reviewer:** ARCHITECT  
**Created:** 2026-06-30  
**Status:** PROPOSED (awaiting human approval)

---

## Executive Summary

**Verdict: ✅ APPROVED**

The architecture for Phase 1 Week 1–2 (Shared Foundation) is sound. All module boundaries are clear, dependencies are acyclic, and API contracts are well-defined. The design supports the FRD's five pillars and maintains alignment with existing ADRs (ADR-001 multi-agent system, ADR-003 evidence capture).

Two new ADRs are required: ADR-004 (Storage Strategy) and ADR-005 (Language Adapter Plugin Model). Both are included below and ready for approval.

---

## Module Boundary Evaluation

### Proposed Modules (New)

The task introduces **4 new top-level modules**, each with clear responsibility:

| Module | Responsibility | Dependencies | Cohesion |
|--------|---------------|----|----------|
| `shared/types/` | Canonical data models (TS) — Repository, Symbol, Artifact, Architecture, Workflow, Context, LLM types | None (leaf module) | ✅ High — single purpose: define contracts |
| `shared/storage/` | SQLite database abstraction + migrations (Python) — OrthoDatabase, VectorStore, OrthoConfig | `shared/types` (imports types for serialization) | ✅ High — single purpose: persist + retrieve |
| `apps/cli/` | User-facing CLI (TypeScript) — command parser, init command | `shared/types`, `shared/storage` (types + config) | ✅ High — single purpose: user interface |
| `apps/api-server/` | FastAPI server backend (Python) — routing, health check, future endpoints | `shared/storage`, `shared/types` | ✅ High — single purpose: HTTP interface to storage |

### Existing Modules (Unchanged)

- `.ases/` — ASES framework (governance, workflows, templates, agents) — **unaffected**
- All other project folders — **no changes**

### Boundary Assessment

✅ **Verdict: Clear and coherent boundaries**

- Each module has **one reason to change**
- **No boundary violations** — modules do not access each other's private state
- **Clear API contracts** between modules (defined below)
- **Cohesion is high** — each module groups related functionality
- **No side effects** between modules

---

## Dependency Analysis

### Dependency Graph

```
apps/cli/
  → shared/types/ (imports types for CLI operations)
  → shared/storage/ (imports OrthoConfig to initialize)
      ↓
apps/api-server/
  → shared/storage/ (imports OrthoDatabase, VectorStore)
  → shared/types/ (imports types for serialization)
      ↓
shared/storage/
  → shared/types/ (imports types for dataclass fields)
      ↓
shared/types/
  (no dependencies — leaf module)
```

### Circular Dependency Check

✅ **No circular dependencies detected**

- `shared/types` has no dependencies (foundation)
- `shared/storage` depends only on `shared/types` (one-way)
- `apps/cli` and `apps/api-server` both depend on lower layers (one-way)
- No module depends on its own dependents

**Dependency flow is strictly downward:** CLI/API → Storage → Types → (nothing)

### Fan-In / Fan-Out Analysis

| Module | Fan-In | Fan-Out | Assessment |
|--------|--------|---------|------------|
| `shared/types` | 3 (storage, cli, api) | 0 | ✅ Good — widely used, no outbound deps |
| `shared/storage` | 2 (cli, api) | 1 (types) | ✅ Good — stable, minimal outbound |
| `apps/cli` | 0 | 2 (storage, types) | ✅ Good — leaf application |
| `apps/api-server` | 0 | 2 (storage, types) | ✅ Good — leaf application |

---

## API Contract Definitions

### 1. CLI → Storage API

**Invoked By:** `apps/cli/src/commands/init.ts`  
**Implements:** `shared/storage/src/config.py` + `shared/storage/src/database.py`

**Contract:**
```python
# OrthoConfig (from storage layer)
OrthoConfig.load(path: Path) -> OrthoConfig
OrthoConfig.validate() -> None  # raises ValueError if invalid

# OrthoDatabase (from storage layer)
OrthoDatabase(project_root: Path)
OrthoDatabase.migrate() -> None  # applies 001_initial_schema.sql
OrthoDatabase.connection() -> sqlite3.Connection
```

**Example Flow:**
```
CLI calls:
  config = OrthoConfig.load(Path(".ortho/config.toml"))
  db = OrthoDatabase(Path("."))
  db.migrate()
  # .ortho/ortho.db now has full schema
```

### 2. API Server → Storage API

**Invoked By:** `apps/api-server/src/main.py`  
**Implements:** Same as above (shared storage layer)

**Contract:**
```python
db = OrthoDatabase(project_root)
conn = db.connection()  # returns sqlite3.Connection for queries
```

### 3. HTTP API (FastAPI)

**Exposed By:** `apps/api-server/src/main.py`  
**Endpoints (Phase 1):**

```
GET /health
  Response: 200 OK
  Body: { "status": "ok" }
```

**Future Endpoints (Phase 2+):**
- `POST /api/init` — Initialize database (called by CLI)
- `POST /api/scan` — Scan repository
- `GET /api/context/search` — Search artifacts

### 4. Type Serialization Contract

**Defined In:** `shared/types/src/*.ts`

All types must serialize/deserialize correctly between TypeScript (CLI) and Python (API/Storage):

```typescript
// TypeScript
const artifact: Artifact = {
  id: "abc123",
  repo_id: "repo1",
  type: "frd",
  // ...
};
JSON.stringify(artifact);  // → JSON string

// Python receives JSON, deserializes to dataclass
artifact_json = json.loads(json_string)
artifact = Artifact(**artifact_json)  # pydantic or dataclass
```

✅ **All types in shared/types/ are JSON-serializable** (no circular references, no special objects)

---

## Data Flow Review

### Phase 1 Data Flow: `ortho init`

```
User runs: ortho init
  ↓
CLI (init.ts) parses command
  ↓
CLI loads config from template: OrthoConfig.load(".ortho/config.toml")
  ↓
CLI initializes database: OrthoDatabase(".").migrate()
  ↓
Database applies 001_initial_schema.sql
  ↓
SQLite creates tables: repositories, files, symbols, call_edges, import_edges, artifacts, etc.
  ↓
CLI reports success: ".ortho/ initialized"
```

### Data Validation Layers

**Validation happens at correct layers:**

| Layer | What Gets Validated | Examples |
|-------|---------------------|----------|
| **Config** (OrthoConfig) | Configuration TOML structure | Required keys present, types correct |
| **Database Schema** (SQL) | Data constraints | NOT NULL, UNIQUE, FK constraints, CHECK clauses |
| **Application** (future) | Business logic | (Phase 2+: symbol name format, import validity) |

✅ **Validation placement is sound** — configuration at load time, schema constraints in DB, business logic deferred

### Future Phase 2–4 Data Flow

As new features are added:

```
ortho scan → LanguageAdapter.extract_symbols() → symbols inserted into DB
ortho context search → ContextHub.retrieve() → RRF ranking → JSON response
ortho run → Orchestrator → Selector → LLM → Evidence collection
```

All flows route through `shared/storage/` layer — single point of data persistence.

---

## Risk Assessment

### Security Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Local database access** | Low | SQLite local-only, no network exposure in Phase 1. File permissions managed by OS. |
| **SQL injection** | Low | Will use parameterized queries in Phase 2+. Phase 1 uses migrations only (no user input). |
| **Type safety** | Low | Strict TypeScript + mypy --strict enforce type safety. No `any` types allowed. |
| **Config exposure** | Low | Config file is local. No secrets in Phase 1 (embedding API key deferred to Phase 2). |

✅ **No critical security gaps** — risks are documented and deferred appropriately

### Scalability Risks

| Risk | Severity | Impact | Mitigation |
|------|----------|--------|-----------|
| **Single SQLite database** | Medium | Will hit concurrency limits at ~100 concurrent queries. Acceptable for solo dev tool. | Document in Phase 2 if needed. PostgreSQL migration path exists. |
| **Full schema in memory** | Low | Python objects for all symbols could consume memory on very large repos (1M+ symbols). | Phase 4: Implement lazy loading + pagination. |
| **No query pagination** | Medium | Large result sets (e.g., 10k artifacts) will be slow. | Phase 2+: Add limit/offset to queries. |

✅ **Scalability acceptable for Phase 1** — solo developer tool, document for Phase 2+

### Extensibility Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **LanguageAdapter interface needs validation** | Low | ADR-005 documents plugin model. Future adapters implement abstract class. No changes needed to shared types/storage. |
| **Type system evolves** | Low | Types in shared/types/ are versioned. Migrations handle schema evolution. |
| **New modules in Pillars 2–5** | Medium | Each new pillar will create new modules (context-hub, arch-intelligence, etc.). Design allows parallel modules without coupling. |

✅ **Extensibility is strong** — plugin model supports future language adapters, pillar modules remain decoupled

### Data Integrity Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Concurrent writes to SQLite** | Low | Single CLI process only in Phase 1. Lock contention not a concern. Phase 2: API server handles concurrency (WAL mode enables readers). |
| **Schema migrations can corrupt data** | Low | Migrations are idempotent (IF NOT EXISTS). Rollback plan exists. Manual verification required. |
| **Foreign key violations** | Low | SQLite FK constraints enforced. BUILDER must respect FK relationships. |

✅ **Data integrity safeguards in place** — constraints + migrations + rollback plan

### Breaking Changes

| Change | Impact | Mitigation |
|--------|--------|-----------|
| **New types added to shared/types/** | High | Any phase 2+ code importing old types still works (forward-compatible). ADR documents type versioning strategy. |
| **SQLite schema changes** | High | Migrations handle evolution. Each new version in `002_*.sql`, `003_*.sql`, etc. |
| **CLI command changes** | Medium | Phase 1 is first CLI version. No breaking changes to existing commands. |

✅ **No backwards-incompatible changes in Phase 1** — foundation is being built for first time

---

## ADR References

### Existing ADRs (Apply to This Task)

| ADR | Title | Applicability |
|-----|-------|----------------|
| ADR-001 | ASES Multi-Agent Orchestration | ✅ **Applies** — task-001 is built under ASES governance; module boundaries support agent handoffs |
| ADR-002 | Bootstrap Protocol | ✅ **Applies** — task-001 uses Phase 0 bootstrap (no full ASES gates yet; planning phase under simple rules) |
| ADR-003 | Evidence Capture Terminal-Only | ✅ **Applies** — verification will use `tsc --noEmit`, `mypy --strict`, `eslint` outputs; no Claude assessment |

### New ADRs (Required for This Task)

Two new ADRs must be created and approved before BUILDER proceeds:

1. **ADR-004: Storage Strategy (SQLite + sqlite-vec, Local-First)**
2. **ADR-005: Language Adapter Plugin Model**

Both are written below.

---

## ADR-004: Storage Strategy (SQLite + sqlite-vec, Local-First)

```markdown
# ADR-004: Storage Strategy — SQLite + sqlite-vec, Local-First

Status: PROPOSED  
Date: 2026-06-30  
Author: ARCHITECT  
Approved by: [pending human approval]

## Context

Ortho must persist three types of data:
1. Repository metadata (files, symbols, dependencies)
2. Engineering artifacts (FRD, ADRs, specs, conversation history)
3. Embeddings for semantic search

The system must work offline (no cloud), require no authentication, and support local development.

## Problem Statement

What database backend should Ortho use?

- Option A: PostgreSQL (heavyweight, requires setup, cloud options available)
- Option B: SQLite + sqlite-vec (lightweight, no setup, purely local)
- Option C: Cloud firestore/dynamodb (requires credentials, network-dependent)

## Alternatives Considered

**Option A: PostgreSQL**
- Pros: Mature, supports full-text search (pg_trgm), vector search (pgvector), concurrent writes
- Cons: Requires server setup, external database to manage, not portable, not offline-first
- Rejected because: Contradicts FRD Principle 6 (local-first), adds operational burden

**Option C: Cloud (Firestore/DynamoDB)**
- Pros: Highly scalable, managed, supports complex queries
- Cons: Requires API credentials, network-dependent, not offline-capable, violates FRD "zero cloud"
- Rejected because: Directly contradicts FRD local-first + zero cloud requirements

**Option B (chosen): SQLite + sqlite-vec**
- Pros: Zero setup, purely local, single .db file, supports FTS5 (full-text), sqlite-vec (embeddings), offline-capable, portable
- Cons: Single-process concurrency, not suitable for multi-user server (acceptable for Phase 1 solo tool)
- Rationale: Matches FRD principles 6 (local-first), supports Phase 1 scope, clear upgrade path to PostgreSQL later

## Decision

Ortho stores all data in SQLite (`.ortho/ortho.db` for schema data, `.ortho/vectors.db` for embeddings):
- Metadata: SQLite with FTS5 for full-text search
- Embeddings: sqlite-vec extension for KNN similarity search
- Configuration: TOML file (`.ortho/config.toml`)
- Migrations: Versioned SQL files in `shared/storage/src/migrations/`

Local-first, zero cloud, no auth required.

## Rationale

1. **Aligns with FRD Principle 6:** "Local-first whenever practical" — SQLite is purely local
2. **Aligns with FRD Section 8:** "Storage: Local-first — SQLite + sqlite-vec"
3. **Phase 1 appropriate:** Solo developer, single process, no concurrency concerns
4. **Clear upgrade path:** If Phase 3+ needs PostgreSQL, migrate SQLite → PG (well-understood process)
5. **Developer experience:** Single `.ortho/` folder, no configuration, works offline
6. **Embedding support:** sqlite-vec provides embedding storage + KNN search without external service

## Consequences

Positive:
- Zero setup — `ortho init` creates everything locally
- Offline-capable — no network calls required for core functionality
- Portable — single project directory contains all state
- Debugging — direct SQL access to inspect data
- Phase 1 fast — no time spent on database operations

Negative:
- Concurrency limited — single-writer model (WAL mode helps, but multi-process writes not recommended)
- Query performance — optimization needed for large tables (1M+ rows in Phase 3+)
- Not suitable for multi-user server — Phase 3 Expense App may need separate DB

Neutral:
- Embedding dimension fixed at 1536 (Voyage embedding model)
- Schema migrations require manual version bumps

## Future Considerations

If Ortho scales to multi-user or team-based, migrate to PostgreSQL:
1. Export SQLite → CSV
2. Import CSV → PostgreSQL
3. Update connection string in config
4. Minimal code changes (use generic SQL, avoid SQLite-specific functions)

Phase 3: Evaluate if Expense App (team-facing) needs PostgreSQL. Ortho (solo tool) remains SQLite unless proven otherwise.

## Related Tasks
- task-001: Shared Foundation (this task — implements ADR-004)

## Related ADRs
- ADR-001: Multi-agent orchestration (independent of storage choice)
- ADR-003: Evidence capture (uses terminal tools, not DB queries)
```

---

## ADR-005: Language Adapter Plugin Model

```markdown
# ADR-005: Language Adapter Plugin Model — Extensible Source Code Analysis

Status: PROPOSED  
Date: 2026-06-30  
Author: ARCHITECT  
Approved by: [pending human approval]

## Context

Ortho's Pillar 1 (Repository Intelligence) must support multiple programming languages:
- Phase 1: Python
- Phase 2: TypeScript
- Phase 3+: Go, Java, Rust, etc.

The system needs a clean way to add language support without monolithic code.

## Problem Statement

How should Ortho support multiple languages?

- Option A: Single monolithic file with if-statements (language == "python" if language == "typescript")
- Option B: Abstract adapter interface + concrete implementations per language (plugin model)
- Option C: External language servers (LSP protocol — complex, overkill for Phase 1)

## Alternatives Considered

**Option A: Monolithic with if-statements**
- Pros: Simple for one language
- Cons: Unmaintainable at scale, hard to test per-language, violates FRD Principle 5 (small composable modules)
- Rejected because: Doesn't scale beyond 2–3 languages, couples unrelated logic

**Option C: LSP (Language Server Protocol)**
- Pros: Industry-standard, works for any LSP-compatible language
- Cons: Requires external processes, complex JSON-RPC setup, overkill for Phase 1
- Rejected because: Adds dependency and complexity; Phase 1 doesn't need it

**Option B (chosen): Abstract LanguageAdapter interface + concrete per-language classes**
- Pros: Clean separation, easy to add languages, testable per-language, FRD Principle 5 compliance
- Cons: Requires abstract class + implementation per language (more files)
- Rationale: Matches FRD vision, enables independent adapter development, supports skill delegation (future)

## Decision

Implement `LanguageAdapter` abstract base class in `packages/repo-intelligence/src/adapters/`:
- Abstract methods: `extract_symbols()`, `extract_imports()`, `extract_calls()`, `chunk()`
- Concrete implementations: `PythonAdapter`, `TypeScriptAdapter`, (later: `GoAdapter`, etc.)
- Registry: `AdapterRegistry` maps file extension → adapter instance
- Instantiation: BUILDER creates adapters at runtime, no hard-coded language list

Each adapter is independently testable and deployable.

## Rationale

1. **FRD Principle 5:** "Small composable modules" — each adapter is a module
2. **FRD Section 6:** Defines `LanguageAdapter` interface; ADR documents why
3. **Extensibility:** Adding Go support = write `GoAdapter`, register in AdapterRegistry, no core changes
4. **Testability:** Each adapter has dedicated test suite (fixtures per language)
5. **Decoupling:** Python adapter changes don't affect TypeScript adapter

## Consequences

Positive:
- Easy to add new languages (write adapter, no core changes)
- Independent testing per language
- Clear responsibility boundary (each adapter handles one language)
- Supports future "skill delegation" (hire Python expert, TypeScript expert, etc.)

Negative:
- More files/classes (one per language + base class)
- Must maintain compatibility across adapters (identical interface)
- No shared code between adapters (may duplicate logic for common patterns like AST traversal)

Neutral:
- Performance: same as monolithic (no overhead from abstraction)
- Complexity: manageable if interfaces stay stable

## Future Considerations

Phase 3+: If too many adapters accumulate (10+), consider grouping by family:
- Statically-typed family: Go, Java, Rust → share common AST patterns
- Dynamically-typed family: Python, JavaScript, Ruby → share common patterns

ADR would document this refactoring.

## Related Tasks
- task-001: Shared Foundation (defines adapter interface in types)
- task-003-repo-intelligence-python: Implements PythonAdapter

## Related ADRs
- ADR-001: Multi-agent orchestration (adapters may become specialist agent inputs later)
```

---

## Modules.md Update

The following entry should be added to `.ases/architecture/modules.md` under "Planned — Phase 2+" section:

```markdown
### 3. Ortho (Phase 1–4)

**Status:** Phase 1 in progress  
**Owner:** Solo developer (under ASES governance)  
**Location:** Root directory  
**Dependencies:** ASES (governance, workflows, templates)

**Purpose:** AI software engineering assistant — repository intelligence, context management, architectural analysis, workflow orchestration, token optimization.

**Submodules (Phase 1 Week 1–2):**
- `packages/repo-intelligence/` — Language adapters, symbol extraction, call graphs (Phase 1 Week 3–6)
- `packages/context-hub/` — Artifact store, hybrid search, project memory (Phase 1 Week 7–8)
- `packages/arch-intelligence/` — Architecture detection, impact analysis (Phase 2)
- `packages/orchestration/` — Intent routing, agent selection, workflow execution (Phase 3)
- `packages/token-optimizer/` — Context ranking, deduplication, compression (Phase 4)
- `shared/types/` — Canonical data models (Phase 1 Week 1–2)
- `shared/storage/` — SQLite + sqlite-vec layer (Phase 1 Week 1–2)
- `apps/cli/` — CLI interface (Phase 1 Week 1–2)
- `apps/api-server/` — FastAPI backend (Phase 1 Week 1–2)

**Stack:** Python (packages) + TypeScript (CLI, types)

**Development:** All Ortho features follow ASES workflow (feature.md).

**Key Contracts:**
- CLI → Storage API: `OrthoConfig.load()`, `OrthoDatabase.migrate()`
- Storage → Types: All types from `shared/types/`
- API Server → Storage: Same as CLI
```

---

## Verdict

### ✅ APPROVED — Architecture is Sound

**Approval Criteria Met:**

| Gate | Check | Result |
|-----|-------|--------|
| **Module Soundness** | Boundaries clear, responsibilities cohesive | ✅ PASS |
| **Dependency Health** | No cycles, one-way dependencies | ✅ PASS |
| **API Clarity** | Contracts defined (CLI→Storage→Types) | ✅ PASS |
| **Data Flow** | Validation at right layers (config, schema, business logic) | ✅ PASS |
| **Risk Assessment** | Security, scalability, extensibility reviewed | ✅ PASS |
| **ADR Completeness** | 2 new ADRs (004, 005) with all required fields | ✅ PASS |
| **Breaking Changes** | None — Phase 1 foundation, no prior code affected | ✅ PASS |

---

## Next Steps

### For Human Approval (GATE 2)

Review this architecture-review.md:
1. ✅ Module boundaries clear?
2. ✅ Dependencies acyclic?
3. ✅ API contracts defined?
4. ✅ ADR-004 + ADR-005 justified?
5. ✅ Risks documented?

**Decision Options:**
- ✅ **APPROVED** → Proceed to BUILDER (GATE 2 closed)
- ❌ **SEND BACK** → Specify issues, ARCHITECT revises
- ❌ **REJECTED** → Feature blocked, document reason

### For BUILDER (After Approval)

- Read: `spec.md`, `rollback-plan.md` (MANDATORY)
- Implement: 9 atomic tasks in order (monorepo → types/storage → schema → config → CLI/API/ADRs)
- Produce: Production code + `implementation-notes.md`
- Commit: Each atomic task with evidence reference

### For VERIFIER (After Scope Approval)

- Build: `tsc --noEmit`, `python -m py_compile`
- Type: `tsc --noEmit`, `mypy --strict`
- Lint: `eslint` (TypeScript code)
- Test: Manual verification (CLI runs, DB initializes)
- Regression: N/A (Phase 1 foundation, no prior code)

---

*End of architecture-review.md*
