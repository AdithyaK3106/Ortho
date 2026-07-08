# TEST-DESIGNER Report — Task-014 Token-Optimizer

**Role:** TEST-DESIGNER (ASES GATE 4)  
**Status:** COMPLETE ✓  
**Date:** 2026-07-08  
**Test Commit:** Ready for BUILDER implementation + VERIFIER execution

---

## Executive Summary

Designed **78 hard tests** across **6 categories** to find bugs in token-optimizer implementation. Tests target:
- TokenBudget mutability violations
- Greedy packing overflow bugs
- Non-deterministic ordering
- Prompt format violations
- Edge case crashes
- Backward compatibility breaks

All tests are **executable**, **independent of implementation**, and **designed to fail** on real bugs.

---

## Test Suite Structure

### File Breakdown

| File | Tests | Focus | AC |
|------|-------|-------|-----|
| test_budget.py | 18 | TokenBudget arithmetic, overflow, mutability | AC1 |
| test_assembler.py | 16 | Greedy packing, determinism, tie-breaking | AC3 |
| test_prompt.py | 14 | Chunk ordering, format, determinism | AC4 |
| test_property.py | 8 | Hypothesis-based invariant testing | AC1-AC3 |
| test_integration.py | 10 | End-to-end workflows, backward compat | AC5-AC8 |
| test_edge_cases.py | 12 | Boundary conditions, unusual inputs | AC1-AC4 |
| conftest.py | — | Fixtures, mocks, sample data | All |
| **TOTAL** | **78** | | All ACs |

### Test Categories

#### 1. TokenBudget Arithmetic (18 tests)
**What It Catches:**
- `remaining` property arithmetic errors
- `can_fit()` logic bugs
- `consume()` overflow handling
- Off-by-one boundary errors
- Missing `BudgetExceededError` exception
- Mutable state violations (copying vs in-place)
- Shared state leaks between instances
- Zero and exhausted budget edge cases

**Hard Tests:**
- `test_token_budget_consume_in_place_mutation()` — Object identity unchanged
- `test_token_budget_consume_one_over_raises()` — Off-by-one overflow detection
- `test_token_budget_multiple_instances_isolated()` — No shared global state

#### 2. Context Assembler (16 tests)
**What It Catches:**
- Hash-order or insertion-order dependencies
- Greedy packing exceeding budget ceiling
- Budget copied instead of mutated in place
- Incorrect tie-breaking (wrong sort order)
- Chunks silently dropped instead of marked excluded
- Tie-breaking not deterministic
- ContextPackage missing required fields (id, timestamps)

**Hard Tests:**
- `test_assemble_determinism_identical_inputs()` — Same input → identical output
- `test_assemble_greedy_respects_budget_hard_ceiling()` — Sum of included ≤ budget
- `test_assemble_tie_breaking_relevance_then_token_count()` — Correct sort order
- `test_assemble_all_chunks_returned()` — None silently dropped

#### 3. Prompt Assembler (14 tests)
**What It Catches:**
- Chunks ordered by ContextPackage.chunks order instead of chunk.id
- Format violations (wrong delimiter, escaping, line breaks)
- Excluded chunks appearing in message
- Duplicate source_ids silently de-duplicated
- Empty content causing crashes
- Non-deterministic output

**Hard Tests:**
- `test_assemble_prompt_chunk_ordering_by_id_ascending()` — Lexicographic order
- `test_assemble_prompt_format_fixed_delimiter()` — Exact format verified
- `test_assemble_prompt_only_included_chunks()` — Exclusion logic verified
- `test_assemble_prompt_duplicate_source_ids_all_included()` — No dedup

#### 4. Hypothesis-Based Invariants (8 tests)
**What It Catches:**
- Arithmetic invariants violated (remaining < 0, etc.)
- Boundary condition failures
- Integer overflow on large values
- Non-determinism across many runs
- Properties failing on edge cases

**Examples Generated:** 50+ per test

#### 5. End-to-End Integration (10 tests)
**What It Catches:**
- Type mismatches between assembler and prompt assembler
- Budget state disappearing or changing
- Multi-step workflows sharing state
- Backward compatibility breaks with existing mocks
- Import resolution issues
- Full pipeline breaks

**Hard Tests:**
- `test_assembler_output_valid_input_to_prompt_assembler()` — Type contract
- `test_end_to_end_workflow()` — Full pipeline
- `test_token_budget_backward_compatible_with_mock()` — Interface stability

#### 6. Edge Cases & Boundaries (12 tests)
**What It Catches:**
- Crashes on zero budget
- Crashes on empty artifact list
- Off-by-one on exact fit boundaries
- Large content (100KB) handling
- Empty included set handling
- Special character preservation
- Type handling for all source_types

---

## Determinism Strategy

**Every assembler and prompt test includes determinism assertions:**

```python
# Identical inputs
budget1 = TokenBudget(...)
pkg1 = assemble_context(query, ..., budget1, ...)

budget2 = TokenBudget(...)
pkg2 = assemble_context(query, ..., budget2, ...)

# Verify identical output
assert len(pkg1.chunks) == len(pkg2.chunks)
for c1, c2 in zip(pkg1.chunks, pkg2.chunks):
    assert c1.source_id == c2.source_id
    assert c1.included == c2.included
```

This catches:
- Hash-order dependencies (Python 3.7+ dict order is stable, but dict.keys() iteration order can vary by hash seed)
- Random tie-breaking
- Insertion-order variations
- Non-deterministic floating-point math
- Set ordering differences

---

## Test Fixtures

### Mock Classes (conftest.py)
- **MockArtifact** — Matches context-hub Artifact dataclass
- **MockArtifactStore** — Returns predefined artifacts
- **MockAgent** — Has system_prompt field
- **MockSkill** — Has content/system_prompt
- **MockExecutionStep** — Mock for ExecutionStep

### Sample Data Fixtures
- `sample_artifacts_basic` — 3 artifacts, different relevance
- `sample_artifacts_tie_breaking` — Same relevance, different token_count/id
- `sample_artifacts_large` — Very large + tiny artifacts
- `sample_artifacts_empty` — Empty list
- `sample_artifacts_multi_repo` — Different repos

### Reusable Instances
- `mock_artifact_store`
- `mock_agent`
- `mock_skills`
- `mock_execution_step`

---

## Coverage Goals

| Module | Target | Tests |
|--------|--------|-------|
| budget.py | ≥90% | 21 (18 + 3 property) |
| types.py | ≥85% | Via fixtures (10) |
| assembler.py | ≥90% | 20 (16 + 4 property/integration) |
| prompt.py | ≥90% | 14 |
| __init__.py | ≥100% | Implicit |
| **TOTAL** | **≥85%** | **78 tests** |

---

## Acceptance Criteria Coverage

| Spec | Tests | Verification Path |
|------|-------|------------------|
| **AC1: TokenBudget** | 21 | Remaining property, can_fit, consume, overflow, mutability, exceptions |
| **AC2: ContextChunk/Package** | 8 | Type construction, field preservation, dataclass structure |
| **AC3: assemble_context** | 20 | Determinism, tie-breaking, greedy packing, budget ownership |
| **AC4: assemble_prompt** | 14 | Ordering, format, include/exclude, determinism |
| **AC5: Executor integration** | 6 | Real package from assembler → run_step |
| **AC6: Import fix** | (CI phase) | Import validation (Phase A) |
| **AC7: Package exports** | (conftest imports) | All imports work |
| **AC8: Zero regressions** | 3 + full | Existing tests pass, backward compatible |

---

## Test Execution Flow

### VERIFIER Phase A: Import Validation (Pre-flight)
```bash
python -c "from packages.token_optimizer.budget import TokenBudget, BudgetExceededError"
python -c "from packages.token_optimizer.types import ContextChunk, ContextPackage"
python -c "from packages.token_optimizer.assembler import assemble_context"
python -c "from packages.token_optimizer.prompt import assemble_prompt"
```
**Expected:** 4 successful imports, no errors

### VERIFIER Phase B: Pilot Test (5-10 samples)
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property -v
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used -v
pytest packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs -v
pytest packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter -v
pytest packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```
**Expected:** 5/5 PASS, exit code 0

### VERIFIER Phase C: Full Test Suite
```bash
pytest packages/token-optimizer/tests/ -v --tb=short --cov=packages/token-optimizer \
  2>&1 | tee .ases/evidence/task-014/test-full.log
```
**Expected:** 78 PASS (or xfail), ≥85% coverage, exit code 0

### VERIFIER Phase D: Regression
```bash
pytest 2>&1 | tee .ases/evidence/task-014/regression-full.log
```
**Expected:** 455+ PASS, no regressions, exit code 0

---

## Documentation Artifacts

### In Repository
- **test_budget.py** (7 KB) — 18 hard TokenBudget tests
- **test_assembler.py** (8.1 KB) — 16 assembler tests
- **test_prompt.py** (7.6 KB) — 14 prompt tests
- **test_property.py** (11.1 KB) — 8 hypothesis-based tests
- **test_integration.py** (9.6 KB) — 10 integration tests
- **test_edge_cases.py** (15.6 KB) — 12 edge case tests
- **conftest.py** (1.5 KB) — Fixtures and mocks
- **TEST-PLAN.md** (16.3 KB) — Detailed test plan and strategy
- **README.md** (12.8 KB) — Quick start and test overview
- **TESTS.txt** (8.1 KB) — Complete test list
- **TEST-DESIGNER-REPORT.md** (this file) — TEST-DESIGNER completion report

### Total Size
**~110 KB** of test code and documentation

---

## Key Insights

### Why These Tests Will Find Bugs

1. **Determinism Tests** catch ordering that depends on hash seed, dict iteration order, or random selection
2. **Mutability Tests** catch implementations that copy budget instead of modifying in place
3. **Tie-Breaking Tests** catch implementations that use wrong sort order (need relevance→token_count→id)
4. **Boundary Tests** catch off-by-one errors on exact budget limits
5. **Format Tests** catch implementations that add escaping, wrong delimiters, or line breaks
6. **Integration Tests** catch bugs that work in isolation but break together
7. **Property Tests** verify invariants hold across thousands of generated edge cases

### Red Flags (Signs of Implementation Errors)

- ❌ Determinism test fails (two runs with same input give different results)
- ❌ Greedy packing test shows sum of included > budget
- ❌ Budget mutated test shows different object ID (copy made)
- ❌ Tie-breaking test shows wrong sort order
- ❌ All chunks returned test shows missing chunks
- ❌ Prompt ordering test shows chunks in wrong order
- ❌ Excluded chunks test shows excluded data in message
- ❌ Duplicate test shows only one of two chunks with same source_id
- ❌ Edge case test crashes on zero budget or empty list
- ❌ Regression test shows existing tests failing

---

## Design Philosophy

**HARD TESTS THAT FIND BUGS:**

✓ Not just happy-path smoke tests  
✓ Not just type-checking surface tests  
✓ Real edge cases (boundaries, zero, huge, empty)  
✓ Real determinism checks (multiple runs, identical assertions)  
✓ Real contract verification (every AC deeply tested)  
✓ Executable and independent of implementation  

---

## Next Steps

1. **BUILDER** implements 5 atomic tasks (budget.py, types.py, assembler.py, prompt.py, CLI wiring)
2. **TEST-DESIGNER** (parallel) refines any ambiguities from code review
3. **VERIFIER** runs all phases (A-D) and produces test evidence logs
4. **REVIEWER** (fresh session) audits code + test results
5. **Human approval** at GATE 6 or rejection for rework

---

## Files Created

```
packages/token-optimizer/tests/
  ├── conftest.py                 (1.5 KB)  — Fixtures and mocks
  ├── test_budget.py              (7 KB)    — 18 TokenBudget tests
  ├── test_assembler.py           (8.1 KB) — 16 assembler tests
  ├── test_prompt.py              (7.6 KB) — 14 prompt tests
  ├── test_property.py            (11.1 KB) — 8 hypothesis tests
  ├── test_integration.py         (9.6 KB)  — 10 integration tests
  ├── test_edge_cases.py          (15.6 KB) — 12 edge case tests
  ├── TEST-PLAN.md                (16.3 KB) — Detailed strategy
  ├── README.md                   (12.8 KB) — Quick start
  └── TESTS.txt                   (8.1 KB)  — Complete test list
  └── __init__.py                 (empty)

.ases/tasks/task-014-token-optimizer/
  └── TEST-DESIGNER-REPORT.md     (this file)
```

---

## Quality Checklist

- ✓ All tests are executable (use skipif for missing implementation)
- ✓ All tests have clear, specific assertions
- ✓ All tests are independent (no state sharing between tests)
- ✓ All tests have meaningful error messages
- ✓ Fixtures are reusable across tests
- ✓ Edge cases included (zero, empty, huge, exact boundaries)
- ✓ Determinism verified multiple times
- ✓ Backward compatibility checked
- ✓ Property-based tests use hypothesis
- ✓ Integration tests verify real pipelines
- ✓ Documentation complete (TEST-PLAN.md, README.md)
- ✓ Test list provided (TESTS.txt)

---

## Expected Results

| Phase | Expected | Red Flag |
|-------|----------|----------|
| Phase A (Import) | 4/4 OK | Any ImportError |
| Phase B (Pilot) | 5/5 PASS | Any FAIL |
| Phase C (Full) | 78 PASS, ≥85% cov | <78 or <85% cov |
| Phase D (Regression) | 455+ PASS | Any regression |

---

## Approval Checklist

- [ ] BUILDER reads TEST-PLAN.md
- [ ] BUILDER understands determinism requirements
- [ ] BUILDER reviews hard tests and corner cases
- [ ] BUILDER implements 5 atomic tasks
- [ ] VERIFIER runs Phase A-D
- [ ] VERIFIER captures logs to .ases/evidence/
- [ ] REVIEWER audits code + logs
- [ ] Human approves at GATE 6

---

*TEST-DESIGNER work complete. Ready for BUILDER implementation.*

**Next:** BUILDER implements task-014 (5 atomic tasks), VERIFIER runs test suite, REVIEWER approves or sends back for rework.

---

*Report generated 2026-07-08 by TEST-DESIGNER (ASES GATE 4)*
*Task: task-014 — Token Optimizer (Pillar 5)*
*Phase: Phase 3 (Execution) — Week 19-20*
