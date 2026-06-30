# ASES Gate Checklist — Quick Reference

All 10 gates and their requirements. No gate can be skipped.

---

## Gate 1: PLANNER Completion

**Blocks:** READY-FOR-ARCHITECT → ARCHITECTURE-REVIEW  
**Required Artifacts:** plan.md, spec.md, rollback-plan.md  
**Sign-off:** Human approval

### Checklist

- [ ] plan.md exists and is complete (objective, atomic tasks, dependencies, risks, acceptance criteria)
- [ ] spec.md exists and is complete (objective, files-to-modify, contracts, acceptance criteria, impact)
- [ ] rollback-plan.md exists and is complete (trigger, procedure, affected components, post-rollback verification)
- [ ] No placeholders in any document
- [ ] All acceptance criteria are testable and binary (pass/fail)
- [ ] No vague criteria like "should work correctly"
- [ ] No sensitive data in artifacts (credentials, keys, etc.)

**Failure:** If rejected, task returns to PLANNING. PLANNER revises and resubmits.

---

## Gate 2: ARCHITECT Completion

**Blocks:** READY-FOR-BUILDER → BUILDING  
**Required Artifacts:** architecture-review.md (and optional ADRs)  
**Sign-off:** Human approval

### Checklist

- [ ] architecture-review.md exists and is complete
- [ ] Module boundaries are clearly defined
- [ ] Dependency analysis shows no circular dependencies
- [ ] API contracts are explicit
- [ ] Risk flags identify potential issues (security, performance, compliance)
- [ ] Verdict is APPROVED or REJECTED (never CONDITIONAL)
- [ ] If APPROVED: module boundaries and contracts are clear enough for BUILDER to implement
- [ ] ADRs created (if decisions deviate from bootstrap)
  - [ ] Each ADR follows template exactly
  - [ ] Each ADR indexed in .ases/architecture/adrs/INDEX.md
  - [ ] Each ADR linked in .ases/architecture/decisions.md (append-only)
- [ ] No placeholders

**Failure:** If rejected, task returns to ARCHITECTURE-REVIEW. ARCHITECT revises and resubmits.

---

## Gate 3: BUILDER Completion

**Blocks:** READY-FOR-TEST-DESIGNER → TEST-DESIGN  
**Required Artifacts:** implementation-notes.md (and source code committed)  
**Sign-off:** Human approval

### Checklist

- [ ] Source code is committed to git with descriptive messages
- [ ] implementation-notes.md exists and is complete
  - [ ] What was built: features, modules, changes
  - [ ] What was NOT built: deferred work, marked as future tasks
  - [ ] Deviations: any changes from spec.md explained
  - [ ] Files modified: exact list of files changed
  - [ ] Verification commands: how to test locally
- [ ] Code is syntactically correct (tsc, eslint, build passes locally)
- [ ] No obvious bugs (code review shows reasonable quality)
- [ ] Rollback plan was read before implementation began
- [ ] All dependencies are documented (new packages, external services, etc.)
- [ ] No sensitive data committed (credentials, keys, etc.)
- [ ] No placeholders

**Failure:** If rejected, task returns to BUILDING. BUILDER revises code and resubmits.

---

## Gate 4: TEST-DESIGNER Completion

**Blocks:** READY-FOR-VERIFIER → VERIFICATION-MODE-A  
**Required Artifacts:** test-plan.md (and test code committed)  
**Sign-off:** Human approval

### Checklist

- [ ] **NEW SESSION:** TEST-DESIGNER did not work in same session as BUILDER
- [ ] Test code is committed to git with descriptive messages
- [ ] test-plan.md exists and is complete
  - [ ] Unit tests per criterion: each acceptance criterion has at least one unit test
  - [ ] Integration tests: cross-module workflows tested
  - [ ] Edge cases: boundary conditions, null/empty inputs, large inputs, etc.
  - [ ] Failure scenarios: error handling, missing dependencies, invalid data
  - [ ] Regression candidates: existing tests that must still pass
- [ ] All tests pass locally (fixture: assume code is correct)
- [ ] Coverage data available (jest --coverage, pytest --cov)
- [ ] test-plan.md covers 100% of acceptance criteria from spec.md
- [ ] No vague tests (tests must produce binary pass/fail results)
- [ ] No placeholders

**Failure:** If rejected, task returns to TEST-DESIGN. TEST-DESIGNER revises tests and resubmits.

---

## Gate 5: VERIFIER Completion

**Blocks:** READY-FOR-REVIEWER → REVIEW  
**Required Artifacts:** verification-report.md, evidence-package.md (and evidence logs)  
**Sign-off:** Human approval

### Checklist

**Mode A (Evidence Capture):**
- [ ] `./ases/commands/capture-evidence.sh [task-id] [stack]` completed successfully
- [ ] All evidence logs exist in .ases/evidence/[task-id]/:
  - [ ] build-[timestamp].log (or summary equivalent)
  - [ ] types-[timestamp].log (type checking)
  - [ ] lint-[timestamp].log (linting)
  - [ ] test-[timestamp].log (unit tests + coverage)
  - [ ] regression-[timestamp].log (full regression suite)
- [ ] Log files reflect actual tool output (no manual editing)
- [ ] If tools are missing: log documents that (e.g., "mypy not found")
- [ ] If tests fail: log shows exact error messages

**Mode B (Evidence Interpretation):**
- [ ] verification-report.md exists and is complete
  - [ ] For each log file: exact quotes from logs (never paraphrased)
  - [ ] Criteria pass/fail summary
  - [ ] Evidence gaps documented (MANUAL-REQUIRED, MISSING, LIMITATION)
  - [ ] Each gap explained: why it exists, how to address it
- [ ] evidence-package.md exists and is complete
  - [ ] Checklist: do gates 1–5 artifacts exist? (yes/no per artifact)
  - [ ] Known limitations documented
  - [ ] Ready-for-review verdict: YES or NO
  - [ ] If NO: reasons documented clearly
- [ ] No fabricated output (only tool output is evidence)
- [ ] No paraphrasing (exact log quotes)
- [ ] No placeholders

**Failure:** If rejected, task returns to VERIFICATION-MODE-A. VERIFIER recaptures evidence and re-interprets.

---

## Gate 6: REVIEWER Completion

**Blocks:** READY-FOR-RELEASE → COMPLETED  
**Required Artifacts:** review.md  
**Sign-off:** Human approval (final release gate)

### Checklist

- [ ] **NEW SESSION:** REVIEWER did not work in same session as BUILDER or VERIFIER
- [ ] All prior artifacts read:
  - [ ] spec.md (what was supposed to be built)
  - [ ] implementation-notes.md (what was actually built)
  - [ ] test-plan.md (test strategy)
  - [ ] verification-report.md (evidence)
- [ ] review.md exists and addresses all 7 adversarial questions:
  - [ ] Q1: Does implementation match spec exactly?
  - [ ] Q2: Are there obvious bugs or edge cases the tests miss?
  - [ ] Q3: Are there security vulnerabilities (injection, XSS, auth bypass, etc.)?
  - [ ] Q4: Does rollback procedure actually work? (any blocking dependencies?)
  - [ ] Q5: Are there performance or scalability issues?
  - [ ] Q6: Is code maintainable, well-structured, documented?
  - [ ] Q7: Are there compliance or legal implications (privacy, SOC 2, GDPR, etc.)?
- [ ] For each issue raised: specific file/line citations
- [ ] Verdict is APPROVED or REJECTED (never CONDITIONAL)
- [ ] If APPROVED: reviewer is confident in implementation
- [ ] If REJECTED: specific action items for remediation are listed
- [ ] Security assessment complete (pass/fail/conditional)
- [ ] Architecture compliance verified (does code follow module contracts?)
- [ ] No placeholders

**Failure:** If rejected, task returns to REVIEW. REVIEWER raises specific issues. BUILDER creates new task for remediation.

---

## Gate Summary Table

| Gate | From | To | Artifacts | Questions Answered |
|------|------|----|-----------|----|
| **1** | READY-FOR-ARCHITECT | ARCHITECTURE-REVIEW | plan, spec, rollback | Are criteria testable? Is scope clear? |
| **2** | READY-FOR-BUILDER | BUILDING | arch-review | Are module boundaries clear? Can BUILDER implement this? |
| **3** | READY-FOR-TEST-DESIGNER | TEST-DESIGN | impl-notes, code | Is code correct? Is implementation complete? |
| **4** | READY-FOR-VERIFIER | VERIFICATION-MODE-A | test-plan, tests | Do tests cover all criteria? Can we run them? |
| **5** | READY-FOR-REVIEWER | REVIEW | verification-report, evidence-package | Did tests pass? Are there evidence gaps? Is task ready for review? |
| **6** | READY-FOR-RELEASE | COMPLETED | review | Is this safe to release? Any critical issues? |

---

## Rejection Recovery

If a gate is rejected:

1. **Identify:** Which gate? (Gate 1–6)
2. **Read feedback:** Human comments explain what's wrong
3. **Revert:** Task returns to state before the gate
4. **Revise:** Appropriate agent (PLANNER, ARCHITECT, BUILDER, TEST-DESIGNER, VERIFIER, REVIEWER) fixes artifacts
5. **Resubmit:** Artifacts re-committed, gate re-evaluated

**Example:** Gate 3 rejected (implementation has bugs). Task returns to BUILDING. BUILDER fixes code, updates implementation-notes.md, re-commits. Gate 3 re-evaluated.

---

## Quick Debug

**"Why can't we proceed?"**

1. Check CLAUDE.md IN PROGRESS section — what state is the task in?
2. Find the last gate passed (Gates 1–6)
3. Verify all required artifacts for that gate exist and are complete
4. Check for placeholders in artifacts
5. If an artifact is missing: which agent produces it? That agent must work next

**Example:** Task is in READY-FOR-ARCHITECT but Gate 1 never passed. Check plan.md, spec.md, rollback-plan.md — one or more is missing or incomplete. PLANNER must complete the missing artifact.

---

*End of GATE-CHECKLIST.md*
