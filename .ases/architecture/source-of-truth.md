# Source of Truth Hierarchy

**Last Updated:** 2026-07-02 (ASES v2)
**Status:** Active

This file formally defines artifact precedence across the ASES workflow. It resolves the question: "when two artifacts disagree, which one is right?" Every other ASES v2 governance artifact (`contract-report.md`, `architecture-arbitration.md`, `traceability-matrix.md`) cites this hierarchy for its verdict language.

---

## The Hierarchy

```
FRD
  ↓
Task Specification (spec.md)
  ↓
Architecture Review (architecture-review.md)
  ↓
Implementation (production code)
  ↓
Tests (test suite)
  ↓
Verification Evidence (logs, verification-report.md)
```

Higher levels always override lower levels. An artifact never gets to override the level above it — it can only be flagged as divergent from it.

### Why each level exists

- **FRD** — the single mission-level source of truth for the entire project (`ortho-v3-frd.md`). Nothing is built that doesn't trace back to it. It changes rarely and only by deliberate amendment.
- **Task Specification** — the FRD scoped down to one task's acceptance criteria, files, and contracts. It exists so PLANNER can commit to a testable, binary definition of done before anyone writes code.
- **Architecture Review** — the specification validated against module boundaries, dependency direction, and existing ADRs. It exists to catch design problems before implementation cost is sunk.
- **Implementation** — the actual code. It exists to satisfy the specification, not to define it. Code that adds behavior beyond spec is scope creep; code that implements less is incomplete.
- **Tests** — an independent, fresh-context check that implementation satisfies specification. Tests exist to verify the specification was met — not to define a new specification of their own (see task-008 incident below).
- **Verification Evidence** — the terminal-captured, timestamped proof that tests actually ran and implementation actually builds. It exists because unverified claims are worthless; see ADR-003.

---

## Conflict Resolution

| Conflict | Resolution |
|---|---|
| Implementation vs. Tests disagree | **Consult Architecture.** Architecture Review defines the approved contracts; whichever artifact (implementation or tests) matches Architecture is correct. The other deviated. |
| Implementation vs. Architecture disagree | **Architecture wins.** Implementation must be brought into compliance with the approved architecture-review.md, or Architecture must be revised through a new ARCHITECT session (not silently overridden by BUILDER). |
| Architecture vs. Specification disagree | **Specification wins.** Architecture elaborates the specification; it cannot contradict it. If Architecture reveals the specification is unbuildable as written, return to PLANNER. |
| Specification vs. FRD disagree | **FRD wins**, unless the FRD is formally amended. A specification that quietly diverges from the FRD is a planning error, not a valid interpretation. |

**Worked example (task-008):** BUILDER's stateless `LayerDetector.extract_layers(import_graph, files)` matched `spec.md` exactly. TEST-DESIGNER's tests expected a stateful `LayerDetector(mock_symbol_repo, sample_repo_id)` constructor with a parameterless `extract_layers()` call — an API never specified. This is the "Implementation vs. Tests disagree" row: consulting Architecture (which mirrors spec.md's stateless design, consistent with FRD Section 1 Principle 5, "Small composable modules") confirmed Implementation was correct and Tests had deviated. See `.ases/tasks/task-008-architecture-detection/architecture-contract-audit.md` for the full contract matrix that produced this resolution.

---

## Escalation Procedure

When two artifacts disagree:

1. **Compare against the higher artifact** in the hierarchy — never guess, never assume the more-recently-written artifact is correct.
2. **Identify the divergence** precisely — cite file and line for both the higher artifact's requirement and the lower artifact's deviation.
3. **Return only the divergent artifact** for revision. Do not touch the artifact that already matches the higher level, even if it "could be improved" — that is scope creep.
4. **Never modify multiple artifacts** for a single conflict unless the specification itself is being formally changed (in which case PLANNER re-opens spec.md and every artifact below it may need to follow).

This procedure is what `.ases/agents/architecture-arbitrator.md` (Phase 3) automates as a repeatable session, and what the API Contract Gate (Phase 1) checks for before VERIFIER runs.

---

## Ownership

| Artifact | Owner (Role) |
|---|---|
| FRD | Product (Human) |
| Task Specification (spec.md) | PLANNER |
| Architecture Review (architecture-review.md) | ARCHITECT |
| Implementation (production code) | BUILDER |
| Tests (test suite) | TEST-DESIGNER |
| Verification Evidence (logs, verification-report.md) | VERIFIER |
| Audit (review.md, architecture-arbitration.md) | REVIEWER |

Ownership means: only that role's session may edit the artifact. When an artifact is found divergent, the escalation procedure returns it to its owner — not to whichever role most recently touched it.

---

*End of source-of-truth.md*
