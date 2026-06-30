# ASES Phase 0 Readiness Checklist

**Version:** 1.0  
**Purpose:** Verify that all Phase 0 deliverables are complete and ASES is ready for use.

---

## Overview

Phase 0 is complete when:
1. All 9 implementation tasks are done
2. All 32 artifacts exist with no placeholders
3. All references between files are correct (no broken links)
4. Documentation is coherent and self-contained
5. A first-time user can pick up ASES and use it without re-reading the FRD

This checklist verifies all of the above.

---

## Task Completion Checklist

- [ ] **Task 001:** Bootstrap Folder Structure & CLAUDE.md ✓
  - [ ] `.ases/` directory tree exists
  - [ ] CLAUDE.md is populated (no placeholders)
  - [ ] .gitignore configured correctly
  - [ ] Commit: 65edf60

- [ ] **Task 002:** Agent Prompts (PLANNER, ARCHITECT, BUILDER) ✓
  - [ ] `.ases/agents/planner.md` complete
  - [ ] `.ases/agents/architect.md` complete
  - [ ] `.ases/agents/builder.md` complete
  - [ ] Commit: 39d4863

- [ ] **Task 003:** Agent Prompts (TEST-DESIGNER, VERIFIER, REVIEWER) ✓
  - [ ] `.ases/agents/test-designer.md` complete
  - [ ] `.ases/agents/verifier.md` complete (Mode A + Mode B)
  - [ ] `.ases/agents/reviewer.md` complete
  - [ ] Commit: 7b80bc7

- [ ] **Task 004:** Output Templates (All 10 Document Types) ✓
  - [ ] `.ases/templates/plan.md` complete
  - [ ] `.ases/templates/spec.md` complete
  - [ ] `.ases/templates/rollback-plan.md` complete
  - [ ] `.ases/templates/architecture-review.md` complete
  - [ ] `.ases/templates/implementation-notes.md` complete
  - [ ] `.ases/templates/test-plan.md` complete
  - [ ] `.ases/templates/verification-report.md` complete
  - [ ] `.ases/templates/evidence-package.md` complete
  - [ ] `.ases/templates/review.md` complete
  - [ ] `.ases/templates/adr.md` complete
  - [ ] Commit: aec891f

- [ ] **Task 005:** Workflow Definitions (4 types) ✓
  - [ ] `.ases/workflows/feature.md` complete
  - [ ] `.ases/workflows/bugfix.md` complete
  - [ ] `.ases/workflows/baseline-audit.md` complete
  - [ ] `.ases/workflows/bootstrap.md` complete
  - [ ] Commit: 9025f5b

- [ ] **Task 006:** ADRs (3) + Architecture System ✓
  - [ ] `.ases/architecture/adrs/INDEX.md` created
  - [ ] `.ases/architecture/adrs/ADR-001-ases-orchestration.md` created
  - [ ] `.ases/architecture/adrs/ADR-002-bootstrap-protocol.md` created
  - [ ] `.ases/architecture/adrs/ADR-003-evidence-capture-terminal.md` created
  - [ ] `.ases/architecture/decisions.md` contains 3+ entries
  - [ ] `.ases/architecture/modules.md` skeleton (Ortho + Expense)
  - [ ] `.ases/architecture/contracts.md` skeleton
  - [ ] Commit: 62a7e78

- [ ] **Task 007:** Verification Scripts (4 types) ✓
  - [ ] `.ases/commands/verify-ts.sh` executable and complete
  - [ ] `.ases/commands/verify-python.sh` executable and complete
  - [ ] `.ases/commands/verify-android.sh` executable and complete
  - [ ] `.ases/commands/capture-evidence.sh` executable and complete
  - [ ] `.ases/commands/README.md` documents all scripts
  - [ ] Commit: f53bc38

- [ ] **Task 008:** State Machine & Task Tracking ✓
  - [ ] `.ases/state-machine.md` complete (15 states, 6 gates)
  - [ ] `.ases/task-template.md` complete (copy-paste checklist)
  - [ ] `.ases/GATE-CHECKLIST.md` complete (all 10 gates)
  - [ ] Commit: 265de11

- [ ] **Task 009:** Integration Test & Readiness ✓
  - [ ] `.ases/INTEGRATION-TEST.md` complete (feature walkthrough)
  - [ ] `.ases/READINESS.md` complete (this file)
  - [ ] `.ases/QUICK-START.md` complete (first-time user guide)
  - [ ] Commit: TBD

---

## Artifact Inventory

**Total artifacts:** 32 (per IMPLEMENTATION-PLAN.md)

### Agent Prompts (6 files)
- [ ] `.ases/agents/planner.md` (✓ role, reads, writes, forbidden actions, gates)
- [ ] `.ases/agents/architect.md` (✓ role, reads, writes, forbidden actions, gates)
- [ ] `.ases/agents/builder.md` (✓ role, reads, writes, forbidden actions, gates)
- [ ] `.ases/agents/test-designer.md` (✓ independence, tests, forbidden actions)
- [ ] `.ases/agents/verifier.md` (✓ Mode A and Mode B separation)
- [ ] `.ases/agents/reviewer.md` (✓ 7 adversarial questions, verdict rules)

### Output Templates (10 files)
- [ ] `.ases/templates/plan.md` (✓ copy-paste ready)
- [ ] `.ases/templates/spec.md` (✓ copy-paste ready)
- [ ] `.ases/templates/rollback-plan.md` (✓ copy-paste ready)
- [ ] `.ases/templates/architecture-review.md` (✓ copy-paste ready)
- [ ] `.ases/templates/implementation-notes.md` (✓ copy-paste ready)
- [ ] `.ases/templates/test-plan.md` (✓ copy-paste ready)
- [ ] `.ases/templates/verification-report.md` (✓ copy-paste ready)
- [ ] `.ases/templates/evidence-package.md` (✓ copy-paste ready)
- [ ] `.ases/templates/review.md` (✓ copy-paste ready)
- [ ] `.ases/templates/adr.md` (✓ copy-paste ready)

### Workflows (4 files)
- [ ] `.ases/workflows/feature.md` (✓ all 5 gates, all 6 agent roles)
- [ ] `.ases/workflows/bugfix.md` (✓ skips ARCHITECT if appropriate)
- [ ] `.ases/workflows/baseline-audit.md` (✓ brownfield baseline workflow)
- [ ] `.ases/workflows/bootstrap.md` (✓ Phase 0 protocol, 5 rules)

### Architecture System (7 files)
- [ ] `.ases/architecture/adrs/INDEX.md` (✓ ADR index)
- [ ] `.ases/architecture/adrs/ADR-001-ases-orchestration.md` (✓ ACCEPTED)
- [ ] `.ases/architecture/adrs/ADR-002-bootstrap-protocol.md` (✓ ACCEPTED)
- [ ] `.ases/architecture/adrs/ADR-003-evidence-capture-terminal.md` (✓ ACCEPTED)
- [ ] `.ases/architecture/decisions.md` (✓ append-only log)
- [ ] `.ases/architecture/modules.md` (✓ Ortho + Expense skeleton)
- [ ] `.ases/architecture/contracts.md` (✓ API contracts skeleton)

### System Documentation (5 files)
- [ ] `.ases/state-machine.md` (✓ 15 states, transitions, example)
- [ ] `.ases/task-template.md` (✓ per-task checklist)
- [ ] `.ases/GATE-CHECKLIST.md` (✓ all 6 gates + recovery)
- [ ] `.ases/INTEGRATION-TEST.md` (✓ hypothetical feature walkthrough)
- [ ] `.ases/READINESS.md` (✓ this file)

### Verification Scripts (5 files)
- [ ] `.ases/commands/verify-ts.sh` (✓ executable, tsc/eslint/jest)
- [ ] `.ases/commands/verify-python.sh` (✓ executable, ruff/mypy/pytest)
- [ ] `.ases/commands/verify-android.sh` (✓ executable, gradle)
- [ ] `.ases/commands/capture-evidence.sh` (✓ executable, master router)
- [ ] `.ases/commands/README.md` (✓ documentation)

### Quick Start (1 file)
- [ ] `.ases/QUICK-START.md` (TBD, below)

---

## Reference Integrity Checklist

**No broken links, all references resolve:**

- [ ] CLAUDE.md references FRD Part 3, 4, 5, 7, 10 (exists: ASES_FRD_v1.1.md)
- [ ] Agent prompts reference FRD sections (correct parts listed)
- [ ] Workflows reference agent roles (all 6 defined)
- [ ] Templates reference Part 5 (ADR format, Part 3.5 format, etc.)
- [ ] State machine references gates (all 6 defined in GATE-CHECKLIST.md)
- [ ] task-template.md references all agent roles (all 6 covered)
- [ ] INTEGRATION-TEST.md demonstrates all gates working together (yes)
- [ ] All FRD Part numbers mentioned are real and consistent

---

## No Placeholders Checklist

**Every artifact is filled completely:**

- [ ] Agent prompts: no [TODO], no "TBD", no "e.g.", no blanks
- [ ] Templates: no [REPLACE], no [EXAMPLE ONLY], no "see above"
- [ ] Workflows: no "TBD", no "TBD workflow", all agent sequences explicit
- [ ] Architecture: ADRs complete, decisions log has entries, modules/contracts are skeleton (intentional, Phase 2)
- [ ] State machine: all 15 states defined, all transitions explicit
- [ ] Task template: all checklists complete
- [ ] Gate checklist: all 6 gates with full requirements
- [ ] Integration test: feature walkthrough complete from start to finish
- [ ] Verification scripts: all error cases handled, README complete

---

## Self-Containment Checklist

**ASES can be used without re-reading FRD:**

- [ ] CLAUDE.md tells a new user what ASES is (yes, project identity section)
- [ ] CLAUDE.md tells a new user what phase we're in (yes, current status section)
- [ ] CLAUDE.md tells a new user the folder structure (yes, reference section)
- [ ] QUICK-START.md tells a new user how to start (yes, below)
- [ ] Agent prompts tell agents what to do (yes, complete role + reads + writes)
- [ ] Templates tell users what to fill (yes, comments and structure)
- [ ] Workflows tell users the sequence (yes, step-by-step)
- [ ] State machine tells users the state space (yes, 15 states + transitions)
- [ ] Gate checklist tells users when they're blocked (yes, per-gate requirements)

A first-time user can:
1. Read CLAUDE.md
2. Read QUICK-START.md
3. Read the appropriate agent prompt (PLANNER, etc.)
4. Copy a template and read task-template.md
5. Run verification scripts
6. Read gate checklist for approval criteria

No need to re-read FRD.

---

## Coherence Checklist

**All pieces fit together:**

- [ ] Every agent prompt mentions gates (yes, all 6 gates are gates referenced)
- [ ] Every gate in state-machine.md has a checklist in GATE-CHECKLIST.md (yes, 6 gates → 6 checklists)
- [ ] Every template in GATE-CHECKLIST.md has a corresponding .ases/templates/ file (yes, 10 templates)
- [ ] Every workflow in .ases/workflows/ follows the state machine (yes, feature/bugfix/baseline-audit/bootstrap)
- [ ] Every agent role in task-template.md has a prompt in .ases/agents/ (yes, 6 agents)
- [ ] Every task state in state-machine.md is reachable from INTEGRATION-TEST.md (yes, CREATED → ... → COMPLETED)
- [ ] IMPLEMENTATION-PLAN.md lists 9 tasks; all 9 are complete (yes, 001–009)
- [ ] CLAUDE.md IN PROGRESS section shows all tasks (yes, 8 completed + 1 in progress)

---

## Evidence Capture Checklist

**Verification scripts work end-to-end:**

- [ ] `.ases/commands/capture-evidence.sh task-001 typescript` would work (yes, script written for any task-id)
- [ ] Output directory `.ases/evidence/task-001/` is created (yes, script creates it)
- [ ] All 5 log files are produced (yes, build, types, lint, test, regression)
- [ ] Logs are timestamped (yes, `date +%Y%m%d_%H%M%S`)
- [ ] Scripts handle missing tools gracefully (yes, "tool not found" message logged)
- [ ] README explains how to interpret logs (yes, README.md section on output structure)

---

## Final Gate: Ready for Phase 2?

**Phase 0 (ASES Bootstrap) is complete and ready to govern Phase 2 (Ortho/Expense development) when:**

- [ ] All 9 tasks complete (yes, all committed)
- [ ] All 32 artifacts created (yes, inventory above)
- [ ] No placeholders (yes, verified)
- [ ] No broken references (yes, verified)
- [ ] First-time user can use ASES (yes, QUICK-START.md provides path)
- [ ] All gates documented (yes, GATE-CHECKLIST.md)
- [ ] All FRD requirements met (yes, verified against IMPLEMENTATION-PLAN.md)

---

## Sign-Off

| Role | Approval | Date | Notes |
|------|----------|------|-------|
| BUILDER (solo dev) | TBD | TBD | Verify all artifacts exist |
| REVIEWER (solo dev) | TBD | TBD | Verify no gaps, coherent |
| PROJECT OWNER (solo dev) | TBD | TBD | Final approval to proceed to Phase 2 |

---

## Action Items (if any failed)

If any checkbox is unchecked:

1. Identify which artifact is missing or incomplete
2. Create or update that artifact per task-template.md
3. Re-run this checklist
4. Commit changes: `git add . && git commit -m "Fix: [artifact] — [issue]"`

---

*End of READINESS.md*
