task: task-002
title: Week 3–4 — Python Language Adapter
owner: Solo Developer
created: 2026-06-30
status: DRAFT
architecture_impact: NONE (implements existing LanguageAdapter pattern, no new architecture decisions)

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
  - File content (string or bytes)

contract_out:
  - parse() returns AST tree object (tree-sitter Tree type, used for querying)
  - extract_symbols() returns list of Symbol dataclass objects: {name, qualified_name, type (function|class|method), lineno, docstring}
  - analyze_dependencies() returns list of ImportEdge dataclass objects: {source_module, target_module, import_type (from|import|relative), lineno}

acceptance:
  - LanguageAdapter interface defined and exported — evidence: tsc --noEmit
  - PythonAdapter implements LanguageAdapter, loads tree-sitter Python grammar — evidence: unit test
  - parse(file_path) parses Python file and returns tree-sitter AST object — evidence: unit test with .py file
  - extract_symbols() returns Symbol list with all required fields — evidence: unit test assertions
  - Symbol objects include functions, classes, methods, nested classes — evidence: test with representative Python examples
  - All Symbol objects serializable to JSON — evidence: json.dumps() test
  - analyze_dependencies() extracts import statements (from/import/relative) — evidence: unit test with import patterns
  - Circular imports handled without infinite loops — evidence: test with circular import file
  - All Python code passes mypy --strict — evidence: mypy exit code 0
  - All TypeScript code passes tsc --noEmit — evidence: tsc exit code 0
  - All code passes linting (ruff check, eslint) — evidence: linter exit codes 0
  - Every acceptance criterion has at least one corresponding test — evidence: test-plan.md

dependencies: task-001 (shared types and monorepo structure)

risk: MEDIUM — tree-sitter grammar installation, circular import handling, performance with large files

verification_commands: |
  tsc --noEmit
  ruff check .
  mypy --strict .
  pytest

change_impact:
  modules: repo-intelligence (new package, implements existing LanguageAdapter pattern)
  apis: None (internal API, not CLI/HTTP)
  regression_candidates: None (new feature, no existing tests affected)

notes_for_builder: Implement Symbol and ImportEdge as dataclasses. Use tree-sitter QueryCursor for AST traversal. Handle edge cases: decorators, async functions, nested classes, empty files. No database writes — this is analysis only. Type hints required everywhere. Code should be clear and extensible for future language adapters (Kotlin, Go, etc.).

---
