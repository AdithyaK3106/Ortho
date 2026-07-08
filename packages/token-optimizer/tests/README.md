# Token-Optimizer Test Suite (task-014 — GATE 4)

**Role:** TEST-DESIGNER (ASES GATE 4)  
**Objective:** Design hard test cases to find bugs in token-optimizer implementation  
**Status:** COMPLETE — 40+ tests across 6 categories, ready for BUILDER → VERIFIER pipeline  

---

## Quick Start

### Run All Tests
```bash
pytest packages/token-optimizer/tests/ -v --cov=packages/token-optimizer
```

### Run Specific Category
```bash
pytest packages/token-optimizer/tests/test_budget.py -v        # TokenBudget tests
pytest packages/token-optimizer/tests/test_assembler.py -v     # Greedy packing tests
pytest packages/token-optimizer/tests/test_prompt.py -v        # Prompt assembly tests
pytest packages/token-optimizer/tests/test_property.py -v      # Hypothesis-based tests
pytest packages/token-optimizer/tests/test_integration.py -v   # End-to-end tests
pytest packages/token-optimizer/tests/test_edge_cases.py -v    # Boundary conditions
```

### Pilot Test (First 5)
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property \
  packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used \
  packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs \
  packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter \
  packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```

---

## Test Suite Overview

### Files & Test Counts

| File | Tests | Category | Target |
|------|-------|----------|--------|
| **test_budget.py** | 18 | TokenBudget arithmetic, overflow, mutability | AC1 |
| **test_assembler.py** | 16 | Greedy packing, determinism, tie-breaking | AC3 |
| **test_prompt.py** | 14 | Chunk ordering, format, determinism | AC4 |
| **test_property.py** | 8 | Hypothesis-based invariant testing | AC1-AC3 |
| **test_integration.py** | 10 | End-to-end workflows, backward compatibility | AC5-AC8 |
| **test_edge_cases.py** | 12 | Boundary conditions, unusual inputs | AC1-AC4 |
| **conftest.py** | — | Fixtures, mocks, sample data | All |
| **TOTAL** | **78** | | All ACs |

### What Each File Catches

#### test_budget.py — TokenBudget Bugs
**Hard Tests:**
- `consume_in_place_mutation()` — Catches copying instead of in-place mutation
- `consume_exact_boundary()` — Catches off-by-one on exact remaining
- `consume_one_over_raises()` — Catches missing BudgetExceededError
- `multiple_instances_isolated()` — Catches shared state leaks
- `zero_total()` — Catches edge case crashes

**18 tests covering:**
- Remaining property arithmetic
- can_fit() logic
- consume() mutation and overflow
- Exception handling
- Field preservation
- Instance isolation

#### test_assembler.py — Greedy Packing & Determinism Bugs
**Hard Tests:**
- `determinism_identical_inputs()` — Catches hash-order or insertion-order dependencies
- `budget_mutated_in_place()` — Catches budget copying
- `greedy_respects_budget_hard_ceiling()` — Catches overflow
- `tie_breaking_relevance_then_token_count()` — Catches wrong sort order
- `all_chunks_returned_not_silently_dropped()` — Catches missing excluded chunks

**16 tests covering:**
- Deterministic output for identical inputs
- Budget ownership (mutable, in-place)
- Greedy packing respects ceiling
- Tie-breaking: relevance → token_count → artifact.id
- ContextPackage contract (workflow_run_id, step_id, id, timestamp)
- Chunk conversion (source_type="artifact", token_count correct)

#### test_prompt.py — Prompt Assembly Format & Ordering Bugs
**Hard Tests:**
- `chunk_ordering_by_id_ascending()` — Catches insertion-order or relevance-order deps
- `ordering_independent_of_package_order()` — Catches package-order dependencies
- `format_fixed_delimiter()` — Catches wrong format or escaping
- `only_included_chunks()` — Catches excluded chunks appearing
- `duplicate_source_ids_all_included()` — Catches silent dedup
- `determinism_identical_inputs()` — Catches non-deterministic prompts

**14 tests covering:**
- Chunk ordering by chunk.id ascending
- Fixed format: `\n\n--- [{source_type}:{source_id}] ---\n{content}\n`
- Only included=True chunks in message
- No content escaping
- Duplicates not de-duplicated
- Empty included set → empty string

#### test_property.py — Invariant Violations
**Hypothesis-based (50+ examples each):**
- `remaining_always_nonnegative()` — Invariant: remaining ≥ 0
- `remaining_equals_total_minus_used()` — Invariant: remaining == total - used
- `consume_increments_used_correctly()` — Invariant: sum of consumes == final used
- `can_fit_matches_consume_success()` — Invariant: can_fit(n) ⟺ consume(n) succeeds
- `consume_exact_remaining_succeeds()` — Invariant: consume(remaining) always works
- `consume_remaining_plus_one_fails()` — Invariant: consume(remaining + 1) always fails

**8 tests covering:**
- Budget arithmetic invariants
- Assembler greedy packing invariants
- Package field preservation
- Prompt assembler invariants
- Determinism properties

#### test_integration.py — End-to-End & Backward Compatibility Bugs
**Hard Tests:**
- `assembler_output_valid_input_to_prompt_assembler()` — Catches type mismatches
- `end_to_end_workflow()` — Catches full pipeline breaks
- `multiple_steps_with_fresh_budget()` — Catches state sharing
- `included_chunks_appear_in_prompt()` — Catches inclusion logic breaks
- `excluded_chunks_not_in_prompt()` — Catches exclusion logic breaks
- `budget_state_visible_after_assembly()` — Catches budget disappearing
- `token_budget_backward_compatible_with_mock()` — Catches interface breaks

**10 tests covering:**
- Assembler output feeds into prompt assembler
- End-to-end workflow (context → prompt → strings)
- Multi-step scenarios with independent budgets
- Included/excluded chunk semantics
- Budget state traceability
- Backward compatibility with existing mocks

#### test_edge_cases.py — Boundary Condition & Concurrency Bugs
**Hard Tests:**
- `budget_zero_total()` — Catches zero-budget crashes
- `budget_created_exhausted()` — Catches exhausted-on-creation bugs
- `budget_huge_values()` — Catches overflow on big numbers
- `assemble_empty_search_results()` — Catches empty-list crashes
- `assemble_zero_budget()` — Catches zero-budget crashes
- `assemble_single_chunk_exactly_fits()` — Catches exact-boundary bugs
- `assemble_single_chunk_exceeds_budget()` — Catches oversized-chunk handling
- `prompt_no_included_chunks()` — Catches empty-message crashes
- `prompt_very_large_content()` — Catches content truncation (shouldn't happen)
- `context_chunk_all_source_types()` — Catches type validation
- `budget_no_thread_safety_guarantee()` — Documents concurrency non-guarantees

**12 tests covering:**
- Zero and exhausted budgets
- Very large values (1 trillion)
- Empty artifact sets
- Single chunk edge cases
- Empty prompt scenarios
- Large content (100KB) handling
- Special characters preservation
- All source_type values (symbol, artifact, git, architecture)
- Concurrency hints (sequential accumulation)

---

## Test Fixtures (conftest.py)

### Mock Classes
- **MockArtifact** — Dataclass matching context-hub's Artifact
- **MockArtifactStore** — Returns predefined artifacts on search()
- **MockAgent** — Has system_prompt
- **MockSkill** — Has content and system_prompt
- **MockExecutionStep** — Mock for ExecutionStep

### Sample Data
- `sample_artifacts_basic` — 3 artifacts with different relevance
- `sample_artifacts_tie_breaking` — Identical relevance for sorting tests
- `sample_artifacts_large` — Mix of very large and tiny artifacts
- `sample_artifacts_empty` — Empty list
- `sample_artifacts_multi_repo` — Artifacts from different repos

### Instances
- `mock_artifact_store`
- `mock_agent`
- `mock_skills`
- `mock_execution_step`

---

## Determinism Strategy

Every assembler and prompt test includes **determinism assertions**:

```python
# Run 1
pkg1 = assemble_context(query, repo_id, store, budget1, step_id, run_id)

# Run 2 (identical input)
pkg2 = assemble_context(query, repo_id, store, budget2, step_id, run_id)

# Assert identical output
assert len(pkg1.chunks) == len(pkg2.chunks)
for c1, c2 in zip(pkg1.chunks, pkg2.chunks):
    assert c1.source_id == c2.source_id
    assert c1.included == c2.included
    assert c1.token_count == c2.token_count
```

This catches:
- Hash-order dependencies
- Random tie-breaking
- Insertion-order variations
- Non-deterministic floats

---

## Coverage Goals

| Module | Target | Hard Tests |
|--------|--------|-----------|
| budget.py | ≥90% | test_budget.py (18) |
| types.py | ≥85% | Via fixtures (10) |
| assembler.py | ≥90% | test_assembler.py (16) |
| prompt.py | ≥90% | test_prompt.py (14) |
| __init__.py | ≥100% | Implicit (imports) |
| **TOTAL** | **≥85%** | **78 tests** |

---

## Acceptance Criteria Mapping

| Spec | Tests | Coverage |
|------|-------|----------|
| AC1: TokenBudget | test_budget.py (18) + test_property.py (3) | 21 tests |
| AC2: ContextChunk/Package | test_assembler.py (2) + test_prompt.py (2) | 4 tests |
| AC3: assemble_context | test_assembler.py (14) + test_property.py (3) | 17 tests |
| AC4: assemble_prompt | test_prompt.py (12) | 12 tests |
| AC5: Executor integration | test_integration.py (6) | 6 tests |
| AC6: Import fix | (CI phase) | — |
| AC7: Package exports | conftest.py imports | — |
| AC8: Zero regressions | test_integration.py (3) + full pytest | 3 + full |

---

## Expected Test Results

### Pilot Test (First 5)
- **Expected:** 5/5 PASS (exit code 0)
- **If failed:** Stop and report to BUILDER/TEST-DESIGNER

### Full Test Suite
- **Expected:** 78 PASS (or acceptable xfail), ≥85% coverage, exit code 0
- **If failed:** Report failing test, log, error message to BUILDER

### Full Regression (All 455+ existing tests)
- **Expected:** 455+ PASS, no regressions
- **If failed:** Report regression to BUILDER

---

## How Tests Will Run

### VERIFIER Phase A: Import Validation
```bash
python -c "from packages.token_optimizer.budget import TokenBudget"
python -c "from packages.token_optimizer.types import ContextChunk"
python -c "from packages.token_optimizer.assembler import assemble_context"
python -c "from packages.token_optimizer.prompt import assemble_prompt"
```

### VERIFIER Phase B: Pilot Test
```bash
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property -v
pytest packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used -v
pytest packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs -v
pytest packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter -v
pytest packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```

### VERIFIER Phase C: Full Suite
```bash
pytest packages/token-optimizer/tests/ -v --tb=short --cov=packages/token-optimizer \
  2>&1 | tee .ases/evidence/task-014/test-full.log
```

### VERIFIER Phase D: Regression
```bash
pytest 2>&1 | tee .ases/evidence/task-014/regression-full.log
```

---

## Known Acceptable Failures

None currently. All tests are designed to pass when implementation is correct.

**If real bugs found during verification:**
1. Mark test with `@pytest.mark.xfail(reason="...")`
2. Document in implementation-notes.md
3. BUILDER fixes bug
4. Remove xfail marker
5. Re-run

---

## Key Insights

### Why These Tests Find Bugs

1. **Determinism Tests** catch implementation that relies on dict order, random tie-breaking, or insertion order
2. **Mutability Tests** catch implementations that copy budget instead of modifying in place
3. **Tie-Breaking Tests** catch sorting that doesn't follow spec order (relevance → token_count → id)
4. **Boundary Tests** catch off-by-one errors on exact budget limits
5. **Format Tests** catch formatting that adds escaping or wrong delimiters
6. **Integration Tests** catch that work in isolation but break together
7. **Property Tests** verify invariants hold across thousands of generated inputs

### Red Flags (If See These, Implementation Is Wrong)

- ❌ Determinism test fails (same input gives different output)
- ❌ Budget consumed greater than budget.total
- ❌ Chunks silently dropped from package
- ❌ Budget copied instead of mutated in place
- ❌ Prompt chunks in different order than chunk.id ascending
- ❌ Excluded chunks appear in prompt
- ❌ Duplicate source_ids de-duplicated (should keep both)
- ❌ Crashes on empty artifact list or zero budget
- ❌ Existing tests in orchestration fail

---

## Test Design Philosophy

**HARD TESTS THAT FIND BUGS:**
- Not just "happy path" smoke tests
- Not just "type checking" surface tests
- **Real edge cases** (boundaries, zero, huge, empty)
- **Real determinism checks** (multiple runs, identical assertions)
- **Real contract verification** (every AC tested deeply)

---

*TEST-DESIGNER report — task-014 gate-4 complete*
*Ready for BUILDER implementation + VERIFIER execution*
