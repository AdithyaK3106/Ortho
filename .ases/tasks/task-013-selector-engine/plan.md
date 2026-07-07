# task-013: Selector Engine + Execution — GATE 1 Plan

**Phase:** Phase 3 (Execution), Weeks 17–18  
**Scope:** Selector Engine (Stage 4) + Workflow Executor (orchestration runtime)  
**Dependent On:** task-012 (Intent Router + Registries) — COMPLETE  
**Deliverable:** Full agent/skill selection + step-by-step workflow execution with human approval gates

---

## Feature Summary

After task-012 classifies user intent, task-013 scores agents and skills using pure Python logic, builds an execution plan, and runs that plan step-by-step with human-approval checkpoints. This connects intent → execution with zero LLM in the selector itself (LLM is only the worker within selected agents).

**What it Does:**
1. Selector Engine (stage 4 from FRD §11): scores agents/skills from task-012's registries, builds ExecutionPlan
2. Workflow Executor: runs ExecutionPlan, state management, pauses at human approval gates
3. Step runner: invokes selected agents with context packages
4. Evidence collector: gathers outputs as Evidence artifacts

---

## Atomic Tasks (5)

### Task 1: SelectorEngine class — Agent + Skill Scoring
**Goal:** Pure Python logic to score agents and skills  
**Input:** IntentClassification (from task-012), AgentRegistry, SkillRegistry, available_context list  
**Output:** dict[agent_name → float], dict[agent_name → dict[skill_name → float]]

**Acceptance Criteria:**
- ✓ Score agents: intent triggers (1.0) + priority weight (0.3/0.15/0.0) + context availability penalty (−0.2)
- ✓ Score skills: agent_type match (0.8) + intent trigger match (0.6) + preferred (0.4)
- ✓ Hard exclude skills if token budget exceeded
- ✓ Returns deterministic scores (same input → same output)
- ✓ Tests: score_agent, score_skill, boundary cases (zero score, context missing, over-budget skills)

**Files:**
- `packages/orchestration/src/selector/engine.py` — SelectorEngine class
- `packages/orchestration/tests/test_selector_engine.py` — 12+ tests

---

### Task 2: ExecutionPlan Builder
**Goal:** Assemble plan from scores (order agents, assign skills, estimate tokens)

**Input:** IntentClassification, agent_scores dict, skill_scores dict, TokenBudget  
**Output:** ExecutionPlan dataclass (intent_class, steps[], total_tokens, human_approval_required)

**Acceptance Criteria:**
- ✓ Select top agents (score ≥ 0.5)
- ✓ Order agents by workflow (Architect → Coder → Tester/Reviewer for feature_dev; Analyst → Reporter for analysis)
- ✓ Assign skills to agents (score > 0.3)
- ✓ Sum token estimates from all skills
- ✓ Set human_approval_required = True for feature_dev/bug_fix/refactor, False for analysis
- ✓ Deterministic (tie-breaking by agent name alphabetically)

**Files:**
- `packages/orchestration/src/selector/engine.py` — build_execution_plan() function
- Tests in task-1 file

---

### Task 3: WorkflowExecutor class — Step Runner
**Goal:** Execute ExecutionPlan, manage state, pause at approval gates

**Input:** ExecutionPlan, LLM client, artifact registry  
**Output:** WorkflowRun (with status: pending → running → awaiting_approval → approved → complete)

**Acceptance Criteria:**
- ✓ State transitions per feature.md (DRAFT → PLANNED → ... → COMMITTED)
- ✓ Run steps sequentially (receive_from chain)
- ✓ Pause before human-approval-gate steps, wait for approval
- ✓ Store state in WorkflowStateStore (resumable after restart)
- ✓ Evidence collection after each step
- ✓ Error handling (step fails → mark as failed, don't auto-continue)

**Files:**
- `packages/orchestration/src/executor/workflow_executor.py` — WorkflowExecutor class
- `packages/orchestration/src/executor/state_store.py` — WorkflowStateStore (SQLite backend)
- `packages/orchestration/tests/test_workflow_executor.py` — 15+ tests

---

### Task 4: Step Runner + Agent Invocation
**Goal:** Call selected agent with assembled context, capture output

**Input:** ExecutionStep, agent manifest, skills, context package, LLM client  
**Output:** StepResult (agent_output, evidence array)

**Acceptance Criteria:**
- ✓ Assemble system_prompt (agent.md content + selected skills)
- ✓ Assemble user_message from task intent
- ✓ Call LLM with context package (prepared by token optimizer — stubbed here, not built yet)
- ✓ Parse LLM response into structured output (if agent returns JSON)
- ✓ Collect evidence (prompt, response, tokens, timestamp)
- ✓ Error handling (LLM timeout, parsing failure, rate limits)

**Files:**
- `packages/orchestration/src/executor/step_runner.py` — run_step() function
- `packages/orchestration/src/executor/evidence_collector.py` — Evidence struct + collection logic
- Tests in task-3 file

---

### Task 5: CLI Integration + `ortho run` Command
**Goal:** Wire executor into CLI, implement full end-to-end `ortho run` flow

**Input:** User intent string (e.g., "add rate limiting")  
**Output:** Workflow completion or pause at approval gate

**Acceptance Criteria:**
- ✓ `ortho run "<intent>"` → classify → select agents → build plan → run
- ✓ `ortho run --dry-run "<intent>"` → show plan without executing
- ✓ `ortho status` → show current workflow state
- ✓ `ortho approve` → approve pending human gate, resume
- ✓ `ortho reject "<reason>"` → reject and mark workflow as failed
- ✓ `ortho history` → list past workflow runs
- ✓ Context request stub (returns empty context for now — token optimizer built in task-014+)

**Files:**
- `apps/cli/src/commands/run.ts` — run command
- `apps/cli/src/commands/status.ts` — status command
- `apps/cli/src/commands/approve.ts` — approve command
- `apps/cli/src/commands/reject.ts` — reject command
- `apps/cli/src/commands/history.ts` — history command
- `apps/api-server/src/routers/orchestration.py` — /api/run, /api/status, etc. endpoints

---

## Dependencies

**Must be complete:**
- ✓ task-012 (Intent Router + Registries)
- ✓ task-011 (Scan Persistence — provides DB for state storage)
- ✓ task-010, task-009, task-008 (Architecture models, impact analysis, debt scoring — context data)

**Blocks:**
- task-014 (Token Optimizer — needs executor step runner to call agents)
- Future orchestration features (task planning, approval workflows)

---

## Formal Definitions (Determinism & Clarity)

This plan is grounded in five formal definitions to ensure determinism and eliminate ambiguity:

1. **Deterministic Workflow Ordering Algorithm** (spec.md, §1)
   - Agents grouped into workflow stages (architect → coder → tester → reviewer for feature_dev)
   - Ties broken by (stage, score desc, name asc)
   - Same intent + selected agents → identical step order (always)

2. **Formal State Transition Table** (spec.md, §3)
   - Every valid transition enumerated (pending → running → awaiting_approval → complete, etc.)
   - Invalid transitions rejected with error
   - Resume behavior explicit per state

3. **Approval Gate Semantics** (spec.md, §3.1)
   - Approval occurs **before** step execution
   - Each gate independent (approval of gate N does not approve gate N+1)
   - Rejection is terminal (workflow → rejected state)
   - Multiple gates supported, timeout default 300s

4. **Evidence Contract** (spec.md, §3.3)
   - One Evidence artifact per step (dataclass with system_prompt, user_message, output, tokens, timestamp)
   - Evidence types: agent_execution, approval_gate, rejection, timeout, error
   - Deterministic generation (same step → same evidence structure)

5. **Migration 003 Ownership** (spec.md, §4)
   - BUILDER creates migration file (migration_003_workflow_schema.sql)
   - OrthoDatabase.migrate() executes (standard mechanism)
   - BUILDER's rollback plan includes cleanup (DROP tables)
   - Append-only schema (new tables only, no ALTER existing)

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Selector scoring too conservative (picks no agents) | Threshold tuning (0.5 baseline). Property tests with synthetic intents (task-4 AC). |
| Workflow state lost on crash | WorkflowStateStore in SQLite with resumable state. Formal state table validates all transitions. Resume tests (task-3 AC). |
| Agent invocation hangs (LLM timeout) | Timeout parameter (default 60s). Explicit TimeoutError handling in step_runner. |
| Approval gate deadlock (never resolves) | Approval timeout (task spec, 300s). Human must reject or approve. Timeout → rejected state. |
| Token budget overrun (skills exceed budget) | Hard exclude in score_skill (score = 0 if over budget). Sum validation before step. |
| Migration 003 corrupts existing schema | Append-only (new tables only). No ALTER on workflow_runs/symbols/artifacts. Rollback cleanup documented. |
| Evidence loss on crash | Evidence appended to WorkflowRun in DB (transactional). No in-memory buffer; all data persisted. |

---

## Acceptance Criteria (All Tasks)

**Scope Verification (GATE 3):**
- [ ] 5 atomic tasks committed (one per task above)
- [ ] No extra files created
- [ ] implementation-notes.md lists any deviations

**Testing (GATE 4):**
- [ ] 40+ unit tests (selector scoring, plan building, executor state, approval gates)
- [ ] 10+ integration tests (full run from intent → plan → step execution)
- [ ] 5+ property-based tests (hypothesis, diverse intents)
- [ ] Real-repo test (ortho run against actual codebase, end-to-end)
- [ ] Coverage ≥85%
- [ ] Zero regressions

**Verification (GATE 5):**
- [ ] All tests pass (pytest exit 0)
- [ ] All CLI commands callable (no import/syntax errors)
- [ ] WorkflowRun creates artifacts in .ortho/ortho.db
- [ ] State store persists and resumes correctly
- [ ] No regressions in task-011/010/009/008 tests

**Code Quality (GATE 6):**
- [ ] No circular dependencies
- [ ] Type safety (mypy --strict)
- [ ] Security review (no injection, safe LLM calls)
- [ ] API contracts match spec.md

---

## Files to Create

```
packages/orchestration/src/
├── selector/
│   ├── __init__.py
│   └── engine.py (SelectorEngine, build_execution_plan)
├── executor/
│   ├── __init__.py
│   ├── workflow_executor.py (WorkflowExecutor class)
│   ├── state_store.py (WorkflowStateStore)
│   ├── step_runner.py (run_step function)
│   └── evidence_collector.py (Evidence collection)
└── ...existing files...

packages/orchestration/tests/
├── test_selector_engine.py (Task 1 & 2 tests)
├── test_workflow_executor.py (Task 3 & 4 tests)
└── test_integration.py (Task 5 integration tests)

apps/cli/src/commands/
├── run.ts (new — Task 5)
├── status.ts (new — Task 5)
├── approve.ts (new — Task 5)
├── reject.ts (new — Task 5)
├── history.ts (new — Task 5)
└── ...existing commands...

apps/api-server/src/routers/
├── orchestration.py (new — Task 5)
└── ...existing routers...
```

**Files to NOT touch:**
- task-012 artifacts (Intent Router, Registries)
- Pillar 1-3 packages (repo-intelligence, context-hub, arch-intelligence)
- CLI commands not in {run, status, approve, reject, history}

---

## Rollback Plan

**Triggers:**
- GATE 5: Test failures (executor doesn't resume, approval gates hang)
- GATE 6: Code review blocks merge (security issue, API mismatch)

**Procedure:**
```bash
# Local (not yet merged)
git reset --hard HEAD~5  # Undo all 5 commits

# Published (after merge)
git revert -n [commit-1]..[commit-5]  # Create revert commits
git commit -m "Revert task-013: Selector Engine (reason)"
```

**Verification After Rollback:**
- IntentRouter (task-012) still works independently
- Existing test suites (task-011/010/009/008) all pass
- No orphaned database tables (WorkflowRun, workflow_runs tables cleaned)

---

## What Success Looks Like

- `ortho run "add caching to the auth module"` classifies intent, selects architect/coder/tester agents, builds plan
- `ortho run --dry-run ...` shows plan without running
- `ortho status` shows "Awaiting human approval at: architect step"
- `ortho approve` resumes, architect agent runs with context
- `ortho history` lists all past workflow runs with status
- All states persist in SQLite (resumable after process restart)
- Full test suite passes with zero regressions
- Code review approves (no security, API, or architectural issues)

---

*End of GATE 1 Plan*
