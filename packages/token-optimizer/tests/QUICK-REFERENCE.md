# Quick Reference — Task-014 Test Suite

## 78 Hard Tests ✓

### Files at a Glance

| File | Tests | Key Focus | AC |
|------|-------|-----------|-----|
| **test_budget.py** | 18 | TokenBudget, overflow, mutability | 1 |
| **test_assembler.py** | 16 | Greedy packing, determinism | 3 |
| **test_prompt.py** | 14 | Formatting, ordering, determinism | 4 |
| **test_property.py** | 8 | Hypothesis invariants | 1,3 |
| **test_integration.py** | 10 | End-to-end, compatibility | 5,8 |
| **test_edge_cases.py** | 12 | Boundaries, edge cases | 1-4 |

## Run Tests

### All tests
```bash
pytest packages/token-optimizer/tests/ -v --cov=packages/token-optimizer
```

### Single category
```bash
pytest packages/token-optimizer/tests/test_budget.py -v        # Budget
pytest packages/token-optimizer/tests/test_assembler.py -v     # Packing
pytest packages/token-optimizer/tests/test_prompt.py -v        # Prompt
pytest packages/token-optimizer/tests/test_property.py -v      # Hypothesis
pytest packages/token-optimizer/tests/test_integration.py -v   # E2E
pytest packages/token-optimizer/tests/test_edge_cases.py -v    # Edges
```

### Pilot test (first 5)
```bash
pytest \
  packages/token-optimizer/tests/test_budget.py::test_token_budget_remaining_property \
  packages/token-optimizer/tests/test_budget.py::test_token_budget_consume_increments_used \
  packages/token-optimizer/tests/test_assembler.py::test_assemble_determinism_identical_inputs \
  packages/token-optimizer/tests/test_prompt.py::test_assemble_prompt_format_fixed_delimiter \
  packages/token-optimizer/tests/test_property.py::test_remaining_always_nonnegative -v
```

## Top 20 Hard Tests (Red Flags)

These 20 find most bugs:

### Budget (5)
1. `test_token_budget_consume_in_place_mutation` — Catches copying bug
2. `test_token_budget_consume_one_over_raises` — Catches off-by-one
3. `test_token_budget_multiple_instances_isolated` — Catches shared state
4. `test_token_budget_zero_total` — Edge case
5. `test_token_budget_very_large_values` — Overflow

### Assembler (5)
6. `test_assemble_determinism_identical_inputs` — Catches non-determinism
7. `test_assemble_budget_mutated_in_place` — Catches budget copying
8. `test_assemble_greedy_respects_budget_hard_ceiling` — Catches overflow
9. `test_assemble_tie_breaking_relevance_then_token_count` — Catches wrong sort
10. `test_assemble_all_chunks_returned_not_silently_dropped` — Catches drops

### Prompt (5)
11. `test_assemble_prompt_chunk_ordering_by_id_ascending` — Catches wrong order
12. `test_assemble_prompt_format_fixed_delimiter` — Catches format bugs
13. `test_assemble_prompt_only_included_chunks` — Catches inclusion bugs
14. `test_assemble_prompt_duplicate_source_ids_all_included` — Catches dedup
15. `test_assemble_prompt_determinism_identical_inputs` — Catches non-determinism

### Integration (5)
16. `test_assembler_output_valid_input_to_prompt_assembler` — Type contract
17. `test_end_to_end_workflow` — Full pipeline
18. `test_included_chunks_appear_in_prompt` — Semantics
19. `test_budget_exceeded_during_assembly` — Error handling
20. `test_assemble_empty_artifact_set_handles_gracefully` — Edge handling

## What Each Test Catches

### Determinism Tests
- `test_assemble_determinism_identical_inputs` — Catches hash-order, random selection, dict iteration variation
- `test_assemble_prompt_chunk_ordering_by_id_ascending` — Catches chunk order by relevance instead of id
- `test_assembler_output_valid_input_to_prompt_assembler` — Catches pipeline breaks

### Mutability Tests
- `test_token_budget_consume_in_place_mutation` — Budget copied instead of mutated
- `test_assemble_budget_mutated_in_place` — Budget not modified
- `test_assemble_budget_reference_same_instance` — Budget not same instance

### Overflow Tests
- `test_token_budget_consume_one_over_raises` — Off-by-one on boundary
- `test_assemble_greedy_respects_budget_hard_ceiling` — Sum > budget.total
- `test_budget_exceeded_during_assembly` — No graceful error handling

### Tie-Breaking Tests
- `test_assemble_tie_breaking_relevance_then_token_count` — Wrong sort order (relevance→token_count→id)
- `test_assemble_tie_breaking_final_tiebreaker_artifact_id` — Missing final tiebreaker

### Format Tests
- `test_assemble_prompt_format_fixed_delimiter` — Wrong delimiter, escaping, line breaks
- `test_assemble_prompt_no_escaping_in_content` — Content modified

### Edge Cases
- `test_budget_zero_total` — Crashes on zero budget
- `test_assemble_empty_search_results` — Crashes on empty list
- `test_assemble_single_chunk_exactly_fits` — Boundary off-by-one
- `test_prompt_no_included_chunks` — Crashes on empty message

## Expected Results

```
======================== 78 passed in 1.5s ========================
```

Or:

```
======================== 76 passed, 2 xfailed in 1.5s ========================
```

(If 2 acceptable failures marked with `@pytest.mark.xfail(reason="...")`)

## Coverage Goals

- **budget.py:** ≥90%
- **types.py:** ≥85%
- **assembler.py:** ≥90%
- **prompt.py:** ≥90%
- **__init__.py:** ≥100%
- **Overall:** ≥85%

## Fixtures Available

### Mocks
- `mock_artifact_store` — Returns 3 sample artifacts
- `mock_agent` — Has system_prompt
- `mock_skills` — List of 2 mock skills
- `mock_execution_step` — Mock ExecutionStep

### Sample Data
- `sample_artifacts_basic` — 3 artifacts, diff relevance
- `sample_artifacts_tie_breaking` — Same relevance, diff tokens/id
- `sample_artifacts_large` — 5000 token + 1 token
- `sample_artifacts_empty` — []
- `sample_artifacts_multi_repo` — diff repos

Use in tests:
```python
def test_something(mock_artifact_store, mock_agent):
    ...
```

## Common Patterns

### Test Determinism
```python
pkg1 = assemble_context(query, ..., budget1, ...)
pkg2 = assemble_context(query, ..., budget2, ...)
assert len(pkg1.chunks) == len(pkg2.chunks)
for c1, c2 in zip(pkg1.chunks, pkg2.chunks):
    assert c1.source_id == c2.source_id
```

### Test Mutability
```python
budget = TokenBudget(total=100, used=0, model="claude")
budget_id = id(budget)
budget.consume(50)
assert id(budget) == budget_id  # Same object
assert budget.used == 50  # Modified in place
```

### Test Boundary
```python
budget = TokenBudget(total=100, used=90, model="claude")
budget.consume(10)  # Exact fit
assert budget.remaining == 0
with pytest.raises(BudgetExceededError):
    budget.consume(1)  # One over
```

## Troubleshooting

### ImportError: No module named 'packages.token_optimizer'
- BUILDER hasn't created token_optimizer package yet
- Tests use `@pytest.mark.skipif` to skip if missing

### Test skipped (yellow dot)
- Normal during development
- Use `-v` flag to see which are skipped

### Test failed (red X)
- Real bug found in implementation
- Check error message for details
- Red flags listed above help diagnose

## Documentation

- **TEST-PLAN.md** (16 KB) — Full test strategy and design
- **README.md** (13 KB) — Quick start and test overview
- **TESTS.txt** (8 KB) — Complete test list with descriptions
- **QUICK-REFERENCE.md** (this file) — At-a-glance reference

## Timeline

1. **Now:** TEST-DESIGNER complete (this report)
2. **Next:** BUILDER implements 5 atomic tasks (4-6 hours)
3. **Then:** VERIFIER runs all 4 phases (30 min)
4. **Then:** REVIEWER audits code + logs (30 min)
5. **Final:** Human approval at GATE 6

---

*TEST-DESIGNER GATE 4 COMPLETE*
*Ready for BUILDER implementation*
