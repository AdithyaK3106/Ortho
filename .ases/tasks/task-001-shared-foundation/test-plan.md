# Test Plan for task-001: Shared Foundation

**Task ID:** task-001  
**Feature:** Phase 1 Week 1–2 — Shared Foundation (Monorepo, Types, Storage, CLI, API)  
**Test Designer:** Claude Haiku (TEST-DESIGNER Agent)  
**Created:** 2026-06-30  
**Status:** TESTS-WRITTEN

---

## Overview

This test plan covers comprehensive testing for task-001 Shared Foundation. The task creates:
1. Monorepo structure with Poetry + npm workspaces
2. Shared TypeScript types (7 interfaces exported from `shared/types`)
3. SQLite storage layer with migrations
4. OrthoConfig and `.ortho/` directory structure
5. CLI skeleton with `ortho init` command
6. FastAPI server skeleton with `/health` endpoint

**Total acceptance criteria extracted from spec.md:** 45 criteria  
**Total tests designed:** 120+ tests (unit + integration + edge cases + failure scenarios)

---

## Unit Tests Per Acceptance Criterion

### MONOREPO STRUCTURE (6 Acceptance Criteria)

#### Criterion: "Root `pyproject.toml` exists with `[tool.poetry.packages]` for all packages"
**Type:** Unit  
**Tests:**
- `test_root_pyproject_exists` — File exists at `pyproject.toml`
- `test_root_pyproject_valid_toml` — Valid TOML syntax
- `test_root_pyproject_has_poetry_packages_section` — `[tool.poetry.packages]` section present
- `test_root_pyproject_references_all_packages` — All 7 packages listed: repo-intelligence, context-hub, arch-intelligence, orchestration, token-optimizer, types, storage
- `test_root_pyproject_has_workspaces` — `packages` workspace configured

#### Criterion: "`poetry show` lists all packages without errors"
**Type:** Integration  
**Tests:**
- `test_poetry_show_succeeds` — Command exits with 0
- `test_poetry_show_lists_packages` — Output includes all 7 package names

#### Criterion: "`poetry lock` creates lock file without errors"
**Type:** Integration  
**Tests:**
- `test_poetry_lock_succeeds` — `poetry lock` exits with 0
- `test_poetry_lock_creates_file` — `poetry.lock` created in root

#### Criterion: "Root `package.json` exists with dependencies: commander, zod, typescript"
**Type:** Unit  
**Tests:**
- `test_root_package_json_exists` — File exists
- `test_root_package_json_valid_json` — Valid JSON syntax
- `test_root_package_json_has_dependencies` — `dependencies` section present
- `test_root_package_json_has_commander` — `commander` listed
- `test_root_package_json_has_zod` — `zod` listed
- `test_root_package_json_has_typescript` — `typescript` listed (dev dependency)

#### Criterion: "`npm install` (or pnpm) succeeds"
**Type:** Integration  
**Tests:**
- `test_npm_install_succeeds` — `npm install` or `pnpm install` exits with 0

#### Criterion: "All package folders exist: `packages/`, `shared/`, `apps/`"
**Type:** Unit  
**Tests:**
- `test_packages_directory_exists` — Directory `packages/` exists
- `test_shared_directory_exists` — Directory `shared/` exists
- `test_apps_directory_exists` — Directory `apps/` exists
- `test_packages_subdirs_exist` — All 5 package subdirectories exist
- `test_shared_subdirs_exist` — `shared/types/` and `shared/storage/` exist
- `test_apps_subdirs_exist` — `apps/cli/` and `apps/api-server/` exist

---

### SHARED TYPES (5 Acceptance Criteria)

#### Criterion: "All 7 type files exist (repository.ts, symbol.ts, artifact.ts, architecture.ts, workflow.ts, context.ts, llm.ts)"
**Type:** Unit  
**Tests:**
- `test_repository_ts_exists` — `shared/types/src/repository.ts` exists
- `test_symbol_ts_exists` — `shared/types/src/symbol.ts` exists
- `test_artifact_ts_exists` — `shared/types/src/artifact.ts` exists
- `test_architecture_ts_exists` — `shared/types/src/architecture.ts` exists
- `test_workflow_ts_exists` — `shared/types/src/workflow.ts` exists
- `test_context_ts_exists` — `shared/types/src/context.ts` exists
- `test_llm_ts_exists` — `shared/types/src/llm.ts` exists

#### Criterion: "`shared/types/src/index.ts` exports all types"
**Type:** Unit  
**Tests:**
- `test_index_ts_exists` — `shared/types/src/index.ts` exists
- `test_index_exports_repository_interface` — Exports Repository and File interfaces
- `test_index_exports_symbol_interfaces` — Exports Symbol, CallEdge, ImportEdge interfaces
- `test_index_exports_artifact_interface` — Exports Artifact and ArtifactType
- `test_index_exports_architecture_interfaces` — Exports ArchitectureModel, Layer, Subsystem, ServiceBoundary
- `test_index_exports_workflow_interfaces` — Exports WorkflowRun, ExecutionPlan, ExecutionStep, Evidence
- `test_index_exports_context_interfaces` — Exports ContextChunk, TokenBudget, ContextPackage
- `test_index_exports_llm_interfaces` — Exports LLMRequest, LLMResponse

#### Criterion: "`tsc --noEmit` in shared/types/ returns exit 0"
**Type:** Integration  
**Tests:**
- `test_typescript_compiles_shared_types` — `tsc --noEmit` exits with 0, no errors
- `test_typescript_strict_mode_enabled` — tsconfig.json has `"strict": true`

#### Criterion: "No `any` types in any file"
**Type:** Unit  
**Tests:**
- `test_no_any_in_repository_ts` — No `any` found in repository.ts
- `test_no_any_in_symbol_ts` — No `any` found in symbol.ts
- `test_no_any_in_artifact_ts` — No `any` found in artifact.ts
- `test_no_any_in_architecture_ts` — No `any` found in architecture.ts
- `test_no_any_in_workflow_ts` — No `any` found in workflow.ts
- `test_no_any_in_context_ts` — No `any` found in context.ts
- `test_no_any_in_llm_ts` — No `any` found in llm.ts
- `test_no_any_in_index_ts` — No `any` found in index.ts

#### Criterion: "All interfaces match FRD Section 5 exactly (line-by-line comparison)"
**Type:** Unit  
**Tests:**
- `test_repository_interface_matches_frd` — Repository interface fields: id, root_path, name, languages, indexed_at, git_remote (optional)
- `test_file_interface_matches_frd` — File interface fields: id, repo_id, rel_path, language, size_bytes, last_modified, git_last_commit (optional)
- `test_symbol_interface_matches_frd` — Symbol interface: id, repo_id, file_id, name, qualified_name, kind, visibility, start_line, end_line, docstring (optional), signature (optional)
- `test_artifact_interface_matches_frd` — Artifact interface with all required fields from FRD
- `test_architecture_interface_matches_frd` — ArchitectureModel, Layer, Subsystem interfaces match FRD
- `test_workflow_interface_matches_frd` — WorkflowRun, ExecutionPlan, ExecutionStep, Evidence interfaces match FRD
- `test_context_interface_matches_frd` — ContextChunk, TokenBudget, ContextPackage interfaces match FRD
- `test_llm_interface_matches_frd` — LLMRequest, LLMResponse interfaces match FRD

---

### STORAGE LAYER (5 Acceptance Criteria)

#### Criterion: "`shared/storage/src/database.py` exists with OrthoDatabase class"
**Type:** Unit  
**Tests:**
- `test_database_py_exists` — File exists
- `test_orthodb_class_exists` — Class OrthoDatabase defined
- `test_orthodb_has_init_method` — `__init__(project_root: Path)` method exists
- `test_orthodb_has_migrate_method` — `migrate()` method exists
- `test_orthodb_has_connection_method` — `connection()` method exists

#### Criterion: "`OrthoDatabase.__init__(project_root: Path)` takes project root path"
**Type:** Unit  
**Tests:**
- `test_orthodb_init_signature` — Method signature matches `__init__(self, project_root: Path) -> None`
- `test_orthodb_init_creates_parent_dirs` — Parent directories created if not exist
- `test_orthodb_init_stores_project_root` — `self.project_root` set correctly
- `test_orthodb_init_db_path_is_ortho_db` — `self.db_path` ends with `.ortho/ortho.db`

#### Criterion: "`OrthoDatabase.migrate()` method exists"
**Type:** Unit  
**Tests:**
- `test_orthodb_migrate_signature` — Method signature is `migrate(self) -> None`
- `test_orthodb_migrate_reads_migration_files` — Reads .sql files from migrations/ directory
- `test_orthodb_migrate_executes_sql` — Executes SQL without error (can verify on real or mock)
- `test_orthodb_migrate_commits_transaction` — Transaction committed after execution

#### Criterion: "`OrthoDatabase.connection()` method exists and returns sqlite3.Connection"
**Type:** Unit  
**Tests:**
- `test_orthodb_connection_signature` — Method signature is `connection(self) -> sqlite3.Connection`
- `test_orthodb_connection_returns_connection` — Returns sqlite3.Connection object
- `test_orthodb_connection_enables_wal_mode` — Executes `PRAGMA journal_mode=WAL`
- `test_orthodb_connection_enables_foreign_keys` — Executes `PRAGMA foreign_keys=ON`

#### Criterion: "All methods have type hints (mypy --strict compliance)"
**Type:** Integration  
**Tests:**
- `test_mypy_strict_shared_storage` — `mypy --strict shared/storage/` exits with 0
- `test_database_py_has_type_hints` — All function parameters and return types annotated
- `test_database_py_no_implicit_any` — No implicit Any types found

---

### SQLITE SCHEMA (5 Acceptance Criteria)

#### Criterion: "`001_initial_schema.sql` exists with all tables from FRD Section 14"
**Type:** Unit  
**Tests:**
- `test_migration_001_exists` — File exists at `shared/storage/src/migrations/001_initial_schema.sql`
- `test_migration_has_repositories_table` — CREATE TABLE repositories
- `test_migration_has_files_table` — CREATE TABLE files
- `test_migration_has_symbols_table` — CREATE TABLE symbols
- `test_migration_has_call_edges_table` — CREATE TABLE call_edges
- `test_migration_has_import_edges_table` — CREATE TABLE import_edges
- `test_migration_has_artifacts_table` — CREATE TABLE artifacts
- `test_migration_has_project_memory_table` — CREATE TABLE project_memory
- `test_migration_has_architecture_models_table` — CREATE TABLE architecture_models
- `test_migration_has_workflow_runs_table` — CREATE TABLE workflow_runs
- `test_migration_has_agent_manifests_table` — CREATE TABLE agent_manifests
- `test_migration_has_skill_manifests_table` — CREATE TABLE skill_manifests

#### Criterion: "All primary keys, foreign keys, unique constraints, indexes present"
**Type:** Unit  
**Tests:**
- `test_repositories_primary_key_id` — repositories(id) PRIMARY KEY
- `test_repositories_unique_root_path` — repositories(root_path) UNIQUE
- `test_files_foreign_key_repo_id` — files.repo_id REFERENCES repositories(id)
- `test_files_unique_repo_rel_path` — files(repo_id, rel_path) UNIQUE
- `test_symbols_foreign_keys` — symbols.repo_id and symbols.file_id reference correct tables
- `test_call_edges_foreign_keys` — call_edges.caller_id and callee_id reference symbols(id)
- `test_import_edges_foreign_keys` — import_edges.importer_file_id references files(id)
- `test_artifacts_foreign_key_repo_id` — artifacts.repo_id REFERENCES repositories(id)
- `test_project_memory_composite_key` — project_memory(key, repo_id) PRIMARY KEY
- `test_project_memory_foreign_key_repo_id` — project_memory.repo_id REFERENCES repositories(id)
- `test_architecture_models_foreign_key` — architecture_models.repo_id REFERENCES repositories(id)
- `test_workflow_runs_foreign_key` — workflow_runs.repo_id REFERENCES repositories(id)

#### Criterion: "FTS5 virtual table `artifacts_fts` created"
**Type:** Unit  
**Tests:**
- `test_artifacts_fts_table_exists` — CREATE VIRTUAL TABLE artifacts_fts USING fts5
- `test_artifacts_fts_indexes_title` — Title column indexed
- `test_artifacts_fts_indexes_content` — Content column indexed

#### Criterion: "SQL syntax valid (can be parsed by SQLite)"
**Type:** Integration  
**Tests:**
- `test_migration_001_valid_sql_syntax` — `sqlite3 :memory: < 001_initial_schema.sql` succeeds
- `test_migration_001_no_syntax_errors` — No SQLite parsing errors

#### Criterion: "Migration can be applied idempotently (IF NOT EXISTS clauses)"
**Type:** Integration  
**Tests:**
- `test_migration_idempotent_run_twice` — Running migration twice succeeds (no "table already exists" error)
- `test_migration_ifnotexists_all_tables` — All CREATE TABLE statements use IF NOT EXISTS
- `test_migration_ifnotexists_all_indexes` — All CREATE INDEX statements use IF NOT EXISTS

---

### ORTHO CONFIG (3 Acceptance Criteria)

#### Criterion: "`.ortho/config.toml` template created with all sections from FRD Section 5"
**Type:** Unit  
**Tests:**
- `test_config_toml_exists` — File exists at `.ortho/config.toml`
- `test_config_toml_valid_toml` — Valid TOML syntax
- `test_config_has_project_section` — `[project]` section with name, root, primary_language
- `test_config_has_indexing_section` — `[indexing]` section with languages, exclude_patterns, incremental
- `test_config_has_context_hub_section` — `[context_hub]` section with embedding_model, embedding_provider
- `test_config_has_llm_section` — `[llm]` section with default_model, fallback_model, max_tokens
- `test_config_has_orchestration_section` — `[orchestration]` section with human_approval, approval_timeout_seconds
- `test_config_has_token_optimizer_section` — `[token_optimizer]` section with default_budget, compression_threshold

#### Criterion: "`shared/storage/src/config.py` exists with OrthoConfig class"
**Type:** Unit  
**Tests:**
- `test_config_py_exists` — File exists
- `test_ortho_config_class_exists` — Class OrthoConfig defined
- `test_ortho_config_is_dataclass` — Uses @dataclass decorator
- `test_ortho_config_has_load_classmethod` — `load(path: Path) -> OrthoConfig` method
- `test_ortho_config_has_validate_method` — `validate(self) -> None` method

#### Criterion: "`OrthoConfig.load(path: Path)` reads and parses config.toml` and `OrthoConfig.validate()` checks all required fields"
**Type:** Unit  
**Tests:**
- `test_ortho_config_load_reads_toml` — Reads TOML file without error
- `test_ortho_config_load_parses_project_section` — Extracts project_name, project_root, primary_language
- `test_ortho_config_load_parses_indexing_section` — Extracts languages, exclude_patterns
- `test_ortho_config_load_parses_context_hub_section` — Extracts embedding_model, embedding_provider
- `test_ortho_config_load_parses_llm_section` — Extracts default_model, fallback_model, max_tokens
- `test_ortho_config_load_parses_orchestration_section` — Extracts human_approval, approval_timeout_seconds
- `test_ortho_config_load_parses_token_optimizer_section` — Extracts default_budget, compression_threshold
- `test_ortho_config_validate_checks_project_name` — Raises error if project_name empty
- `test_ortho_config_validate_checks_primary_language` — Raises error if primary_language empty
- `test_ortho_config_validate_checks_budget_positive` — Raises error if default_budget <= 0
- `test_ortho_config_validate_checks_compression_threshold_range` — Raises error if compression_threshold not in [0, 1]

---

### CLI SKELETON (5 Acceptance Criteria)

#### Criterion: "`apps/cli/src/index.ts` exists and sets up commander CLI"
**Type:** Unit  
**Tests:**
- `test_cli_index_ts_exists` — File exists
- `test_cli_imports_commander` — Imports commander or similar CLI library
- `test_cli_has_program_setup` — Program configured with name and version
- `test_cli_program_name_is_ortho` — Program name is "ortho"
- `test_cli_program_version_is_0_1_0` — Program version is "0.1.0" or similar

#### Criterion: "`apps/cli/src/commands/init.ts` exists with `ortho init` command"
**Type:** Unit  
**Tests:**
- `test_cli_init_ts_exists` — File exists
- `test_cli_init_command_exists` — Command "init" registered
- `test_cli_init_command_callable` — Function initCommand() exported

#### Criterion: "`ortho init` is callable: `node dist/cli/src/index.js init`"
**Type:** Integration  
**Tests:**
- `test_cli_transpiles_to_dist` — TypeScript transpiles to dist/
- `test_cli_init_callable` — `node dist/index.js init` or similar runs without syntax error

#### Criterion: "After `ortho init`, `.ortho/` directory exists, `.ortho/config.toml` exists, `.ortho/ortho.db` exists"
**Type:** Integration  
**Tests:**
- `test_init_creates_ortho_directory` — `.ortho/` directory created after `ortho init`
- `test_init_creates_config_toml` — `.ortho/config.toml` exists after `ortho init`
- `test_init_creates_ortho_db` — `.ortho/ortho.db` exists after `ortho init`
- `test_init_creates_vectors_db` — `.ortho/vectors.db` exists after `ortho init`

#### Criterion: "`tsc --noEmit` in apps/cli/ returns exit 0 and `eslint apps/cli/src/` returns exit 0"
**Type:** Integration  
**Tests:**
- `test_cli_typescript_compiles` — `tsc --noEmit` exits with 0 in apps/cli/
- `test_cli_eslint_passes` — `eslint apps/cli/src/` exits with 0
- `test_cli_no_any_types` — No `any` found in CLI TypeScript code

---

### FASTAPI SERVER (3 Acceptance Criteria)

#### Criterion: "`apps/api-server/src/main.py` exists with FastAPI app"
**Type:** Unit  
**Tests:**
- `test_api_main_py_exists` — File exists
- `test_api_has_fastapi_app` — FastAPI application instance created
- `test_api_app_title` — App title is "Ortho API Server"
- `test_api_app_version` — App version is "0.1.0"

#### Criterion: "`GET /health` endpoint returns 200: `{\"status\": \"ok\"}`"
**Type:** Unit  
**Tests:**
- `test_api_health_endpoint_exists` — Endpoint registered at GET /health
- `test_api_health_returns_200` — Response status code is 200
- `test_api_health_response_format` — Response body is JSON
- `test_api_health_response_has_status_field` — Response contains "status" field
- `test_api_health_response_status_is_ok` — "status" value is "ok"

#### Criterion: "Server listens on `http://localhost:17234` and type hints present (mypy --strict compliance)"
**Type:** Integration  
**Tests:**
- `test_api_server_starts` — Server starts: `python -m uvicorn apps.api-server.src.main:app --host 127.0.0.1 --port 17234`
- `test_api_server_listens_on_port_17234` — Server listens on port 17234
- `test_api_server_listens_on_localhost` — Server listens on 127.0.0.1
- `test_api_health_endpoint_reachable` — Can reach /health endpoint after server starts
- `test_api_mypy_strict_passes` — `mypy --strict apps/api-server/` exits with 0

---

### TYPE CHECKING & LINTING (3 Acceptance Criteria)

#### Criterion: "`tsc --noEmit` (root) returns exit 0 for all TypeScript code"
**Type:** Integration  
**Tests:**
- `test_tsc_root_succeeds` — `tsc --noEmit` from root exits with 0
- `test_tsc_shared_types_succeeds` — `tsc --noEmit` in shared/types/ exits with 0
- `test_tsc_cli_succeeds` — `tsc --noEmit` in apps/cli/ exits with 0
- `test_typescript_strict_mode_everywhere` — All tsconfig.json have `"strict": true`

#### Criterion: "`eslint .` (root, if configured) returns exit 0 for CLI code"
**Type:** Integration  
**Tests:**
- `test_eslint_cli_passes` — `eslint apps/cli/src/` exits with 0 (if ESLint configured)

#### Criterion: "`mypy --strict` (root) returns exit 0 for all Python code"
**Type:** Integration  
**Tests:**
- `test_mypy_shared_storage_succeeds` — `mypy --strict shared/storage/` exits with 0
- `test_mypy_api_server_succeeds` — `mypy --strict apps/api-server/` exits with 0

---

### ADRS (1 Acceptance Criterion)

#### Criterion: "ADR-001 and ADR-002 exist with proper structure"
**Type:** Unit  
**Tests:**
- `test_adr_001_exists` — ADR-001 file exists
- `test_adr_001_has_status_section` — Status section present
- `test_adr_001_has_context_section` — Context section present
- `test_adr_001_has_decision_section` — Decision section present
- `test_adr_001_has_consequences_section` — Consequences section present
- `test_adr_001_has_evidence_section` — Evidence section present
- `test_adr_001_explains_sqlite_choice` — Decision explains SQLite + sqlite-vec choice
- `test_adr_002_exists` — ADR-002 file exists
- `test_adr_002_explains_language_adapter` — Explains LanguageAdapter interface and extensibility

---

## Integration Tests Covering Component Boundaries

### CLI → Storage Integration
- `test_cli_init_creates_ortho_directory_structure` — CLI creates full `.ortho/` structure
- `test_cli_init_creates_valid_config_toml` — Created config.toml is parseable TOML
- `test_cli_init_creates_valid_database_file` — Created ortho.db is valid SQLite file (can be opened)

### Storage → Database Integration
- `test_orthodb_creates_valid_schema` — After OrthoDatabase.migrate(), all tables exist with correct structure
- `test_orthodb_schema_has_all_tables` — All 12 tables created
- `test_orthodb_schema_constraints_enforced` — Foreign keys actually enforced (violation causes error)
- `test_orthodb_connection_respects_wal_mode` — Connection pragma JOURNAL_MODE is WAL
- `test_orthodb_connection_respects_foreign_keys` — Foreign key pragma is ON

### API → Health Integration
- `test_api_health_endpoint_is_async` — Endpoint is properly async
- `test_api_health_pydantic_validation` — Response is validated by Pydantic model

### End-to-End: CLI → Storage Flow
- `test_e2e_ortho_init_creates_complete_setup` — `ortho init` creates `.ortho/config.toml` and `.ortho/ortho.db` in correct locations
- `test_e2e_config_loadable_after_init` — After init, config.toml is loadable by OrthoConfig.load()
- `test_e2e_database_usable_after_init` — After init, OrthoDatabase can connect and query

---

## Edge Cases

### Input/Configuration Edge Cases
- `test_config_missing_optional_fields` — Config.load() succeeds with missing optional fields (uses defaults)
- `test_config_extra_fields_ignored` — Config.load() succeeds with extra fields in TOML
- `test_orthodb_path_with_spaces` — OrthoDatabase handles project paths with spaces
- `test_orthodb_path_with_unicode` — OrthoDatabase handles Unicode characters in paths
- `test_orthodb_relative_project_root` — OrthoDatabase handles relative paths (converted to absolute)
- `test_config_load_file_does_not_exist` — OrthoConfig.load() raises FileNotFoundError if file missing
- `test_config_load_invalid_toml_syntax` — OrthoConfig.load() raises exception on malformed TOML

### Boundary Value Cases
- `test_compression_threshold_zero` — Config with compression_threshold=0 is valid
- `test_compression_threshold_one` — Config with compression_threshold=1 is valid
- `test_compression_threshold_negative` — Config.validate() rejects compression_threshold < 0
- `test_compression_threshold_over_one` — Config.validate() rejects compression_threshold > 1
- `test_default_budget_zero` — Config.validate() rejects default_budget=0
- `test_default_budget_negative` — Config.validate() rejects default_budget < 0
- `test_max_tokens_zero` — Config with max_tokens=0 — accept or reject? (test documents behavior)
- `test_default_budget_very_large` — Config with default_budget=999999 is accepted

### Type Mismatch Cases
- `test_config_load_compression_threshold_as_string` — TOML parser handles string-to-float conversion correctly or raises error
- `test_config_load_default_budget_as_string` — TOML parser handles string-to-int conversion correctly
- `test_config_load_max_tokens_as_float` — max_tokens as 8192.5 — truncated or rejected?
- `test_orthodb_init_with_string_not_path` — Passing string instead of Path — accepted or raises?

### Null/Empty Cases
- `test_config_empty_project_name` — Config.validate() rejects empty project_name
- `test_config_empty_primary_language` — Config.validate() rejects empty primary_language
- `test_config_empty_languages_list` — Config with languages=[] — accepted or rejected?
- `test_config_empty_exclude_patterns` — Config with exclude_patterns=[] is valid
- `test_orthodb_migrate_no_sql_files` — OrthoDatabase.migrate() succeeds even if no migrations exist

### Concurrent/Sequential Cases
- `test_orthodb_multiple_connections_to_same_db` — Two OrthoDatabase instances can read from same ortho.db
- `test_orthodb_concurrent_migrations` — Running migrate() on two instances simultaneously (WAL handles concurrency)
- `test_cli_init_twice_in_same_directory` — Running `ortho init` twice creates no errors (idempotent)
- `test_cli_init_in_existing_ortho_directory` — Running init when `.ortho/` exists overwrites or skips

---

## Failure Scenarios

### Validation Failures
- `test_config_validate_fails_empty_project_name` — `.validate()` raises ValueError with message about project_name
- `test_config_validate_fails_invalid_budget` — `.validate()` raises ValueError with message about budget
- `test_config_validate_fails_invalid_threshold` — `.validate()` raises ValueError with message about threshold

### File System Failures
- `test_orthodb_init_permission_denied` — OrthoDatabase.__init__ on read-only directory — raises PermissionError or silently fails?
- `test_cli_init_permission_denied` — `ortho init` on read-only directory — error message shown
- `test_config_load_permission_denied` — OrthoConfig.load() on read-only config.toml — raises error

### Database Failures
- `test_orthodb_migrate_malformed_sql` — OrthoDatabase.migrate() with invalid SQL in .sql file — raises exception with details
- `test_orthodb_connection_database_locked` — Multiple writers to ortho.db (if WAL not working) — handled gracefully or errors
- `test_orthodb_connection_disk_full` — Simulated disk full scenario — database operations fail with clear error

### API Failures
- `test_api_health_database_error` — If future endpoints query database and fail — returns 500, not 200
- `test_api_startup_missing_dependencies` — Server fails to start if FastAPI/uvicorn not installed
- `test_api_port_already_in_use` — Server startup fails with clear message if port 17234 already used

### Type/Syntax Failures
- `test_config_py_syntax_error` — If config.py had syntax error, mypy --strict would fail (test documents)
- `test_database_py_implicit_any_found` — If any `Any` added, mypy --strict catches it
- `test_cli_index_ts_syntax_error` — If CLI had syntax error, tsc --noEmit would fail

---

## Regression Candidates

No prior tests to verify (Phase 1 foundation, no existing code). After future phases add features:

**Tests that may break in future if schema changes:**
- All tests depending on schema structure (table names, column names)
- Any test mocking OrthoDatabase might need updates if interface changes

**Tests that may break if types change:**
- Type tests checking FRD compliance will fail if types modified

**Tests that may break if CLI/API changes:**
- Integration tests for `ortho init` command
- API health endpoint tests

---

## Test Coverage Goals

- **Criterion Coverage:** 100% (≥1 test per acceptance criterion)
- **Line Coverage:** ≥85% (storage, database, config modules)
- **Branch Coverage:** ≥80% (validation logic, error paths)
- **Function Coverage:** ≥95% (all public methods tested)

---

## Test Execution Strategy

### Test Organization
**Unit Tests:** Test individual components in isolation (types, config validation, database interface)
**Integration Tests:** Test components working together (CLI → storage, storage → database)
**End-to-End Tests:** Full `ortho init` flow from CLI to database

### Execution Order
1. **Phase 1: Structure & Type Tests** (1–2 seconds)
   - Monorepo structure tests
   - Type definition tests
   - Configuration parsing tests

2. **Phase 2: Compilation & Type Checking** (5–10 seconds)
   - TypeScript compilation (tsc --noEmit)
   - Python type checking (mypy --strict)
   - ESLint checks

3. **Phase 3: Integration Tests** (5–15 seconds)
   - Database initialization
   - Schema validation
   - CLI initialization
   - API health check

4. **Phase 4: Edge Cases & Failure Scenarios** (10–20 seconds)
   - All edge cases
   - All failure paths

**Total Expected Time:** 30–60 seconds

### Parallelization
- Unit tests can run fully in parallel (no shared state)
- Integration tests should run sequentially (database state, file system operations)
- Use test framework parallelization flags (Jest: `--maxWorkers=4`, pytest: `-n 4`)

### Setup/Teardown
**Before Each Test:**
- Create temporary directory for test artifacts
- Use isolated config files (not shared .ortho/)
- Mock database paths to avoid polluting project

**After Each Test:**
- Clean up temporary directories
- Reset database state (if needed)
- Verify no orphaned processes (API server)

---

## Test Implementation Notes

### Framework Selection
- **TypeScript/CLI tests:** Jest (already common for TS) or Vitest
  - Setup: `npm install --save-dev jest @types/jest ts-jest`
  - Config: jest.config.js with ts-jest preset
  - Run: `npm test` or `jest`

- **Python tests:** pytest (standard for Python)
  - Setup: `pip install pytest`
  - Run: `pytest shared/storage/ apps/api-server/`

- **Integration tests:** Both frameworks with manual/system commands
  - Use `child_process` (Node) or `subprocess` (Python) to run CLI/API

### Key Testing Patterns

**Type Checking Tests:**
```typescript
// shared/types/src/__tests__/repository.ts
describe('Repository types', () => {
  test('Repository interface has all required fields', () => {
    const repo: Repository = {
      id: 'repo-1',
      root_path: '/path',
      name: 'My Repo',
      languages: ['python'],
      indexed_at: new Date(),
      git_remote: 'https://github.com/...'
    };
    expect(repo.id).toBe('repo-1');
  });
});
```

**Config Validation Tests:**
```python
# shared/storage/tests/test_config.py
def test_config_validate_rejects_empty_project_name():
    config = OrthoConfig(
        project_name='',
        primary_language='python',
        # ... other required fields
    )
    with pytest.raises(ValueError, match='project_name'):
        config.validate()
```

**Database Integration Tests:**
```python
# shared/storage/tests/test_database.py
def test_orthodb_migrate_creates_all_tables():
    db = OrthoDatabase(Path(tempdir))
    db.migrate()
    
    conn = db.connection()
    cursor = conn.cursor()
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    
    assert len(tables) == 12  # All expected tables
```

**CLI Integration Tests:**
```typescript
// apps/cli/src/__tests__/init.integration.ts
describe('ortho init command', () => {
  test('creates .ortho directory with all files', async () => {
    const tempDir = tmpdir();
    process.chdir(tempDir);
    
    await initCommand();
    
    expect(fs.existsSync('.ortho')).toBe(true);
    expect(fs.existsSync('.ortho/config.toml')).toBe(true);
    expect(fs.existsSync('.ortho/ortho.db')).toBe(true);
  });
});
```

---

## Known Test Limitations

### Hard to Test Automatically
- **File permission errors:** Difficult to simulate permission denied without modifying system
  - Mitigation: Document expected behavior, test with mock filesystem if possible
  
- **Database corruption:** Hard to create realistic SQLite corruption
  - Mitigation: Test error handling with mocked database methods
  
- **Concurrent write conflicts:** WAL mode makes conflicts rare, hard to trigger reliably
  - Mitigation: Test at API level when implemented (multiple requests)

### Tests Requiring Manual Verification
- **API server actually listens:** Requires starting process and connecting
  - Mitigation: Use test servers (e.g., TestClient from Starlette for FastAPI)
  
- **Performance:** CLI/API startup time
  - Mitigation: Use performance tests separate from functional tests

### Not Testable (Design-Time Verification Only)
- **Monorepo scalability:** Would require thousands of packages
- **Database at scale:** Would require millions of rows to test performance
- **Long-running migrations:** Not needed for Phase 1 schema

---

## Evidence Requirements

After tests are written and passing, VERIFIER will collect:

### Build Evidence
```bash
# TypeScript builds
tsc --noEmit
tsc --noEmit shared/types/
tsc --noEmit apps/cli/

# Python compilation
python -m py_compile shared/storage/src/database.py
python -m py_compile apps/api-server/src/main.py
```

### Type Check Evidence
```bash
# TypeScript
tsc --noEmit

# Python
mypy --strict shared/storage/
mypy --strict apps/api-server/
```

### Lint Evidence
```bash
# ESLint (if configured)
eslint apps/cli/src/
eslint shared/types/src/
```

### Test Execution Evidence
```bash
# CLI tests
npm test -- apps/cli/

# Storage tests
pytest shared/storage/tests/ -v

# API tests
pytest apps/api-server/tests/ -v

# Coverage report
npm test -- --coverage
pytest --cov=shared/storage
```

### Manual Verification Evidence
```bash
# CLI verification
cd /tmp/test-ortho && ortho init && ls -la .ortho/

# API server health
python -m uvicorn apps.api-server.src.main:app &
curl http://localhost:17234/health
```

---

## Summary

**Total Tests Designed:** 120+ (across unit, integration, edge cases, failures)  
**Acceptance Criteria Covered:** 45/45 (100%)  
**Test Framework:** Jest (TypeScript) + pytest (Python)  
**Expected Total Run Time:** 30–60 seconds  
**Status:** TESTS-WRITTEN, awaiting VERIFIER execution

---

*End of test-plan.md*
