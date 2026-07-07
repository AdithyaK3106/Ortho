# ADR-014: Pure Python Selector (No LLM in Routing)

**Date:** 2026-07-07  
**Author:** ARCHITECT (task-013 GATE 2)  
**Status:** Proposed  
**Related:** FRD §9 (Pillar 4), §11 (Selector System, Stage 4), ADR-013 (semantic-router Stage 1)

---

## Context

Ortho's orchestration layer has two stages of intent classification/routing:

1. **Stage 1 — Intent Router (task-012, ADR-013):** Semantic-router (no LLM) for fast classification
2. **Stage 4 — Selector Engine (task-013, this ADR):** Must select agents and skills from intent class

FRD §11.4 specifies Selector Engine as "Pure Python. No LLM. Scores agents and skills, builds the execution plan."

**Question:** Should SelectorEngine call an LLM to rank agents/skills semantically, or use pure Python scoring?

---

## Decision

**SelectorEngine uses pure Python scoring. No LLM calls.**

**Algorithm (deterministic, rule-based):**

```python
# Agent Scoring
score(agent) = (intent_trigger_match: 1.0)
             + (priority_weight: 0.3|0.15|0.0)
             + (semantic_similarity: 0.5 * similarity)
             - (context_penalty: 0.2 × num_missing_context)

# Skill Scoring
score(skill) = (agent_type_match: 0.8)
             + (intent_trigger_match: 0.6)
             + (preferred_by_agent: 0.4)
# Hard exclude if: skill.tokens > remaining_budget

# Tie-Breaking
order_by = (stage, score DESC, name ASC)
```

**No LLM involved.** SelectorEngine is deterministic (same intent + agents → identical plan).

---

## Consequences

### Positive

- ✓ **Deterministic:** Same inputs produce identical execution plans (repeatable, testable)
- ✓ **Fast:** No API latency; typical runtime <100ms
- ✓ **Testable:** Pure functions; no mock LLM needed
- ✓ **Offline-capable:** No API key, no rate limits, no network dependency
- ✓ **FRD Compliance:** Directly implements §11.4 specification
- ✓ **Composable:** Easy to swap scoring weights without code changes
- ✓ **Verifiable:** Output (ExecutionPlan) is auditable and reproducible

### Negative

- ✗ **Accuracy Trade-off:** Scoring accuracy depends on hand-tuned weights; less flexible than LLM
- ✗ **Limited Semantics:** Cannot understand nuanced intent variations (e.g., "refactor for performance" vs. "refactor for maintainability" scored identically)
- ✗ **Maintenance Burden:** Weights may need tuning empirically; no automatic adaptation
- ✗ **Expansion Cost:** Adding new agent types requires formula updates

### Constraints

- No tuning of weights without code changes (scoring formula is in spec.md, not database)
- Scoring formula must remain deterministic (no randomness, no temporal effects)
- Custom agents must fit into existing stage model (cannot override stage assignment)

---

## Alternatives Considered

### 1. LLM-Based Selector
**Concept:** Call Claude to "rank these agents for this intent"

**Pros:**
- More flexible (handles nuanced variations)
- Self-adapting (learns from feedback)
- Semantic understanding

**Cons:**
- Non-deterministic (LLM stochasticity, temperature sampling)
- Slow (API latency 500ms–5s)
- Requires API key, subject to rate limits
- Harder to test and debug
- Violates FRD §11.4 ("Pure Python")
- Adds cost (LLM API calls per execution plan)

**Verdict:** Rejected. Contradicts FRD and determinism requirement.

---

### 2. Hybrid Approach (Semantic Router + LLM Fallback)
**Concept:** Use semantic-router (fast, no LLM) for agent selection; LLM fallback if ambiguous

**Pros:**
- Fast in common case (semantic-router)
- Flexible in edge cases (LLM fallback)
- Combines benefits of both approaches

**Cons:**
- Already implemented at Stage 1 (IntentRouter, ADR-013)
- Unnecessary duplication at Stage 4
- Introduces non-determinism (fallback path different from fast path)
- Violates "Pure Python" spec (LLM in fallback)

**Verdict:** Rejected. Duplication of IntentRouter logic; contradicts spec.

---

### 3. Simple Threshold Matching
**Concept:** For each intent type, hard-code agent list (e.g., "feature_dev" → [architect, coder, tester, reviewer])

**Pros:**
- Simplest implementation
- Fully deterministic

**Cons:**
- No scoring/ranking (agents equally weighted)
- No skill selection
- No token budget awareness
- Cannot handle custom agents
- Violates FRD §11.4 ("scores agents and skills, builds the execution plan")

**Verdict:** Rejected. Insufficient (must rank agents, select skills, estimate tokens).

---

### 4. Machine Learning (Offline Trained)
**Concept:** Train a lightweight model on past intent/agent decisions; use at runtime

**Pros:**
- Deterministic (once trained)
- Fast
- Flexible

**Cons:**
- Requires training data (not available in Phase 3)
- Model maintenance burden
- Overkill for Phase 3 (spec is simple enough for rule-based scoring)
- Cannot adapt to new custom agents without retraining

**Verdict:** Deferred. Not appropriate for Phase 3.

---

## Why This Decision

**FRD §11.4 is explicit:**

> "Stage 4 — Selector Engine
> Pure Python. No LLM. Scores agents and skills, builds the execution plan."

**Determinism is mandatory** (from FRD §1 "Evidence before confidence," ASES principle "Verify before deploy"):

- Execution plan must be reproducible
- Test results must be repeatable
- Debugging must be auditable
- No "LLM said so" as explanation

**Semantic routing is already handled** by Stage 1 (IntentRouter, task-012):

- IntentRouter uses semantic-router for fast intent classification
- This provides semantic understanding at the classification layer
- Stage 4 can be pure Python (lower stakes, already narrowed to one intent class)

---

## Implementation Notes

**Scoring weights are in spec.md (not code):**
- Intent trigger match: +1.0
- Priority weight: {high: +0.3, medium: +0.15, low: +0.0}
- Semantic similarity: +0.5 * (0.0–1.0)
- Context penalty: −0.2 per missing required context
- Skill agent_type match: +0.8
- Skill intent_triggers: +0.6
- Skill preferred: +0.4
- Hard budget exclusion: score = 0 if tokens > remaining

**Semantic similarity (used in agent scoring):**
- For now: simple keyword matching (agent description vs. intent text)
- Alternative later: embed descriptions + intent with shared embedding model
- Either way: must remain fast (<10ms) and deterministic

---

## Future Reconsideration

**Re-evaluate if:**
- Scoring accuracy drops measurably (empirical evaluation, task-015+)
- Custom agents frequently select wrong skills
- New intent types have conflicting scoring patterns
- Performance requirements change (e.g., sub-10ms becomes unachievable)

**Reconsideration would require:**
- Evidence of accuracy problem (metrics from Phase 4+)
- Cost/benefit analysis (LLM cost vs. accuracy gain)
- Alternative with determinism preserved (e.g., lightweight learned model)

---

## Related Decisions

| ADR | Decision | Relationship |
|---|---|---|
| ADR-013 | Semantic-router for IntentRouter (Stage 1) | Complementary: Stage 1 has LLM fallback (llm_classify_intent stub); Stage 4 is pure Python |
| ADR-011 | Scan persistence (SQLite) | ExecutionPlan persisted to workflow_runs.execution_plan_json; determinism enables resumable workflows |

---

## Sign-Off

**ARCHITECT:** Recommends APPROVED  
**Rationale:** FRD-compliant, deterministic, testable, meets Phase 3 requirements  

**Status:** Proposed (awaiting human approval GATE 2)

---

*End of ADR-014*
