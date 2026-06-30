# ASES Task State Machine

**Version:** 1.0  
**Source:** FRD Part 4  
**Purpose:** Define all valid task states, transitions, and rules for state changes

---

## Overview

Each task in ASES progresses through a series of states. This document defines:
- **15 states** with clear definitions
- **Valid transitions** between states
- **Conditions** for entering/exiting each state
- **Artifacts required** at each state
- **Decision points** (gates) that block progression

---

## State Definitions

### 1. CREATED
**Definition:** Task exists in IMPLEMENTATION-PLAN.md and CLAUDE.md but no work has begun.

**Entry:** Manual task creation in planning phase  
**Exit:** Begin PLANNER session  
**Artifacts:** None (task description only)  
**Agent Role:** PLANNER (prepares to read)

---

### 2. PLANNING
**Definition:** PLANNER is actively working on plan.md, spec.md, rollback-plan.md.

**Entry:** PLANNER session starts  
**Exit:** PLANNER completes all three artifacts  
**Artifacts:** plan.md (draft), spec.md (draft), rollback-plan.md (draft)  
**Agent Role:** PLANNER  
**Blocked by:** PLANNER cannot complete if accepting criteria are vague

---

### 3. READY-FOR-ARCHITECT
**Definition:** PLANNER has produced complete plan, spec, and rollback. Waiting for ARCHITECT review.

**Entry:** PLANNER outputs all three artifacts  
**Exit:** Human approves plan (Gate 1) OR PLANNER revises  
**Artifacts:** plan.md (final), spec.md (final), rollback-plan.md (final)  
**Agent Role:** Human reviewer  
**Gate:** Gate 1 (PLANNER completion) — requires all three documents, no placeholders

---

### 4. ARCHITECTURE-REVIEW
**Definition:** ARCHITECT is analyzing the plan and producing architecture-review.md and ADRs.

**Entry:** Gate 1 passed (human approval of plan)  
**Exit:** ARCHITECT completes architecture-review.md  
**Artifacts:** architecture-review.md (draft)  
**Agent Role:** ARCHITECT  
**Blocked by:** ARCHITECT cannot proceed without reading FRD Part 5 (ADR system)

---

### 5. READY-FOR-BUILDER
**Definition:** Architecture review is complete. BUILDER is ready to implement.

**Entry:** ARCHITECT outputs architecture-review.md  
**Exit:** Human approves architecture (Gate 2) OR ARCHITECT revises  
**Artifacts:** architecture-review.md (final), ADRs (if created)  
**Agent Role:** Human reviewer  
**Gate:** Gate 2 (ARCHITECT completion) — architecture-review.md must have "APPROVED" verdict, module boundaries clear

---

### 6. BUILDING
**Definition:** BUILDER is writing code/configuration per spec.md and rollback-plan.md.

**Entry:** Gate 2 passed (human approval of architecture)  
**Exit:** BUILDER completes implementation-notes.md  
**Artifacts:** Modified source files, implementation-notes.md (draft)  
**Agent Role:** BUILDER  
**Forbidden:** BUILDER must read rollback-plan.md before writing a single line  
**Blocked by:** Cannot proceed if rollback-plan.md is incomplete

---

### 7. READY-FOR-TEST-DESIGNER
**Definition:** Code is complete. TEST-DESIGNER is ready to design independent tests.

**Entry:** BUILDER outputs implementation-notes.md  
**Exit:** Human approves implementation (Gate 3) OR BUILDER revises  
**Artifacts:** implementation-notes.md (final), modified source files (committed)  
**Agent Role:** Human reviewer  
**Gate:** Gate 3 (BUILDER completion) — source code reviewed, no obvious bugs, implementation-notes explains what was built

---

### 8. TEST-DESIGN
**Definition:** TEST-DESIGNER (independent session) is writing test-plan.md and tests.

**Entry:** Gate 3 passed (human approval of implementation)  
**Exit:** TEST-DESIGNER completes test-plan.md and test code  
**Artifacts:** test-plan.md (draft), test code committed  
**Agent Role:** TEST-DESIGNER  
**Rule:** TEST-DESIGNER must work in a NEW, independent session (never same session as BUILDER)  
**Blocked by:** Cannot access BUILDER's session state; reads only spec.md and implementation-notes.md

---

### 9. READY-FOR-VERIFIER
**Definition:** Tests are written. VERIFIER is ready to run evidence capture.

**Entry:** TEST-DESIGNER outputs test-plan.md  
**Exit:** Human approves tests (Gate 4) OR TEST-DESIGNER revises  
**Artifacts:** test-plan.md (final), test code (committed)  
**Agent Role:** Human reviewer  
**Gate:** Gate 4 (TEST-DESIGNER completion) — test-plan.md covers all acceptance criteria, edge cases documented

---

### 10. VERIFICATION-MODE-A
**Definition:** VERIFIER is running build/test commands and capturing raw terminal output.

**Entry:** Gate 4 passed (human approval of tests)  
**Exit:** VERIFIER captures all required evidence logs  
**Artifacts:** Evidence logs in .ases/evidence/[task-id]/ (build, lint, types, test, regression)  
**Agent Role:** VERIFIER (Mode A)  
**Rule:** VERIFIER never fabricates logs; only tools produce evidence  
**Command:** `./capture-evidence.sh [task-id] [stack]` (TypeScript, Python, Android, or all)

---

### 11. VERIFICATION-MODE-B
**Definition:** VERIFIER is interpreting evidence logs and producing verification-report.md.

**Entry:** All evidence logs exist in .ases/evidence/[task-id]/  
**Exit:** VERIFIER outputs verification-report.md and evidence-package.md  
**Artifacts:** verification-report.md (draft), evidence-package.md (draft)  
**Agent Role:** VERIFIER (Mode B)  
**Rule:** VERIFIER quotes exact error lines from log files, never paraphrases  
**Rule:** VERIFIER marks evidence gaps honestly (MANUAL-REQUIRED, MISSING, LIMITATION)

---

### 12. READY-FOR-REVIEWER
**Definition:** All evidence is captured and interpreted. REVIEWER is ready for final assessment.

**Entry:** VERIFIER outputs verification-report.md and evidence-package.md  
**Exit:** Human approves evidence (Gate 5) OR VERIFIER recaptures  
**Artifacts:** verification-report.md (final), evidence-package.md (final)  
**Agent Role:** Human reviewer  
**Gate:** Gate 5 (VERIFIER completion) — all gates 1–4 artifacts present, evidence gaps documented, ready-for-review verdict = YES

---

### 13. REVIEW
**Definition:** REVIEWER (independent session) is conducting final adversarial review.

**Entry:** Gate 5 passed (human approval of evidence)  
**Exit:** REVIEWER outputs review.md  
**Artifacts:** review.md (draft)  
**Agent Role:** REVIEWER  
**Rule:** REVIEWER must work in a NEW, independent session (never same session as BUILDER or VERIFIER)  
**Rule:** REVIEWER must ask all 7 adversarial questions (see GATE-CHECKLIST.md)

---

### 14. READY-FOR-RELEASE
**Definition:** REVIEWER has approved all artifacts. Task is eligible for integration/release.

**Entry:** REVIEWER outputs review.md with "APPROVED" verdict  
**Exit:** Human approves review (Gate 6) OR REVIEWER raises concerns  
**Artifacts:** review.md (final)  
**Agent Role:** Human reviewer  
**Gate:** Gate 6 (REVIEWER completion) — review.md verdict = APPROVED, no critical issues flagged, security assessment passed

---

### 15. COMPLETED
**Definition:** Task is finished. All artifacts are committed. No further changes.

**Entry:** Gate 6 passed (human approval of review)  
**Exit:** —  
**Artifacts:** All 10 per-task artifacts in .ases/tasks/[task-id]/  
**Status:** Marked in CLAUDE.md COMPLETED section  
**Rule:** Post-completion changes require a new task

---

## State Transition Diagram

```
CREATED
   ↓
PLANNING ← (revise) ─┐
   ↓               │
READY-FOR-ARCHITECT ← (reject) ─┐
   ↓                            │
ARCHITECTURE-REVIEW ← (revise) ──┤
   ↓                            │
READY-FOR-BUILDER ← (reject) ────┤
   ↓                             │
BUILDING ← (revise) ─────────────┤
   ↓                             │
READY-FOR-TEST-DESIGNER ← (reject)
   ↓
TEST-DESIGN ← (revise) ────┐
   ↓                       │
READY-FOR-VERIFIER ← (reject)
   ↓
VERIFICATION-MODE-A
   ↓
VERIFICATION-MODE-B ← (recapture logs) ──┐
   ↓                                      │
READY-FOR-REVIEWER ← (reject) ───────────┤
   ↓                                      │
REVIEW ← (revise) ──────────────────────┐│
   ↓                                      ││
READY-FOR-RELEASE ← (reject) ────────────┼┤
   ↓                                      ││
COMPLETED ◄─────────────────────────────┘│
                                          │
(After rejection at any gate, task returns to most recent working state)
```

---

## Valid Transitions

| From | To | Condition | Gate | Artifact Required |
|------|----|-----------|----|-------------------|
| CREATED | PLANNING | PLANNER starts | — | none |
| PLANNING | READY-FOR-ARCHITECT | PLANNER outputs all 3 docs | — | plan, spec, rollback |
| READY-FOR-ARCHITECT | ARCHITECTURE-REVIEW | Gate 1 approved | Gate 1 | Human sign-off |
| READY-FOR-ARCHITECT | PLANNING | Gate 1 rejected | Gate 1 | Human feedback |
| ARCHITECTURE-REVIEW | READY-FOR-BUILDER | ARCHITECT outputs arch review | — | architecture-review.md |
| READY-FOR-BUILDER | BUILDING | Gate 2 approved | Gate 2 | Human sign-off |
| READY-FOR-BUILDER | ARCHITECTURE-REVIEW | Gate 2 rejected | Gate 2 | Human feedback |
| BUILDING | READY-FOR-TEST-DESIGNER | BUILDER outputs impl notes | — | implementation-notes.md |
| READY-FOR-TEST-DESIGNER | TEST-DESIGN | Gate 3 approved | Gate 3 | Human sign-off |
| READY-FOR-TEST-DESIGNER | BUILDING | Gate 3 rejected | Gate 3 | Human feedback |
| TEST-DESIGN | READY-FOR-VERIFIER | TEST-DESIGNER outputs test plan | — | test-plan.md |
| READY-FOR-VERIFIER | VERIFICATION-MODE-A | Gate 4 approved | Gate 4 | Human sign-off |
| READY-FOR-VERIFIER | TEST-DESIGN | Gate 4 rejected | Gate 4 | Human feedback |
| VERIFICATION-MODE-A | VERIFICATION-MODE-B | All evidence logs exist | — | evidence logs |
| VERIFICATION-MODE-B | READY-FOR-REVIEWER | VERIFIER outputs reports | — | verification-report, evidence-package |
| VERIFICATION-MODE-B | VERIFICATION-MODE-A | Gate 5 rejected (recapture) | Gate 5 | Human feedback |
| READY-FOR-REVIEWER | REVIEW | Gate 5 approved | Gate 5 | Human sign-off |
| REVIEW | READY-FOR-RELEASE | REVIEWER outputs review | — | review.md |
| READY-FOR-RELEASE | COMPLETED | Gate 6 approved | Gate 6 | Human sign-off |
| READY-FOR-RELEASE | REVIEW | Gate 6 rejected | Gate 6 | Human feedback |

---

## Gate Checklist

**Six gates block progression:**

| Gate | From | To | Requires | Sign-off |
|------|------|----|-----------|----|
| **Gate 1** | READY-FOR-ARCHITECT | ARCHITECTURE-REVIEW | plan.md, spec.md, rollback-plan.md; acceptance criteria testable | Human |
| **Gate 2** | READY-FOR-BUILDER | BUILDING | architecture-review.md; verdict = APPROVED; module boundaries clear | Human |
| **Gate 3** | READY-FOR-TEST-DESIGNER | TEST-DESIGN | implementation-notes.md; code committed; no obvious bugs | Human |
| **Gate 4** | READY-FOR-VERIFIER | VERIFICATION-MODE-A | test-plan.md; all acceptance criteria covered; edge cases listed | Human |
| **Gate 5** | READY-FOR-REVIEWER | REVIEW | verification-report.md, evidence-package.md; gates 1–4 artifacts exist; ready-for-review = YES | Human |
| **Gate 6** | READY-FOR-RELEASE | COMPLETED | review.md; verdict = APPROVED; security assessment passed; no critical issues | Human |

---

## Rules for State Transitions

1. **No skipping gates.** Every task must pass gates 1–6 in order. No exceptions.

2. **Rejection loops back.** If Gate N is rejected, task returns to the working state *before* Gate N (not to CREATED).

3. **Session isolation:** TEST-DESIGNER and REVIEWER must work in new, independent sessions. They cannot access prior session state.

4. **Artifact immutability within state:** Once an artifact is produced and gate passed, that artifact is frozen. Changes require a new task.

5. **Rollback-plan mandatory:** BUILDER cannot enter BUILDING state until rollback-plan.md exists and is read.

6. **Evidence non-fabrication:** VERIFIER can only produce evidence that comes from tool output. If a tool is missing or fails, the log reflects that. No manual log writing.

7. **Human approval required:** Every gate requires explicit human approval. Implicit approval (no objection) is not sufficient.

---

## Example: Feature Development Workflow

```
Task: Add authentication to Ortho

CREATED
  ↓ (PLANNER session begins)
PLANNING (PLANNER reads FRD, writes plan.md, spec.md, rollback-plan.md)
  ↓ (All 3 artifacts complete)
READY-FOR-ARCHITECT
  ↓ (Human reviews, approves) — GATE 1
ARCHITECTURE-REVIEW (ARCHITECT session begins; reads plan, spec, FRD Part 5)
  ↓ (ARCHITECT writes architecture-review.md, ADR-004: auth-strategy)
READY-FOR-BUILDER
  ↓ (Human reviews architecture, approves) — GATE 2
BUILDING (BUILDER session begins; reads rollback-plan.md, spec.md, implements auth module)
  ↓ (BUILDER commits code, writes implementation-notes.md)
READY-FOR-TEST-DESIGNER
  ↓ (Human reviews code, approves) — GATE 3
TEST-DESIGN (NEW SESSION: TEST-DESIGNER reads spec.md, impl-notes, FRD Part 3.4)
  ↓ (TEST-DESIGNER writes test-plan.md, writes test code, commits)
READY-FOR-VERIFIER
  ↓ (Human reviews tests, approves) — GATE 4
VERIFICATION-MODE-A (VERIFIER runs: ./capture-evidence.sh task-auth typescript)
  ↓ (Evidence logs created: build, lint, types, test, regression)
VERIFICATION-MODE-B (VERIFIER reads logs, writes verification-report.md, evidence-package.md)
  ↓ (All evidence captured)
READY-FOR-REVIEWER
  ↓ (Human reviews evidence, approves) — GATE 5
REVIEW (NEW SESSION: REVIEWER reads spec, impl-notes, test-plan, review.md)
  ↓ (REVIEWER asks 7 adversarial questions, writes review.md verdict=APPROVED)
READY-FOR-RELEASE
  ↓ (Human final sign-off) — GATE 6
COMPLETED (Task auth is done. All artifacts in .ases/tasks/task-auth/)
```

---

## Status Queries

To find the current state of a task, check:
1. CLAUDE.md — IN PROGRESS section (quick state)
2. .ases/tasks/[task-id]/ — which artifacts exist (infer state from artifact set)
3. Latest commit message — may indicate state transition

---

*End of state-machine.md*
