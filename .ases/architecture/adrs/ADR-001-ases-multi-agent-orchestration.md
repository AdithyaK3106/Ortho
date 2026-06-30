# ADR-001: ASES as Multi-Agent Engineering System

**Status:** ACCEPTED  
**Date:** 2026-06-27  
**Author:** ARCHITECT  
**Approved by:** Human on 2026-06-27

---

## Context

Claude, when used without structure to build software, exhibits three compounding failure modes:

1. **Isolated Implementation** — Claude implements components in isolation. Function A works. Module B works. But nobody verified A and B work together with real data in real sequence. Integration is assumed, never verified.

2. **Fabricated Confidence** — When asked "does this work?", Claude pattern-matches to confidence rather than evidence. It says "yes, tested and working" because that is what a competent engineer sounds like. It has no actual evidence. It is pattern-matching to reassurance.

3. **No Honest Uncertainty** — Claude will not say "I don't know if this works end to end." It fills uncertainty with false confidence. This is structurally unavoidable without an external enforcement system.

The developer builds on top of unverified foundations. The product appears complete. When tested as a whole, it crashes. Claude then diagnoses fake fixes instead of admitting it never verified integration in the first place.

---

## Problem Statement

We need a system that:

1. **Prevents isolated implementation** — Every component must be verified to work with other components before claiming completion
2. **Prevents fabricated confidence** — Completion claims must be backed by evidence (tool output, test results, verification logs)
3. **Enforces honest uncertainty** — If something cannot be verified, the system must say so explicitly instead of guessing
4. **Separates concerns** — Different roles (planning, architecture, implementation, testing, verification, review) must be played by independent sessions with zero context carryover between roles
5. **Gates advancement** — No agent can proceed to the next stage without explicit human approval at each gate
6. **Maintains persistence** — Across multiple agent sessions, there must be a single source of truth (CLAUDE.md) that persists

---

## Alternatives Considered

### Option A: No Structure (rejected)
**Description:** Let Claude build without guardrails, assume it will do the right thing.

**Pros:**
- Fastest to implement
- No overhead or scaffolding

**Cons:**
- Leads directly to the three failure modes
- No evidence of correctness
- No verification of integration
- Fabricated confidence becomes standard practice

**Rejection Reason:** This is the current problem we're trying to solve. Structure is necessary.

### Option B: Linear Single-Agent Workflow (rejected)
**Description:** One agent handles everything (planning, coding, testing, reviewing) in sequence.

**Pros:**
- Simple to coordinate
- Context is never lost between stages

**Cons:**
- No adversarial review (can't catch own mistakes)
- Conflicts of interest (implementer also judges own implementation)
- Encourages cutting corners ("I'm confident this is right")
- Single source of error (mistakes propagate through all stages)

**Rejection Reason:** Lack of independence allows unconscious bias and prevents critical review.

### Option C: Multi-Agent with Role Separation (chosen) ✓
**Description:** Six independent agents (PLANNER, ARCHITECT, BUILDER, TEST-DESIGNER, VERIFIER, REVIEWER) each in separate sessions with zero context carryover. Handoffs via persistent artifacts on disk. Evidence gates prevent advancement.

**Pros:**
- ✓ Role separation prevents conflicts of interest
- ✓ Fresh-session reviews (adversarial, catch mistakes)
- ✓ Evidence requirements prevent false claims
- ✓ Each agent has single responsibility
- ✓ Human gates block bad work before it advances
- ✓ Explicit uncertainty (if we can't verify it, we say so)

**Cons:**
- ✗ More complex to coordinate
- ✗ More overhead (multiple sessions, artifacts)
- ✗ Requires structured handoffs

**Selection Reason:** The problems we're solving (confidence without evidence, integration failures, isolated implementation) are exactly what this structure prevents. The overhead is worth it.

---

## Decision

ASES is a multi-agent engineering operating system that runs inside Claude CLI. It transforms a single Claude session into a disciplined multi-agent team through:

1. **Six Independent Agents:**
   - PLANNER — Translates requirements into specifications
   - ARCHITECT — Validates architecture, maintains ADRs
   - BUILDER — Implements to spec, reads rollback-plan.md first
   - TEST-DESIGNER — Writes tests independently (zero BUILDER context)
   - VERIFIER — Produces evidence, interprets it honestly (two modes)
   - REVIEWER — Adversarial code review (zero BUILDER context)

2. **Artifact-Driven Handoffs:**
   - Each agent reads from files on disk (`.ases/tasks/[task-id]/`)
   - Each agent writes to files on disk (plans, specs, code, tests, reports)
   - No context passes between agents except through files

3. **Evidence-Gated Completion:**
   - No agent can claim completion without evidence
   - Evidence is terminal output (compiler, linter, tests) saved to timestamped log files
   - Claude never generates evidence, only interprets it
   - Human must spot-check log files directly

4. **Five Explicit Gates:**
   - Gate 1: Plan Approval (human reviews plan.md, spec.md, rollback-plan.md)
   - Gate 2: Architecture Approval (human reviews architecture-review.md)
   - Gate 3: Scope Review (human checks implementation-notes.md for drift)
   - Gate 4: Test Coverage Review (human reviews test-plan.md)
   - Gate 5: Evidence Review (human reads verification-report.md AND opens log files)
   - (Plus REVIEWER approval before commit)

5. **Task State Machine:**
   - Explicit states (DRAFT, PLANNED, ARCH-REVIEW, READY-TO-BUILD, IMPLEMENTED, TESTS-WRITTEN, VERIFICATION, VERIFIED, REVIEW, APPROVED, COMMITTED)
   - Valid transitions documented
   - No ambiguous states

---

## Rationale

**Why multi-agent over single-agent?**

Isolation of concerns prevents conflicts of interest. A BUILDER cannot fairly review its own work. A TEST-DESIGNER who reads BUILDER's implementation notes becomes biased. Only independent sessions with fresh reads can catch subtle mistakes.

**Why evidence gates?**

"I tested this and it works" has been shown to be unreliable. But "here is the test output showing 42 tests passed" is verifiable. Evidence forces honesty.

**Why five gates?**

Each gate represents a critical quality checkpoint:
- Plan gate: Requirements are understood, not vague
- Architecture gate: Design is sound before coding
- Scope gate: Implementation stayed in bounds
- Test gate: Coverage is comprehensive, not just happy path
- Evidence gate: Work actually passes verification

**Why CLAUDE.md?**

Without persistence between agent sessions, context is lost. CLAUDE.md is the only bridge. It tracks task state, completed work, blockers, decisions. Every agent reads it first, updates it last.

---

## Consequences

### Positive
- ✓ Integration verified before claiming completion
- ✓ Evidence required for all advancement (no false confidence)
- ✓ Honest uncertainty (if we can't verify it, we document that)
- ✓ Adversarial review (fresh sessions catch mistakes)
- ✓ Clear responsibility (each agent has defined role)
- ✓ Reversible (rollback plans make changes undoable)
- ✓ Auditable (all decisions and evidence logged)

### Negative
- ✗ More overhead than monolithic approach
- ✗ More sessions required (coordination complexity)
- ✗ Slower than single-agent (multiple rounds of work)
- ✗ Requires discipline (no skipping gates)

### Neutral
- ~ Artifacts are persistent (files on disk, not ephemeral)
- ~ Handoffs are explicit (no assumed context)

---

## Future Considerations

1. **If integration testing is insufficient:**
   - Could add integration-test-designer role (separate from unit test designer)
   - Would add more gates but increase confidence

2. **If evidence model is too strict:**
   - Could allow "spot check" evidence (run on representative sample) instead of full suite
   - Would reduce evidence rigor slightly but decrease overhead

3. **If multi-agent overhead becomes prohibitive:**
   - Could merge some roles for simpler features (e.g., BUILDER + TEST-DESIGNER for trivial bugs)
   - Would require explicit deviation decision, not automatic

4. **If human gates become bottleneck:**
   - Could automate some gates (linting gate passes automatically if exit 0)
   - Would keep critical gates (Plan, Architecture, Evidence, Review) manual

5. **If ASES needs to scale to large teams:**
   - Would need to support team roles (multiple BUILDER sessions in parallel)
   - Current design assumes single developer, would need extension

---

## Related Tasks

- task-001: Bootstrap Folder Structure (implementation starts here)
- task-002: PLANNER Agent Prompt (first agent)
- task-003: ARCHITECT Agent Prompt (second agent)
- task-004: BUILDER Agent Prompt (third agent)
- task-005: TEST-DESIGNER Agent Prompt (fourth agent)
- task-006: VERIFIER Agent Prompt (fifth agent)
- task-007: REVIEWER Agent Prompt (sixth agent)

---

## Related ADRs

- ADR-002: Bootstrap Protocol for ASES Construction — How Phase 0 itself is built (minimal protocol since full ASES can't govern its own construction)
- ADR-003: Evidence Capture Strategy — Implementation of evidence requirement (terminal output only, never Claude assessment)

---

*End of ADR-001*
