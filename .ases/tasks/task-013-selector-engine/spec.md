# task-013: Selector Engine + Execution — GATE 1 Spec

**Phase:** Phase 3 (Execution), Weeks 17–18  
**Objective:** Pure Python selector and workflow executor for end-to-end orchestration  
**Related FRD Sections:** §9 (Pillar 4), §11 (Agent/Skill Selector System — Stage 4, full execution flow)  
**Previous Task:** task-012 (Intent Router + Registries, Stage 1–3) — REQUIRED

---

## Specification

### Goal
Build the orchestration engine's execution layer: agent/skill selection (Stage 4 from FRD §11), workflow execution, state management, and human approval gates. Closes Phase 3 Weeks 17–18 per FRD roadmap.

### Input/Output Contracts

#### Input
- **User intent:** String (e.g., "add rate limiting to the auth service")
- **IntentClassification:** From task-012's IntentRouter (type, confidence, method)
- **AgentRegistry:** Loaded from `.ases/agents/` (8 core + N custom)
- **SkillRegistry:** Loaded from `.ases/skills/` (10 core + N custom)
- **Available context:** List of context keys (e.g., ["architecture_model", "dependency_graph"])
- **TokenBudget:** Current budget (model, total, used)

#### Output
- **ExecutionPlan:** ordered steps, agent/skill assignments, total token estimate, approval requirements
- **WorkflowRun:** status (pending → running → awaiting_approval → approved → complete), evidence array
- **Evidence artifacts:** prompt, response, tokens, timestamp per step

### Deterministic Workflow Ordering Algorithm

**Definition:** After SelectorEngine selects agents (score ≥ 0.5), ExecutionPlan must order them deterministically using this algorithm:

**Input:**
- Selected agents: dict[agent_name → score]
- Intent type: str (e.g., "feature_development", "bug_fix", "analysis")

**Algorithm:**

1. **Define Workflow Stages** (per intent type):

   ```
   feature_development:
     Stage 1: architect
     Stage 2: coder
     Stage 3: tester
     Stage 4: reviewer
   
   bug_fix:
     Stage 1: debugger (or analyst if debugger absent)
     Stage 2: coder
     Stage 3: tester
     Stage 4: reviewer
   
   refactor:
     Stage 1: architect
     Stage 2: coder
     Stage 3: reviewer
   
   analysis:
     Stage 1: analyst
     Stage 2: (no fixed stage; see step 4 below)
   
   documentation:
     Stage 1: documenter
   
   architecture_review:
     Stage 1: architect
   ```

2. **Assign agents to stages:**
   - For each selected agent, look up which stages it belongs to (from AgentManifest.intent_triggers)
   - If agent matches multiple intent stages, use the **earliest stage** it matches
   - If agent matches no intent stages (custom agent), assign to **Stage 99** (end, before cleanup)

3. **Break ties within a stage** (deterministically):
   - Sort by: **(score desc, agent_name asc)**
   - Example: both "coder" and "reviewer" selected for feature_dev, both score 1.2 → order by stage first, then by score desc within stage
   - If scores tie within same stage: sort by agent_name alphabetically

4. **Handle custom agents:**
   - Custom agents not in core set inserted at **Stage 99** (after all core stages)
   - Sorted by score desc, then name asc within Stage 99

5. **Build ordered steps:**
   - Iterate stages 1, 2, 3, 4, ..., 99
   - For each stage, emit ExecutionStep objects in (stage, score desc, name asc) order
   - Set step.receives_from = prior_step.step_id (null for first step)
   - Set step.approval_gate = True iff agent_name in {architect, reviewer, debugger, documenter}

**Example (feature_development intent, agents selected: architect=1.8, coder=1.5, tester=1.0, reviewer=0.9):**
```
Step 1: architect (1.8, stage 1)
Step 2: coder (1.5, stage 2)
Step 3: tester (1.0, stage 3)
Step 4: reviewer (0.9, stage 4)
```

**Example (analysis intent, agents selected: analyst=0.8, custom_report_gen=0.6):**
```
Step 1: analyst (0.8, stage 1)
Step 2: custom_report_gen (0.6, stage 99)
```

**Invariant:** Same input intent + selected agents → same step order (always deterministic).

---

### Core Components

#### 1. SelectorEngine (Stage 4 from FRD §11.4)

**Class:** `SelectorEngine`

```python
class SelectorEngine:
    def __init__(self, agent_registry: AgentRegistry, skill_registry: SkillRegistry):
        self.agents = agent_registry
        self.skills = skill_registry
    
    def score_agents(
        self,
        intent: IntentClassification,
        available_context: list[str],
    ) -> dict[str, float]:
        """Score all agents for this intent.
        
        Scoring formula (per FRD §11.4):
        - Direct intent trigger match: +1.0
        - Semantic similarity (intent keywords vs description): +0.5 * sim_score
        - Priority weight: +{0.3|0.15|0.0} for {high|medium|low}
        - Context penalty: -0.2 per missing required context
        
        Returns: dict[agent_name → score], clipped to [0.0, ∞)
        """
        ...
    
    def score_skills(
        self,
        agent: AgentManifest,
        intent: IntentClassification,
        remaining_budget: int,
    ) -> dict[str, float]:
        """Score all skills for this agent.
        
        Scoring formula (per FRD §11.4):
        - Agent type match: +0.8
        - Intent trigger match: +0.6
        - Agent preferred: +0.4
        - Hard exclude: score = 0.0 if skill.estimated_tokens > remaining_budget
        
        Returns: dict[skill_name → score]
        """
        ...
    
    def build_plan(
        self,
        intent: IntentClassification,
        available_context: list[str],
        token_budget: TokenBudget,
    ) -> ExecutionPlan:
        """Build execution plan from scoring.
        
        Steps:
        1. Score all agents
        2. Select agents with score ≥ 0.5
        3. Order by workflow (architect → coder → tester/reviewer for feature_dev; analyst → reporter for analysis)
        4. For each agent, score skills and select those with score > 0.3
        5. Sum token estimates
        6. Set human_approval_required based on intent type
        
        Returns: ExecutionPlan with ordered steps, each with agent_name, skill_names[]
        
        Deterministic tie-breaking: agents sorted by (score desc, name asc)
        """
        ...
```

**Acceptance Criteria:**
- ✓ Scoring matches FRD formula exactly
- ✓ Hard skill budget exclusion (score = 0 if over budget)
- ✓ Deterministic output (same input → same output)
- ✓ Context penalty applies per missing context (e.g., 2 missing → −0.4)
- ✓ Agent ordering follows workflow (architect before coder for feature_dev)
- ✓ Skill selection only includes score > 0.3

#### 2. ExecutionPlan Dataclass

```python
@dataclass
class ExecutionPlan:
    intent_class: str                   # e.g., "feature_development"
    steps: list[ExecutionStep]          # ordered list of steps
    total_estimated_tokens: int
    human_approval_required: bool       # True for {feature_dev, bug_fix, refactor}, False for analysis
    
@dataclass
class ExecutionStep:
    step_id: str                        # unique ID for this step
    agent_name: str                     # e.g., "architect"
    skill_names: list[str]              # e.g., ["repo-analysis", "adr-writer"]
    context_package_id: str             # prepared by token optimizer (stub here)
    receives_from: str | None           # prior step_id (None for first step)
    produces: str                       # output key for next step
    approval_gate: bool                 # pause before this step?
    status: str                         # pending | running | complete | failed
```

**Acceptance Criteria:**
- ✓ All fields populated by build_plan()
- ✓ step_id unique per plan (e.g., "step-1", "step-2", ...)
- ✓ receives_from chain is acyclic
- ✓ approval_gate = True iff step.agent_name in approval_required_agents (e.g., architect, reviewer)

#### 3. Formal State Transition Table

**WorkflowRun State Machine:**

| Current State | Trigger | Next State | Conditions | Notes |
|---|---|---|---|---|
| `pending` | execute() called | `running` | plan is valid | Initial state → first step begins |
| `running` | step.approval_gate=True | `awaiting_approval` | current step requires approval | Blocks until approval/rejection |
| `awaiting_approval` | approve() called | `running` | approval callback returns True | Current gate releases; plan continues |
| `awaiting_approval` | reject() called | `rejected` | approval callback returns False | Workflow terminates immediately |
| `awaiting_approval` | timeout (default 300s) | `rejected` | no decision in time window | Explicit timeout handling |
| `running` | step completes (non-gated) | `running` | next step exists | Move to next step (loop) |
| `running` | all steps complete | `complete` | last step done | Terminal state |
| `running` | step error occurs | `failed` | error in step runner | Terminal state (no auto-retry) |
| `running` | explicit rejection | `rejected` | human calls reject() | Terminal state |
| `complete` | N/A | — | — | Terminal state |
| `failed` | N/A | — | — | Terminal state |
| `rejected` | N/A | — | — | Terminal state |

**Resume Behavior After Restart:**

```
Current State: awaiting_approval → resume(workflow_id)
  Load from DB
  Prompt human for decision (via on_approval_gate callback)
  If approval → continue to next step
  If rejection → mark as rejected
  
Current State: running → resume(workflow_id)
  Load last completed step from DB
  Continue from next pending step (no re-execution)
  
Current State: complete/failed/rejected → resume(workflow_id)
  Return as-is (no change)
```

**Invalid Transitions (must reject):**
- Any transition not in table above
- pending → (state other than running)
- complete → any state
- failed → any state
- rejected → any state

**Acceptance Criteria:**
- ✓ WorkflowExecutor validates all transitions against this table
- ✓ Invalid transitions raise InvalidStateTransition error
- ✓ Resume correctly loads state from DB and continues

---

#### 3.1 Approval Gate Semantics (Formal Definition)

**Approval Gate Behavior:**

1. **Execution Order:**
   - Approval occurs **before** step execution
   - If step.approval_gate = True:
     a. Mark step status as `pending_approval`
     b. Call on_approval_gate(current_workflow_run) → blocks until human decides
     c. If approval granted → execute step
     d. If approval rejected → mark workflow as `rejected`, terminate

2. **Per-Gate Independence:**
   - Each approval gate is independent
   - Approving gate N does **not** approve gate N+1
   - Each subsequent gate requires explicit separate approval
   - Example: architect (gate 1) approved → architect step runs → coder (gate 2) still requires approval

3. **Multiple Gates Supported:**
   - Workflows can have 0+ approval gates
   - Gates can appear at any stage (not just beginning or end)
   - Each gate blocks independently per step

4. **Rejection Behavior:**
   - Reject immediately transitions workflow to `rejected` state
   - All pending steps cancelled (not executed)
   - Evidence collected for rejection (reason, timestamp, step_id)
   - Workflow becomes unresumable (reject is terminal)

5. **Timeout Behavior:**
   - Default approval timeout: 300 seconds
   - If no decision within timeout → reject workflow
   - Configurable per workflow (ExecutionPlan.approval_timeout_seconds)

**Invariant:** Only one approval gate can be active at a time. The workflow pauses at exactly one gate, waiting for human input.

**Acceptance Criteria:**
- ✓ Approval gate pauses **before** step execution
- ✓ Approval only releases current gate (subsequent gates independent)
- ✓ Rejection is terminal (workflow → rejected state)
- ✓ Multiple gates supported (each independent)
- ✓ Timeout enforced (default 300s)

---

#### 3.2 WorkflowExecutor (Step Runner + State Management)

**Class:** `WorkflowExecutor`

```python
class WorkflowExecutor:
    def __init__(self, state_store: WorkflowStateStore, llm_client, artifact_registry):
        self.state = state_store
        self.llm = llm_client
        self.artifacts = artifact_registry
    
    def execute(
        self,
        plan: ExecutionPlan,
        on_approval_gate: Callable[[WorkflowRun], bool],  # human approval callback (blocks)
    ) -> WorkflowRun:
        """Execute plan step by step.
        
        Steps:
        1. Create WorkflowRun entry in state store (status=pending)
        2. Transition to running
        3. For each step in plan (in order):
           a. If step.approval_gate:
              - Transition workflow to awaiting_approval
              - Call on_approval_gate(current_state) → blocks until human decides
              - If result=False: transition to rejected, return
              - If result=True: continue to step b
           b. Transition step to running
           c. Call run_step(step, ...) to invoke agent
           d. Collect evidence (see Evidence Contract below)
           e. Transition step to complete, update workflow
        4. After all steps: transition workflow to complete
        5. Return final WorkflowRun
        
        State transitions are validated against formal state transition table.
        """
        ...
    
    def resume(self, workflow_run_id: str) -> WorkflowRun:
        """Resume interrupted workflow.
        
        Loads state from store. Behavior depends on current state:
        - awaiting_approval: resume approval gate (call on_approval_gate again)
        - running: resume from next pending step (no re-execution)
        - complete/failed/rejected: return as-is (no change)
        """
        ...
```

**Acceptance Criteria:**
- ✓ State transitions validated against formal table
- ✓ Resume works after process crash (load from DB, continue)
- ✓ Evidence collected per step (per Evidence Contract)
- ✓ Error handling: step fails → mark failed, stop (don't auto-continue)
- ✓ Approval gate: pause before execution, wait for callback, separate per gate

#### 3.3 Evidence Contract (Formal Definition)

**Evidence Dataclass Structure:**

```python
@dataclass
class Evidence:
    """Deterministic evidence artifact produced by each workflow step."""
    
    step_id: str                        # ExecutionStep.step_id (e.g., "step-1")
    step_name: str                      # ExecutionStep.agent_name (e.g., "architect")
    evidence_type: str                  # "agent_execution" | "approval_gate" | "rejection" | "timeout" | "error"
    
    # LLM Interaction (for evidence_type="agent_execution")
    system_prompt: str                  # Full system prompt sent to LLM
    user_message: str                   # Full user message sent to LLM
    agent_output: str                   # Raw LLM response
    
    # Token Metrics
    input_tokens: int                   # Tokens in system_prompt + user_message
    output_tokens: int                  # Tokens in agent_output
    total_tokens: int                   # input_tokens + output_tokens
    
    # Approval Gate Evidence (for evidence_type="approval_gate" | "rejection" | "timeout")
    approval_decision: str | None       # "approved" | "rejected" | "timeout" (None for execution evidence)
    approval_reason: str | None         # Human-provided reason (if approval_decision != None)
    
    # Metadata
    created_at: str                     # ISO-8601 timestamp (UTC)
    completed_at: str | None            # ISO-8601 timestamp (UTC), None if pending
    duration_ms: int                    # Elapsed time in milliseconds
    status: str                         # "success" | "error" | "timeout" | "rejected"
    error_message: str | None           # If status="error"
```

**Evidence Generation Invariants:**

1. **Each step generates exactly one Evidence artifact** (per ExecutionStep.step_id)
2. **Evidence fields are deterministic** (same inputs → same evidence)
3. **Timestamps are ISO-8601 UTC** (no local timezone, no fractional seconds beyond milliseconds)
4. **Token counts are exact** (not estimated)
5. **Error messages are captured verbatim** (no summarization)

**Evidence Types:**

| Type | When | Fields Populated |
|---|---|---|
| `agent_execution` | Step runs successfully | system_prompt, user_message, agent_output, input/output tokens, duration |
| `approval_gate` | Approval gate passes | approval_decision=approved, approval_reason, duration |
| `rejection` | Workflow rejected | approval_decision=rejected, approval_reason, status=rejected |
| `timeout` | Approval timeout | approval_decision=timeout, status=timeout |
| `error` | Step fails | error_message, status=error, duration |

**Storage:** Each Evidence appended to WorkflowRun.evidence array (ordered chronologically, never modified/deleted).

**Acceptance Criteria:**
- ✓ Evidence structure defined normatively (no ambiguity)
- ✓ One Evidence per step
- ✓ All required fields populated
- ✓ Timestamps ISO-8601 UTC
- ✓ Evidence retrieved deterministically (same step → same evidence)

---

#### 4. Migration 003 — Workflow Schema

**Ownership & Responsibility:**

Task-013 (BUILDER) is responsible for:
1. **Creating** the migration file: `shared/storage/src/migrations/migration_003_workflow_schema.sql`
2. **NOT executing** the migration (OrthoDatabase.migrate() handles execution)
3. **Rollback-safe:** Schema is append-only (new tables only, no ALTER existing)
4. **Cleanup during rollback:** BUILDER's rollback plan includes table DROP commands

**Migration File Location:** `shared/storage/src/migrations/migration_003_workflow_schema.sql`

**Schema Definition:**

```sql
-- Migration 003: Workflow Schema
-- Tracks execution plans, workflow runs, and orchestration state
-- Append-only: new tables only, no changes to existing schema

CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    intent TEXT NOT NULL,
    intent_class TEXT NOT NULL,
    execution_plan_json TEXT NOT NULL,  -- full ExecutionPlan serialized as JSON
    status TEXT NOT NULL CHECK(status IN ('pending','running','awaiting_approval','rejected','complete','failed')),
    started_at TEXT NOT NULL,  -- ISO-8601 UTC timestamp
    completed_at TEXT,  -- ISO-8601 UTC timestamp (NULL if in-progress)
    evidence_json TEXT NOT NULL DEFAULT '[]',  -- Evidence[] serialized as JSON array
    created_by TEXT NOT NULL DEFAULT 'orchestration'  -- system identifier
);

CREATE INDEX idx_workflow_runs_repo ON workflow_runs(repo_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_started ON workflow_runs(started_at DESC);

CREATE TABLE execution_steps (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,  -- ExecutionStep.step_id (e.g., "step-1")
    agent_name TEXT NOT NULL,
    skill_names TEXT NOT NULL,  -- JSON array of skill names
    approval_gate INTEGER NOT NULL DEFAULT 0,  -- 1 if requires approval, 0 otherwise
    status TEXT NOT NULL CHECK(status IN ('pending','pending_approval','running','complete','failed','rejected')),
    result_json TEXT,  -- Agent output (JSON, optional)
    evidence_json TEXT NOT NULL DEFAULT '[]',  -- Evidence[] serialized as JSON array
    started_at TEXT NOT NULL,  -- ISO-8601 UTC timestamp
    completed_at TEXT  -- ISO-8601 UTC timestamp (NULL if in-progress)
);

CREATE INDEX idx_execution_steps_workflow ON execution_steps(workflow_run_id);
CREATE INDEX idx_execution_steps_status ON execution_steps(status);
CREATE INDEX idx_execution_steps_step_id ON execution_steps(step_id);

CREATE TABLE approval_gates (
    id TEXT PRIMARY KEY,
    workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    step_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','timeout')),
    decision_reason TEXT,  -- Human-provided reason for approval/rejection
    created_at TEXT NOT NULL,  -- ISO-8601 UTC timestamp
    decided_at TEXT  -- ISO-8601 UTC timestamp (NULL if pending)
);

CREATE INDEX idx_approval_gates_workflow ON approval_gates(workflow_run_id);
CREATE INDEX idx_approval_gates_step ON approval_gates(step_id);

-- Ledger entry for migration tracking (optional, for debugging)
INSERT INTO schema_migrations (version, description, applied_at)
VALUES (3, 'Workflow schema: workflow_runs, execution_steps, approval_gates', datetime('now', 'utc'));
```

**Schema Invariants:**

1. **Append-only:** No ALTER TABLE on existing tables from task-011/010/009/008
2. **Foreign keys:** Enforce referential integrity (ON DELETE CASCADE for workflow_runs)
3. **Timestamps:** All in ISO-8601 UTC (no local timezone)
4. **JSON columns:** Serialized Evidence and ExecutionPlan objects (not normalized)
5. **Status values:** Exactly match formal state transition table (no extra values)

**Acceptance Criteria:**
- ✓ Migration file created in shared/storage/src/migrations/
- ✓ BUILDER executes migration during implementation (via OrthoDatabase.migrate())
- ✓ Schema validated in VERIFIER (CREATE TABLE statements idempotent, FK constraints work)
- ✓ Rollback drops tables explicitly (documented in rollback-plan.md)

**Class:** `WorkflowStateStore`

```python
class WorkflowStateStore:
    def __init__(self, db: OrthoDatabase):
        self.db = db
    
    def create_run(self, repo_id: str, intent: str, plan: ExecutionPlan) -> WorkflowRun:
        """Create new workflow run in DB.
        
        Inserts into workflow_runs table with:
        - id: generated UUID
        - status: "pending"
        - execution_plan_json: serialized ExecutionPlan
        - started_at: current ISO-8601 UTC timestamp
        - evidence_json: empty array []
        
        Returns: WorkflowRun object
        """
        ...
    
    def get_run(self, run_id: str) -> WorkflowRun:
        """Load workflow run from DB (with all steps and evidence)."""
        ...
    
    def update_run_status(self, run_id: str, status: str) -> None:
        """Update workflow run status.
        
        Validates transition against formal state transition table.
        Raises InvalidStateTransition if invalid.
        Updates completed_at if status is terminal (complete/failed/rejected).
        """
        ...
    
    def update_step_status(self, run_id: str, step_id: str, status: str) -> None:
        """Update execution step status.
        
        Valid statuses: pending, pending_approval, running, complete, failed, rejected
        Updates started_at on first transition to running.
        Updates completed_at on transition to complete/failed/rejected.
        """
        ...
    
    def append_evidence(self, run_id: str, step_id: str, evidence: Evidence) -> None:
        """Append evidence artifact to workflow run.
        
        Appends to workflow_runs.evidence_json array (not to execution_steps table).
        Maintains chronological order.
        """
        ...
    
    def create_approval_gate(self, run_id: str, step_id: str) -> str:
        """Create approval gate record.
        
        Inserts into approval_gates table with:
        - id: generated UUID
        - status: "pending"
        - created_at: current ISO-8601 UTC timestamp
        
        Returns: gate_id
        """
        ...
    
    def decide_approval_gate(self, gate_id: str, approved: bool, reason: str = "") -> None:
        """Record approval/rejection decision.
        
        Updates approval_gates row:
        - status: "approved" or "rejected"
        - decision_reason: reason string
        - decided_at: current ISO-8601 UTC timestamp
        """
        ...
    
    def list_runs(self, repo_id: str, limit: int = 10) -> list[WorkflowRun]:
        """List past workflow runs for repo (ordered by started_at DESC)."""
        ...
```

**Acceptance Criteria:**
- ✓ All CRUD operations atomic (single transaction per operation)
- ✓ Workflow runs resumable (load from DB, continue from pending step)
- ✓ Evidence appended in chronological order (never deleted/modified)
- ✓ Status transitions validated against formal table (no invalid combos)
- ✓ Approval gates tracked independently (separate table)
- ✓ All timestamps ISO-8601 UTC (consistent format)

#### 5. Step Runner (Agent Invocation)

**Function:** `run_step()`

```python
def run_step(
    step: ExecutionStep,
    agent: AgentManifest,
    skills: list[SkillManifest],
    context_package: ContextPackage,  # stub: empty for now
    llm_client,
) -> StepResult:
    """Run a single orchestration step.
    
    Steps:
    1. Assemble system_prompt (agent.md system_prompt + skill content)
    2. Assemble user_message from step.produces key
    3. Call llm_client.complete(system=..., user=..., max_tokens=8192)
    4. Parse response (structured output if JSON, raw text otherwise)
    5. Collect evidence (prompt, response, tokens, timestamp)
    6. Return StepResult(output, evidence)
    
    Error handling:
    - Timeout (>60s): raise TimeoutError
    - LLM error: raise LLMError with message
    - Parsing error (malformed JSON): return raw text as fallback
    """
    ...

@dataclass
class StepResult:
    agent_output: str               # LLM response (raw or parsed)
    evidence: Evidence              # prompt, response, tokens, timestamp
    status: str                     # "success" or "error"
    error_message: str | None       # if status == "error"
```

**Acceptance Criteria:**
- ✓ System prompt assembled from agent.md + skill.md content
- ✓ Context package injected into user_message (stubbed: empty dict for now)
- ✓ LLM timeout respected (60s default, configurable)
- ✓ Evidence captured (prompt, response, token count, timestamp)
- ✓ Structured output parsing optional (JSON if present, raw fallback)
- ✓ Error types explicit (TimeoutError, LLMError, ParsingError)

#### 6. CLI Integration — Five New Commands

**Command:** `ortho run "<intent>" [--dry-run]`

```bash
ortho run "add rate limiting to the auth service"
→ Classifies intent, builds plan, runs (with approval gates)

ortho run --dry-run "add rate limiting to the auth service"
→ Shows plan without executing
```

**Output:**
- Execution plan (agents, skills, steps)
- Running status (current step, approval gate status)
- Evidence links (where to find logs)

**Command:** `ortho status`

```bash
ortho status
→ Shows current workflow state (awaiting approval, running, complete, etc.)
```

**Output:**
- Current run_id
- Current step
- Status (pending, running, awaiting_approval, complete)
- Time elapsed

**Command:** `ortho approve [--reason "<text>"]`

```bash
ortho approve
→ Approve pending approval gate, resume workflow
```

**Output:**
- Confirmation (step approved)
- Next step starting

**Command:** `ortho reject "<reason>"`

```bash
ortho reject "Need more context on auth design"
→ Reject current step, mark workflow as failed
```

**Output:**
- Confirmation (workflow rejected)
- Reason logged

**Command:** `ortho history [--id <run-id>] [--limit N]`

```bash
ortho history
→ List last 10 workflow runs

ortho history --id <run-id>
→ Show details for specific run (steps, evidence, status)
```

**Output:**
- Run list (id, intent, status, timestamp, result)
- Detail view if --id provided

**Acceptance Criteria:**
- ✓ All commands callable without errors
- ✓ API endpoints exist and return JSON
- ✓ State transitions working (dry-run → approve → resume)
- ✓ History persisted and retrievable
- ✓ Approval gates block until approved/rejected

---

## Acceptance Criteria (All 5 Tasks)

### Task 1: SelectorEngine
- [ ] `score_agents()` returns dict[str → float] with correct formula
- [ ] `score_skills()` hard-excludes if over token budget
- [ ] Deterministic (same input → same output)
- [ ] Tests: agent scoring, skill scoring, boundary cases (0 score, missing context, over-budget)

### Task 2: ExecutionPlan Builder
- [ ] `build_plan()` selects agents ≥0.5, skills >0.3
- [ ] Agents ordered by workflow type (architect first for feature_dev)
- [ ] Tokens summed correctly
- [ ] human_approval_required set correctly per intent type

### Task 3: WorkflowExecutor + State Store
- [ ] Execute plan step-by-step in order
- [ ] Pause at approval gates, wait for callback
- [ ] Resume after restart (load from DB)
- [ ] Evidence collected per step
- [ ] State store CRUD operations atomic

### Task 4: Step Runner
- [ ] Assemble system_prompt (agent + skills)
- [ ] Call LLM with context package
- [ ] Evidence captured (prompt, response, tokens)
- [ ] Error handling (timeout, LLM error, parse error)

### Task 5: CLI Commands
- [ ] `ortho run "<intent>"` works end-to-end
- [ ] `ortho run --dry-run` shows plan
- [ ] `ortho status` shows current state
- [ ] `ortho approve` resumes workflow
- [ ] `ortho reject` marks failed
- [ ] `ortho history` lists runs

---

## Expected Test Metrics

| Category | Count | Examples |
|----------|-------|----------|
| Unit tests (selector) | 12+ | score_agent, score_skill, budget exclusion, determinism |
| Unit tests (executor) | 15+ | state transitions, approval gate, resume, error handling |
| Integration tests | 10+ | full flow from intent → plan → execution, approval gate workflow |
| Property-based tests | 5+ | diverse intents, random agent/skill combinations, token budgets |
| Real-repo tests | 2+ | `ortho run` against actual codebase end-to-end |
| **Total** | **44+** | — |
| **Expected coverage** | **≥85%** | selector, executor, step_runner modules |
| **Expected pass rate** | **100%** | all tests pass or marked xfail |

---

## Known Limitations (NONE — All ACs implemented)

If limitations arise during BUILDER phase, document them here (none expected for this feature).

---

## Files to Create/Modify

### Create
- `packages/orchestration/src/selector/__init__.py`
- `packages/orchestration/src/selector/engine.py`
- `packages/orchestration/src/executor/__init__.py`
- `packages/orchestration/src/executor/workflow_executor.py`
- `packages/orchestration/src/executor/state_store.py`
- `packages/orchestration/src/executor/step_runner.py`
- `packages/orchestration/src/executor/evidence_collector.py`
- `packages/orchestration/tests/test_selector_engine.py`
- `packages/orchestration/tests/test_workflow_executor.py`
- `packages/orchestration/tests/test_integration.py`
- `apps/cli/src/commands/run.ts`
- `apps/cli/src/commands/status.ts`
- `apps/cli/src/commands/approve.ts`
- `apps/cli/src/commands/reject.ts`
- `apps/cli/src/commands/history.ts`
- `apps/api-server/src/routers/orchestration.py`
- `shared/storage/src/migrations/migration_003_workflow_schema.sql`

### Modify
- `packages/orchestration/pyproject.toml` — add any new dependencies (none expected)
- `apps/cli/src/index.ts` — register new commands
- `apps/api-server/src/main.py` — register new router
- `.ases/architecture/adrs/` — create ADR-014 if needed (pure Python selector, no LLM)

### Do NOT Modify
- task-012 artifacts (Intent Router, AgentRegistry, SkillRegistry)
- Pillar 1-3 packages (no changes to repo-intelligence, context-hub, arch-intelligence)
- Existing commands (scan, index, analyze, context, init)
- Database schema except migration 003

---

## Data Flow (Execution)

```
ortho run "add rate limiting"
    ↓
IntentRouter.classify() → IntentClassification
    ↓
SelectorEngine.score_agents() → dict[agent → score]
SelectorEngine.score_skills() → dict[skill → score]
    ↓
SelectorEngine.build_plan() → ExecutionPlan
    ↓
WorkflowExecutor.execute(plan)
    ↓
For each ExecutionStep:
    1. If step.approval_gate: pause, wait for on_approval_gate() callback
    2. run_step(step) → invoke agent with context + skills
    3. Collect evidence (prompt, response, tokens)
    4. Update step status
    ↓
WorkflowRun.status = "complete"
    ↓
Return final WorkflowRun to CLI
```

---

## Security & Error Handling

- **LLM Input:** Agent system_prompt and user_message do NOT contain user code — they reference context packages assembled by token optimizer (task-014), which performs input validation
- **LLM Timeout:** Default 60s, configurable. Prevent hangs.
- **State Atomicity:** All DB writes atomic (single transaction per step update)
- **Approval Gate:** Requires explicit human action (cannot be automated or bypassed)
- **Error Propagation:** Step error marks workflow failed, doesn't auto-retry or continue

---

## Formal Definitions Summary

This specification introduces four formal definitions to eliminate planning ambiguities:

### 1. Deterministic Workflow Ordering Algorithm
- **Section:** "Deterministic Workflow Ordering Algorithm" (above Core Components)
- **Defines:** How agents are assigned to workflow stages, how ties are broken, how custom agents are inserted
- **Invariant:** Same intent + selected agents → identical step order (deterministic)
- **Implementation:** ExecutionPlan.build_plan() must follow this algorithm exactly

### 2. Formal State Transition Table
- **Section:** "3. Formal State Transition Table" (WorkflowExecutor)
- **Defines:** Every valid state transition, terminal states, invalid transitions, resume behavior
- **Invariant:** WorkflowExecutor validates all transitions against this table
- **Implementation:** Each state transition raises InvalidStateTransition if not in table

### 3. Approval Gate Semantics
- **Section:** "3.1 Approval Gate Semantics" (WorkflowExecutor)
- **Defines:** Approval occurs before step execution, each gate independent, rejection is terminal
- **Invariant:** Only one approval gate active at a time; subsequent gates require separate approval
- **Implementation:** Approval gate pauses workflow, blocks on on_approval_gate callback, transitions to awaiting_approval state

### 4. Evidence Contract
- **Section:** "3.3 Evidence Contract" (WorkflowExecutor)
- **Defines:** Required Evidence fields, evidence types, generation invariants
- **Invariant:** One Evidence artifact per step; fields deterministic; timestamps ISO-8601 UTC
- **Implementation:** Every step generates exactly one Evidence (either execution, approval, rejection, timeout, or error)

### 5. Migration 003 Ownership
- **Section:** "4. Migration 003 — Workflow Schema"
- **Defines:** BUILDER creates migration file, OrthoDatabase executes it, BUILDER handles rollback cleanup
- **Invariant:** Schema append-only (new tables only), no ALTER existing tables
- **Implementation:** Task-013 creates `migration_003_workflow_schema.sql`, VERIFIER validates execution

---

## Consistency Verification Checklist

- [x] **Workflow ordering is fully deterministic:** Algorithm specified, tie-breaking rules defined, custom agents handled
- [x] **Approval behavior is unambiguous:** Approval before execution, per-gate independence, rejection is terminal, multiple gates supported
- [x] **State transitions are formally defined:** Normative transition table with all valid/invalid transitions, resume behavior explicit
- [x] **Evidence generation follows one contract:** Dataclass structure defined, one artifact per step, evidence types enumerated
- [x] **Migration ownership is documented consistently:** BUILDER creates, OrthoDatabase executes, rollback cleanup documented in rollback-plan.md

---

*End of GATE 1 Spec (Refined)*
