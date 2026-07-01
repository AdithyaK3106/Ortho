# Test Execution Policy Fixes — Applied 2026-07-01

**Commit:** c41203b  
**Status:** COMPLETE — All 6 fixes applied to CLAUDE.md, workflow documents, and agent instructions

---

## Summary

Phase 1 tasks (1–5) revealed a critical gap: **tests were designed but not executed**. Tasks 1-4 showed 100% pass rates that were based on designed tests or simulated logs, not actual pytest runs. Only task-005 (which actually ran pytest) discovered real bugs.

This document tracks the fixes applied to prevent recurrence in Phase 2+.

---

## The 6 Fixes Applied

### ✅ Fix 1: VERIFIER Mode A — Mandatory pytest Execution

**What changed:**
- VERIFIER must run pytest, not just design tests
- All output captured to `.ases/evidence/[task-id]/test-*.log`
- EXIT codes recorded
- If import/syntax errors: declare BLOCKED, don't fabricate logs

**Affected documents:**
- `CLAUDE.md` — "Test Execution Policy" section added
- `CLAUDE.md` — VERIFIER role instructions updated
- `.ases/TEST-EXECUTION-POLICY.md` — Section 1

**Enforcement:** GATE 5 approval requires log files with EXIT codes

---

### ✅ Fix 2: GATE 5 — Human Spot-Checks Real Log Files

**What changed:**
- Human must open actual test log file before GATE 5 approval
- Verify real pytest output format (not fabricated)
- Check EXIT code matches status claim
- Read error messages if failures exist

**Affected documents:**
- `CLAUDE.md` — "How to Continue" section updated (HUMAN role)
- `CLAUDE.md` — "How to Continue" section updated (REVIEWER role)
- `.ases/GATE-5-VERIFICATION-CHECKLIST.md` — New reference guide (6-step checklist)

**Enforcement:** Checklist blocks approval if logs are missing or fabricated

---

### ✅ Fix 3: Environment Validation — Pre-flight Import Checks

**What changed:**
- VERIFIER runs import check BEFORE full pytest suite
- `python -c "import packages.[name]"` fails fast
- If import fails → BLOCKED (wait for BUILDER/TEST-DESIGNER fix)
- Only runs full test suite if imports pass

**Affected documents:**
- `CLAUDE.md` — "Verification Commands Reference" section added
- `CLAUDE.md` — VERIFIER Phase A pre-flight steps added
- `.ases/TEST-EXECUTION-POLICY.md` — Section 3

**Enforcement:** Import check runs first, blocks full suite if broken

---

### ✅ Fix 4: Expected Test Metrics — Document Baseline in Spec

**What changed:**
- Every task spec.md includes "Expected Test Metrics" section
- Baseline: unit test count, integration count, edge cases, coverage %
- Actual results checked against baseline at GATE 5
- Mismatch → approval blocks, task returns to appropriate role

**Affected documents:**
- `CLAUDE.md` — "Verification Status" section added
- `CLAUDE.md` — "Test Execution Policy" section explains metrics
- `.ases/TEST-EXECUTION-POLICY.md` — Section 4

**Enforcement:** Spec review includes metrics; GATE 5 rejects mismatches

---

### ✅ Fix 5: Known Limitations = xfail (Before Verification)

**What changed:**
- Limitations documented in implementation-notes.md (by BUILDER)
- Marked with `@pytest.mark.xfail(reason="...")` in test code (by TEST-DESIGNER)
- Before verification runs (not after-the-fact approval)
- Counted as PASS (expected failure), not regression

**Affected documents:**
- `CLAUDE.md` — "Notes for Next Session" updated for TEST-DESIGNER
- `CLAUDE.md` — "Notes for Next Session" updated for BUILDER
- `.ases/TEST-EXECUTION-POLICY.md` — Section 5

**Enforcement:** Known limitations must be xfail before GATE 5 approval

---

### ✅ Fix 6: GATE 4 Pilot Test — Run 5-10 Sample Tests Before Approval

**What changed:**
- Before approving test-plan.md, run 5-10 sample tests (proof-of-concept)
- Catches test-code bugs early (imports, syntax, setup)
- If pilot fails (EXIT ≠ 0) → return to TEST-DESIGNER to fix
- Only full suite approved if pilot passes

**Affected documents:**
- `CLAUDE.md` — "Notes for Next Session" VERIFIER section updated
- `CLAUDE.md` — "How to Continue" VERIFIER section updated
- `.ases/TEST-EXECUTION-POLICY.md` — Section 6

**Enforcement:** Pilot test runs at GATE 4 boundary, blocks full approval if broken

---

## New Documents Created

### 1. `.ases/TEST-EXECUTION-POLICY.md` (449 lines)
Comprehensive specification of the policy:
- Root cause analysis
- All 6 fixes detailed
- Enforcement checklist (per role)
- Examples (real passes/fails/fabricated)
- Rollout plan
- FAQ

### 2. `.ases/GATE-5-VERIFICATION-CHECKLIST.md` (239 lines)
Step-by-step audit guide for HUMAN reviewer:
- 6-step process to verify real pytest output
- Decision tree (approve/block)
- Red flags (always block if seen)
- Common issues & resolution
- Sign-off section

### 3. Memory record: `test-execution-policy.md`
Persistent memory of policy for future sessions

---

## Modified Documents

### CLAUDE.md (347 → 694 lines, +347 additions)

**New sections added:**
1. "Test Execution Policy (Fixed - Phase 2+)" — 6 fixes + verification commands
2. "Verification Commands Reference (Phase 2+ Tasks)" — exact commands for VERIFIER
3. Updated "Notes for Next Session" — Phase 2+ roles with new enforcement
4. Updated "How to Continue" — Phase 2+ workflow with test execution mandatory
5. Updated "Verification Status" — Policy change effective Phase 2+

**Updated role instructions:**
- PLANNER: Include expected metrics in spec
- BUILDER: Document known limitations
- TEST-DESIGNER: Verify imports before submission, include sample tests
- VERIFIER: Phase A (pre-flight), Phase B (pilot), Phase C (full), all with real pytest
- HUMAN: Spot-check log files at GATE 5
- REVIEWER: Verify log files contain real pytest output

---

## Enforcement Mechanisms

| Fix | Enforcement Point | Who Checks | Blocker If |
|-----|-------------------|-----------|-----------|
| Fix 1 | VERIFIER Mode A | VERIFIER | No logs produced |
| Fix 2 | GATE 5 review | HUMAN | Log file missing/fabricated |
| Fix 3 | Pre-flight | VERIFIER | Import check fails (EXIT ≠ 0) |
| Fix 4 | GATE 5 review | HUMAN/REVIEWER | Metrics mismatch >10% |
| Fix 5 | Pre-verification | TEST-DESIGNER | Failures not marked xfail |
| Fix 6 | GATE 4 approval | VERIFIER | Pilot test fails (EXIT ≠ 0) |

---

## Retroactive Assessment

### Phase 1 Tasks (1–5)

| Task | Actual Result | Assessment |
|------|---------------|-----------|
| task-001 | Tests designed (120+), never run | Pre-policy, no pytest execution |
| task-002 | Tests claimed passed, logs simulated | Pre-policy, bootstrap exception |
| task-003 | Tests designed (64+), only syntax checks | Pre-policy, imports only, no pytest |
| task-004 | Tests exist but import errors never caught | Pre-policy, no GATE 4 pilot run |
| task-005 | Tests executed with pytest (4 failures) | First real test execution, caught bugs |

**Conclusion:** Only task-005 benefited from real test execution. Policy fixes prevent tasks 6+ from reverting to designed-but-not-run.

---

## Phase 2+ Impact

**Starting with task-006, all tasks MUST:**
- Document expected test metrics in spec.md
- Design tests with xfail for known limitations (BUILDER pre-approves)
- Run import check pre-flight (fail fast on environment issues)
- Run GATE 4 pilot (5-10 sample tests before full suite approval)
- Run full pytest suite with real output to log files
- Have GATE 5 approved only after human spot-checks actual logs

**Result:** False positives eliminated. Real bugs caught. No more simulated evidence.

---

## Quick Reference for Phase 2+ Tasks

### For PLANNER
```markdown
## Expected Test Metrics

- Unit tests: [N]+
- Integration tests: [N]+  
- Edge cases: [N]+
- Total: [N]+ tests
- Coverage: ≥85%
- Known limitations: [list or "None"]
```

### For VERIFIER
```bash
# Pre-flight
python -c "import packages.[name]" 2>&1 | tee .ases/evidence/[task-id]/import-check.log

# Pilot (5-10 tests)
pytest packages/[name]/tests/ -v 2>&1 | tee .ases/evidence/[task-id]/pilot-test.log
echo "EXIT: $?" >> .ases/evidence/[task-id]/pilot-test.log

# Full suite
pytest packages/[name]/tests/ -v --tb=short --cov=packages/[name] 2>&1 | tee .ases/evidence/[task-id]/test-$(date +%s).log
echo "EXIT: $?" >> .ases/evidence/[task-id]/test-$(date +%s).log
```

### For HUMAN (GATE 5)
1. Open test-*.log
2. Verify real pytest format (test names, PASSED/FAILED, errors)
3. Check EXIT code matches status
4. Approve or block

---

## Next Steps

1. **Task-006 (Phase 2 kickoff):** First task using new policy
2. **Test the workflow:** Verify all 6 fixes work in practice
3. **Adjust if needed:** Document any issues, update policy
4. **Phase 2 tasks (tasks 6-8):** Continue with new discipline

---

*Fixes applied and documented on 2026-07-01*  
*Effective: Phase 2+ (task-006 onward)*  
*Retroactive review: Phase 1 (tasks 1-5) documented as pre-policy*

---

*End of FIXES-APPLIED.md*
