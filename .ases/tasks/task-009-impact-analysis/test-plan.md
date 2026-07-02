---
name: task-009-test-plan
type: test-plan
created_by: TEST-DESIGNER
created_at: 2026-07-02
gate: GATE 4
status: SUBMITTED
---

# Task-009 Test Plan (GATE 4)

## Summary

Comprehensive test suite for Task-009 components written concurrently with BUILDER implementation (GATE 3 and GATE 4 ran in parallel per ASES best practice). All tests are written, committed, and awaiting execution by VERIFIER at GATE 5.

---

## Authoritative Test Count Baseline

| Category | Written | Planned | Total | Status |
|----------|:-------:|:-------:|:-----:|--------|
| Unit tests | 40 | 0 | 40 | ✅ Implemented |
| Property-based tests | 5 | 0 | 5 | ✅ Implemented |
| Integration tests | 0 | 16+ | 16+ | ⏳ GATE 5 |
| CLI tests | 0 | 8+ | 8+ | ⏳ GATE 5 |
| **GATE 4 Total** | **45** | **0** | **45** | **✅ Complete** |
| **Full Suite Target** | **45** | **24+** | **69+** | **⏳ GATE 5** |

**Critical distinction:**
- **GATE 4 (TEST-DESIGNER):** All 45 tests written, committed, and ready for execution
- **GATE 5 (VERIFIER):** Will execute these 45 tests, plus add integration/CLI tests, measure coverage (target ≥85%), verify 100% pass rate

---

## Test Execution Status

**GATE 4 Deliverable: 45 Written Tests**
- ✅ test_impact_analyzer.py: 14 tests (13 unit + 1 property-based) — WRITTEN and COMMITTED
- ✅ test_debt_scorer.py: 16 tests (14 unit + 2 property-based) — WRITTEN and COMMITTED
- ✅ test_dependency_health.py: 15 tests (13 unit + 2 property-based) — WRITTEN and COMMITTED
- ✅ All tests deterministic, executable, awaiting GATE 5 pytest execution

**GATE 5 Deliverable (Planned): Integration + CLI Tests**
- ⏳ Integration tests: ~16+ tests (multi-component scenarios) — To be executed by VERIFIER
- ⏳ CLI tests: ~8+ tests (user-facing commands) — To be executed by VERIFIER
- ⏳ Real-repo tests: Using fastapi fixtures — To be executed by VERIFIER

**Total after GATE 5:** 69+ tests, ≥85% coverage

---

## Test Files & Counts (GATE 4 — All Written and Committed)

### test_impact_analyzer.py — 14 Tests Written

**Unit Tests (13):**
1. `test_analyze_simple_import_chain()` — A → B → C chain detection
2. `test_analyze_no_dependents()` — Leaf file, blast_radius = 0
3. `test_analyze_cycle_handling()` — A ↔ B cycles don't infinite loop
4. `test_analyze_depth_limit()` — Depth 1/2/3 affect blast radius
5. `test_analyze_symbol_level()` — Symbol-scoped impact analysis
6. `test_analyze_with_symbols()` — Using Symbol objects for call graph
7. `test_risk_score_high_fan_in()` — High fan-in → high risk
8. `test_confidence_with_unresolved()` — Low-confidence calls reduce confidence
9. `test_evidence_generated()` — ImpactReport includes evidence
10. `test_empty_graphs()` — Empty inputs handled gracefully
11. `test_self_import_no_double_count()` — Self-imports not double-counted
12. `test_symbol_not_found()` — Non-existent symbol returns graceful report
13. `test_external_imports_excluded()` — External imports don't create dependents

**Property-Based Tests (1, via hypothesis):**
14. `test_depth_parameter_bounds()` — Depth 1–10 always bounded and valid

**Subtotal: 14 tests (13 unit + 1 property-based)**

**Coverage (implementation):**
- ✅ All public methods (analyze, analyze_symbol)
- ✅ Core algorithm (BFS traversal)
- ✅ Risk score computation
- ✅ Confidence calculation
- ✅ Edge cases (cycles, empty, missing data)

---

### test_debt_scorer.py — 16 Tests Written

**Unit Tests (14):**
1. `test_score_isolated_module()` — No deps → low coupling
2. `test_score_high_churn_module()` — 30 commits → churn_score = 1.0
3. `test_score_stable_module()` — 2 commits → churn_score < 0.2
4. `test_score_hub_module()` — High fan-in/out → high coupling
5. `test_score_all_modules_sorted()` — Results sorted by total_score desc
6. `test_test_coverage_not_found()` — No tests → test_coverage_score = 0.5
7. `test_weights_sum_to_one()` — DEFAULT_WEIGHTS = 1.0
8. `test_evidence_generated()` — DebtScore includes evidence
9. `test_empty_inputs()` — Empty graph → empty scores
10. `test_single_file()` — Single file scorable
11. `test_missing_git_metadata()` — Missing metadata defaults to 0.0
12. `test_total_score_weighted_average()` — Scores within min/max bounds
13. `test_score_module_deterministic()` — Same input → same output
14. `test_all_scores_normalized()` — All scores in [0.0, 1.0]

**Property-Based Tests (2, via hypothesis):**
15. `test_coupling_score_bounds()` — 0–50 fan-in/out all bounded [0.0, 1.0]
16. `test_churn_score_bounds()` — 0–100 commits all bounded [0.0, 1.0]

**Subtotal: 16 tests (14 unit + 2 property-based)**

**Coverage (implementation):**
- ✅ All 5 scoring dimensions
- ✅ Coupling, churn, complexity, coverage formulas
- ✅ Weighted average computation
- ✅ Edge cases (empty, missing metadata)
- ✅ Property bounds on all dimensions

---

### test_dependency_health.py — 15 Tests Written

**Unit Tests (13):**
1. `test_analyze_isolated_module()` — No issues for isolated file
2. `test_analyze_high_fan_in()` — 11 imports → high_fan_in = True
3. `test_analyze_high_fan_out()` — 16 dependencies → high_fan_out = True
4. `test_analyze_hub_module()` — 9 fan-in + 9 fan-out → is_hub = True
5. `test_analyze_simple_cycle()` — A ↔ B detected
6. `test_find_global_cycles()` — find_cycles() returns all cycles
7. `test_analyze_all_modules()` — Batch analysis returns all modules
8. `test_recommendations_generated()` — High-fan modules get recommendations
9. `test_empty_graph()` — Empty graph → no cycles
10. `test_external_imports_excluded()` — External imports don't count
11. `test_self_import_no_cycle()` — Self-imports handled
12. `test_three_node_cycle()` — A → B → C → A detected
13. `test_all_modules_sorted_by_priority()` — Hub and high-fan modules ranked first

**Property-Based Tests (2, via hypothesis):**
14. `test_threshold_consistency()` — fan_in 0–100 threshold applied correctly
15. `test_hub_detection_property()` — is_hub iff fan_in > 8 AND fan_out > 8

**Subtotal: 15 tests (13 unit + 2 property-based)**

**Coverage (implementation):**
- ✅ Pattern detection (high_fan_in, high_fan_out, is_hub)
- ✅ Cycle detection (simple, three-node, global)
- ✅ Batch analysis and sorting
- ✅ Recommendations generation
- ✅ Edge cases (external imports, self-imports)
- ✅ Property-based threshold validation

---

## Test Categories & GATE Responsibilities

### GATE 4 (TEST-DESIGNER) — 45 Tests Written and Committed

#### Category 1: Unit Tests (40 written, 0 planned)
**Purpose:** Test each component in isolation

**Written tests (40):**
- ImpactAnalyzer: 13 unit tests (graph traversal, risk/confidence scoring, edge cases)
- DebtScorer: 14 unit tests (dimension computation, weighting, batch sorting)
- DependencyHealthAnalyzer: 13 unit tests (pattern detection, cycle finding, recommendations)

**Characteristics:**
- ✅ No external dependencies (mock graphs as dicts/lists)
- ✅ Deterministic inputs → deterministic outputs
- ✅ One method per test (single responsibility)
- ✅ Clear assertions (expected vs actual)
- ✅ All executable and committed

---

#### Category 2: Property-Based Tests (5 written, 0 planned)
**Purpose:** Verify bounds and invariants across many inputs

**Written tests (5):**
- Depth parameter: 1–10 always valid (1 test)
- Coupling/churn scores: Always bounded [0.0, 1.0] (2 tests)
- Threshold consistency: Correctly applied (1 test)
- Hub detection: Correct boolean logic (1 test)

**Characteristics:**
- ✅ Use hypothesis.strategies for input generation
- ✅ Verify invariants (bounds, consistency, properties)
- ✅ Catch off-by-one errors and edge cases
- ✅ ~10 generated test cases per property
- ✅ All executable and committed

---

### GATE 5 (VERIFIER) — 45 Tests to Execute + 24+ Tests to Add

#### Category 3: Integration Tests (0 written, 16+ planned for GATE 5)
**Purpose:** Test components working together

**Planned tests (~16+):**
- ImpactAnalyzer + DebtScorer: Impact + debt for same codebase
- All three components: Full health report pipeline
- Cross-component consistency: Symbiotic dependencies

**Status:** To be written and executed by VERIFIER at GATE 5

**Responsibility:** GATE 5 (VERIFIER) will implement and run these tests

---

#### Category 4: CLI Tests (0 written, 8+ planned for GATE 5)
**Purpose:** Test user-facing commands

**Planned tests (~8+):**
- `ortho analyze --impact <file>` : Returns blast radius
- `ortho analyze --debt` : Returns debt report table
- `ortho analyze --health` : Returns health report
- JSON output format validation
- Error handling (missing files, bad input)

**Status:** To be written and executed by VERIFIER at GATE 5

**Responsibility:** GATE 5 (VERIFIER) will implement and run these tests

---

## Test Execution Plan

### GATE 4 Deliverable (TEST-DESIGNER)
✅ **45 tests written and committed** to:
- `packages/impact-analysis/tests/test_impact_analyzer.py`
- `packages/impact-analysis/tests/test_debt_scorer.py`
- `packages/impact-analysis/tests/test_dependency_health.py`

**Status:** Ready for execution; awaiting GATE 5 (VERIFIER)

---

### GATE 5 Phase A: Import Validation (VERIFIER)
```bash
python -c "import impact_analysis; print('OK')"
```
**Responsibility:** Verify all modules importable  
**Expected:** OK — all components can be imported without errors

---

### GATE 5 Phase B: Pilot Test (VERIFIER)
```bash
pytest packages/impact-analysis/tests/ -v --tb=short -k "test_analyze_simple or test_score_isolated or test_analyze_isolated"
```
**Responsibility:** Run 5-10 sample tests from the 45 written tests  
**Expected:** Sample tests PASS (no import errors, no syntax errors)

---

### GATE 5 Phase C: Full Test Execution (VERIFIER)
```bash
pytest packages/impact-analysis/tests/ -v --tb=short --cov=impact_analysis --cov-report=term-missing
```
**Responsibility:** Execute all 45 written tests and measure coverage  
**Expected:**
- All 45 tests PASS (13+14+13 unit, 1+2+2 property-based)
- Coverage ≥85%
- No test failures

---

### GATE 5 Phase D: Regression Testing (VERIFIER)
```bash
pytest packages/impact-analysis/tests/ -v --cov
pytest  # Full regression (all packages)
```
**Responsibility:** Verify no regressions in other packages  
**Expected:**
- No regressions in repo-intelligence, arch-intelligence, or shared
- Full regression suite passes

---

### GATE 5 Phase E: Integration + CLI Tests (VERIFIER)
**Responsibility:** Implement and execute 16+ integration tests + 8+ CLI tests (planned for GATE 5)  
**Expected:** All new tests pass, coverage maintained ≥85%

---

## Test Data Strategy

### Graph Fixtures
All tests use in-memory graph structures (lists of CallEdge, ImportEdge):
```python
call_graph = [
    CallEdge(caller_id="a", callee_id="b", confidence=1.0),
]
import_graph = [
    ImportEdge(importer_file_id="B", imported_file_id="A"),
]
```

**Advantage:** No file I/O, deterministic, fast

### Sample Graphs (for integration tests, GATE 5)
- Simple chain: A → B → C
- Hub: Central module with many dependencies
- Cycle: A ↔ B or A → B → C → A
- Realistic codebase: Re-use fastapi fixtures from task-007

---

## Coverage Target

**Phase 1 Target:** ≥85% (each component)

**Breakdown (estimated):**
- impact_analyzer.py: 90%+ (BFS, risk, confidence)
- debt_scorer.py: 85%+ (5 dimensions, weighting)
- dependency_health.py: 88%+ (patterns, cycles)
- types.py: 100% (dataclasses, validation)
- __init__.py: 100% (exports)

**Total:** ≥86% (aggregate)

---

## Known Test Limitations

1. **CLI tests deferred:** Will add in GATE 5 (requires apps/cli setup)
2. **Integration tests deferred:** Will add in GATE 5 (multi-component scenarios)
3. **Performance tests:** Not included (O(n) analysis acceptable for Phase 1)
4. **Real repo tests:** Will add in GATE 5 (use fastapi fixtures)

All limitations acceptable for Phase 1.

---

## Test Quality Checklist

- ✅ Each test has one clear assertion (or hypothesis.assert)
- ✅ Test names describe what's being tested
- ✅ No shared state between tests (stateless design)
- ✅ Edge cases covered (empty, cycles, missing data)
- ✅ Property-based tests verify invariants
- ✅ All fixtures in-memory (no file I/O)
- ✅ No sleep, timeouts, or flakiness
- ✅ Can run in any order
- ✅ Fast (no external calls)
- ✅ Deterministic (no randomness)

---

## Test Readiness

### GATE 4 Status: COMPLETE
**Written and Committed (45 tests):**
- ✅ 40 unit tests (13 + 14 + 13 across all components)
- ✅ 5 property-based tests with hypothesis (1 + 2 + 2)
- ✅ All tests follow ASES specifications
- ✅ Tests verify deterministic behavior
- ✅ Edge case coverage (cycles, empty graphs, missing data)
- ✅ All tests executable, awaiting pytest execution

### GATE 5 Responsibilities
**To be executed by VERIFIER:**
- ⏳ Phase A: Import validation
- ⏳ Phase B: Pilot test (5-10 sample tests from written 45)
- ⏳ Phase C: Full execution of all 45 tests with coverage report
- ⏳ Phase D: Regression testing (all packages)
- ⏳ Phase E: Integration tests (16+, to be written)
- ⏳ Phase E: CLI tests (8+, to be written)

---

## GATE 4 Status: APPROVED FOR SUBMISSION

✅ **45 tests written and committed** by TEST-DESIGNER (concurrent with BUILDER per ASES best practice)

**Authoritative counts:**
- Unit tests written: 40 (implemented in test files)
- Property-based tests written: 5 (using hypothesis)
- Integration tests planned: 16+ (for GATE 5)
- CLI tests planned: 8+ (for GATE 5)
- **GATE 4 total: 45 tests, all executable**

**Handoff to GATE 5 (VERIFIER):**
All 45 tests are:
- ✅ Written and committed
- ✅ Deterministic and repeatable
- ✅ Ready for pytest execution
- ✅ Awaiting GATE 5 for runtime verification

Expected GATE 5 results:
- ✅ All 45 tests pass
- ✅ No import errors
- ✅ Coverage ≥85%
- ✅ No regressions in existing packages

**GATE 5 will add:** Integration tests (~16+) and CLI tests (~8+) for total ≥69 tests

---

*Created by TEST-DESIGNER, 2026-07-02*  
*Concurrent with BUILDER (GATE 3 and GATE 4 ran in parallel per ASES)*  
*All 45 tests committed and ready for GATE 5 (VERIFIER) execution*
