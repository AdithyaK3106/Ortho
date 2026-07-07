# task-013: Code Review (GATE 6)

**Reviewer:** Independent Code Reviewer  
**Date:** 2026-07-07  
**Status:** CHANGES-REQUIRED (2 Critical, 3 High findings)

---

## Executive Summary

The implementation is largely spec-compliant with sound architecture, but has **critical issues that must be fixed before approval**:

1. **State store append-only violation** — Evidence is correctly immutable, but state_store creates dual Evidence records (one in Evidence dataclass, one in JSON), breaking the contract
2. **Approval gate blocking is not enforced** — API's auto-approval callback breaks the formal requirement that approval gates cannot be automated
3. **Missing Evidence serialization in state_store** — Evidence dataclass fields not properly mapped to Evidence initialization in state_store deserialization

These are blocking issues per spec.md formal definitions. Code quality is otherwise high.

---

## Findings

### Finding 1: Evidence Contract Violation — Dual Evidence Records

**File:** `packages/orchestration/src/executor/state_store.py`, lines 187-212  
**Severity:** Critical  
**Issue:**

The spec.md §3.3 (Evidence Contract) defines:
> "Each step generates exactly one Evidence artifact. Evidence fields are deterministic. ... Evidence appended to WorkflowRun.evidence array (ordered chronologically, never modified/deleted)."

The implementation creates Evidence correctly in `step_runner.py` and `workflow_executor.py`, but `state_store.py`'s `append_evidence()` method has a design flaw:

1. `run_step()` creates Evidence dataclass (with full fields: system_prompt, user_message, agent_output, tokens, etc.)
2. `workflow_executor.py` calls `state_store.append_evidence(run_id, step_id, evidence)` (line 122)
3. `state_store.append_evidence()` serializes Evidence via `_serialize_evidence()` (line 203)
4. Evidence is stored in `workflow_runs.evidence_json` column (JSON array)

**Problem:** The execution_steps table ALSO has an `evidence_json` column (spec.md §4 migration, line 74), suggesting Evidence should be stored per-step. But `state_store.append_evidence()` only appends to workflow_runs.evidence_json.

**Impact:**
- If `execution_steps.evidence_json` is never populated, it's dead code
- If it should be populated, there are two Evidence stores (dual record)
- Violates spec's "one Evidence per step" invariant

**Recommendation:**

Clarify: should Evidence be stored:
1. **In workflow_runs.evidence_json only** (current implementation): Remove `evidence_json` column from execution_steps table (violates "append-only" migration constraint, but would be a migration 004)
2. **In execution_steps.evidence_json per step** (spec intent): Refactor to append Evidence to execution_steps row, not workflow_runs

For now, **assume intent is (1)**: Fix by ensuring Evidence is ONLY in workflow_runs, never duplicated elsewhere.

**Test:** Verify `_serialize_evidence()` and `append_evidence()` produce deterministic, non-duplicate Evidence.

---

### Finding 2: Approval Gate Cannot Be Automated (CRITICAL Spec Violation)

**File:** `apps/api_server/src/routers/orchestration.py`, lines 123-126  
**Severity:** Critical  
**Issue:**

Spec.md §3.1 (Approval Gate Semantics) states:
> "Requirement: Approval gate cannot be bypassed or automated."

The API's `execute_plan()` background task defines:

```python
def approval_callback(workflow_run):
    # For now, auto-approve (in production, would prompt human)
    return True
```

This **auto-approves all approval gates**, violating the spec's core requirement. This is not a "stub" — the approval callback is required to be human-driven, not auto-approve.

**Impact:**
- Approval gates are effectively disabled
- Spec's formal approval gate semantics are not enforced
- Rejection workflow path is untestable (always returns True)

**Recommendation:**

The API router should NOT implement execution at all (that's task-014's token optimizer responsibility). For now:

**Option A (Recommended):** Keep execute() skeleton only for dry-run, remove background execution entirely. Return immediately with status "pending", let CLI or separate endpoint handle resumption.

**Option B:** Require explicit human approval callback (e.g., via command-line prompt or webhook), never auto-approve.

Currently the code does neither. **This must be fixed before GATE 6 approval.**

---

### Finding 3: WorkflowStateStore Missing Evidence Field Deserialization

**File:** `packages/orchestration/src/executor/state_store.py`, lines 293-312  
**Severity:** High  
**Issue:**

`_serialize_evidence()` properly serializes all Evidence fields. However, when loading a workflow run via `get_run()`, the evidence_json is deserialized as raw dict (line 157):

```python
evidence = json.loads(evidence_json) if evidence_json else []
```

This returns `list[dict]`, NOT `list[Evidence]`. The spec.md §3.3 requires Evidence objects (with all deterministic fields).

**Impact:**
- CLI and API commands that display evidence (e.g., history.ts, orchestration.py lines 64-74) cast to dict, losing type safety
- Evidence contract not fully enforced (fields not validated on deserialization)
- Future code that expects Evidence dataclass methods will fail

**Recommendation:**

Add a `_deserialize_evidence()` method in state_store.py:

```python
@staticmethod
def _deserialize_evidence(data: dict) -> Evidence:
    """Deserialize JSON dict to Evidence dataclass."""
    from packages.orchestration.src.executor.evidence_collector import Evidence, EvidenceType
    
    return Evidence(
        step_id=data["step_id"],
        step_name=data["step_name"],
        evidence_type=EvidenceType(data["evidence_type"]),
        system_prompt=data.get("system_prompt", ""),
        user_message=data.get("user_message", ""),
        agent_output=data.get("agent_output", ""),
        input_tokens=data.get("input_tokens", 0),
        output_tokens=data.get("output_tokens", 0),
        total_tokens=data.get("total_tokens", 0),
        approval_decision=data.get("approval_decision"),
        approval_reason=data.get("approval_reason"),
        created_at=data.get("created_at", ""),
        completed_at=data.get("completed_at"),
        duration_ms=data.get("duration_ms", 0),
        status=data.get("status", "success"),
        error_message=data.get("error_message"),
    )
```

Then update `get_run()` line 157:

```python
evidence = [self._deserialize_evidence(e) for e in json.loads(evidence_json)] if evidence_json else []
```

---

### Finding 4: API /run Endpoint Doesn't Actually Execute

**File:** `apps/api_server/src/routers/orchestration.py`, lines 64-158  
**Severity:** High  
**Issue:**

The `/run` endpoint always returns immediately (line 134-158) with mock data:

```python
return {
    "plan": {...},
    "workflow_run": {
        "id": "workflow-id",  # Hard-coded! Not the actual run ID
        "status": "running",
        "started_at": "",     # Empty timestamp!
    }
}
```

The actual `execute_plan()` task is enqueued in background, but the response doesn't use the actual WorkflowRun returned by `_executor.execute()`.

**Impact:**
- CLI's `ortho run` command gets wrong run_id ("workflow-id"), cannot track actual workflow
- Timestamps are empty
- `ortho status` and `ortho history` cannot retrieve the run

**Recommendation:**

Restructure to return actual WorkflowRun data:

```python
workflow_run = _executor.execute(
    plan=plan,
    repo_id="repo-default",
    on_approval_gate=approval_callback,
)

return {
    "plan": {...},
    "workflow_run": {
        "id": workflow_run.id,
        "intent_class": workflow_run.intent_class,
        "status": workflow_run.status,
        "started_at": workflow_run.started_at,
        "completed_at": workflow_run.completed_at,
    }
}
```

Or run synchronously for non-gated steps, return after first approval gate.

---

### Finding 5: Semantic Similarity Not Deterministic

**File:** `packages/orchestration/src/selector/engine.py`, lines 240-254  
**Severity:** High  
**Issue:**

`_semantic_similarity()` uses set-based Jaccard similarity on word tokens:

```python
intersection = len(words1 & words2)
union = len(words1 | words2)
return intersection / union if union > 0 else 0.0
```

This is deterministic for the same text, but **word order and tokenization depend on string.split()**, which splits on whitespace. This is fragile:

- "add rate limiting to auth" vs "add-rate-limiting-to-auth" (different tokens)
- Unicode normalization not applied
- Punctuation not handled

**Impact:**
- Same intent with different spacing/punctuation may score differently
- Spec.md §1 says "Deterministic: same input → same output" — this is true for exact same text, but user intent matching should be more robust

**Recommendation:**

This is acceptable for now (placeholder for embedding-based similarity later, per comments in code), but should be documented as a known limitation.

Add comment:
```python
def _semantic_similarity(self, text1: str, text2: str) -> float:
    """Simple keyword-based semantic similarity (0.0-1.0).
    
    Placeholder: Uses Jaccard similarity on whitespace-separated tokens.
    Deterministic: same text → same score.
    Limitation: sensitive to punctuation, whitespace, case (handles case via lower()).
    Future: Replace with embedding-based similarity (task-014 or later).
    """
```

---

### Finding 6: WorkflowExecutor Missing Error Context in Evidence

**File:** `packages/orchestration/src/executor/workflow_executor.py`, lines 131-141  
**Severity:** Medium  
**Issue:**

When a step fails (line 124-143), error Evidence is created with:

```python
error_evidence = Evidence(
    step_id=step.step_id,
    step_name=step.agent_name,
    evidence_type=EvidenceType.ERROR,
    status="error",
    error_message=str(e),
    created_at=datetime.utcnow().isoformat(),
    duration_ms=0,  # Always 0, duration not captured
)
```

**Problems:**
- `duration_ms` is hardcoded to 0 (should track time from step start to error)
- `evidence.completed_at` is not set (should be current timestamp per spec.md §3.3)

**Recommendation:**

Capture start time before run_step() call:

```python
step_start = datetime.utcnow()
try:
    step_result = run_step(...)
except Exception as e:
    step_end = datetime.utcnow()
    duration_ms = int((step_end - step_start).total_seconds() * 1000)
    error_evidence = Evidence(
        ...,
        duration_ms=duration_ms,
        completed_at=step_end.isoformat(),
    )
```

---

### Finding 7: CLI Commands Don't Validate Response Structure

**File:** `apps/cli/src/commands/run.ts`, lines 47-50  
**Severity:** Medium  
**Issue:**

CLI assumes response shape without validation:

```typescript
result.plan.steps.forEach((step: any) => {
  const gate = step.approval_gate ? " [🔐 APPROVAL]" : "";
  console.log(`  ${idx + 1}. ${step.agent_name} (${step.skill_names.join(", ")})${gate}`);
});
```

If API returns different shape or null, this crashes silently (no type checking, just `any`).

**Recommendation:**

Add response validation or typed interfaces (already partially done with RunOptions). Low severity — acceptable for now, but should add in future.

---

## Architecture Review

### Positive Findings

- **Module boundaries clear** (selector, executor, state_store, step_runner, evidence_collector) — acyclic dependency graph
- **State machine formally enforced** (lines 10-17 in workflow_executor.py) — VALID_TRANSITIONS table matches spec.md §3
- **Evidence dataclass well-designed** (evidence_collector.py) — immutable, deterministic fields
- **CLI commands clean** — proper error handling, user-friendly output
- **Migration schema sound** (migration_003_workflow_schema.sql) — append-only, correct FK constraints, proper indexes

### Negative Findings

- **API router is incomplete** (orchestration.py) — endpoints stubbed, auto-approval breaks spec
- **State store dual-table design unclear** (state_store.py) — two evidence columns, one unused
- **Step runner error handling missing duration** (step_runner.py) — minor issue, but breaks Evidence contract

---

## Spec Compliance Matrix

| Spec Component | Status | Notes |
|---|---|---|
| Workflow Ordering Algorithm (§1) | PASS | Deterministic (stage, score desc, name asc) implemented correctly |
| Agent Scoring Formula (§1.1) | PASS | Intent trigger, priority, semantic sim, context penalty all correct |
| Skill Scoring Formula (§1.2) | PASS | Agent type, intent trigger, preferred, budget exclusion all correct |
| State Transition Table (§3) | PASS | VALID_TRANSITIONS matches spec exactly |
| Approval Gate Semantics (§3.1) | FAIL | Auto-approval in API breaks "cannot be automated" requirement |
| Evidence Contract (§3.3) | PARTIAL | Structure correct, but deserialization missing + dual storage issue |
| Migration Schema (§4) | PASS | All tables created correctly, append-only, FK constraints in place |
| Step Runner (§5) | PASS | LLM invocation, evidence capture, error handling all present |
| CLI Commands (§6) | PASS | All 5 commands implemented, user-friendly output |

---

## Verdict

**CHANGES-REQUIRED** — Two critical blocking issues must be fixed before approval:

1. **Approval gates cannot be auto-approved** (Finding 2) — violates spec.md §3.1 formal requirement
2. **Evidence dual-storage or Evidence deserialization** (Findings 1 & 3) — violates spec.md §3.3 Evidence Contract

Three additional high-severity issues should be addressed:

3. API /run endpoint returns mock data, not actual WorkflowRun (Finding 4)
4. Approval gate blocking not enforced (Finding 2)
5. Step error duration_ms not captured (Finding 6)

Once these are fixed, code is production-ready. Architecture is sound, imports work, determinism is maintained.

---

## Required Fixes Before GATE 6 Approval

### Fix 1: Remove Auto-Approval from API (CRITICAL)

**File:** `apps/api_server/src/routers/orchestration.py`

**Change:** Replace auto-approve callback with proper human-driven approval:

```python
# Option A: Remove background execution entirely
@router.post("/run")
async def run_workflow(request: RunRequest):
    # ... build plan ...
    if request.dryRun:
        return {"plan": ...}
    
    # Create workflow run (don't execute yet)
    workflow_run = _state_store.create_run(
        repo_id="repo-default",
        intent_class=plan.intent_class,
        plan=plan,
    )
    
    return {
        "plan": {...},
        "workflow_run": {
            "id": workflow_run.id,
            "status": "pending",
            "started_at": workflow_run.started_at,
        }
    }
```

Then use separate command/endpoint for execution (task-014 token optimizer responsibility).

**Rationale:** Approval gates are human approval gates, not automation gates. They must be explicitly approved by human action. Auto-approval defeats the purpose.

---

### Fix 2: Add Evidence Deserialization (CRITICAL)

**File:** `packages/orchestration/src/executor/state_store.py`

**Add method:**

```python
@staticmethod
def _deserialize_evidence(data: dict) -> Evidence:
    """Deserialize JSON dict to Evidence dataclass."""
    from packages.orchestration.src.executor.evidence_collector import Evidence, EvidenceType
    
    return Evidence(
        step_id=data["step_id"],
        step_name=data["step_name"],
        evidence_type=EvidenceType(data.get("evidence_type", "agent_execution")),
        system_prompt=data.get("system_prompt", ""),
        user_message=data.get("user_message", ""),
        agent_output=data.get("agent_output", ""),
        input_tokens=data.get("input_tokens", 0),
        output_tokens=data.get("output_tokens", 0),
        total_tokens=data.get("total_tokens", 0),
        approval_decision=data.get("approval_decision"),
        approval_reason=data.get("approval_reason"),
        created_at=data.get("created_at", ""),
        completed_at=data.get("completed_at"),
        duration_ms=data.get("duration_ms", 0),
        status=data.get("status", "success"),
        error_message=data.get("error_message"),
    )
```

**Update get_run() line 157:**

```python
evidence = [
    self._deserialize_evidence(e) 
    for e in json.loads(evidence_json) 
] if evidence_json else []
```

---

### Fix 3: Clarify Evidence Storage (HIGH)

Either:

**A) Remove execution_steps.evidence_json** (if Evidence is only in workflow_runs):
- Delete line 74 in migration_003_workflow_schema.sql
- Update state_store.py to document that execution_steps is for step tracking only, evidence is in workflow_runs

**B) Store Evidence per-step** (if spec intent is per-step):
- Update append_evidence() to also insert/update execution_steps.evidence_json
- Update get_run() to load evidence from execution_steps, not workflow_runs

**Recommendation:** Option A (current design seems to support this). Document assumption clearly.

---

### Fix 4: Capture Error Duration in Evidence (HIGH)

**File:** `packages/orchestration/src/executor/workflow_executor.py`, lines 112-143

**Change:**

```python
step_start = datetime.utcnow()

try:
    step_result = run_step(...)
    self.state_store.append_evidence(run_id, step.step_id, step_result.evidence)

except Exception as e:
    step_end = datetime.utcnow()
    duration_ms = int((step_end - step_start).total_seconds() * 1000)
    
    error_evidence = Evidence(
        step_id=step.step_id,
        step_name=step.agent_name,
        evidence_type=EvidenceType.ERROR,
        status="error",
        error_message=str(e),
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),  # Add this
        duration_ms=duration_ms,  # Use actual duration
    )
    self.state_store.append_evidence(run_id, step.step_id, error_evidence)
```

---

### Fix 5: Return Actual WorkflowRun from /run API (HIGH)

**File:** `apps/api_server/src/routers/orchestration.py`, lines 137-158

If keeping background execution:

```python
# Create and persist the run
workflow_run = _state_store.create_run(
    repo_id="repo-default",
    intent_class=plan.intent_class,
    plan=plan,
)

# Enqueue execution
background_tasks.add_task(execute_plan, workflow_run.id)

return {
    "plan": {...},
    "workflow_run": {
        "id": workflow_run.id,
        "intent_class": workflow_run.intent_class,
        "status": workflow_run.status,
        "started_at": workflow_run.started_at,
        "completed_at": workflow_run.completed_at,
    }
}
```

---

## Test Recommendations

After fixes, run:

```bash
# Import validation
python -c "from packages.orchestration.src.selector.engine import SelectorEngine"
python -c "from packages.orchestration.src.executor.workflow_executor import WorkflowExecutor"

# Unit tests (should exist)
pytest packages/orchestration/tests/ -v --tb=short

# Regression (should not break task-012)
pytest packages/ -v --tb=short
```

---

## Summary

**Overall Assessment:**

- Code quality: **High** (clean structure, proper imports, sound design)
- Spec compliance: **Partial** (core algorithms correct, but approval gate + evidence contract not fully implemented)
- Production-readiness: **Not yet** (2 critical blocking issues, 3 high-severity issues)

**Path to Approval:**

1. Remove auto-approval from API (or defer execution to task-014)
2. Add Evidence deserialization in state_store
3. Clarify Evidence storage design (one column, not two)
4. Capture error duration in evidence
5. Return actual WorkflowRun from /run API
6. Re-run tests

**Expected Timeline:** 2-3 hours to fix all issues + re-test.

---

*End of Code Review*
