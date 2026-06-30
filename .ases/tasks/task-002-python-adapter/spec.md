task: task-002
title: Week 3–4 — Python Language Adapter
owner: Solo Developer
created: 2026-06-30
status: DRAFT
architecture_impact: NONE (fits existing LanguageAdapter pattern from ADR-005, no new modules beyond repo-intelligence)

objective: Implement LanguageAdapter interface for Python using tree-sitter AST parsing; extract symbols and build import graph.

files_create: 
  - shared/types/src/adapter.ts
  - packages/repo-intelligence/src/adapters/python_adapter.py
  - packages/repo-intelligence/src/symbol_extractor.py
  - packages/repo-intelligence/src/import_graph.py
  - packages/repo-intelligence/src/__init__.py

files_modify:
  - shared/types/src/index.ts (export LanguageAdapter interface)

files_forbid:
  - Database schema changes
  - CLI commands (ortho scan not yet implemented)
  - API endpoints
  - Shared storage layer

contract_in: 
  - File path (string)
  - File content (string or Path object)

contract_out:
  - Symbol: {name, qualified_name, type (function|class|method), lineno, docstring}
  - ImportEdge: {source_module, target_module, import_type (from|import|relative), lineno}
  - LanguageAdapter interface methods: parse(), extract_symbols(), analyze_dependencies()

acceptance:
  - LanguageAdapter interface defined and exported — evidence: tsc --noEmit
  - PythonAdapter loads tree-sitter Python grammar — evidence: unit test instantiation
  - parse(file_path) parses Python file and returns AST — evidence: unit test with sample .py file
  - extract_symbols() returns list of Symbol objects with all required fields — evidence: unit test assertions
  - All Symbol objects serializable to JSON (via dataclass) — evidence: json.dumps() test passes
  - import_graph.py builds ImportEdge list from file — evidence: unit test with import statements
  - Circular imports detected (no infinite loop) — evidence: test with circular import file
  - All Python code passes mypy --strict — evidence: mypy exit code 0
  - All TypeScript code passes tsc --noEmit — evidence: tsc exit code 0
  - All code passes linting (ruff, eslint) — evidence: linter exit codes 0
  - 100+ tests cover all acceptance criteria — evidence: test count from test-plan.md

dependencies: task-001 (shared types, monorepo structure must exist)

risk: MEDIUM — tree-sitter grammar availability, circular import handling, performance on large files

verification_commands: |
  tsc --noEmit shared/types/src/adapter.ts
  ruff check packages/repo-intelligence/src/
  mypy --strict packages/repo-intelligence/src/
  pytest packages/repo-intelligence/tests/ -v --tb=short

change_impact:
  modules: repo-intelligence (new package, first LanguageAdapter implementation)
  apis: None (this is internal API, not CLI/HTTP)
  regression_candidates: None (new feature, no existing tests affected)

notes_for_builder: Keep Symbol and ImportEdge as dataclasses. Use tree-sitter QueryCursor for efficient AST traversal. Handle edge cases: decorators, async functions, nested classes. No database writes — this is analysis only. Type hints mandatory everywhere. Code should be readable for future Kotlin/Go adapters to follow pattern.

---
