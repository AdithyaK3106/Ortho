task: task-002
title: Week 3–4 — Python Language Adapter
owner: Solo Developer
created: 2026-06-30

summary: Build LanguageAdapter interface and Python-specific implementation using tree-sitter AST parsing. Extract symbols (functions, classes, methods) from Python source files and build import graph. Foundation for repo intelligence in Phase 1 Week 3–4.

atomic_tasks:
  - task: LanguageAdapter interface definition
    scope: Define shared interface in shared/types/src/adapter.ts; abstract methods for parse(), extract_symbols(), analyze_dependencies()
    duration_min: 30
    duration_max: 60
    dependencies: none
    acceptance:
      - Interface exported from shared/types
      - No `any` types
      - All methods documented with JSDoc

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
  - No new linting errors (eslint, ruff pass)
  - All new tests pass (100+ tests designed by TEST-DESIGNER)
  - No regression test failures
  - Architecture review approved (if needed; else waived: fits existing adapter pattern from ADR-005)
  - Code review approved
  - All evidence files exist

notes_for_architect: New module `repo-intelligence` with LanguageAdapter pattern as per ADR-005. Python adapter fits plugin model — no new architecture, just first implementation of existing pattern. Can waive ARCHITECT if architecture_impact: NONE flagged in spec.

notes_for_builder: Follow existing adapter patterns from ADR-005. Keep parser logic separate from symbol extraction. Type hints required everywhere. Use dataclasses for Symbol/ImportEdge. No database writes in this task (task-003 handles ingestion).

---
