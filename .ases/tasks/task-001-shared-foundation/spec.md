# Feature Specification

**Task ID:** task-001  
**Task Title:** Phase 1 Week 1–2 — Shared Foundation  
**Owner:** Solo Developer  
**Created:** 2026-06-30  
**Status:** DRAFT

---

## Objective

Establish monorepo structure, shared data types, SQLite database layer with migrations, configuration system, and CLI skeleton. Ortho will have working `ortho init` command that sets up `.ortho/` directory and initializes the database. All code passes type checking and linting. No AI features. Pure infrastructure.

---

## Files to Create or Modify

### Create

**Monorepo Structure:**
- `pyproject.toml` (root) — Poetry workspace with all packages
- `package.json` (root) — npm/pnpm shared configuration
- `packages/repo-intelligence/pyproject.toml` (empty skeleton)
- `packages/context-hub/pyproject.toml` (empty skeleton)
- `packages/arch-intelligence/pyproject.toml` (empty skeleton)
- `packages/orchestration/pyproject.toml` (empty skeleton)
- `packages/token-optimizer/pyproject.toml` (empty skeleton)
- `shared/types/package.json` (TypeScript)
- `shared/storage/pyproject.toml` (Python)
- `apps/cli/package.json` (TypeScript)
- `apps/api-server/pyproject.toml` (Python)

**Shared Types (TypeScript):**
- `shared/types/src/repository.ts` — Repository, File interfaces
- `shared/types/src/symbol.ts` — Symbol, CallEdge, ImportEdge interfaces
- `shared/types/src/artifact.ts` — Artifact, ArtifactType union
- `shared/types/src/architecture.ts` — ArchitectureModel, Layer, Subsystem
- `shared/types/src/workflow.ts` — WorkflowRun, ExecutionPlan, ExecutionStep, Evidence
- `shared/types/src/context.ts` — ContextChunk, TokenBudget, ContextPackage
- `shared/types/src/llm.ts` — LLMRequest, LLMResponse
- `shared/types/src/index.ts` — Re-export all
- `shared/types/tsconfig.json` — TypeScript config (strict mode)

**Storage Layer (Python):**
- `shared/storage/src/database.py` — OrthoDatabase class
- `shared/storage/src/vector_store.py` — VectorStore stub class
- `shared/storage/src/migrations/__init__.py`
- `shared/storage/src/migrations/001_initial_schema.sql` — Full schema from FRD Section 14
- `shared/storage/src/config.py` — OrthoConfig class
- `shared/storage/src/__init__.py`

**CLI (TypeScript):**
- `apps/cli/src/index.ts` — Commander CLI setup, main entry point
- `apps/cli/src/commands/init.ts` — `ortho init` command implementation
- `apps/cli/tsconfig.json` — TypeScript config (strict mode)
- `apps/cli/package.json` — Dependencies (commander, zod, typescript)

**API Server (Python):**
- `apps/api-server/src/main.py` — FastAPI app, health check endpoint
- `apps/api-server/pyproject.toml` — Dependencies (fastapi, uvicorn)

**ADRs:**
- `.ases/architecture/adrs/ADR-001-storage-strategy.md`
- `.ases/architecture/adrs/ADR-002-language-adapter-plugin-model.md`

---

## Files That Must NOT Be Touched

- FRD (ortho-v3-frd.md) — reference only, no changes
- `.ases/` workflows, templates, agents — these are infrastructure
- Existing project files (if any)
- GitHub (no pushes yet, local work only)

---

## Input/Output Contracts

### CLI → API → Storage Flow

**Input (CLI):**
```bash
ortho init
```

**Processing:**
1. CLI (init.ts) reads `.ortho/config.toml` template
2. CLI spawns API server process (if not running)
3. CLI makes POST request to API: `/api/init` (not yet implemented)
4. API (main.py) calls OrthoDatabase.migrate()
5. Database applies 001_initial_schema.sql
6. Returns success response

**Output (CLI):**
```
✓ Initialized .ortho/ directory
✓ Created config.toml
✓ Created ortho.db with schema
✓ API server listening on localhost:17234
✓ Ready for: ortho scan
```

**Output (File System):**
```
.ortho/
├── config.toml (from template)
├── ortho.db (SQLite, empty schema)
└── vectors.db (placeholder for Phase 2)
```

### Type Contract (Python ← → TypeScript)

All shared types must serialize/deserialize correctly between languages. Example:

```typescript
// TypeScript (shared/types/src/artifact.ts)
interface Artifact {
  id: string;
  repo_id: string;
  type: ArtifactType;
  title: string;
  content: string;
  // ... more fields
}
```

```python
# Python (can receive JSON from API)
artifact_json = {
  "id": "abc123",
  "repo_id": "repo1",
  "type": "frd",
  "title": "My FRD",
  "content": "...",
}
# Must deserialize correctly into Python dataclass
```

---

## Acceptance Criteria (Task Level)

**Infrastructure Acceptance Criteria (Binary, Testable):**

### Monorepo Structure
- [ ] Root `pyproject.toml` exists with `[tool.poetry.packages]` for all packages
- [ ] `poetry show` lists all packages without errors
- [ ] `poetry lock` creates lock file without errors
- [ ] Root `package.json` exists with dependencies: commander, zod, typescript
- [ ] `npm install` (or pnpm) succeeds
- [ ] All package folders exist: `packages/`, `shared/`, `apps/`

### Shared Types
- [ ] All 7 type files exist (repository.ts, symbol.ts, artifact.ts, architecture.ts, workflow.ts, context.ts, llm.ts)
- [ ] `shared/types/src/index.ts` exports all types
- [ ] `tsc --noEmit` in shared/types/ returns exit 0
- [ ] No `any` types in any file
- [ ] All interfaces match FRD Section 5 exactly (line-by-line comparison)

### Storage Layer
- [ ] `shared/storage/src/database.py` exists with OrthoDatabase class
- [ ] `OrthoDatabase.__init__(project_root: Path)` takes project root path
- [ ] `OrthoDatabase.migrate()` method exists
- [ ] `OrthoDatabase.connection()` method exists and returns sqlite3.Connection
- [ ] `shared/storage/src/vector_store.py` exists with VectorStore class stub
- [ ] All methods have type hints (mypy --strict compliance)
- [ ] `python -m py_compile shared/storage/src/database.py` returns exit 0

### SQLite Schema
- [ ] `001_initial_schema.sql` exists with all tables from FRD Section 14
- [ ] Tables: repositories, files, symbols, call_edges, import_edges, artifacts, project_memory, architecture_models, workflow_runs, agent_manifests, skill_manifests
- [ ] All primary keys, foreign keys, unique constraints, indexes present
- [ ] FTS5 virtual table `artifacts_fts` created
- [ ] SQL syntax valid (can be parsed by SQLite: `sqlite3 :memory: < 001_initial_schema.sql`)
- [ ] Migration can be applied idempotently (IF NOT EXISTS clauses)

### OrthoConfig
- [ ] `.ortho/config.toml` template created
- [ ] Sections: [project], [indexing], [context_hub], [llm], [orchestration], [token_optimizer]
- [ ] All values from FRD Section 5 present
- [ ] `shared/storage/src/config.py` exists with OrthoConfig class
- [ ] `OrthoConfig.load(path: Path)` reads and parses config.toml
- [ ] `OrthoConfig.validate()` checks all required fields, raises error on invalid
- [ ] Type hints present (mypy --strict compliance)

### CLI Skeleton
- [ ] `apps/cli/src/index.ts` exists and sets up commander CLI
- [ ] `apps/cli/src/commands/init.ts` exists with `ortho init` command
- [ ] `ortho init` is callable: `node dist/cli/src/index.js init`
- [ ] After `ortho init`, `.ortho/` directory exists
- [ ] After `ortho init`, `.ortho/config.toml` exists
- [ ] After `ortho init`, `.ortho/ortho.db` exists
- [ ] `tsc --noEmit` in apps/cli/ returns exit 0
- [ ] `eslint apps/cli/src/` returns exit 0
- [ ] No `any` types in CLI code

### FastAPI Server
- [ ] `apps/api-server/src/main.py` exists with FastAPI app
- [ ] `GET /health` endpoint returns 200: `{"status": "ok"}`
- [ ] Server starts: `python -m uvicorn apps.api-server.src.main:app --host 127.0.0.1 --port 17234`
- [ ] Server listens on `http://localhost:17234`
- [ ] `python -m py_compile apps/api-server/src/main.py` returns exit 0
- [ ] Type hints present (mypy --strict compliance)

### ADRs
- [ ] `ADR-001-storage-strategy.md` exists
- [ ] Sections present: Status, Context, Decision, Consequences, Evidence
- [ ] Decision explains SQLite + sqlite-vec choice
- [ ] `ADR-002-language-adapter-plugin-model.md` exists
- [ ] Explains LanguageAdapter interface and extensibility

### Type Checking & Linting (No Errors)
- [ ] `tsc --noEmit` (root) returns exit 0 for all TypeScript code
- [ ] `eslint .` (root, if configured) returns exit 0 for CLI code
- [ ] `mypy --strict` (root) returns exit 0 for all Python code
- [ ] No type errors, no lint warnings

---

## Dependencies on Other Tasks

None. This is Phase 1 Week 1–2, the foundation.

---

## Required Evidence to Consider Complete

### Build/Compilation
```bash
# TypeScript compilation
tsc --noEmit shared/types/src/*.ts
tsc --noEmit apps/cli/src/*.ts

# Python module compilation
python -m py_compile shared/storage/src/database.py
python -m py_compile apps/api-server/src/main.py
```

**Expected:** All commands return exit 0

### Type Checking
```bash
# Full TypeScript type check
tsc --noEmit

# Python type check
mypy --strict shared/storage/
mypy --strict apps/api-server/
```

**Expected:** All commands return exit 0, no type errors

### Linting
```bash
# TypeScript linting (if ESLint configured)
eslint apps/cli/src/
eslint shared/types/src/
```

**Expected:** Exit 0, no lint warnings

### Manual Verification
```bash
# Monorepo structure
ls -la packages/ shared/ apps/
poetry show
npm list

# Schema validation
sqlite3 :memory: < shared/storage/src/migrations/001_initial_schema.sql

# CLI startup
node dist/cli/src/index.js init

# API server health check
python -m uvicorn apps.api-server.src.main:app &
sleep 2
curl http://localhost:17234/health
```

**Expected:** All commands succeed, .ortho/ created, API responds

---

## Change Impact

### Affected Modules
- New: `shared/types`, `shared/storage`, `apps/cli`, `apps/api-server`
- Monorepo structure: new package layout

### Affected APIs
- New API: `GET /health` (internal, for CLI)
- New CLI: `ortho init`

### Regression Candidates
None (Phase 1 Week 1–2 is foundation, no prior code affected)

---

## Non-Functional Requirements

- **Build time:** `poetry lock` and `npm install` should complete in <2 minutes
- **CLI startup:** `ortho init` should complete in <5 seconds
- **Database:** SQLite should initialize with schema in <1 second
- **Type checking:** `tsc --noEmit` should complete in <10 seconds
- **Type safety:** 100% type coverage (mypy --strict, tsc strict mode)
- **Scalability:** No concern in Phase 1 (infrastructure only)

---

## Notes for BUILDER

**Precision is critical—this is infrastructure.**

### TypeScript Types
- Copy types directly from FRD Section 5
- Use interface declarations (not types) for extensibility
- All properties must be typed (no implicit any)
- Use union types for enums (e.g., `type ArtifactType = "frd" | "adr" | ...`)
- Document with JSDoc for public interfaces

### Python Storage
- Use dataclasses for config (immutable after init)
- Use type hints on all functions (mypy --strict)
- Use context managers for database connections (with statement)
- Handle migrations idempotently (IF NOT EXISTS in SQL)
- Log migration execution

### CLI Design
- Use commander.js for CLI parsing
- Keep CLI thin—all logic in API/storage
- Error messages should be user-friendly
- Exit codes: 0 for success, 1 for error

### API Server
- FastAPI with async/await
- Keep Phase 1 minimal (just `/health` and eventually `/api/init`)
- Full error handling (try/except all database calls)
- Logging on all operations
- CORS not needed yet (local use only)

---

*End of spec.md*
