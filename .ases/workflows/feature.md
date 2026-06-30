# Feature Workflow

**Version:** 1.0  
**Source:** ASES FRD v1.1, Part 7.1  
**Purpose:** Standard workflow for implementing new features under ASES governance

---

## Overview

This workflow orchestrates a complete feature from request to merged code. It enforces role separation, evidence-gated completion, and honest uncertainty through 5 explicit gates where human approval is required.

**Key Principle:** No agent can proceed without explicit human approval at gates. No false claims of completion without evidence.

---

## Workflow Sequence

```
HUMAN provides feature request
    ↓
[GATE 1: Plan Approval]
    ↓
PLANNER session
  reads: CLAUDE.md, feature request, architecture docs
  produces: plan.md + spec.md + rollback-plan.md
  task state: DRAFT → PLANNED
    ↓
Human reviews all three documents
    ↓ APPROVED
ARCHITECT session (skip only with explicit human waiver for simple tasks)
  reads: plan.md, spec.md, architecture docs, existing ADRs
  produces: architecture-review.md, ADRs if required
  task state: PLANNED → ARCH-REVIEW → READY-TO-BUILD
    ↓
[GATE 2: Architecture Approval]
    ↓
Human reviews architecture-review.md
    ↓ APPROVED
BUILDER session
  reads: spec.md, rollback-plan.md (MANDATORY — must read first)
  produces: production code + implementation-notes.md
  task state: READY-TO-BUILD → IMPLEMENTED
    ↓
[GATE 3: Scope Review]
    ↓
Human reviews implementation-notes.md for scope violations
    ↓ NO VIOLATIONS
TEST-DESIGNER session (MUST be fresh — zero BUILDER context)
  reads: spec.md, implementation-notes.md, actual code (fresh read)
  produces: tests + test-plan.md
  task state: IMPLEMENTED → TESTS-WRITTEN
    ↓
[GATE 4: Test Coverage Review]
    ↓
Human reviews test-plan.md before VERIFIER runs
    ↓ APPROVED
VERIFIER session
  Mode A: runs commands, captures logs to timestamped files
  Mode B: reads logs, produces verification-report.md + evidence-package.md
  task state: TESTS-WRITTEN → VERIFICATION → VERIFIED or FAILED
    ↓
[GATE 5: Evidence Review]
    ↓
Human reads verification-report.md AND opens at least one log file directly
    ↓ VERIFICATION PASSED
REVIEWER session (fresh — zero BUILDER context)
  reads: spec.md, verification-report.md, evidence-package.md, actual logs, code
  produces: review.md
  task state: VERIFIED → REVIEW → APPROVED or CHANGES-REQUIRED
    ↓
[If CHANGES-REQUIRED: Return to BUILDER with specific issues]
    ↓ BUILDER fixes and resubmits (new session) → TEST-DESIGNER (new session) → VERIFIER → REVIEWER
    ↓ [Repeat until APPROVED]
    ↓
Human runs git commit with evidence reference
  task state: APPROVED → COMMITTED
    ↓
CLAUDE.md updated: task moved to COMPLETED
```

---

## Gate Definitions

### GATE 1: Plan Approval

**Required Artifacts:**
- `.ases/tasks/[task-id]/plan.md` — Feature breakdown, atomic tasks, risks, acceptance criteria
- `.ases/tasks/[task-id]/spec.md` — Objective, files, contracts, acceptance criteria
- `.ases/tasks/[task-id]/rollback-plan.md` — Triggers, procedures, verification

**Human Review Checklist:**
- [ ] Feature summary is clear (2-3 sentences describing what and why)
- [ ] Atomic task breakdown is testable (30-90 min per task)
- [ ] Task dependencies are clear and in correct order
- [ ] Risks are identified with mitigation strategies
- [ ] Acceptance criteria are binary and testable (not vague)
- [ ] Files to create/modify are explicit (no patterns)
- [ ] Files to NOT touch are listed
- [ ] Input/output contracts are defined
- [ ] Rollback procedure is repeatable
- [ ] Rollback triggers are clear

**Valid Decisions:**
- ✓ **APPROVED** — Plan is clear, proceed to ARCHITECT
- ✗ **SEND BACK TO PLANNER** — Specific issues (vague criteria, missing dependencies, etc.)
- ✗ **REJECTED** — Feature not approved to proceed; document reason in CLAUDE.md

**Transition:**
- If APPROVED: Move task to ARCH-REVIEW state, proceed to ARCHITECT session
- If SEND BACK: PLANNER session updates plan.md/spec.md with feedback, resubmit
- If REJECTED: Update CLAUDE.md with decision, task moves to BLOCKED

---

### GATE 2: Architecture Approval

**Required Artifacts:**
- `.ases/tasks/[task-id]/architecture-review.md` — Module boundaries, dependencies, APIs, risks, verdict
- `.ases/architecture/adrs/ADR-[NNN]-*.md` (if required) — New ADRs created by ARCHITECT

**Human Review Checklist:**
- [ ] Module boundaries are clear and coherent
- [ ] No circular dependencies detected
- [ ] All new APIs are defined with input/output contracts
- [ ] Data flow is clear (validation at right layer)
- [ ] Security/scalability/extensibility risks are addressed
- [ ] ADRs are created for mandatory decisions (new modules, APIs, schemas, security)
- [ ] Verdict is explicit (APPROVED or REJECTED with specific reasons)

**Valid Decisions:**
- ✓ **APPROVED** — Architecture is sound, proceed to BUILDER
- ✗ **SEND BACK TO PLANNER** — Architecture issues require design rework
- ✓ **WAIVER (for simple tasks)** — Skip architecture review, proceed to BUILDER (explicit human waiver required)

**Transition:**
- If APPROVED: Move task to READY-TO-BUILD state, proceed to BUILDER session
- If SEND BACK: PLANNER session revises plan/spec based on architecture feedback
- If WAIVER: Move to READY-TO-BUILD, document waiver in CLAUDE.md

---

### GATE 3: Scope Review

**Required Artifact:**
- `.ases/tasks/[task-id]/implementation-notes.md` — What was built, what was NOT built, any deviations

**Human Review Checklist:**
- [ ] Files created match spec.md (no extra files)
- [ ] Files modified match spec.md (no extra modifications)
- [ ] "What was NOT built" section lists spec items that were deliberately skipped (none should exist unless justified)
- [ ] "Deviations from spec" section lists any changes with explicit justification (should be empty or rare)
- [ ] All deviations are acceptable and documented
- [ ] Verification commands are reasonable and will catch issues

**Valid Decisions:**
- ✓ **APPROVED** — Implementation is in scope, proceed to TEST-DESIGNER
- ✗ **SEND BACK TO BUILDER** — Scope violations (extra files, missing requirements, unjustified deviations)

**Transition:**
- If APPROVED: Move task to TESTS-WRITTEN state, proceed to TEST-DESIGNER session
- If SEND BACK: BUILDER session fixes scope violations and resubmits

---

### GATE 4: Test Coverage Review

**Required Artifact:**
- `.ases/tasks/[task-id]/test-plan.md` — Tests per criterion, integration tests, edge cases, failure scenarios

**Human Review Checklist:**
- [ ] ≥1 test per acceptance criterion (from spec.md)
- [ ] Integration tests cover component boundaries
- [ ] Edge cases tested (empty, null, boundary, concurrent, type mismatch)
- [ ] Failure scenarios tested (errors return correct status)
- [ ] Regression candidates identified (existing tests listed)
- [ ] No vague tests ("should work" is forbidden — must be specific)
- [ ] Tests can actually run (no syntax errors in examples)

**Valid Decisions:**
- ✓ **APPROVED** — Test coverage is comprehensive, proceed to VERIFIER
- ✗ **SEND BACK TO TEST-DESIGNER** — Coverage gaps (missing criteria, no edge cases, only happy path)

**Transition:**
- If APPROVED: Move task to VERIFICATION state, proceed to VERIFIER session
- If SEND BACK: TEST-DESIGNER session (new session, fresh context) adds tests and resubmits

---

### GATE 5: Evidence Review

**Required Artifacts:**
- `.ases/tasks/[task-id]/verification-report.md` — BUILD, LINT, TYPES, TESTS, REGRESSION status
- `.ases/tasks/[task-id]/evidence-package.md` — Gates checklist (all 10 gates)
- Actual log files in `.ases/evidence/[task-id]/` (human must spot-check at least one)

**Human Review Checklist:**
- [ ] Verification report exists with all checks
- [ ] BUILD status is PASS (exit 0 from tsc/gradle)
- [ ] LINT status is PASS (exit 0 from eslint/ktlint)
- [ ] TYPE-CHECK status is PASS (exit 0, if applicable)
- [ ] UNIT-TESTS status is PASS (X passed, 0 failed)
- [ ] COVERAGE is ≥80% (if measured)
- [ ] REGRESSION status is PASS (0 new failures)
- [ ] Evidence package shows all ✓ (no ✗)
- [ ] Opened actual log file (`.ases/evidence/[task-id]/*.log`) to verify evidence is real
- [ ] No log file references are fabricated

**Valid Decisions:**
- ✓ **VERIFIED** — All checks passed, proceed to REVIEWER
- ✗ **FAILED** — Verification showed failures (tests failed, regressions, etc.)

**Transition:**
- If VERIFIED: Move task to REVIEW state, proceed to REVIEWER session
- If FAILED: BUILDER session fixes failures, TEST-DESIGNER (new session) updates tests, VERIFIER re-runs

---

## Task State Transitions

```
DRAFT
  ↓ (human approves plan)
PLANNED
  ↓ (human approves architecture, or waives)
ARCH-REVIEW
  ↓ (ARCHITECT completes review)
READY-TO-BUILD
  ↓ (BUILDER implements)
IMPLEMENTED
  ↓ (human approves scope)
TESTS-WRITTEN
  ↓ (TEST-DESIGNER completes tests)
VERIFICATION
  ↓ (VERIFIER runs commands and interprets)
VERIFIED ← (all gates pass)
  ↓
REVIEW
  ↓ (REVIEWER audits code)
APPROVED ← (REVIEWER approves)
  ↓
COMMITTED ← (human runs git commit)

Alternative paths:
VERIFICATION → FAILED ← (tests or regression failed)
REVIEW → CHANGES-REQUIRED ← (REVIEWER found issues)
  ↓ (return to BUILDER with specifics)
IMPLEMENTED (new session, fix issue)
```

---

## Failure Recovery

### If BUILD fails (compilation error)

**What happened:** VERIFIER ran `tsc` or equivalent, exit ≠ 0

**Decision Points:**
1. **Bug in BUILDER code** (most likely) → BUILDER session fixes issue, resubmit → TEST-DESIGNER → VERIFIER
2. **Environment issue** (missing dependency) → Document, BUILDER fixes environment, rerun verification
3. **Type system issue** (legitimate disagreement with type checking) → ARCHITECT review → decision

**Next Step:** BUILDER fixes and resubmits. Go back to BUILDER session (new).

### If LINT fails (style violations)

**What happened:** VERIFIER ran `eslint` or equivalent, exit ≠ 0

**Recovery:** BUILDER session fixes style issues, resubmit. Go back to BUILDER session (new).

### If TESTS fail (test failures)

**What happened:** VERIFIER ran tests, exit ≠ 0 or X tests failed

**Decision Points:**
1. **Bug in production code** → BUILDER fixes code, resubmit
2. **Bug in tests** → TEST-DESIGNER fixes tests (new session), resubmit
3. **Legitimate test failure** (test is correct, code is wrong) → BUILDER fixes code, resubmit

**Recovery:** Depends on root cause. Either BUILDER or TEST-DESIGNER fixes and resubmits.

### If REGRESSION fails (new test failures)

**What happened:** VERIFIER ran full test suite, previously passing tests now fail

**Recovery:** BUILDER must fix the regression. This is a critical issue — code broke existing functionality.

1. Analyze log file to see which tests broke
2. BUILDER investigates why existing tests fail
3. BUILDER fixes regression
4. Resubmit → TEST-DESIGNER → VERIFIER

### If REVIEWER finds CHANGES-REQUIRED

**What happened:** REVIEWER read code and log files, found issues

**Recovery:** BUILDER fixes specific issues noted by REVIEWER (new session)

1. BUILDER reads review.md with specific issues (file/line/fix)
2. BUILDER implements fixes
3. BUILDER resubmits → TEST-DESIGNER (new session) → VERIFIER → REVIEWER

**Process repeats until REVIEWER verdict is APPROVED.**

---

## Role Responsibilities in Feature Workflow

### PLANNER
- Breaks feature into atomic tasks
- Defines acceptance criteria (testable, binary)
- Identifies risks
- Creates plan + spec + rollback-plan

### ARCHITECT
- Validates module boundaries
- Analyzes dependencies
- Defines API contracts
- Creates ADRs if required
- Produces architecture-review.md

### BUILDER
- Implements exactly what spec says
- Reads rollback-plan.md FIRST
- Documents deviations (with justification)
- Produces production code + implementation-notes.md
- Does NOT claim to have tested or verified

### TEST-DESIGNER
- Writes tests in independent session (zero BUILDER context)
- Covers all acceptance criteria (1+ test per criterion)
- Tests edge cases and failure scenarios
- Produces test files + test-plan.md

### VERIFIER
- Mode A: Runs commands, captures evidence to timestamped logs
- Mode B: Reads logs, compares to spec, produces verification-report.md
- Never claims to have run commands it did not run
- Produces evidence-package.md with gates checklist

### REVIEWER
- Reads code fresh (zero BUILDER context)
- Asks seven adversarial questions
- Checks security, architecture, code quality
- Produces review.md with explicit verdict (APPROVED or CHANGES-REQUIRED)
- Can block merge if issues found

### HUMAN
- Approves plans at 5 gates
- Makes rollback decisions
- Spot-checks evidence (opens actual log files)
- Commits code to git (after all approvals)
- Makes final decisions (reject feature, send back, etc.)

---

## When to Skip Steps

### Skip ARCHITECT Review (simple tasks only)

**Condition:** Task is strictly additive (no new modules, APIs, schemas, or security decisions)

**Requirement:** Human explicitly waives architecture review in CLAUDE.md with reason

**Waiver Template:**
```
Architecture Review Waived:
Task: [task-id]
Reason: [Simple feature, no new modules/APIs/schemas/security]
Date: [YYYY-MM-DD]
Approved by: [Human name]
```

**After Waiver:** Skip to READY-TO-BUILD state, proceed to BUILDER

---

## Commit Message Format

After REVIEWER approves and human commits, use this format:

```
[task-id]: [what changed — specific]

Evidence: .ases/evidence/[task-id]/
Gates: BUILD ✓ LINT ✓ TYPES ✓ TESTS ✓ REGRESSION ✓ REVIEW ✓
ADRs: ADR-[NNN] (if applicable)
Confidence: EVIDENCE-BACKED

Co-Authored-By: Claude [Model] <noreply@anthropic.com>
```

---

## Troubleshooting

### Workflow is blocked at a gate

**Check:**
1. Is the required artifact present? (plan.md, spec.md, etc.)
2. Is the artifact complete? (no placeholders, no vague sections)
3. Has human approved the artifact?

**Action:** Go back to the responsible agent and have them complete or fix the artifact.

### Evidence is missing (no log file)

**What went wrong:** VERIFIER claims verification passed but log file doesn't exist

**Recovery:** 
1. Re-run VERIFIER session
2. VERIFIER must produce log files
3. If VERIFIER cannot execute commands, declare EVIDENCE-SOURCE: HUMAN-TERMINAL and wait for human to provide logs

### Human approved a gate, but task didn't advance

**Check:**
1. Did human update CLAUDE.md with new task state?
2. Is the next agent aware they should start?

**Action:** Manually update CLAUDE.md to reflect current state and notify next agent.

---

*End of feature.md workflow*
