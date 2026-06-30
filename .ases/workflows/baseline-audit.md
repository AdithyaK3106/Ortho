# Baseline Audit Workflow

**Version:** 1.0  
**Source:** ASES FRD v1.1, Part 7.3  
**Purpose:** Establish verified current state of existing brownfield codebase before ASES governance begins

---

## Overview

Baseline audit is a one-time process that establishes an honest snapshot of existing code quality before ASES takes over. It answers: "What's our current verified state? What's known debt?"

**When to run:** Before running any ASES feature workflows on an existing project

**Output:** 
- `.ases/baseline/verification-report.md` — Honest assessment of current code
- `.ases/baseline/audit-report.md` — Code review findings
- `.ases/baseline/baseline-snapshot.md` — Known debt, verified components, decision log

---

## Workflow Sequence

```
Decision: Run baseline audit before first ASES feature
    ↓
VERIFIER session (Phase A only)
  runs: all verification commands (build, lint, types, tests, regression)
  produces: all evidence logs in .ases/baseline/
  task state: BASELINE-AUDIT
    ↓
VERIFIER session (Phase B only)
  reads: all logs produced in Phase A
  produces: .ases/baseline/verification-report.md
    ↓
REVIEWER session (adversarial review of existing codebase)
  reads: verification-report.md + actual logs + existing code
  produces: .ases/baseline/audit-report.md
    ↓
Human reviews both reports
    ↓
[Decision Point: Fix debt first or accept as known?]
    ↓
[If FIX FIRST]
    ↓
  Create task-N for each known issue
  Run feature workflow for each fix
  Re-run baseline audit to confirm cleaned
    ↓
[If ACCEPT AS KNOWN]
    ↓
  PLANNER creates .ases/baseline/baseline-snapshot.md
  Document known issues, verified components
  Accept as starting point
    ↓
From this point forward: ASES standard workflows apply
All new work starts with PLANNER
```

---

## Phase A: Evidence Production

VERIFIER runs all verification commands without interpreting results.

### Commands to Run (per stack)

#### TypeScript
```bash
# Create baseline directory
mkdir -p .ases/baseline

# Build
tsc --noEmit 2>&1 | tee .ases/baseline/build-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/build-$(date +%s).log

# Lint
eslint . 2>&1 | tee .ases/baseline/lint-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/lint-$(date +%s).log

# Type check (usually covered by build, but explicit for clarity)
tsc --noEmit 2>&1 | tee .ases/baseline/types-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/types-$(date +%s).log

# Tests
jest 2>&1 | tee .ases/baseline/test-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/test-$(date +%s).log

# Regression (same as tests for full suite)
jest 2>&1 | tee .ases/baseline/regression-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/regression-$(date +%s).log
```

#### Python
```bash
# Lint
ruff check . 2>&1 | tee .ases/baseline/lint-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/lint-$(date +%s).log

# Types
mypy . --strict 2>&1 | tee .ases/baseline/types-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/types-$(date +%s).log

# Tests
pytest 2>&1 | tee .ases/baseline/test-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/test-$(date +%s).log

# Regression
pytest 2>&1 | tee .ases/baseline/regression-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/regression-$(date +%s).log
```

#### Kotlin/Java
```bash
# Lint
./gradlew ktlintCheck 2>&1 | tee .ases/baseline/lint-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/lint-$(date +%s).log

# Build
./gradlew build 2>&1 | tee .ases/baseline/build-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/build-$(date +%s).log

# Tests
./gradlew test 2>&1 | tee .ases/baseline/test-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/test-$(date +%s).log

# Regression (same as tests)
./gradlew test 2>&1 | tee .ases/baseline/regression-$(date +%s).log
echo "EXIT: $?" >> .ases/baseline/regression-$(date +%s).log
```

### Rules for Phase A
- Run all commands, capture all output
- Never skip a command
- If tool is not installed, document that fact in the log
- Append EXIT code and TIMESTAMP to every log file
- Do not interpret results yet — just capture

---

## Phase B: Evidence Interpretation

VERIFIER reads all logs and produces verification report.

### `.ases/baseline/verification-report.md`

```
TASK:           BASELINE-AUDIT
PROJECT:        [project name]
AUDIT DATE:     [YYYY-MM-DD HH:MM:SS UTC]
EVIDENCE-SOURCE: CLAUDE-CLI

BUILD:          PASS | FAIL | NOT-APPLICABLE — [log file reference]
LINT:           PASS | FAIL | NOT-APPLICABLE — [log file reference]
TYPE-CHECK:     PASS | FAIL | NOT-APPLICABLE — [log file reference]
TESTS:          PASS | FAIL | NOT-APPLICABLE — [X passed, Y failed] — [log file reference]
REGRESSION:     PASS | FAIL | NOT-APPLICABLE — [X failures] — [log file reference]

SUMMARY:
[2-3 paragraphs describing current state]
- What's passing?
- What's failing?
- What tests exist?
- What's untested?

KNOWN ISSUES (copied from logs):
[Exact error text from logs, not summaries]
- Issue 1: [error from build log]
- Issue 2: [error from lint log]
- Issue 3: [failing tests from test log]

ANALYSIS:
[Honest assessment]
- Code compiles: YES | NO
- Code passes lint: YES | NO
- Type safety: STRICT | WARNINGS | ERRORS
- Test coverage: [percentage] | UNKNOWN
- Regressions: [count] | UNKNOWN
- Known debt: [list]
```

---

## Phase C: Code Review

REVIEWER performs adversarial audit of existing codebase.

### `.ases/baseline/audit-report.md`

```markdown
# Baseline Audit Report

**Date:** [YYYY-MM-DD]  
**Project:** [project name]  
**Reviewer:** REVIEWER

---

## Executive Summary

[1-2 paragraphs: What's the overall state? What's risky? What should be fixed first?]

---

## Code Quality Assessment

### Build Status
- Compiles: [YES | NO]
- Type errors: [count]
- Lint errors: [count]
- Assessment: [GOOD | ACCEPTABLE | CONCERNING | CRITICAL]

### Test Coverage
- Test count: [number]
- Coverage: [percentage]
- Assessment: [GOOD | ACCEPTABLE | POOR]

### Known Issues
[List each issue with severity]
- CRITICAL: [List]
- HIGH: [List]
- MEDIUM: [List]
- LOW: [List]

### Security Assessment
- Input validation: [YES | PARTIAL | NO]
- SQL injection risk: [LOW | MEDIUM | HIGH]
- Secrets in code: [FOUND | NOT FOUND]
- Access control: [PRESENT | MISSING]
- Assessment: [SAFE | CONCERNING | CRITICAL]

### Architecture Assessment
- Modularity: [GOOD | ACCEPTABLE | POOR]
- Dependencies: [CLEAN | CIRCULAR | UNMANAGED]
- Debt: [NONE | ACCEPTABLE | SIGNIFICANT]
- Assessment: [SOUND | CONCERNING | NEEDS REWORK]

---

## Recommendations

### Must Fix Before ASES (blockers)
1. [Issue] — [Why it blocks new development]
2. [Issue] — [Why]

### Should Fix Before ASES (high-impact)
1. [Issue] — [Impact if not fixed]
2. [Issue]

### Can Fix Later (known debt)
1. [Issue] — [Why it can wait]
2. [Issue]

### Verified Working
1. [Component] — [Why it's safe to build on]
2. [Component]

---

## Confidence Level

Can ASES begin new development on this codebase?

- ✓ YES (with or without fixing known issues first)
- ✗ NO (blockers must be fixed before proceeding)

---
```

---

## Baseline Snapshot Decision

Human reviews both reports and decides:

### Option A: Fix Known Issues First

```
Action: Create task-N for each CRITICAL/HIGH issue
Workflow: Run standard feature workflow for each fix
Result: Re-run baseline audit after fixes
Output: Updated .ases/baseline/baseline-snapshot.md with "All blockers fixed"
Then: Proceed to ASES feature development
```

### Option B: Accept Known Debt

```
Action: PLANNER creates .ases/baseline/baseline-snapshot.md
Content:
  - Verified components (what works, safe to build on)
  - Known issues (what's broken, what's untested)
  - Debt acceptance (human approves proceeding with known issues)
  - Risk assessment (if known issues cause problems, what's the impact)
  - Mitigation (what we'll do about known issues)

Then: Proceed to ASES feature development

Example:
  Verified: CategoryService works, all tests pass
  Known Issue: AuthService has 2 failing tests, not investigated
  Decision: Proceed with category features; schedule AuthService fix for next sprint
  Risk: Authentication features may be broken (low risk — not touched by category work)
```

---

## `.ases/baseline/baseline-snapshot.md` Template

```markdown
# Baseline Snapshot

**Date:** [YYYY-MM-DD]  
**Project:** [project name]  
**Baseline Audit:** Evidence in `.ases/baseline/verification-report.md` and `audit-report.md`

---

## Verified Working (Safe to Build On)

Components and modules that have been verified through baseline audit:

- CategoryService — All tests pass, no lint errors, type-safe
- ExpenseController — Builds cleanly, no regressions
- Database layer — Migrations run successfully

---

## Known Issues (Accepted Debt)

Issues identified in baseline audit that are not being fixed immediately:

### Issue 1: [Title]
- **Severity:** [CRITICAL | HIGH | MEDIUM | LOW]
- **Location:** [file/module]
- **Problem:** [What's broken or untested]
- **Impact:** [What breaks if this isn't fixed]
- **Decision:** DEFER (not fixing now)
- **When to fix:** [Next sprint | After features X | By date]
- **Mitigation:** [How we'll avoid this causing problems]

---

## Blockers Fixed

- [Issue] — FIXED in task-[N]
- [Issue] — FIXED in task-[N]

---

## From This Point Forward

All new work under ASES governance:
1. PLANNER creates plan.md + spec.md + rollback-plan.md
2. ARCHITECT reviews architecture
3. BUILDER implements (reads rollback-plan.md first!)
4. TEST-DESIGNER writes tests (independent session)
5. VERIFIER produces evidence
6. REVIEWER audits code
7. Human commits with evidence reference

No more development without evidence-gated verification.

---

## Approval

**Baseline established:** [YYYY-MM-DD]  
**Approved by:** [Human name]  
**Decision:** Proceed to ASES feature development with known issues accepted
```

---

## When Baseline Audit Fails

### Scenario: Build doesn't compile

**Decision:**
- Option A: Fix build errors first (create tasks for each error)
- Option B: Document as blocker, cannot proceed to feature development until fixed

### Scenario: Tests have massive failures

**Decision:**
- Option A: Are tests broken or is code broken? Investigate.
- Option B: If code is broken, fix before new development (too risky to build on broken foundation)
- Option C: If tests are broken, fix/remove bad tests before proceeding

### Scenario: No tests exist

**Decision:**
- This is known debt. Can proceed to feature development, but be aware new features must be tested.
- ASES will enforce testing for all NEW work going forward.
- Existing code can be low-test (known debt), but new code must be fully tested.

---

## Baseline Audit Schedule

Run baseline audit:
1. **When starting ASES** — Always, before first feature
2. **When onboarding a codebase** — Always, before ASES takes over
3. **Periodically** — Optional, to track debt over time (quarterly?)

Do not re-run constantly. Once per project lifecycle is standard.

---

*End of baseline-audit.md workflow*
