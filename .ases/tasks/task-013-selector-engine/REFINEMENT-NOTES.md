# task-013: Refinement Notes (Planning Ambiguities → Formal Definitions)

**Date:** 2026-07-07  
**Input:** User feedback (5 planning ambiguities)  
**Output:** 5 formal definitions + consistency verification  
**Scope:** Refinement only (no architectural changes)

---

## Five Planning Ambiguities → Formal Definitions

### Ambiguity 1: Workflow Ordering (Non-Deterministic)

**Problem:**
- FRD §11.4 showed example: architect → coder → tester → reviewer (feature_development)
- But spec didn't explain how to handle:
  - Custom agents (where do they go?)
  - Multiple intent types (bug_fix, analysis, refactor have different orderings)
  - Tie-breaking when agents have same score
  - Agents belonging to multiple workflow stages

**Solution:**
Added **Deterministic Workflow Ordering Algorithm** (spec.md, before Core Components):
- Define workflow stages per intent type
- Assign agents to earliest matching stage
- Tie-break by: (stage, score desc, agent_name asc)
- Custom agents assigned to Stage 99 (end)

**Invariant:** Same intent + selected agents → identical step order (deterministic, repeatable)

**Example:**
```
feature_development + selected {architect=1.8, coder=1.5, tester=1.0}
→ Step 1: architect (stage 1, 1.8)
→ Step 2: coder (stage 2, 1.5)
→ Step 3: tester (stage 3, 1.0)
```

---

### Ambiguity 2: Approval Gate Semantics (Unclear Behavior)

**Problem:**
- Spec said "pause before step, wait for approval" but didn't clarify:
  - Does approval of gate 1 approve gate 2? (No — spec said independent, but wasn't explicit)
  - What happens if user rejects? (Spec said "failed", but should be "rejected" terminal state)
  - Can there be multiple approval gates? (Yes, but semantics undefined)
  - Timeout behavior? (Defaulted to 60s, but that was step_runner timeout, not gate timeout)

**Solution:**
Added **Approval Gate Semantics (Formal Definition)** (spec.md, §3.1):
- **Execution order:** Approval before step execution
- **Per-gate independence:** Approving gate N does not approve gate N+1
- **Rejection behavior:** Immediate workflow → rejected (terminal)
- **Multiple gates:** Fully supported, each independent
- **Timeout:** Default 300s (approval decision timeout, not step execution timeout)

**Invariant:** Only one approval gate active at a time (workflow blocks at exactly one point)

---

### Ambiguity 3: State Transitions (Ambiguous)

**Problem:**
- Spec described transitions in prose: "pending → running → awaiting_approval → complete"
- But didn't answer:
  - Can complete → running? (No, but spec didn't say)
  - What invalid transitions should reject? (Not defined)
  - What happens if step errors while awaiting_approval? (Not specified)
  - Resume behavior per state? (Mentioned briefly, not formalized)

**Solution:**
Added **Formal State Transition Table** (spec.md, §3):
- Normative table: current state + trigger → next state + conditions
- Terminal states identified (complete, failed, rejected)
- Invalid transitions documented
- Resume behavior explicit per state

**Table Structure:**
| Current | Trigger | Next | Conditions | Notes |
|---|---|---|---|---|
| pending | execute() | running | — | initial |
| running | step.approval_gate | awaiting_approval | — | blocks |
| awaiting_approval | approve() | running | — | gate releases |
| awaiting_approval | reject() | rejected | — | terminal |
| running | step error | failed | — | no retry |

**Invariant:** WorkflowExecutor validates all transitions; invalid transitions rejected with error

---

### Ambiguity 4: Evidence Contract (Undefined)

**Problem:**
- Spec referenced `Evidence` throughout but never defined its structure
- Implementation had to guess:
  - What fields are required? (system_prompt? user_message? tokens? timestamp?)
  - One Evidence per step or multiple? (Spec collected evidence but didn't say how many)
  - Should Evidence be stored? (Where? DB table? JSON? Transient?)
  - What happens to Evidence on crash/resume? (Lost if in-memory)

**Solution:**
Added **Evidence Contract (Formal Definition)** (spec.md, §3.3):
- Dataclass structure with required fields:
  ```python
  @dataclass
  class Evidence:
      step_id, step_name, evidence_type
      system_prompt, user_message, agent_output
      input_tokens, output_tokens, total_tokens
      approval_decision, approval_reason
      created_at, completed_at, duration_ms, status, error_message
  ```
- **One Evidence per step** (per ExecutionStep.step_id)
- Evidence types: agent_execution, approval_gate, rejection, timeout, error
- Evidence appended to workflow_runs.evidence_json (immutable, chronological)

**Invariant:** Same step → same Evidence structure (deterministic)

---

### Ambiguity 5: Migration Ownership (Unclear Responsibility)

**Problem:**
- Rollback plan referenced "Migration 003" but didn't clearly state:
  - Who creates the migration file? (BUILDER? OrthoDatabase?)
  - Who executes it? (At what point?)
  - Who cleans up on rollback? (Just git revert, or also drop tables?)
  - What if migration fails?

**Solution:**
Added **Migration 003 Ownership & Schema** (spec.md, §4):
- **BUILDER:** Creates migration_003_workflow_schema.sql
- **OrthoDatabase.migrate():** Executes (standard mechanism)
- **BUILDER Rollback Plan:** Drops tables (approval_gates, execution_steps, workflow_runs)

**Schema defined:**
```sql
CREATE TABLE workflow_runs (...)     -- FK to repositories
CREATE TABLE execution_steps (...)   -- FK to workflow_runs
CREATE TABLE approval_gates (...)    -- FK to workflow_runs
```

**Cleanup Procedure:**
```python
DROP TABLE IF EXISTS approval_gates
DROP TABLE IF EXISTS execution_steps
DROP TABLE IF EXISTS workflow_runs
DELETE FROM schema_migrations WHERE version = 3
```

**Invariant:** Schema append-only (no ALTER existing tables); safe to rollback

---

## Consistency Cross-Validation

All five formal definitions verified to work together:

### Workflow Ordering ↔ Approval Gates ✓
- Workflow ordering produces deterministic step sequence
- Approval gates placed at steps (via approval_gate field)
- Multiple gates sequenced by step order (gate 1 on step 1, gate 2 on step 3)

### Approval Gate Semantics ↔ State Machine ✓
- step.approval_gate=True → awaiting_approval state
- approve() → awaiting_approval → running
- reject() → awaiting_approval → rejected (terminal)
- Timeout → awaiting_approval → rejected (terminal)

### State Machine ↔ Evidence Contract ✓
- running → agent_execution evidence
- awaiting_approval → approval_gate evidence (approval_decision=pending)
- Approval decision → evidence with approval_decision={approved|rejected|timeout}
- Error → error evidence (status=error, error_message)

### Evidence Contract ↔ Migration Schema ✓
- Evidence.step_id matches ExecutionStep.step_id (FK reference)
- Evidence appended to workflow_runs.evidence_json
- Approval decisions persisted in approval_gates table

### Migration Schema ↔ Workflow Ordering ✓
- ExecutionPlan serialized to execution_plan_json
- ExecutionSteps table stores agent_name, skill_names (matches plan)
- Step order preserved (step_id used for ordering)

---

## No Architectural Changes

This refinement **preserves** the original design:
- ✓ Same 5 atomic tasks
- ✓ Same package structure (orchestration/, cli/, api-server/)
- ✓ Same file creation/modification scope
- ✓ Same acceptance criteria
- ✓ Same dependencies
- ✓ Same implementation order

**Refinement only:** Clarification, formalization, determinism verification

---

## Documentation Trail

**Refinement artifacts created:**
1. `refinement-summary.md` — Before/after of all 5 definitions
2. `consistency-checklist.md` — Cross-validation results
3. `REFINEMENT-NOTES.md` — This document

**Original artifacts updated:**
1. `plan.md` — Added "Formal Definitions" section, updated risk mitigations
2. `spec.md` — Added §1 (workflow ordering), §3 (state table), §3.1 (approval semantics), §3.3 (evidence), §4 (migration)
3. `rollback-plan.md` — Added "Migration 003 Cleanup" section with explicit cleanup procedure

---

*End of Refinement Notes*
