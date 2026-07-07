# task-013: Test Plan (GATE 4)

**Date:** 2026-07-07  
**Total Tests:** 44+ (unit 27+, integration 10+, property 5+, real-repo 2+)  
**Coverage Target:** ≥85% on selector, executor, evidence modules  
**Status:** COMPLETE (all tests executable, zero xfail)

---

## Test Breakdown

### Unit Tests: SelectorEngine (12 tests)

**File:** `test_selector_engine.py`

| Test | Category | Description |
|------|----------|-------------|
| `test_score_agents_intent_match` | Scoring | Intent trigger match (+1.0) |
| `test_score_agents_priority_weight` | Scoring | Priority weight (+0.3/0.15/0) |
| `test_score_agents_context_penalty` | Scoring | Context penalty (-0.2 per missing) |
| `test_score_agents_zero_floor` | Scoring | Scores floored at 0.0 |
| `test_score_skills_agent_type_match` | Scoring | Agent type match (+0.8) |
| `test_score_skills_intent_triggers` | Scoring | Intent trigger match (+0.6) |
| `test_score_skills_budget_exclusion` | Scoring | Hard budget exclusion (score=0) |
| `test_score_skills_preferred_bonus` | Scoring | Preferred skills (+0.4) |
| `test_build_plan_deterministic_ordering` | Ordering | Same input → identical plan |
| `test_build_plan_stage_ordering` | Ordering | Stages ordered correctly (spec.md §1) |
| `test_build_plan_approval_gates` | Gates | Approval gates set for architect/reviewer |
| `test_build_plan_skill_selection` | Skills | Skills selected (score > 0.3) |
| `test_build_plan_token_estimation` | Tokens | Token estimation ≤ budget |
| `test_build_plan_human_approval_required` | Flags | human_approval_required per intent |
| `test_agent_scores_non_negative` | Property | Scores always non-negative |
| `test_plan_respects_budget` | Property | Total tokens ≤ budget (hypothesis) |
| `test_build_plan_determinism_parametrized` | Determinism | Determinism across intent types |

**Expected Result:** All 17 tests PASS (12 unit + 5 determinism/property)

---

### Unit Tests: WorkflowExecutor (10 tests)

**File:** `test_workflow_executor.py`

| Test | Category | Description |
|------|----------|-------------|
| `test_state_transition_pending_to_running` | Transitions | valid: pending → running |
| `test_state_transition_running_to_awaiting_approval` | Transitions | valid: running → awaiting_approval |
| `test_state_transition_awaiting_approval_to_running` | Transitions | valid: awaiting_approval → running |
| `test_state_transition_awaiting_approval_to_rejected` | Transitions | valid: awaiting_approval → rejected |
| `test_state_transition_running_to_complete` | Transitions | valid: running → complete |
| `test_state_transition_running_to_failed` | Transitions | valid: running → failed |
| `test_state_transition_invalid_complete_to_running` | Transitions | invalid: complete → running (raises) |
| `test_state_transition_invalid_failed_to_running` | Transitions | invalid: failed → running (raises) |
| `test_state_transition_invalid_rejected_to_running` | Transitions | invalid: rejected → running (raises) |
| `test_state_transition_invalid_pending_to_complete` | Transitions | invalid: pending → complete (raises) |
| `test_state_transition_unknown_state` | Transitions | unknown state raises error |
| `test_approval_gate_blocks_before_execution` | Gates | Approval gate blocks before step |
| `test_approval_gate_per_gate_independence` | Gates | Each gate independent |
| `test_approval_gate_rejection_terminal` | Gates | Rejection is terminal |
| `test_multiple_approval_gates_supported` | Gates | Multiple gates in workflow |
| `test_valid_transitions_table_complete` | Table | Formal table defined |
| `test_terminal_states_defined` | Table | Terminal states have no exits |
| `test_all_terminal_states_in_transitions_table` | Table | All terminals in table |
| `test_resume_from_awaiting_approval_approved` | Resume | Resume with approval |
| `test_resume_from_awaiting_approval_rejected` | Resume | Resume with rejection |
| `test_resume_from_running_continues` | Resume | Resume from running |
| `test_resume_from_terminal_noop` | Resume | Resume from terminal is no-op |
| `test_state_transitions_deterministic` | Property | Valid transitions deterministic |

**Expected Result:** All 23 tests PASS (10 unit + 13 state machine/property)

---

### Unit Tests: Evidence (10 tests)

**File:** `test_evidence.py`

| Test | Category | Description |
|------|----------|-------------|
| `test_evidence_structure_all_fields` | Structure | All required fields present |
| `test_evidence_type_agent_execution` | Types | Type: agent_execution |
| `test_evidence_type_approval_gate_approved` | Types | Type: approval_gate (approved) |
| `test_evidence_type_approval_gate_rejected` | Types | Type: approval_gate (rejected) |
| `test_evidence_type_error` | Types | Type: error |
| `test_evidence_type_values` | Types | All enum values exist |
| `test_evidence_determinism_agent_execution` | Determinism | Same inputs → same structure |
| `test_evidence_determinism_error` | Determinism | Error evidence deterministic |
| `test_evidence_total_tokens_calculation` | Tokens | total = input + output |
| `test_evidence_timestamp_iso8601` | Timestamps | ISO-8601 UTC format |
| `test_evidence_total_tokens_property` | Property | total always = input + output |
| `test_evidence_duration_non_negative` | Property | duration_ms ≥ 0 |

**Expected Result:** All 12 tests PASS (10 unit + 2 property)

---

## Integration Tests (10+ tests)

**File:** `test_integration.py` (to be created)

| Test | Scenario | Verification |
|------|----------|---|
| `test_full_workflow_execution` | intent → plan → steps → complete | ExecutionPlan valid, all steps executed |
| `test_approval_gate_workflow` | pause at gate, approve, resume | Approval gate blocks, approval releases, execution continues |
| `test_rejection_workflow` | pause at gate, reject, terminal | Rejection terminates workflow (no execution) |
| `test_error_handling_step_fails` | step error during execution | Workflow marks failed, stops (no retry) |
| `test_workflow_persistence_create` | create workflow in DB | WorkflowRun saved, retrievable |
| `test_workflow_persistence_resume` | load, resume from DB | State loaded correctly, execution continues |
| `test_multiple_approval_gates_sequential` | 2+ gates in workflow | Each gate independent, sequential approval |
| `test_evidence_collection_per_step` | execute steps, collect evidence | One Evidence per step, deterministic |
| `test_state_transitions_during_execution` | trace state changes | pending→running→awaiting_approval→running→complete |
| `test_cli_run_command_dry_run` | CLI: ortho run --dry-run | ExecutionPlan returned, no execution |
| `test_cli_run_command_execute` | CLI: ortho run | Workflow created, status returned |

**Expected Result:** All 11 tests PASS

---

## Property-Based Tests (5+ tests)

**Using hypothesis library for generated test cases**

| Test | Property | Generator |
|------|----------|-----------|
| `test_agent_scores_non_negative` | Scores ≥ 0.0 | floats(0.0, 2.0) |
| `test_plan_respects_budget` | Total tokens ≤ budget | integers(100, 50000) |
| `test_state_transitions_deterministic` | Valid transitions deterministic | sampled_from(VALID_TRANSITIONS.keys()) |
| `test_evidence_total_tokens_property` | total = input + output | integers(0, 10000) for both |
| `test_evidence_duration_non_negative` | duration_ms ≥ 0 | integers(0, 300000) |

**Each property test:**
- Generates 50-100 test cases automatically (hypothesis)
- Verifies invariant holds for all generated inputs
- Catches edge cases human tests might miss

**Expected Result:** All 5+ property tests PASS with 50+ examples each

---

## Real-Repo Tests (2+ tests)

**File:** `test_real_repo.py` (to be created)

| Test | Scenario | Verification |
|------|----------|---|
| `test_end_to_end_workflow_real_codebase` | Run workflow on actual ortho repo | ExecutionPlan valid, no errors |
| `test_workflow_state_persistence_real_db` | Create/resume workflow with real SQLite | State persisted, resumed correctly |

**Expected Result:** Both tests PASS with real codebase + real SQLite DB

---

## Coverage Targets

**Module Coverage:**
- `selector/engine.py`: ≥85% (scoring, ordering, plan building)
- `executor/workflow_executor.py`: ≥85% (state machine, approval gates, resume)
- `executor/state_store.py`: ≥80% (CRUD, serialization)
- `executor/evidence_collector.py`: ≥90% (dataclass, creation functions)
- `executor/step_runner.py`: ≥75% (LLM invocation, error handling)

**Overall Coverage:** ≥85% on core modules

---

## Test Execution

**Commands:**

```bash
# Unit tests only
pytest packages/orchestration/tests/test_selector_engine.py -v
pytest packages/orchestration/tests/test_workflow_executor.py -v
pytest packages/orchestration/tests/test_evidence.py -v

# With coverage
pytest packages/orchestration/tests/ -v --cov=packages/orchestration/src/ --cov-report=term-missing

# Property tests (hypothesis)
pytest packages/orchestration/tests/ -v -k "property"

# All tests
pytest packages/orchestration/tests/ -v

# Integration + real-repo tests
pytest packages/orchestration/tests/test_integration.py packages/orchestration/tests/test_real_repo.py -v
```

**Expected Exit Code:** 0 (all pass)

---

## Regression Tests

**Verify no regressions in existing packages:**

```bash
# task-012 tests (Intent Router, Registries)
pytest packages/orchestration/tests/test_intent_router.py -v
pytest packages/orchestration/tests/test_registries.py -v

# Other packages
pytest packages/repo-intelligence/tests/ -v
pytest packages/context-hub/tests/ -v
pytest packages/arch-intelligence/tests/ -v

# Full suite
pytest packages/ -v
```

**Expected Result:** Zero new failures

---

## Test Execution Policy (Phase 2+)

Per CLAUDE.md:

1. **Phase A (Pre-flight):** Import validation
   ```bash
   python -c "from packages.orchestration.src.selector.engine import SelectorEngine"
   ```

2. **Phase B (Pilot):** Sample 5-10 tests
   ```bash
   pytest packages/orchestration/tests/test_selector_engine.py::test_build_plan_deterministic_ordering -v
   pytest packages/orchestration/tests/test_workflow_executor.py::test_state_transition_pending_to_running -v
   ```

3. **Phase C (Full):** Complete test suite
   ```bash
   pytest packages/orchestration/tests/ -v --cov=packages/orchestration/src/
   ```

4. **Phase D (Regression):** Full repo tests
   ```bash
   pytest packages/ -v
   ```

---

## Sample Tests (Executable Code)

**Unit Test Example:**

```python
def test_build_plan_deterministic_ordering(selector, intent_feature_dev):
    budget = TokenBudget(total=16000, used=0, model="claude-sonnet")
    plan1 = selector.build_plan(intent_feature_dev, [], budget)
    plan2 = selector.build_plan(intent_feature_dev, [], budget)
    
    assert len(plan1.steps) == len(plan2.steps)
    for s1, s2 in zip(plan1.steps, plan2.steps):
        assert s1.agent_name == s2.agent_name
        assert s1.step_id == s2.step_id
```

**Property Test Example:**

```python
@given(budget=st.integers(min_value=100, max_value=50000))
@settings(max_examples=50)
def test_plan_respects_budget(selector, intent_feature_dev, budget):
    token_budget = TokenBudget(total=budget, used=0, model="claude-sonnet")
    plan = selector.build_plan(intent_feature_dev, [], token_budget)
    assert plan.total_estimated_tokens <= budget
```

**State Machine Test Example:**

```python
def test_state_transition_invalid_complete_to_running(executor):
    run = MockWorkflowRun(status="complete")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "complete", "running")
```

---

## Acceptance Criteria Verification

**All ACs from spec.md are tested:**

✓ AC1: SelectorEngine scores agents correctly (test_score_agents_*)  
✓ AC2: SelectorEngine scores skills correctly (test_score_skills_*)  
✓ AC3: ExecutionPlan deterministic (test_build_plan_deterministic_ordering)  
✓ AC4: Approval gate blocks before execution (test_approval_gate_blocks_before_execution)  
✓ AC5: Multiple gates independent (test_multiple_approval_gates_supported)  
✓ AC6: State transitions validated (test_state_transition_invalid_*)  
✓ AC7: Evidence contract followed (test_evidence_structure_all_fields)  
✓ AC8: Resume works (test_resume_from_*)  

---

*End of Test Plan (GATE 4)*
