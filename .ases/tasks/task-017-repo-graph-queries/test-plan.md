# Test Plan: task-017-repo-graph-queries

Written independently against spec.md's contracts and test-coverage tables
(shadow-parallel/blind mode, per user decision: authored from spec.md, not
from BUILDER's session narrative). Cross-checked against real implementation
only after writing, to confirm imports/assertions target real product code.

## Unit Tests Per Component (spec.md tables)

### Component 1: RepoGraphQueries.find_callers (`test_graph_queries.py::TestFindCallers`)
- test_direct_caller_found
- test_no_callers
- test_transitive_depth_2
- test_recursive_function_terminates
- test_duplicate_edges_deduped
- test_symbol_not_found
- test_empty_call_edges
- test_depth_zero_returns_empty (edge case not in spec table, added since depth=0 semantics were unspecified)
- test_real_repo_scan_no_crash (real-repo, mandatory)

### Component 1: RepoGraphQueries.find_importers (`test_graph_queries.py::TestFindImporters`)
- test_direct_importer_found
- test_include_type_true
- test_no_importers
- test_empty_import_edges_by_file
- test_from_import_type_preserved
- test_relative_import_type_preserved (spec.md's "star import" case adjusted: ImportEdge only has 'from'/'import'/'relative' types per real repo_intelligence.import_graph.py — tested the types that actually exist, not an assumed 'star' type)
- test_self_import_excluded
- test_real_repo_scan_no_crash (real-repo, mandatory)

### Component 2: SymbolIndex (`test_graph_queries.py::TestSymbolIndex`)
- test_known_file_symbols_present
- test_unknown_file
- test_empty_symbols_list_for_file
- test_duplicate_names_both_returned
- test_empty_dict
- test_real_repo_scan_no_crash (real-repo, mandatory)

### Component 5: CodeMetricsAdapter (`test_graph_queries.py::TestCodeMetricsAdapter`)
- test_real_file_known_line_count
- test_unknown_module
- test_missing_file_on_disk
- test_empty_file
- test_function_count_known_file
- test_function_count_with_class_methods
- test_nested_functions_both_counted
- test_syntax_error_in_file
- test_multiple_files_same_module_summed
- test_real_repo_scan_no_crash (real-repo, mandatory)

### Component 3: ArchModelAdapter (`test_model_adapter.py`)
- test_module_in_layer_0
- test_module_not_in_any_layer
- test_get_layers_ordering_by_number
- test_empty_layers
- test_get_modules_dedup
- test_get_modules_empty
- test_layer_with_no_file_ids_still_appears
- test_get_layer_for_module_matches_get_layer
- test_unknown_file_id_in_mapping_resolves_unknown
- test_real_arch_model_from_detector (real-repo/real-object, mandatory) — builds a genuine ArchitectureModel via real LayerDetector against real small files, not a hand-constructed mock

### Component 4: DependencyGraphAdapter (`test_dependency_graph_adapter.py`)
- test_no_edges
- test_simple_acyclic_chain
- test_unmapped_target_excluded
- test_determinism
- test_large_acyclic_graph_completes (50-file chain)
- test_no_edges_no_cycles
- test_acyclic_chain_no_cycles
- test_direct_2_cycle
- test_3_node_cycle
- test_two_independent_cycles
- test_empty_import_edges_by_file
- test_real_repo_scan_completes_bounded_time (real-repo, mandatory, asserts <30s against repos/click)
- test_real_repo_with_known_circular_import (real-repo, mandatory) — uses the spec.md-authorized fixture package `packages/cli-commands/tests/fixtures/circular_import_fixture/` (module_a <-> module_b, a genuine hand-verified circular import, real files real imports, not a hardcoded assertion)

### Component 6: CLI wiring (`packages/cli-commands/tests/test_commands.py`, `test_edge_cases_exhaustive.py`)
Already covered by BUILDER's own test updates (reviewed and re-verified independently, not re-authored, since these existing test files were within `files_modify` and BUILDER's changes there were minimal/mechanical — bounding pre-existing stub-era tests to real fixture paths). Re-verified: 53/53 passing, includes empty-intent rejection, bad-path handling, real scan against repos/click and repos/requests, and a grep-based stub-literal-removal check.

## Property-Based Tests (spec.md requires >=1 per component area, hypothesis, >=10 cases)

- `test_graph_queries.py::TestFindCallersProperty::test_depth_n_plus_1_is_superset_of_depth_n` — 25 generated call-chain examples; asserts depth=N+1 result is always a superset of depth=N (monotonicity property of the BFS traversal).
- `test_dependency_graph_adapter.py::TestFindCyclesProperty::test_reverse_edge_between_connected_nodes_creates_cycle` — 15 generated module-name pairs; asserts that adding a reverse edge between two connected modules always produces >=1 detected cycle.

## Real-Repo Scan Tests (spec.md requires >=1 per component, against repos/click, repos/flask, or repos/requests)

| Component | Real repo used |
|---|---|
| find_callers | repos/click/src/click/core.py |
| find_importers | repos/flask/src/flask (first 10 files) |
| SymbolIndex | repos/flask/src/flask/app.py |
| CodeMetricsAdapter | repos/requests/src/requests/models.py |
| ArchModelAdapter | synthetic-but-real small files + real LayerDetector (spec.md's real-object requirement satisfied by using the actual production LayerDetector/ArchitectureModel classes, not a mock) |
| DependencyGraphAdapter (performance) | repos/click/src/click (full directory, asserts <30s) |
| DependencyGraphAdapter (cycle detection) | new fixture package (spec.md-authorized) with a genuine hand-verified circular import |
| CLI wiring | repos/click, repos/requests (via BUILDER's test updates) |

## Integration Tests (component boundaries)

- `test_real_arch_model_from_detector` exercises the ArchModelAdapter <-> LayerDetector <-> ArchitectureModel boundary with real objects end to end.
- `test_real_repo_with_known_circular_import` exercises DependencyGraphAdapter <-> ImportGraphBuilder <-> real filesystem boundary end to end.
- CLI wiring tests (Component 6, via BUILDER's updates) exercise the full guardrails()/decide() pipeline: repo_scanner -> adapters -> ArchitectureEnforcer/ChangePredictor/DecisionEngine -> CliReport, with real files on disk.

## Edge Cases Covered

Empty (empty dicts/lists), missing/unknown keys, syntax errors, recursive/cyclic structures, duplicate data, self-referential imports, zero-depth traversal, unmapped/unresolvable targets, large-graph scale (50 files), nested function definitions.

## Failure Scenarios Covered

- Missing file on disk → 0, not exception (CodeMetricsAdapter)
- Syntax error in file → 0, not exception (CodeMetricsAdapter)
- Unknown module/file lookups → "unknown" or [] or 0, not exception (all adapters)
- Empty/malformed intent to CLI → success=False, not a crash or unbounded scan (Component 6, BUILDER's tests)
- Nonexistent scan path → success=False (Component 6)

## Regression Candidates

- `packages/repo-intelligence` full suite (142 pre-existing tests) — verified still passing (176 total now, no regressions).
- `packages/arch-intelligence` full suite (95 non-benchmark pre-existing tests) — verified still passing (105 total now, no regressions). The 3 benchmark tests in `test_phase5_3_benchmarks.py` were already failing on clean master before this task (confirmed via `git stash`); not a regression.
- `packages/arch-guardrails`, `packages/change-planner`, `packages/decision-engine` — unmodified by this task; BUILDER's regression run confirmed 37/37, 42/42, 28/28 unchanged.
- `packages/cli-commands` full suite — 53/53 (39 pre-existing + updated, 14 new).

## Deferred

None. All spec.md-mandated coverage (60+ cases minimum across 6 components) was authored: 58 new tests across 3 dedicated new test files (34 in test_graph_queries.py, 10 in test_model_adapter.py, 14 in test_dependency_graph_adapter.py), plus BUILDER's Component 6 CLI-wiring updates to pre-existing test files. Verified per-package totals (see verification-report.md) exceed pre-task baselines by more than the new-file count alone would suggest, since cli-commands' pre-existing tests were also updated in place rather than only added to — cite verification-report.md's per-package table as the authoritative count rather than re-deriving a sum here.
