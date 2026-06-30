task: task-002
title: Week 3–4 — Python Language Adapter
designer: TEST-DESIGNER
created: 2026-06-30
status: COMPLETE

test_strategy: Independent session (fresh context). Read spec.md and implementation-notes.md only. Design tests for all acceptance criteria without prior BUILDER knowledge.

unit_tests:
  parse_method:
    - test_parse_valid_python_file: Parse .py file, verify returns tree-sitter Tree object (not None)
    - test_parse_file_not_found: Parse nonexistent file, verify FileNotFoundError raised
    - test_parse_empty_file: Parse empty .py file, verify returns valid tree
    - test_parse_file_with_syntax_error: Parse .py with syntax error, verify handled gracefully (tree exists or error raised)
    - test_parse_large_file: Parse 1000+ line .py file, verify no timeout, returns valid tree

  extract_symbols_method:
    - test_extract_function_symbol: Parse file with function, extract symbols, verify Symbol returned with name, qualified_name='func_name', type='function', lineno, docstring
    - test_extract_class_symbol: Parse file with class, verify Symbol with type='class', qualified_name
    - test_extract_method_symbol: Parse file with class containing method, verify method extracted with type='method', qualified_name='ClassName.method_name'
    - test_extract_nested_class: Parse file with nested class, verify both outer and nested classes extracted with correct qualified_name (e.g., 'OuterClass.InnerClass')
    - test_extract_decorated_function: Parse function with @decorator, verify still extracted with correct name
    - test_extract_async_function: Parse async def, verify extracted as function
    - test_extract_multiple_symbols: Parse file with 5+ functions/classes, verify all extracted
    - test_extract_with_docstring: Parse function with docstring, verify docstring field populated
    - test_extract_without_docstring: Parse function without docstring, verify docstring=None

  analyze_dependencies_method:
    - test_analyze_import_statement: Parse 'import X', verify ImportEdge returned with source_module='<current>', target_module='X', import_type='import'
    - test_analyze_from_import_statement: Parse 'from X import Y', verify ImportEdge with import_type='from', target_module='X'
    - test_analyze_relative_import: Parse 'from . import X' or 'from .. import Y', verify import_type='relative'
    - test_analyze_multiple_imports: Parse file with 5+ imports, verify all extracted
    - test_analyze_no_imports: Parse file with no imports, verify empty list returned
    - test_analyze_circular_import_pattern: Create mock AST with circular import (A→B→A), verify no infinite loop, ImportEdges returned

edge_cases:
  symbol_extraction:
    - test_extract_property_decorator: Parse @property method, verify extracted
    - test_extract_staticmethod: Parse @staticmethod, verify extracted
    - test_extract_classmethod: Parse @classmethod, verify extracted
    - test_extract_lambda: Parse lambda, verify handled (extracted or skipped consistently)
    - test_extract_dunder_methods: Parse __init__, __str__, verify extracted
    - test_extract_underscore_prefixed: Parse _private_func, __very_private_func, verify extracted

  import_analysis:
    - test_import_star_import: Parse 'from X import *', verify target_module='X'
    - test_import_multiple_targets: Parse 'from X import A, B, C', verify one ImportEdge per target or single edge
    - test_import_with_alias: Parse 'import X as Y' and 'from X import Y as Z', verify target_module='X' (not alias)
    - test_import_with_parentheses: Parse 'from X import (A, B, C)', verify all extracted
    - test_import_multiline: Parse import statement spanning multiple lines, verify parsed correctly

failure_scenarios:
  - test_parse_unicode_file: Parse .py file with unicode characters (é, 中文, etc.), verify parsed without error
  - test_parse_very_deeply_nested_code: Parse code with 10+ levels of nesting, verify extracted correctly
  - test_extract_symbols_from_empty_file: Parse empty file, verify empty list returned (no crash)
  - test_import_graph_from_empty_file: Parse empty file, verify empty ImportEdge list returned

regression_candidates:
  - Existing tests in shared/types/ should pass (adapter interface is pure interface)
  - No existing tests break; no dependencies on repo-intelligence yet

coverage_targets:
  - parse() method: 5 tests (happy path, file not found, empty, syntax error, large file)
  - extract_symbols(): 9 tests (functions, classes, methods, nested, decorators, async, multiple, docstrings)
  - analyze_dependencies(): 6 tests (import, from, relative, multiple, circular, no imports)
  - edge cases: 12 tests (properties, static/class methods, lambdas, dunders, star imports, aliases, parentheses, multiline, unicode, nesting, empty)
  - failure scenarios: 4 tests (unicode, nesting, empty extractions)
  - Total: 36+ tests covering all acceptance criteria and edge cases

test_execution_notes:
  - Tests should use pytest (pytest packages/repo-intelligence/tests/)
  - Mock tree-sitter trees if necessary for edge cases
  - Each test is binary: PASS or FAIL (no ambiguity)
  - All acceptance criteria have at least one corresponding test
  - Parser edge cases covered (empty files, syntax errors, large files)
  - Symbol extraction verified with representative Python examples (functions, classes, nested methods, decorators)
  - Import extraction verified with representative patterns (from/import/relative/circular)
  - Circular import handling verified (no infinite loops)

---
