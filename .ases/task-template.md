# Task Template — Per-Task Checklist

**Copy this file for each new task. Fill in task ID, description, and work through the checklist.**

---

## Task Identity

| Field | Value |
|-------|-------|
| **Task ID** | (e.g., task-001, task-feature-auth, task-bugfix-login) |
| **Title** | One-line feature/bug description |
| **Owner** | (e.g., PLANNER, BUILDER, REVIEWER) |
| **Created** | YYYY-MM-DD HH:MM UTC |
| **State** | (CREATED, PLANNING, ..., COMPLETED) |

---

## Pre-Work Checklist

Before starting, verify:

- [ ] CLAUDE.md read and current
- [ ] Task ID added to CLAUDE.md IN PROGRESS section
- [ ] .ases/tasks/[task-id]/ directory created
- [ ] No conflicting work in progress
- [ ] Rollback plan exists (if BUILDER role)

---

## PLANNER Checklist

**Goal:** Produce plan.md, spec.md, rollback-plan.md

- [ ] Read FRD Part 1 (problem statement)
- [ ] Read FRD Part 2 (feature/bug details)
- [ ] Copy .ases/templates/plan.md → .ases/tasks/[task-id]/plan.md
- [ ] Copy .ases/templates/spec.md → .ases/tasks/[task-id]/spec.md
- [ ] Copy .ases/templates/rollback-plan.md → .ases/tasks/[task-id]/rollback-plan.md
- [ ] Fill plan.md: objective, atomic tasks, dependencies, risks, acceptance criteria
- [ ] Fill spec.md: objective, files-to-modify, input/output contracts, acceptance criteria, impact
- [ ] Fill rollback-plan.md: trigger, procedure, affected components, post-rollback verification
- [ ] Verify: no vague acceptance criteria (all testable, binary pass/fail)
- [ ] Verify: no placeholders in any document
- [ ] Commit to git with message: `task-[id]: Planning complete`

**State transition:** READY-FOR-ARCHITECT (awaiting Gate 1)

---

## ARCHITECT Checklist

**Goal:** Produce architecture-review.md and (optionally) ADRs

**Prerequisite:** Gate 1 passed (plan, spec, rollback approved)

- [ ] Read FRD Part 3 (agent roles)
- [ ] Read FRD Part 5 (ADR system, decision making)
- [ ] Read plan.md, spec.md from .ases/tasks/[task-id]/
- [ ] Copy .ases/templates/architecture-review.md → .ases/tasks/[task-id]/
- [ ] Analyze module boundaries, dependencies, API contracts
- [ ] Check for security/compliance implications
- [ ] Create ADRs if decisions deviate from bootstrap (ADR-001, ADR-002, ADR-003)
  - [ ] Each ADR follows .ases/templates/adr.md
  - [ ] Each ADR linked in .ases/architecture/decisions.md (append-only)
  - [ ] Each ADR indexed in .ases/architecture/adrs/INDEX.md
- [ ] Write architecture-review.md: module boundaries, dependency analysis, API contracts, risk flags, verdict
- [ ] Verdict must be APPROVED or REJECTED (never CONDITIONAL)
- [ ] Verify: no placeholders
- [ ] Commit to git with message: `task-[id]: Architecture review complete`

**State transition:** READY-FOR-BUILDER (awaiting Gate 2)

---

## BUILDER Checklist

**Goal:** Write code/configuration and produce implementation-notes.md

**Prerequisite:** Gate 2 passed (architecture approved)

- [ ] Read FRD Part 3.3 (BUILDER role and responsibilities)
- [ ] Read rollback-plan.md — **MANDATORY** before writing any code
- [ ] Read spec.md: understand objective, files-to-modify, acceptance criteria
- [ ] Read architecture-review.md: understand module boundaries and contracts
- [ ] Implement changes per spec
- [ ] Run initial verification (tsc, eslint, tests) locally — verify no syntax errors
- [ ] Copy .ases/templates/implementation-notes.md → .ases/tasks/[task-id]/
- [ ] Fill implementation-notes.md: what was built, what was NOT built, deviations, files modified, verification commands
- [ ] Commit code changes to git with descriptive message
- [ ] Verify: implementation-notes.md is complete and accurate
- [ ] Commit task artifact with message: `task-[id]: Implementation complete`

**State transition:** READY-FOR-TEST-DESIGNER (awaiting Gate 3)

---

## TEST-DESIGNER Checklist

**Goal:** Produce test-plan.md and write test code

**Prerequisite:** Gate 3 passed (implementation approved)

**CRITICAL:** TEST-DESIGNER must work in a NEW, independent session (never same session as BUILDER).

- [ ] **NEW SESSION:** Do not access prior session state
- [ ] Read FRD Part 3.4 (TEST-DESIGNER role and independence guarantee)
- [ ] Read spec.md and implementation-notes.md from .ases/tasks/[task-id]/
- [ ] Copy .ases/templates/test-plan.md → .ases/tasks/[task-id]/
- [ ] Design tests for each acceptance criterion
- [ ] Identify edge cases and failure scenarios
- [ ] Identify regression candidates (existing tests that must still pass)
- [ ] Write test-plan.md: unit tests per criterion, integration tests, edge cases, failure scenarios, regression list
- [ ] Write test code (unit tests, integration tests, edge cases)
- [ ] Run tests locally: all must pass (fixture: assume code is correct)
- [ ] Verify: test-plan.md covers 100% of acceptance criteria
- [ ] Verify: no placeholders
- [ ] Commit test code and test-plan.md with message: `task-[id]: Test design complete`

**State transition:** READY-FOR-VERIFIER (awaiting Gate 4)

---

## VERIFIER Checklist — Mode A (Evidence Capture)

**Goal:** Run verification commands and capture raw terminal output

**Prerequisite:** Gate 4 passed (tests approved)

- [ ] Read FRD Part 3.5 Mode A (evidence production)
- [ ] Determine stack: TypeScript, Python, Android, or combination
- [ ] Run: `./ases/commands/capture-evidence.sh [task-id] [stack]`
- [ ] Verify: all log files created in .ases/evidence/[task-id]/
  - [ ] build-[timestamp].log (summary)
  - [ ] types-[timestamp].log (type checking)
  - [ ] lint-[timestamp].log (linting)
  - [ ] test-[timestamp].log (unit tests + coverage)
  - [ ] regression-[timestamp].log (full regression suite)
- [ ] Check for failures: if a tool is missing or tests fail, log reflects that
- [ ] Do NOT edit log files manually — only tool output is evidence
- [ ] Proceed to Mode B

---

## VERIFIER Checklist — Mode B (Evidence Interpretation)

**Goal:** Interpret logs and produce verification-report.md and evidence-package.md

**Prerequisite:** Mode A complete (all evidence logs exist)

- [ ] Read FRD Part 3.5 Mode B (evidence interpretation)
- [ ] Read all log files from .ases/evidence/[task-id]/ (exact quotes required)
- [ ] Copy .ases/templates/verification-report.md → .ases/tasks/[task-id]/
- [ ] Copy .ases/templates/evidence-package.md → .ases/tasks/[task-id]/
- [ ] Fill verification-report.md:
  - [ ] For each log file: paste exact error/success lines
  - [ ] Summarize: which criteria passed, which failed
  - [ ] Flag any evidence gaps: MANUAL-REQUIRED, MISSING, LIMITATION
- [ ] Fill evidence-package.md:
  - [ ] Checklist: gates 1–5 artifacts present?
  - [ ] Known limitations documented
  - [ ] Ready-for-review verdict: YES or NO
- [ ] Verify: no paraphrasing (exact quotes from logs)
- [ ] Verify: no fabricated output
- [ ] Verify: gaps documented honestly
- [ ] Commit with message: `task-[id]: Verification complete`

**State transition:** READY-FOR-REVIEWER (awaiting Gate 5)

---

## REVIEWER Checklist

**Goal:** Conduct final adversarial review and produce review.md

**Prerequisite:** Gate 5 passed (evidence approved)

**CRITICAL:** REVIEWER must work in a NEW, independent session (never same session as BUILDER or VERIFIER).

- [ ] **NEW SESSION:** Do not access prior session state
- [ ] Read FRD Part 3.6 (REVIEWER role and 7 adversarial questions)
- [ ] Read spec.md, implementation-notes.md, test-plan.md, verification-report.md
- [ ] Copy .ases/templates/review.md → .ases/tasks/[task-id]/
- [ ] Ask all 7 adversarial questions (see GATE-CHECKLIST.md):
  - [ ] Q1: Does implementation match spec?
  - [ ] Q2: Are there obvious bugs or edge cases the tests miss?
  - [ ] Q3: Are there security vulnerabilities?
  - [ ] Q4: Does rollback procedure actually work?
  - [ ] Q5: Are there performance or scalability issues?
  - [ ] Q6: Is the code maintainable and well-structured?
  - [ ] Q7: Are there compliance or legal implications?
- [ ] Cite specific lines/files for each concern
- [ ] Write review.md: verdict (APPROVED or REJECTED), specific issues, security assessment, architecture compliance
- [ ] Verdict must be APPROVED or REJECTED (never CONDITIONAL)
- [ ] Verify: all 7 questions addressed
- [ ] Verify: specific file/line citations for issues
- [ ] Commit with message: `task-[id]: Review complete`

**State transition:** READY-FOR-RELEASE (awaiting Gate 6)

---

## Post-Completion Checklist

**After Gate 6 passed (task COMPLETED):**

- [ ] All 10 per-task artifacts exist in .ases/tasks/[task-id]/
- [ ] All artifacts committed to git
- [ ] CLAUDE.md updated: task moved from IN PROGRESS to COMPLETED
- [ ] No artifacts have placeholders
- [ ] No evidence has been manually edited (only tool output)
- [ ] Rollback plan was tested (documented in notes or evidence)

---

## State Tracking

After each major milestone, update CLAUDE.md:

```markdown
| [task-id] | [description] | [state] | [current-activity] | [next-step] |
```

States: CREATED, PLANNING, READY-FOR-ARCHITECT, ARCHITECTURE-REVIEW, READY-FOR-BUILDER, BUILDING, READY-FOR-TEST-DESIGNER, TEST-DESIGN, READY-FOR-VERIFIER, VERIFICATION-MODE-A, VERIFICATION-MODE-B, READY-FOR-REVIEWER, REVIEW, READY-FOR-RELEASE, COMPLETED

---

*End of task-template.md*
