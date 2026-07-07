# task-013: GATE 1 Refinement Summary

**Date:** 2026-07-07  
**Refinement Focus:** Determinism, Formal Definitions, Internal Consistency  
**No Architectural Changes:** All refinements are clarifications only

---

## Changes Made

### 1. Deterministic Workflow Ordering Algorithm

**Added:** New section in spec.md (before Core Components)

**Defines:**
- Workflow stages per intent type (feature_development: architect → coder → tester → reviewer; bug_fix: debugger/analyst → coder → tester → reviewer; etc.)
- Agent assignment to stages (earliest match for agents with multiple triggers)
- Tie-breaking rule: **(stage, score desc, agent_name asc)**
- Custom agent handling (Stage 99, after all core stages)
- Resume behavior (if interrupted, same algorithm produces same order)

**Invariant:** Same (intent_class, selected_agents) → identical ExecutionPlan step order (deterministic, repeatable)

**Example:**
```
feature_development + selected agents {architect=1.8, coder=1.5, tester=1.0, reviewer=0.9}
→ Step 1: architect (stage 1, score 1.8)
→ Step 2: coder (stage 2, score 1.5)
→ Step 3: tester (stage 3, score 1.0)
→ Step 4: reviewer (stage 4, score 0.9)
```

---

### 2. Formal State Transition Table

**Added:** New section 3 (replaced descriptive state changes with normative table)

**Defines:**
- Every valid transition (pending → running, running → awaiting_approval, awaiting_approval → running, etc.)
- Terminal states (complete, failed, rejected)
- Invalid transitions (complete → any state, failed → any state, etc.)
- Resume behavior per state

| Current State | Trigger | Next State | Conditions |
|---|---|---|---|
| pending | execute() | running | initial transition |
| running | step.approval_gate=True | awaiting_approval | current step requires approval |
| awaiting_approval | approve() | running | approval granted |
| awaiting_approval | reject() | rejected | workflow rejected |
| awaiting_approval | timeout (300s) | rejected | no decision in time |
| running | step completes | running | loop to next step |
| running | all steps done | complete | final step done |
| running | step error | failed | step error (no retry) |
| complete | — | — | terminal |
| failed | — | — | terminal |
| rejected | — | — | terminal |

**Invariant:** WorkflowExecutor validates all transitions against this table; invalid transitions raise InvalidStateTransition error

---

### 3. Approval Gate Semantics (Formal Definition)

**Added:** New section 3.1 (clarifies approval behavior)

**Defines:**

**Execution Order:**
- Approval occurs **before** step execution
- If step.approval_gate = True:
  1. Mark step status as `pending_approval`
  2. Call on_approval_gate(current_workflow_run) → blocks until human decides
  3. If approval granted → execute step
  4. If approval rejected → mark workflow as `rejected`, terminate

**Per-Gate Independence:**
- Each approval gate is independent
- Approving gate N does **not** approve gate N+1
- Each subsequent gate requires explicit separate approval
- Example: architect approved → architect step runs → coder requires separate approval

**Multiple Gates Supported:**
- Workflows can have 0+ approval gates
- Gates can appear at any stage
- Each gate blocks independently per step

**Rejection Behavior:**
- Reject immediately transitions workflow to `rejected` state
- All pending steps cancelled
- Evidence collected for rejection
- Workflow unresumable (reject is terminal)

**Timeout Behavior:**
- Default: 300 seconds
- No decision within timeout → reject workflow
- Configurable per workflow

**Invariant:** Only one approval gate active at a time (workflow pauses at exactly one gate)

---

### 4. Evidence Contract (Formal Definition)

**Added:** New section 3.3 (defines Evidence structure and generation)

**Defines Dataclass:**

```python
@dataclass
class Evidence:
    step_id: str                    # ExecutionStep.step_id
    step_name: str                  # ExecutionStep.agent_name
    evidence_type: str              # agent_execution | approval_gate | rejection | timeout | error
    
    # LLM Interaction (for evidence_type="agent_execution")
    system_prompt: str
    user_message: str
    agent_output: str
    
    # Token Metrics
    input_tokens: int
    output_tokens: int
    total_tokens: int
    
    # Approval Gate Evidence
    approval_decision: str | None   # approved | rejected | timeout
    approval_reason: str | None
    
    # Metadata
    created_at: str                 # ISO-8601 UTC
    completed_at: str | None
    duration_ms: int
    status: str                     # success | error | timeout | rejected
    error_message: str | None
```

**Evidence Generation Invariants:**
1. Each step generates exactly one Evidence artifact
2. Evidence fields deterministic (same inputs → same evidence)
3. Timestamps ISO-8601 UTC (no local timezone)
4. Token counts exact (not estimated)
5. Error messages captured verbatim

**Evidence Types:**
- `agent_execution`: Step runs successfully
- `approval_gate`: Approval gate passes
- `rejection`: Workflow rejected
- `timeout`: Approval timeout
- `error`: Step fails

**Storage:** Appended to WorkflowRun.evidence array (chronological, immutable)

**Invariant:** Same step → same evidence structure (deterministic)

---

### 5. Migration 003 Ownership & Schema

**Added:** New section 4 (clarifies migration responsibility and schema)

**Ownership:**
- **BUILDER:** Creates migration file (migration_003_workflow_schema.sql)
- **OrthoDatabase.migrate():** Executes migration (standard mechanism)
- **BUILDER Rollback Plan:** Includes DROP TABLE cleanup

**Schema Definition:**

Three new tables (append-only, no ALTER existing):

1. **workflow_runs**
   - id (PK), repo_id (FK), intent, intent_class, execution_plan_json, status, started_at, completed_at, evidence_json

2. **execution_steps**
   - id (PK), workflow_run_id (FK), step_id, agent_name, skill_names, approval_gate, status, result_json, evidence_json, started_at, completed_at

3. **approval_gates**
   - id (PK), workflow_run_id (FK), step_id, status, decision_reason, created_at, decided_at

**Schema Invariants:**
- Append-only (new tables only)
- Foreign key constraints enforced (ON DELETE CASCADE)
- All timestamps ISO-8601 UTC
- Status values match formal state transition table
- JSON columns for serialized objects

**Cleanup on Rollback:**
1. DROP TABLE IF EXISTS approval_gates
2. DROP TABLE IF EXISTS execution_steps
3. DROP TABLE IF EXISTS workflow_runs
4. DELETE FROM schema_migrations WHERE version = 3

**Acceptance:** VERIFIER validates CREATE TABLE execution, BUILDER's rollback cleanup verified

---

## Consistency Verification

All refinements cross-validated for consistency:

### Workflow Ordering ↔ Approval Gates
- ✓ Workflow ordering produces step sequence
- ✓ Approval gates placed at specific steps (approval_gate field in ExecutionStep)
- ✓ Each gate is independent per formal approval semantics
- ✓ Multiple gates sequenced deterministically (one approval per gate required)

### State Transitions ↔ Approval Gate Semantics
- ✓ awaiting_approval state maps to step requiring approval (step.approval_gate=True)
- ✓ approve() transitions awaiting_approval → running (re-enters execution)
- ✓ reject() transitions awaiting_approval → rejected (terminal)
- ✓ Timeout transitions awaiting_approval → rejected (after 300s)
- ✓ Invalid transitions rejected (complete/failed/rejected are terminal)

### Evidence Contract ↔ State Transitions
- ✓ Evidence generated for every step (per evidence_type)
- ✓ Approval gate evidence captures decision (approved/rejected/timeout)
- ✓ Evidence timestamps match workflow timestamps
- ✓ Evidence step_id matches ExecutionStep.step_id
- ✓ Evidence immutable (append-only in DB)

### Workflow Ordering ↔ Migration 003
- ✓ ExecutionPlan serialized to execution_plan_json (migration 003 schema)
- ✓ ExecutionSteps persisted with agent_name, skill_names (matches step ordering)
- ✓ Approval gates table tracks approval_gate field (matches formal approval semantics)
- ✓ Schema supports resume (all state persisted, no in-memory buffer)

### Migration 003 ↔ Rollback Plan
- ✓ Migration ownership: BUILDER creates, OrthoDatabase executes, BUILDER cleans up
- ✓ Schema append-only: no ALTER, safe to rollback
- ✓ Cleanup procedure documented: DROP in dependency order
- ✓ Rollback verification: tables dropped, schema_migrations updated

---

## No Architectural Changes

This refinement **does not**:
- Change the 5 atomic tasks
- Modify API signatures
- Add new packages or modules
- Alter package layout (orchestration/, cli/, api-server/)
- Change acceptance criteria
- Add/remove files from implementation scope
- Modify dependencies
- Change implementation order

**Scope remains identical:**
- Task 1: SelectorEngine (score_agents, score_skills)
- Task 2: ExecutionPlan builder (with formal workflow ordering)
- Task 3: WorkflowExecutor (with formal state machine + approval gate semantics)
- Task 4: Step runner (generates Evidence per formal contract)
- Task 5: CLI commands (state transitions validated against formal table)

---

## Summary

All five ambiguities resolved with formal definitions:

| Ambiguity | Resolution |
|---|---|
| Workflow ordering non-deterministic | Formal algorithm: stages → score desc → name asc |
| Approval gate semantics unclear | Formal definition: before execution, per-gate independent, rejection terminal |
| State transitions ambiguous | Formal table: every transition enumerated, invalid transitions rejected |
| Evidence structure undefined | Formal dataclass: required fields, evidence types, generation invariants |
| Migration ownership unclear | Formal ownership: BUILDER creates, OrthoDatabase executes, BUILDER cleans up |

**Consistency verified:** All definitions cross-validated, no contradictions, ready for GATE 2 (ARCHITECT).

---

*End of Refinement Summary*
