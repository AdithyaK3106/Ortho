# Feature Plan

**Task ID:** task-001  
**Feature Name:** Phase 1 Week 1–2 — Shared Foundation  
**Owner:** Solo Developer  
**Created:** 2026-06-30  
**Last Updated:** 2026-06-30

---

## Feature Summary

Establish the foundational infrastructure for Ortho: monorepo structure (Poetry workspaces), shared data types (TypeScript + Python), SQLite database layer with migrations, `.ortho/` directory structure, configuration system, and CLI skeleton. This enables all subsequent Ortho development. No AI features yet—pure infrastructure.

---

## Atomic Task Breakdown

### Task 1: Monorepo Structure + Poetry Setup
- **Scope:** Root `pyproject.toml`, `package.json`, Poetry workspace configuration, folder structure for packages, shared, and apps. No code yet.
- **Duration:** 45-60 minutes
- **Dependencies:** None
- **Acceptance Criteria:**
  - [ ] Root `pyproject.toml` created with Poetry workspace members (`packages/repo-intelligence`, `packages/context-hub`, `packages/arch-intelligence`, `packages/orchestration`, `packages/token-optimizer`, `shared/storage`, `apps/cli`, `apps/api-server`)
  - [ ] All package folders exist with empty `pyproject.toml` files
  - [ ] Root `package.json` created with shared TypeScript dependencies (commander, zod, typescript)
  - [ ] All packages can be listed: `poetry show`
  - [ ] No Python syntax errors in any `pyproject.toml`
  - [ ] Shared workspace builds without errors: `poetry lock` succeeds

### Task 2: Shared Types (TypeScript)
- **Scope:** `shared/types/src/` directory with canonical data models. Implementation of Repository, File, Symbol, Artifact, Architecture, Workflow, Context, LLM types from FRD Section 5.
- **Duration:** 75-90 minutes
- **Dependencies:** Task 1 (monorepo structure)
- **Acceptance Criteria:**
  - [ ] `shared/types/src/repository.ts` — Repository, File types with all fields from FRD
  - [ ] `shared/types/src/symbol.ts` — Symbol, CallEdge, ImportEdge types
  - [ ] `shared/types/src/artifact.ts` — Artifact type with all ArtifactType variants
  - [ ] `shared/types/src/architecture.ts` — ArchitectureModel, Layer, Subsystem types
  - [ ] `shared/types/src/workflow.ts` — WorkflowRun, ExecutionPlan, ExecutionStep, Evidence types
  - [ ] `shared/types/src/context.ts` — ContextChunk, TokenBudget, ContextPackage types
  - [ ] `shared/types/src/llm.ts` — LLMRequest, LLMResponse types
  - [ ] `shared/types/src/index.ts` — Re-exports all types
  - [ ] TypeScript compiles without errors: `tsc --noEmit`
  - [ ] All types are strict (no `any` types)
  - [ ] All types match FRD Section 5 exactly

### Task 3: SQLite Storage Layer (Python)
- **Scope:** `shared/storage/src/database.py` and `shared/storage/src/vector_store.py` with migration infrastructure. Implementation of OrthoDatabase, VectorStore classes from FRD Section 5.
- **Duration:** 75-90 minutes
- **Dependencies:** Task 1 (monorepo structure)
- **Acceptance Criteria:**
  - [ ] `shared/storage/src/database.py` — OrthoDatabase class with init, migrate(), connection() methods
  - [ ] `shared/storage/src/vector_store.py` — VectorStore class with upsert(), search(), delete() stubs
  - [ ] `shared/storage/src/migrations/` directory structure created
  - [ ] Migration runner implemented (apply migrations in order)
  - [ ] All type hints present (mypy compliance)
  - [ ] No syntax errors: `python -m py_compile shared/storage/src/database.py`
  - [ ] Schema from FRD Section 14 ready (not yet applied, just ready)

### Task 4: SQLite Schema + Migrations
- **Scope:** Create first migration file (001_initial_schema.sql) with all tables from FRD Section 14. Schema for repositories, files, symbols, call_edges, import_edges, artifacts, workflow_runs, etc.
- **Duration:** 60-75 minutes
- **Dependencies:** Task 3 (storage layer structure)
- **Acceptance Criteria:**
  - [ ] `shared/storage/src/migrations/001_initial_schema.sql` created
  - [ ] All tables from FRD Section 14 present (repositories, files, symbols, call_edges, import_edges, artifacts, project_memory, architecture_models, workflow_runs, agent_manifests, skill_manifests)
  - [ ] All primary keys, foreign keys, unique constraints, indexes present
  - [ ] FTS5 virtual table for artifacts_fts created
  - [ ] SQL syntax valid (can be parsed by SQLite)
  - [ ] Down-migration prepared (rollback procedure exists)

### Task 5: OrthoConfig + .ortho/ Directory
- **Scope:** Create `.ortho/config.toml` structure, config loading/saving in Python, directory initialization.
- **Duration:** 45-60 minutes
- **Dependencies:** Task 4 (schema created)
- **Acceptance Criteria:**
  - [ ] `.ortho/config.toml` template created with all sections from FRD (project, indexing, context_hub, llm, orchestration, token_optimizer)
  - [ ] Python class OrthoConfig created to load/save/validate config
  - [ ] `.ortho/` directory structure can be initialized: `.ortho/`, `.ortho/ortho.db`, `.ortho/vectors.db`, `.ortho/config.toml`
  - [ ] Config defaults sensible (model: claude-sonnet-4-6, budget: 16000)
  - [ ] No validation errors on default config
  - [ ] Type hints present (mypy compliance)

### Task 6: CLI Skeleton + `ortho init`
- **Scope:** TypeScript CLI with commander.js. Implement `ortho init` command that creates `.ortho/` structure, initializes database, starts API server.
- **Duration:** 75-90 minutes
- **Dependencies:** Tasks 1, 5 (monorepo + config)
- **Acceptance Criteria:**
  - [ ] `apps/cli/src/index.ts` created with commander CLI setup
  - [ ] `apps/cli/src/commands/init.ts` — `ortho init` command implemented
  - [ ] Running `ortho init` creates `.ortho/` folder, config.toml, database files
  - [ ] TypeScript compiles: `tsc --noEmit apps/cli/src/`
  - [ ] ESLint passes: `eslint apps/cli/src/`
  - [ ] No `any` types in CLI code

### Task 7: FastAPI Server Skeleton (Python)
- **Scope:** `apps/api-server/src/main.py` with FastAPI setup, basic health check endpoint, integration with storage layer.
- **Duration:** 45-60 minutes
- **Dependencies:** Task 3 (storage layer)
- **Acceptance Criteria:**
  - [ ] `apps/api-server/src/main.py` created with FastAPI app
  - [ ] `GET /health` endpoint returns 200 with {"status": "ok"}
  - [ ] Server listens on localhost:17234 (configurable)
  - [ ] No syntax errors: `python -m py_compile apps/api-server/src/main.py`
  - [ ] Can be started: `python -m uvicorn apps.api-server.src.main:app`
  - [ ] Type hints present (mypy compliance)

### Task 8: ADR-001 Storage Strategy
- **Scope:** Write ADR-001 documenting storage design decisions (SQLite + sqlite-vec, no cloud, local-first).
- **Duration:** 30-45 minutes
- **Dependencies:** Tasks 3, 4 (storage implemented)
- **Acceptance Criteria:**
  - [ ] `.ases/architecture/adrs/ADR-001-storage-strategy.md` created
  - [ ] Sections: Status, Context, Decision, Consequences, Evidence
  - [ ] Explains why SQLite + sqlite-vec over PostgreSQL/cloud
  - [ ] Addresses performance, scalability, offline-first requirements
  - [ ] Decision is justified with evidence from FRD

### Task 9: ADR-002 Language Adapter Plugin Model
- **Scope:** Write ADR-002 documenting LanguageAdapter interface design and plugin architecture.
- **Duration:** 30-45 minutes
- **Dependencies:** Task 2 (types defined)
- **Acceptance Criteria:**
  - [ ] `.ases/architecture/adrs/ADR-002-language-adapter-plugin-model.md` created
  - [ ] Explains abstract LanguageAdapter class, why plugin model, interface contract
  - [ ] Shows how Python/TypeScript/Go adapters will implement it
  - [ ] Addresses extensibility, isolation, testing

---

## Task Dependency Order

```
Task 1 (Monorepo + Poetry)
    ↓
Task 2 (Shared Types)  [parallel: Task 3]
Task 3 (Storage Layer)  [parallel: Task 2]
    ↓
Task 4 (Schema + Migrations)
    ↓
Task 5 (OrthoConfig + .ortho/)
    ↓
Task 6 (CLI Skeleton) [parallel: Task 7, Task 8, Task 9]
Task 7 (FastAPI Server)
Task 8 (ADR-001)
Task 9 (ADR-002)
```

---

## Risk Identification

- **Risk 1: Dependency Hell** — If Poetry or npm version constraints are wrong, workspaces won't build. **Impact:** Cannot proceed to Week 3. **Mitigation:** Use latest stable versions, test workspace builds before proceeding.

- **Risk 2: Schema Design Wrong** — If FRD Section 14 is misinterpreted, entire storage layer breaks. **Impact:** Everything downstream fails. **Mitigation:** ARCHITECT reviews schema line-by-line against FRD. Create rollback migration.

- **Risk 3: Type System Incompatibility** — If TypeScript and Python types don't align (union types vs discriminated types), serialization breaks. **Impact:** Context exchange between components fails. **Mitigation:** TEST-DESIGNER writes serialization tests.

- **Risk 4: CLI/API Contract Missing** — If CLI and API server don't agree on request/response format, CLI calls fail. **Impact:** `ortho` command doesn't work. **Mitigation:** REVIEWER checks CLI → API → storage flow end-to-end.

---

## Feature-Level Acceptance Criteria

This feature is "done" when ALL these are true:

- [ ] All 9 atomic tasks completed and verified
- [ ] Monorepo structure matches FRD Section 4 exactly
- [ ] All shared types defined (no placeholders, no `any`)
- [ ] SQLite schema includes all tables from FRD Section 14
- [ ] Migrations apply without errors
- [ ] OrthoConfig loads default config without validation errors
- [ ] `ortho init` creates `.ortho/` structure correctly
- [ ] FastAPI server starts and responds to /health
- [ ] ADRs are written and justified
- [ ] No new type errors introduced (tsc + mypy pass)
- [ ] No new linting errors (eslint passes)
- [ ] Code review approved
- [ ] All evidence files exist

---

## Notes for ARCHITECT

**CRITICAL: This is infrastructure, not just boilerplate. Architecture review is MANDATORY.**

- New module: All of `shared/` (types, storage, utils)
- New database: SQLite with FTS5 + sqlite-vec
- New API: FastAPI server at localhost:17234
- New CLI: TypeScript command-line interface
- Security: Local database only, no network calls in Phase 1
- Storage: Local-first, no cloud backends
- Type System: Strict TypeScript, full Python type hints (mypy)

**Questions ARCHITECT must answer:**
1. Does the schema in 001_initial_schema.sql match FRD Section 14 exactly?
2. Are LanguageAdapter plugin boundaries clear (Repo Intelligence will implement)?
3. Is CLI → API → Storage data flow correct?
4. Are there any circular dependencies between packages?
5. Is the config structure extensible for Phase 2–4?

---

## Notes for BUILDER

**Infrastructure-level work — precision is critical.**

- Use Poetry for Python, npm/pnpm for TypeScript
- Copy types directly from FRD Section 5 (don't invent)
- SQL schema must match FRD Section 14 (line-by-line)
- All Python code must pass `mypy --strict`
- All TypeScript code must use `strict: true` in tsconfig
- No `any` types anywhere
- Config structure must match FRD exactly
- `ortho init` must be idempotent (safe to run twice)
- FastAPI server must start cleanly: `uvicorn apps.api-server.src.main:app --host 127.0.0.1 --port 17234`

---

*End of plan.md*
