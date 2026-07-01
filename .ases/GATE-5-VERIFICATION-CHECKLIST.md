# GATE 5 Verification Checklist

**For:** HUMAN approver and REVIEWER  
**Purpose:** Verify VERIFIER actually ran tests and didn't fabricate logs  
**Time:** 5-10 minutes  

---

## Before You Approve GATE 5

### Step 1: Read verification-report.md (2 min)

- [ ] Status is **VERIFIED** or **BLOCKED**
- [ ] All 5 checks present:
  - [ ] BUILD — PASS/FAIL/NOT-RUN
  - [ ] LINT — PASS/FAIL/NOT-RUN
  - [ ] TYPES — PASS/FAIL/NOT-RUN
  - [ ] UNIT-TESTS — PASS/FAIL/NOT-RUN with X passed, Y failed
  - [ ] REGRESSION — PASS/FAIL/NOT-RUN
- [ ] If any FAIL → return to BUILDER/TEST-DESIGNER (don't approve)
- [ ] If BLOCKED → return to VERIFIER, wait for human-terminal evidence

### Step 2: Open Actual Test Log File (3 min)

**Find the log file:**
```
.ases/evidence/[task-id]/test-*.log
```

**Expected filename examples:**
- `.ases/evidence/task-006/test-1719534330.log`
- `.ases/evidence/task-006/test-1719534400.log`

**If file does NOT exist:**
- [ ] Report to VERIFIER: "test-*.log not found in .ases/evidence/[task-id]/"
- [ ] Do NOT approve GATE 5
- [ ] Return task to VERIFIER

### Step 3: Verify Real pytest Output (2 min)

**Open the log file. Look for these markers:**

✓ **Real pytest output contains:**
```
============================= test session starts =============================
platform [os] -- Python [version], pytest-[version]
...
packages/[name]/tests/test_*.py::[TestClass]::[test_name] PASSED [ 25%]
packages/[name]/tests/test_*.py::[TestClass]::[test_name] FAILED [ 50%]
...
=============================== FAILURES =======================================
_ [TestClass].[test_name] _
  [error message here]
  assert expected == actual
...
====================== [X passed, Y failed] in [time]s =========================
EXIT: [0 or 1]
TIMESTAMP: [ISO 8601 date]
```

✗ **Fabricated output looks like:**
```
Test passed. All criteria met. Status OK.
EXIT: 0
```

✗ **Suspicious patterns:**
- "All [N] tests passed" (no test names listed)
- No PASSED/FAILED markers per test
- No error messages for failures
- Doesn't mention pytest version or platform
- No timestamps
- Vague language ("working correctly", "no issues")

### Step 4: Verify Exit Code (1 min)

**Check last line of test-*.log:**
```
EXIT: 0    ← means tests passed
EXIT: 1    ← means tests failed
```

**Cross-check against verification-report.md:**
- If report says "PASS" → EXIT code should be 0
- If report says "FAIL" → EXIT code should be 1 or non-zero
- If mismatch → report to VERIFIER, don't approve

### Step 5: Spot-Check Error Messages (2 min, if failures exist)

**If test failures are reported:**
- [ ] Open test-*.log
- [ ] Find FAILURES section
- [ ] Read actual error messages (e.g., `AssertionError: Expected 'hexagonal', got 'layered'`)
- [ ] Verify error messages are quoted verbatim in verification-report.md (or at minimum, sense-checked)

**Red flags:**
- [ ] Error messages are vague ("test failed") — should be specific
- [ ] No AssertionError or Exception details — should show what went wrong
- [ ] Error messages don't match what VERIFIER claimed

### Step 6: Spot-Check Test Names (2 min)

**Compare test-*.log output to test-plan.md:**

From log file, find test names:
```
test_layered_fixture_detects_as_layered PASSED
test_hexagonal_fixture_detects_as_hexagonal FAILED
test_mvc_fixture_detects_as_mvc PASSED
```

From test-plan.md, verify these tests exist:
- [ ] `test_layered_fixture_detects_as_layered` (listed in spec)
- [ ] `test_hexagonal_fixture_detects_as_hexagonal` (listed in spec)
- [ ] `test_mvc_fixture_detects_as_mvc` (listed in spec)

**Red flag:** Test names in log don't match test-plan.md (might be old or wrong log)

---

## Decision Tree

```
Is verification-report.md STATUS = VERIFIED?
├─ NO (BLOCKED or FAILED)
│  └─ Return to VERIFIER (don't approve)
│
└─ YES
   ├─ Does test-*.log exist in .ases/evidence/[task-id]/?
   │  ├─ NO
   │  │  └─ BLOCK — report missing log file
   │  │
   │  └─ YES
   │     ├─ Does log contain real pytest output format?
   │     │  ├─ NO (fabricated or vague)
   │     │  │  └─ BLOCK — report fabricated evidence
   │     │  │
   │     │  └─ YES (real format with test names, PASSED/FAILED, errors)
   │     │     ├─ Does EXIT code match report claim?
   │     │     │  ├─ NO
   │     │     │  │  └─ BLOCK — report mismatch
   │     │     │  │
   │     │     │  └─ YES
   │     │     │     ├─ Are test names reasonable (match plan)?
   │     │     │     │  ├─ NO
   │     │     │     │  │  └─ QUERY — might be wrong log
   │     │     │     │  │
   │     │     │     │  └─ YES
   │     │     │     │     └─ ✓ APPROVE GATE 5
```

---

## What to Report if You Block

**Template for returning task:**

```
GATE 5 VERIFICATION FAILED

Issue: [Choose one]
  - test-*.log not found in .ases/evidence/[task-id]/
  - Log file contains fabricated output (not real pytest format)
  - EXIT code mismatch: report claims PASS but EXIT: 1
  - Test failures not documented/understood
  - Error messages in log don't match report claims

Details:
  - Expected: [what should be there]
  - Found: [what was actually there]

Next Step:
  - VERIFIER: Re-run verification, capture real logs
  - Or: BUILDER/TEST-DESIGNER fix code/tests, re-run verification
```

**Do NOT:**
- [ ] Approve with reservations ("looks probably ok")
- [ ] Assume logs are correct without reading them
- [ ] Trust claims without spot-checking evidence
- [ ] Approve if log files are missing entirely

---

## Common Issues & Resolution

### Issue: "test-*.log doesn't exist"
**Cause:** VERIFIER never ran pytest  
**Fix:** Return to VERIFIER to run Mode A (evidence production)

### Issue: "Log contains 'All tests passed' but no details"
**Cause:** Fabricated evidence  
**Fix:** Return to VERIFIER with instruction: "Run actual pytest, capture real output"

### Issue: "Report says PASS but EXIT: 1"
**Cause:** VERIFIER misread exit code or fabricated report  
**Fix:** Return task for re-verification

### Issue: "Log mentions Python 2.7 but we use Python 3.12"
**Cause:** Old log file, or wrong environment  
**Fix:** Return to VERIFIER to re-run in correct environment

### Issue: "Test names in log don't match test-plan.md"
**Cause:** Possibly old log or test code changed  
**Fix:** Query VERIFIER, verify test-plan.md matches actual code

---

## Red Flags (BLOCK Immediately)

🚩 **ALWAYS block GATE 5 if:**
- [ ] No test log files exist at all
- [ ] Log file format is not pytest (e.g., "Test passed. OK.")
- [ ] Log claims "100% pass rate" but shows 0 tests
- [ ] Error messages are generic ("test failed") without actual assertion details
- [ ] Exit code contradicts status claim
- [ ] Report says "69/72 tests passing" but log shows different counts

---

## Sign-Off

Once you've completed all 6 steps:

- [ ] All checks passed (no red flags)
- [ ] test-*.log contains real pytest output
- [ ] EXIT code matches report status
- [ ] Test names are reasonable (match plan)

**Verdict:** ✓ APPROVE GATE 5

Signatures:
- Human Reviewer: _________________ Date: _______
- Task ID: [task-006, etc.]
- Verification Log: .ases/evidence/[task-id]/test-*.log

---

*End of GATE-5-VERIFICATION-CHECKLIST.md*
