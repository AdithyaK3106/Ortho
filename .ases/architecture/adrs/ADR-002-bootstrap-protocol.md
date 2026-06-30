# ADR-002: Bootstrap Protocol for ASES Construction

**Status:** ACCEPTED  
**Date:** 2026-06-27  
**Author:** ARCHITECT  
**Approved by:** Human on 2026-06-27

---

## Context

ASES is a system designed to enforce evidence-gated development and role separation. But ASES itself is being built in Phase 0. We face a bootstrapping paradox:

- Full ASES workflow requires 6 agents working in concert with 5 gates
- But ASES doesn't exist yet, so we can't use full ASES to build ASES
- We need enough structure to avoid chaos, but not so much that we're blocked

How do we build the system that governs software engineering without the system to govern the building?

---

## Problem Statement

We need a minimal protocol for Phase 0 that:

1. **Prevents chaos** — No total freedom (that leads to unverified work)
2. **Prevents over-engineering** — No requirement for full ASES workflow (we don't have ASES yet)
3. **Enforces honesty** — No false confidence claims
4. **Maintains context** — Persist state across sessions
5. **Gates advancement** — Require review before marking tasks done
6. **Produces complete output** — All artifacts must be non-placeholder

---

## Alternatives Considered

### Option A: Full ASES Workflow During Bootstrap (rejected)
**Description:** Use the five-gate feature workflow even while building ASES.

**Pros:**
- Proven process
- Complete evidence trail

**Cons:**
- Circular dependency (need ASES to build ASES)
- Massive overhead for building infrastructure
- No agent prompts yet (PLANNER doesn't exist to plan ASES construction)
- Would require manual implementation of all five gates

**Rejection Reason:** Circular dependency makes this infeasible. We don't have agents yet.

### Option B: No Structure (rejected)
**Description:** Build ASES with no guardrails, "we'll be careful."

**Pros:**
- Fast to implement
- No overhead

**Cons:**
- Leads to same problems ASES is designed to prevent (unverified integration, false confidence)
- ASES itself becomes an example of sloppy engineering
- No evidence of correctness

**Rejection Reason:** Defeats the purpose if ASES itself is built without discipline.

### Option C: Bootstrap Protocol (five minimal rules) (chosen) ✓
**Description:** Phase 0 uses five rules only (read CLAUDE.md, update CLAUDE.md, no false claims, verify and capture, commit). All other decisions deferred to Phase 2.

**Pros:**
- ✓ Minimal overhead (just five rules)
- ✓ Prevents chaos (structure exists)
- ✓ Prevents false confidence (evidence required)
- ✓ Maintains context (CLAUDE.md persists)
- ✓ Gates advancement (human review required)
- ✓ Produces complete output (templates and prompts finished, not stubs)

**Cons:**
- ✗ Less rigorous than full ASES
- ✗ Single developer (true role separation impossible with one person)
- ✗ Manual verification (no CI/CD)

**Selection Reason:** Perfect balance of structure and pragmatism. Prevents the worst failures while allowing rapid progress.

---

## Decision

Phase 0 (Bootstrap) uses a five-rule minimal protocol:

1. **Every session reads CLAUDE.md first**
   - CLAUDE.md is the only persistent memory across sessions
   - Contains project status, completed tasks, blockers, architecture decisions
   - Reading it ensures no stale context carries over

2. **Every session updates CLAUDE.md at the end**
   - Record what changed
   - Update task state
   - Note new blockers or decisions
   - Never delete previous content (append or update only)

3. **No session claims completion without evidence**
   - Forbidden: "Implementation complete", "All tests passing", "Fully tested"
   - Required: "Implemented, unverified" or "Verified: [log file path]"
   - Evidence can be: terminal output, file verification (ls, wc -l), git log
   - Evidence must be observable (human can check it)

4. **After implementation, run verification and capture output to a file**
   - Do not summarize from memory
   - Do not say "I checked it and it's fine"
   - Run the verification command (e.g., tsc, jest, wc -l)
   - Pipe output to a file
   - Read the file
   - Report based on what the file shows

5. **Git commit after every verified unit**
   - Commit after a task is implemented and verified
   - Not after every tiny change (commits should be meaningful)
   - Commit message includes evidence reference
   - Never force-push or amend public commits (always new commits)

---

## Rationale

**Why these five rules specifically?**

1. Reading CLAUDE.md prevents stale context (one session doesn't interfere with next)
2. Updating CLAUDE.md persists progress (work doesn't disappear)
3. No false claims prevents confidence inflation (similar to ASES core principle)
4. Verification + capture prevents memory-based false evidence (evidence is on disk)
5. Committing persists work and creates audit trail (git is the checkpoint)

**Why this is minimal but sufficient:**

- These five rules prevent the three failure modes (isolated implementation, fabricated confidence, no honest uncertainty)
- They don't require a full multi-agent workflow (not possible with one developer)
- They don't require CI/CD or automated gates (human reviews are sufficient for bootstrap)
- They can be followed in every session without massive overhead

**Why Phase 0 is temporary:**

Once ASES is built (end of Task 009), we transition to Phase 2. From then on:
- Use full feature/bugfix workflows (PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER)
- Use five gates with explicit human approval
- Use automated verification where possible
- Use role separation even though solo developer (via session isolation)

Bootstrap protocol is a temporary ladder. Once at the top, we kick it away.

---

## Consequences

### Positive
- ✓ Prevents chaos (five rules create structure)
- ✓ Prevents false confidence (evidence required)
- ✓ Maintains progress (CLAUDE.md persists state)
- ✓ Fast iteration (minimal overhead)
- ✓ Creates audit trail (git commits)
- ✓ Produces complete output (no stubs or placeholders)

### Negative
- ✗ Less rigorous than full ASES
- ✗ No true role separation (one developer)
- ✗ Manual verification (no automated tests in Phase 0)
- ✗ No peer review (human is only reviewer)

### Neutral
- ~ Temporary by design (Phase 0 only)
- ~ Not meant to be permanent (will be replaced by Phase 2)

---

## Future Considerations

1. **When does Bootstrap end?**
   - End of Task 009 (all ASES components built)
   - Transition to Phase 1 (baseline audit of Ortho)
   - Then to Phase 2 (full ASES workflow)

2. **If Bootstrap needs extension:**
   - If tasks beyond Phase 0 are needed, extend bootstrap
   - But goal is to complete Phase 0 and transition to full ASES as soon as possible

3. **If bootstrap rules are insufficient:**
   - Could add more structure (e.g., add ARCHITECT gate for major decisions)
   - But this defeats the purpose of being minimal

4. **After Phase 0 completes:**
   - Do a baseline audit of ASES itself (Phase 1 equivalent)
   - Document any debt or limitations found
   - Then transition to Phase 2 (full governance)

---

## Related Tasks

- All Phase 0 tasks (001-009) use this protocol
- No tasks use full ASES workflow until Phase 2

---

## Related ADRs

- ADR-001: ASES as Multi-Agent Engineering System — The full system we're bootstrapping toward
- ADR-003: Evidence Capture Strategy — Why evidence must come from terminals, not Claude assessment

---

*End of ADR-002*
