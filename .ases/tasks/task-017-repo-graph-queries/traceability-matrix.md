# Traceability Matrix — task-017-repo-graph-queries

| Requirement | Architecture | Code | Tests | Evidence | Status |
|---|---|---|---|---|---|
| RepoGraphQueries.find_callers (spec.md Component 1) | Same-package, no cross-boundary concern (architecture-review.md) | graph_queries.py:31-61 | test_graph_queries.py::TestFindCallers (8 tests) + TestFindCallersProperty (1 property test) | tests_20260714_231609.log (repo-intelligence: 176 passed) | Complete |
| RepoGraphQueries.find_importers (spec.md Component 1) | Same-package | graph_queries.py:63-95 | test_graph_queries.py::TestFindImporters (8 tests) | tests_20260714_231609.log | Complete |
| SymbolIndex.symbols_in_file (spec.md Component 2) | Same-package | graph_queries.py:98-105 | test_graph_queries.py::TestSymbolIndex (6 tests) | tests_20260714_231609.log | Complete |
| ArchModelAdapter.get_layer/get_layer_for_module/get_layers/get_modules (spec.md Component 3) | arch-intelligence-only, constrained constructor (architecture-review.md, ADR-016) | model_adapter.py:15-45 | test_model_adapter.py (10 tests) | tests_20260714_231609.log (arch-intelligence: 105 passed) | Complete |
| DependencyGraphAdapter.get_edges/find_cycles (spec.md Component 4) | Relocated to cli-commands (architecture-review.md, ADR-016) | dependency_graph_adapter.py:18-86 | test_dependency_graph_adapter.py (14 tests, incl. 1 property test + new circular-import fixture) | tests_20260714_231609.log (cli-commands: 53 passed) | Complete |
| CodeMetricsAdapter.get_module_lines/get_module_functions (spec.md Component 5) | Same-package | graph_queries.py:108-142 | test_graph_queries.py::TestCodeMetricsAdapter (10 tests) | tests_20260714_231609.log | Complete |
| ortho guardrails() real scan wiring (spec.md Component 6) | cli-commands orchestrates all lower layers (architecture-review.md) | commands.py:69-105, repo_scanner.py | test_commands.py::test_guardrails_command_real_scan, test_guardrails_command_bad_path; test_edge_cases_exhaustive.py::test_guardrails_check, test_guardrails_with_path | tests_20260714_231609.log | Complete |
| ortho decide() real scan + prediction wiring (spec.md Component 6) | cli-commands orchestrates all lower layers | commands.py:109-165 | test_commands.py::test_decide_command_file_intent, test_decide_command_text_intent_with_scan_path, test_decide_command_empty_intent; test_edge_cases_exhaustive.py::test_decide_with_valid_intent | tests_20260714_231609.log | Complete |
| Old stub literals removed | N/A | commands.py (guardrails/decide bodies) | test_commands.py::test_no_stub_literals_remain | tests_20260714_231609.log | Complete |
| ADR-015 compliance (no Intelligence-to-Intelligence import) | ADR-016 corrected placement | model_adapter.py (no repo_intelligence import), dependency_graph_adapter.py (in cli-commands, not arch-intelligence) | Verified by REVIEWER via direct import inspection (review.md, Architecture Compliance section) | review.md | Complete |
| mypy --strict on all new files | N/A | 5 new files | N/A (type-check, not a test) | mypy_20260714_231609.log | Complete |
| No regression in existing 303+ tests | N/A | N/A (regression is a property of unchanged behavior, not new code) | Full suite runs across 6 packages | tests_20260714_231609.log, verification-report.md's REGRESSION section | Complete |

## Automatically Detected Gaps

- **Missing implementation:** None.
- **Missing tests:** None. The gap identified by REVIEWER (no test for `repo_scanner.py`'s `SyntaxError` handling) was closed: `test_commands.py::test_guardrails_skips_file_with_syntax_error_without_crashing` added and verified passing.
- **Missing verification:** None.
- **Missing review:** None — all 6 components addressed in review.md.
- **Orphaned code:** None — every new class/function traces back to a spec.md component.
- **Untested implementation:** None at the component level. See "Missing tests" above for the one sub-branch gap.
- **Acceptance criteria without evidence:** None.
- **Evidence without originating requirement:** None.

## Coverage Summary

- Requirements implemented: 12 / 12
- Requirements tested: 12 / 12
- Requirements verified: 12 / 12
- Requirements reviewed: 12 / 12
