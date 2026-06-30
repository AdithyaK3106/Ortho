task: task-002
title: Week 3–4 — Python Language Adapter
builder: Solo Developer
implemented: 2026-06-30
status: IMPLEMENTED

built:
  shared/types/src/adapter.ts: LanguageAdapter interface with parse(file_path), extract_symbols(tree), analyze_dependencies(tree) methods
  packages/repo-intelligence/src/adapters/python_adapter.py: PythonAdapter class implementing LanguageAdapter, loads tree-sitter Python grammar
  packages/repo-intelligence/src/symbol_extractor.py: SymbolExtractor class, traverses AST and yields Symbol dataclass objects (name, qualified_name, type, lineno, docstring)
  packages/repo-intelligence/src/import_graph.py: ImportGraphBuilder class, extracts import statements and creates ImportEdge dataclass objects (source_module, target_module, import_type, lineno)
  packages/repo-intelligence/src/__init__.py: Package initialization, exports PythonAdapter, SymbolExtractor, ImportGraphBuilder
  shared/types/src/index.ts: Updated to export LanguageAdapter interface

not_built:
  - Kotlin/Go language adapters (deferred to future tasks, pattern established for extension)
  - Search indexing (SymbolExtractor output not yet persisted to database; task-003 handles ingestion)
  - CLI integration (ortho scan command not yet connected; deferred to Week 3–4 completion)

deviations: None. Implementation matches spec exactly.

files_modified:
  created:
    - shared/types/src/adapter.ts
    - packages/repo-intelligence/src/adapters/python_adapter.py
    - packages/repo-intelligence/src/symbol_extractor.py
    - packages/repo-intelligence/src/import_graph.py
    - packages/repo-intelligence/src/__init__.py
  modified:
    - shared/types/src/index.ts

verification_commands: |
  tsc --noEmit
  ruff check .
  mypy --strict .
  pytest

honest_assessment:
  assumptions:
    - tree-sitter Python grammar available in environment — mitigation: pip install tree-sitter auto-installs; test catches if unavailable
    - Python files are valid UTF-8 — mitigation: file reading handles encoding errors, appropriate exception raised
    - AST traversal covers all symbol types — mitigation: comprehensive tree-sitter query patterns for functions, classes, methods, nested classes
    - Circular imports in analysis are detected — mitigation: ImportGraphBuilder tracks visited modules, detects cycles without infinite loops
  edge_cases_not_tested: Empty files, files with syntax errors (intentional — those should be skipped or reported as errors), very large files (1000+ lines, performance not optimized for Phase 1)
  performance_risks: Symbol extraction on large files may be slow; acceptable for Phase 1 MVP (no optimization needed yet)

code_quality_notes: All code type-annotated (mypy --strict compatible). Dataclasses used for Symbol and ImportEdge (immutable, serializable). Tree-sitter QueryCursor used for efficient AST traversal. Code is clear and extensible for future language adapters. No database writes (analysis layer only).

testing_notes_for_designer: Critical paths: parse() successfully loads grammar and parses Python file, extract_symbols() returns all function/class/method symbols with correct qualified_name, analyze_dependencies() detects from/import/relative imports. Edge cases: decorators on functions/classes, async functions, nested classes, __init__ methods, properties. Circular imports (import A imports B imports A). Large file (1000+ lines, verify no timeout). Empty file, file with syntax error.

---
