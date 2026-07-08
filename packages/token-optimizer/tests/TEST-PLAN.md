# Test Plan: Token-Optimizer (task-014)

**Target:** 40+ hard tests designed to FIND BUGS in token-optimizer implementation  
**Coverage Goal:** ≥85%  
**Pass Rate Target:** 100% (0 failing tests, or acceptable failures marked `@pytest.mark.xfail`)

---

## Test Files & Categories

### 1. test_budget.py (18 tests)
**Focus:** `TokenBudget` arithmetic, overflow, mutable state, boundary conditions.

**What It Catches:**
- Off-by-one errors on budget consumption
- Mutability violations (copying instead of in-place mutation)
- Missing `BudgetExceededError` exception handling
- Incorrect `remaining` property arithmetic
- Shared state leaks between budget instances
- Negative token consumption attacks
- Zero budget edge cases

**Hard Tests:**
- `test_token_budget_consume_in_place_mutation()` — Verifies budget object identity unchanged
- `test_token_budget_consume_exact_boundary()` — Consumes exactly to remaining=0
- `test_token_budget_consume_one_over_raises()` — Off-by-one overflow detection
- `test_token_budget_multiple_instances_isolated()` — No shared state between budgets
- `test_token_budget_zero_total()` — Edge case: zero-capacity budget

**Acceptance Criteria Verified:**
- AC1 (TokenBudget exists with correct fields and methods)
- AC1 (consume raises BudgetExceededError on overflow)
- AC1 (mutable state: used incremented in place)

---

### 2. test_assembler.py (16 tests)
**Focus:** Greedy packing algorithm, determinism, tie-breaking, budget ownership.

**What It Catches:**
- Non-deterministic ordering (hash-order, insertion-order dependencies)
- Greedy packing exceeds budget
- Incorrect tie-breaking algorithm
- Budget not mutated in place
- Chunks silently dropped (not returned)
- Wrong chunk conversion (token_count incorrect)
- ContextPackage contract violations

**Hard Tests:**
- `test_assemble_determinism_identical_inputs()` — Same input → identical output across runs
- `test_assemble_budget_mutated_in_place()` — Budget instance modified, not copied
- `test_assemble_greedy_respects_budget_hard_ceiling()` — Sum of included tokens ≤ budget
- `test_assemble_tie_breaking_relevance_then_token_count()` — Secondary sort by token_count asc
- `test_assemble_all_chunks_returned_not_silently_dropped()` — All chunks present (included=False if excluded)
- `test_assemble_package_has_uuid_id()` — ContextPackage.id is UUID
- `test_assemble_chunk_source_type_is_artifact()` — Chunks correctly labeled

**Acceptance Criteria Verified:**
- AC3 (assemble_context function exists with correct signature)
- AC3 (deterministic output for identical inputs)
- AC3 (tie-breaking: relevance desc → token_count asc → artifact.id asc)
- AC3 (budget mutated in place, reference returned in package)
- AC3 (greedy algorithm respects hard ceiling)
- AC3 (all chunks returned with included/excluded status)

---

### 3. test_prompt.py (14 tests)
**Focus:** Prompt assembly ordering, format, deduplication handling, determinism.

**What It Catches:**
- Non-deterministic chunk ordering
- Format violations (wrong delimiter, escaping)
- Duplicate source_ids silently removed (should keep all)
- Only excluded chunks appear (should be excluded ones)
- Chunk order depends on ContextPackage.chunks order (should be deterministic by chunk.id)
- Empty content crashes or formats incorrectly
- Special characters escaped or lost

**Hard Tests:**
- `test_assemble_prompt_chunk_ordering_by_id_ascending()` — Chunks sorted by chunk.id asc
- `test_assemble_prompt_ordering_independent_of_package_order()` — Output deterministic regardless of input order
- `test_assemble_prompt_format_fixed_delimiter()` — Exact format: `\n\n--- [{source_type}:{source_id}] ---\n{content}\n`
- `test_assemble_prompt_only_included_chunks()` — Only included=True chunks in message
- `test_assemble_prompt_duplicate_source_ids_all_included()` — Multiple chunks with same source_id kept (no dedup)
- `test_assemble_prompt_determinism_identical_inputs()` — Same input → identical prompt text
- `test_assemble_prompt_empty_included_set()` — No included chunks → empty string

**Acceptance Criteria Verified:**
- AC4 (assemble_prompt function exists)
- AC4 (deterministic output for identical input)
- AC4 (chunks ordered by chunk.id ascending)
- AC4 (only included=True chunks in user message)
- AC4 (fixed format: triple-dash delimiter, no escaping)
- AC4 (duplicates not de-duplicated)

---

### 4. test_property.py (8 tests)
**Focus:** Hypothesis-based invariant testing for determinism and correctness.

**What It Catches:**
- Arithmetic overflows in budget math
- Non-deterministic behavior with random inputs
- Invariant violations (e.g., remaining can't be negative)
- Boundary condition failures with extreme values

**Property Tests:**
- `test_remaining_always_nonnegative()` — remaining ≥ 0 for all valid budgets
- `test_remaining_equals_total_minus_used()` — remaining == total - used (arithmetic invariant)
- `test_consume_increments_used_correctly()` — sum of consumed == final used
- `test_can_fit_matches_consume_success()` — can_fit(n) == True iff consume(n) succeeds
- `test_consume_exact_remaining_succeeds()` — consume(remaining) always works
- `test_consume_remaining_plus_one_fails()` — consume(remaining + 1) always fails

**Generated Examples:** 50+ per property (hypothesis-driven)

**Acceptance Criteria Verified:**
- AC1 (TokenBudget arithmetic properties hold across all valid inputs)
- AC3 (assembler greedy packing respects invariant: sum ≤ budget.total)

---

### 5. test_integration.py (10 tests)
**Focus:** End-to-end workflows: assembler → prompt assembly, multi-step scenarios, error paths.

**What It Catches:**
- Assembler output invalid for prompt assembler (type mismatches, missing fields)
- Budget state not visible after assembly
- Multi-step workflows share state incorrectly
- Backward compatibility with existing mocks broken

**Integration Tests:**
- `test_assembler_output_valid_input_to_prompt_assembler()` — assemble_context output feeds into assemble_prompt
- `test_end_to_end_workflow()` — Full pipeline: query → context package → prompt strings
- `test_multiple_steps_with_fresh_budget()` — Sequential steps with independent budgets
- `test_included_chunks_appear_in_prompt()` — Chunks marked included=True visible in prompt
- `test_excluded_chunks_not_in_prompt()` — Chunks marked included=False NOT in prompt
- `test_budget_state_visible_after_assembly()` — Budget inspectable, same object as pkg.budget
- `test_token_budget_backward_compatible_with_mock()` — Compatible with existing test mock
- `test_budget_exceeded_during_assembly()` — Graceful handling of budget exhaustion
- `test_empty_artifact_set_handles_gracefully()` — Empty search results don't crash
- AC5 integration: WorkflowExecutor calls assemble_context + run_step calls assemble_prompt

**Acceptance Criteria Verified:**
- AC5 (WorkflowExecutor integration stub replaced with real assembler call)
- AC8 (zero regressions: existing tests still pass, backward compatible)

---

### 6. test_edge_cases.py (12 tests)
**Focus:** Boundary conditions, concurrency hints, unusual-but-valid inputs.

**What It Catches:**
- Edge case panics (crashes on zero budget, empty list, huge values)
- Isolation violations (shared state between tests)
- Concurrency bugs (if implementation ignores thread-safety disclaimer)
- Type handling errors (invalid timestamps, wrong source_type)

**Edge Cases:**
- `test_budget_zero_total()` — Zero-capacity budget
- `test_budget_created_exhausted()` — used == total on creation
- `test_budget_huge_values()` — 1 trillion tokens
- `test_assemble_empty_search_results()` — Empty artifact list
- `test_assemble_zero_budget()` — Budget.total=0
- `test_assemble_single_chunk_exactly_fits()` — Chunk tokens == budget
- `test_assemble_single_chunk_exceeds_budget()` — Chunk tokens > budget
- `test_prompt_no_included_chunks()` → empty message
- `test_prompt_chunk_with_empty_content()` → formats anyway
- `test_prompt_very_large_content()` → no truncation by assembler (100KB content)
- `test_context_chunk_all_source_types()` — symbol, artifact, git, architecture
- `test_budget_no_thread_safety_guarantee()` — Documents concurrency non-guarantees

**Acceptance Criteria Verified:**
- AC8 (no crashes on edge cases)
- Implementation-notes.md guidance: "no thread safety; caller manages lifecycle"

---

## Test Execution Strategy

### Phase A: Import Validation (Pre-flight)
```bash
python -c "from packages.token_optimizer.budget import TokenBudget, BudgetExceededError; print('OK')"
python -c "from packages.token_optimizer.types import ContextChunk, ContextPackage; print('OK')"
python -c "from packages.token_optimizer.assembler import assemble_context; print('OK')"
python -c "from packages.token_optimizer.prompt import assemble_prompt; print('OK')"
```

**Expected:** 4 successful imports, no ImportError or circular dependencies.

### Phase B: Pilot Test (Sample 5-10 tests)
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property -v
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used -v
pytest packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs -v
pytest packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter -v
pytest packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```

**Expected:** ≥5/5 PASS (exit code 0). If any fail, VERIFIER stops and reports to BUILDER/TEST-DESIGNER.

### Phase C: Full Test Suite
```bash
pytest packages/token-optimizer/tests/ -v --tb=short --cov=packages/token-optimizer 2>&1 | \
  tee .ases/evidence/task-014/test-full.log
```

**Expected:**
- 40+ tests
- ≥85% code coverage
- 100% pass rate (or acceptable xfail markers with documented reasons)
- Exit code 0

### Phase D: Full Regression
```bash
pytest 2>&1 | tee .ases/evidence/task-014/regression-full.log
```

**Expected:**
- All existing tests in orchestration (27+ selector, 10+ executor, 5+ evidence) still pass
- All existing tests in context-hub (54+) still pass
- All existing tests in other packages unchanged
- Total: 455+ passing tests remain passing
- Exit code 0

---

## Test Fixtures (conftest.py)

### Mock Classes
- **MockArtifact:** Dataclass matching context-hub's Artifact (id, content, estimated_tokens, relevance_score)
- **MockArtifactStore:** Returns predefined artifacts on search()
- **MockAgent:** Has system_prompt field
- **MockSkill:** Has content and system_prompt fields
- **MockExecutionStep:** Mock for ExecutionStep (step_id, agent_name, workflow_run_id)

### Sample Data Fixtures
- `sample_artifacts_basic`: 3 artifacts with different relevance scores
- `sample_artifacts_tie_breaking`: Artifacts with identical relevance (tests sorting by token_count, then id)
- `sample_artifacts_large`: Mix of very large (5000 tokens) and tiny (1 token) artifacts
- `sample_artifacts_empty`: Empty list
- `sample_artifacts_multi_repo`: Artifacts from different repos

### Mock Instances
- `mock_artifact_store`: Store with sample_artifacts_basic
- `mock_agent`: Basic mock agent
- `mock_skills`: List of 2 mock skills
- `mock_execution_step`: Basic mock step

---

## Determinism Verification Strategy

Every test that exercises `assemble_context` or `assemble_prompt` includes a **determinism assertion**:

```python
# Same input, two runs
pkg1 = assemble_context(query, repo_id, store, budget1, step_id, workflow_run_id)
pkg2 = assemble_context(query, repo_id, store, budget2, step_id, workflow_run_id)

# Verify identical output
assert len(pkg1.chunks) == len(pkg2.chunks)
for c1, c2 in zip(pkg1.chunks, pkg2.chunks):
    assert c1.source_id == c2.source_id
    assert c1.included == c2.included
    assert c1.token_count == c2.token_count
```

This catches:
- Hash-order dependencies (dict iteration)
- Random tie-breaking
- Insertion-order variations
- Non-deterministic floating-point arithmetic

---

## Coverage Goals

| Module | Expected Coverage | Hard Tests Targeting |
|--------|-------------------|----------------------|
| `budget.py` | ≥90% | test_budget.py (18 tests) |
| `types.py` | ≥85% | test_assembler.py + test_prompt.py (via fixtures) |
| `assembler.py` | ≥90% | test_assembler.py (16 tests) |
| `prompt.py` | ≥90% | test_prompt.py (14 tests) |
| `__init__.py` | ≥100% | Implicit (imports) |

**Total:** 40+ tests, ≥85% package-level coverage

---

## Known Acceptable Failures (if any)

None at this stage. All tests are designed to pass when implementation is correct.

If any real bugs are discovered during VERIFIER run:
1. Mark failing test with `@pytest.mark.xfail(reason="...")`
2. Document in implementation-notes.md as "Known Limitation"
3. BUILDER fixes the bug
4. Remove xfail marker
5. Re-run VERIFIER

---

## Sample Test Output Format

```
packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property PASSED
packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used PASSED
packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_in_place_mutation PASSED
packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs PASSED
packages/token-optimizer/tests/test_assembler.py::test_assemble_budget_mutated_in_place PASSED
packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_chunk_ordering_by_id_ascending PASSED
packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter PASSED
packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative[100-50] PASSED
packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative[200-150] PASSED
packages/token-optimizer/tests/test_integration.py::test_assembler_output_valid_input_to_prompt_assembler PASSED
packages/token-optimizer/tests/test_edge_cases.py::test_budget_zero_total PASSED

======================== 40+ passed in 1.23s ========================
```

---

## How to Run Tests

### Single Test
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_in_place_mutation -v
```

### Single File
```bash
pytest packages/token-optimizer/tests/test_budget.py -v
```

### All Tests with Coverage
```bash
pytest packages/token-optimizer/tests/ -v --cov=packages/token-optimizer --cov-report=term-missing
```

### Quick Smoke Test (first 5 tests)
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property -v
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_can_fit_positive -v
pytest packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs -v
pytest packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter -v
pytest packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```

---

## Relationship to Specification

| Spec Section | Tests | Verification |
|--------------|-------|--------------|
| AC1: TokenBudget | test_budget.py (18) | Fields, properties, methods, exceptions, mutability |
| AC2: ContextChunk/Package | test_assembler.py, test_prompt.py (10) | Types, fields, dataclass structure |
| AC3: assemble_context | test_assembler.py (16), test_property.py (4) | Determinism, greedy packing, tie-breaking, budget ownership |
| AC4: assemble_prompt | test_prompt.py (14) | Ordering, format, include/exclude, determinism |
| AC5: WorkflowExecutor integration | test_integration.py (6) | Real package passed to run_step |
| AC6: Broken import fixed | (CI/lint phase, not test phase) | Import resolution check |
| AC7: Package exports | (conftest.py imports) | Module exports accessible |
| AC8: Zero regressions | test_integration.py (3), full pytest run | Existing tests unchanged |

---

## Test Design Principles

1. **Find Bugs, Not Just Pass:** Every test is designed to expose a real implementation mistake (off-by-one, mutability violation, tie-breaking bug, etc.)

2. **Determinism First:** Multiple identical runs with determinism assertions in every assembler/prompt test.

3. **Boundary Testing:** Edge cases (zero budget, empty set, huge values, exact boundaries) are core, not afterthoughts.

4. **Mutable State Verification:** Budget mutability is explicitly tested (object identity, in-place changes).

5. **Contract Enforcement:** Every test verifies a spec commitment (AC1-AC8).

6. **No Fabrication:** All tests are real, executable, not simulated or hand-wavy.

---

*Test plan version 1.0 — ready for BUILDER implementation + VERIFIER execution*
