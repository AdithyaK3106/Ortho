task: task-002
title: Week 3–4 — Python Language Adapter
owner: Solo Developer
created: 2026-06-30

summary: Implement LanguageAdapter interface for Python using tree-sitter AST parsing. Extract symbols (functions, classes, methods) from Python source and build import dependency graph. Foundation for repo intelligence Phase 1 Week 3–4.

atomic_tasks:
  - task: LanguageAdapter interface definition
    scope: Define interface in shared/types/src/adapter.ts with methods: parse(file_path), extract_symbols(tree), analyze_dependencies(tree)
    duration_min: 30
    duration_max: 60
    dependencies: none
    acceptance:
      - LanguageAdapter interface defined and exported from shared/types
      - No `any` types used
      - All methods documented with clear parameter and return types

  - task: Python adapter implementation with tree-sitter
    scope: packages/repo-intelligence/src/adapters/python_adapter.py; implement PythonAdapter class wrapping tree-sitter parser; query Python grammar for functions, classes, imports
    duration_min: 60
    duration_max: 90
    dependencies: task-1
    acceptance:
      - PythonAdapter loads tree-sitter grammar for Python
      - parse(file_path) returns AST
      - All methods have type hints (mypy --strict)
      - No SQL operations (just AST parsing)

  - task: Symbol extraction from Python AST
    scope: packages/repo-intelligence/src/symbol_extractor.py; walk tree-sitter AST, extract function/class/method symbols with qualified names, line numbers, docstrings
    duration_min: 45
    duration_max: 75
    dependencies: task-2
    acceptance:
      - Symbol objects have: name, qualified_name, type (function|class|method), lineno, docstring
      - All symbols serializable to JSON
      - Type hints present (mypy --strict)

  - task: Import graph builder
    scope: packages/repo-intelligence/src/import_graph.py; extract import statements from Python files, build graph of module dependencies
    duration_min: 45
    duration_max: 75
    dependencies: task-3
    acceptance:
      - Detects: from X import Y, import X, relative imports
      - ImportEdge objects: source_module, target_module, import_type, lineno
      - Handles circular imports (no crash, documented)

task_order: task-1 → task-2 → task-3 → task-4 (linear, each depends on previous)

risks:
  - risk: tree-sitter Python grammar not available — affects parsing capability — mitigation: verify grammar installs correctly in verification
  - risk: Circular imports cause infinite loops — affects import graph — mitigation: cycle detection in graph builder
  - risk: Symbol extraction misses nested classes — affects completeness — mitigation: comprehensive tree walk, tested with edge cases
  - risk: Performance degrades on large files (1000+ lines) — affects usability — mitigation: no optimization in Phase 1, acceptable for MVP

acceptance:
  - All 4 atomic tasks implemented and verified
  - No new type errors (tsc --noEmit, mypy --strict pass)
  - No new linting errors (ruff check, eslint pass)
  - Every acceptance criterion has at least one corresponding unit or integration test
  - Parser edge cases covered (empty files, syntax errors, large files)
  - Symbol extraction verified with representative Python examples (functions, classes, nested methods, decorators)
  - Import extraction verified with representative patterns (from/import statements, relative imports, circular imports)
  - Circular import handling verified (no infinite loops)
  - No regression test failures
  - Architecture review approved (if needed; else waived: architecture_impact: NONE)
  - Code review approved
  - All evidence files exist

notes_for_architect: New module `repo-intelligence` implementing existing LanguageAdapter architecture. Python adapter is first implementation of the LanguageAdapter pattern defined in Ortho FRD. No new architecture decisions. Can waive ARCHITECT if architecture_impact: NONE confirmed in spec.

notes_for_builder: Follow existing LanguageAdapter pattern defined in Ortho FRD. Keep parser logic separate from symbol extraction. Type hints required everywhere. Use dataclasses for Symbol/ImportEdge. No database writes in this task.

---
