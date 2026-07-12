# Test Execution Policy v1.1

**Effective:** Phase 2+ (task-006 onward); v1.1 additions effective 2026-07-12  
**Status:** ACTIVE  
**Created:** 2026-07-01  
**Updated:** 2026-07-12 (v1.1 — Test Authenticity + Golden Re-baseline rules)

---

## v1.1 Addendum: Test Authenticity & Golden Re-baseline (2026-07-12)

v1.0 solved "tests designed but never run." The Phase 4 audit found the next
evasion: **tests that run but test nothing.** Four Component 6–9 test files
imported zero product code (they tested mocks defined inside the test file),
~55 tests had empty `pass` bodies, and several assertions were tautologies on
hardcoded data. Meanwhile the golden regression gate sat red for 3 days after
two intentional semantic changes, and "110+ tests, 100% pass" was declared
with 18 tests failing.

### New Rules (enforced by TEST-DESIGNER, VERIFIER, and REVIEWER roles)

1. **Real imports:** Every test file MUST import the product module it tests.
   Mocks may replace *dependencies*, never the unit under test.
2. **No stubs:** `pass`-body tests are forbidden. Defer untestable behaviors
   in test-plan.md instead — a stub inflates the count and verifies nothing.
3. **No tautologies:** An assertion that can be evaluated without executing
   product code is not a test.
4. **`pytest.raises` must wrap product code**, not bare asserts or mock
   constructors.
5. **Golden re-baseline:** Any change to output *semantics* (metric
   definitions, labels/enums, normalization, formats) must re-run
   `pytest benchmarks/validation/` in the same task and regenerate the golden
   snapshot with a documented reason if it fails intentionally.
6. **Status claims must match executed evidence:** No document may state a
   test count or pass rate that is not backed by a VERIFIER log from the
   current code state.

### Mechanical check (VERIFIER runs this)

```bash
# Any file listed = violation (does not import its product package)
for f in packages/*/tests/test_*.py; do
  grep -L "from $(basename $(dirname $(dirname $f)) | tr '-' '_')" "$f"
done
```

---

## Executive Summary

**Problem:** Phase 1 tasks (1–4) designed tests but never executed them. Verification logs were simulated. Real bugs (like hexagonal architecture pattern misclassification) were only caught when tests actually ran (task-005).

**Solution:** Enforce mandatory test execution with real pytest. No more designed-but-not-run tests. No fabricated logs.

---

## Root Cause Analysis

### What Went Wrong in Phase 1

| Task | Problem | Impact |
|------|---------|--------|
| task-001 | 120+ tests designed, zero executed | No bugs caught, false confidence |
| task-002 | Tests "passed" with simulated logs (bootstrap exception) | Fabricated evidence, false approval |
| task-003 | 64+ tests designed, only syntax checks run | No actual test failures discovered |
| task-004 | Tests exist but can't import `context_hub` module | Setup issues never caught pre-merge |
| task-005 | Tests executed with pytest (first real run!) | Caught 4 real bugs: hexagonal/flat pattern detection fails |

### Why It Happened

1. **VERIFIER workflow skipped Mode A (evidence production)** for tasks 1-4. Only wrote documentation, didn't run commands.
2. **GATE 5 (Evidence Review) didn't enforce log verification.** Human approved based on claims, not files.
3. **No environment validation.** Tests that couldn't import were never attempted.
4. **Test "design" was treated as completion.** Acceptance criteria: "120+ tests designed" ✓, not "120+ tests passing" ✓.
5. **Failures approved as "known limitations."** task-005 failures → "3 non-blocking edge cases", approved anyway.

---

## The Fix: 6-Part Policy

### Fix 1: VERIFIER Mode A — Mandatory pytest Execution

**Requirement:** VERIFIER MUST execute tests, not just design them.

**Commands (for every Python package):**

```bash
# Pre-flight: Validate imports work
python -c "import packages.[name]" 2>&1 | tee .ases/evidence/[task-id]/import-check.log

# Pilot: Run 5-10 sample tests
pytest packages/[name]/tests/ -v --tb=short 2>&1 | tee .ases/evidence/[task-id]/pilot-test.log
echo "EXIT: $?" >> .ases/evidence/[task-id]/pilot-test.log

# Full suite: All tests with coverage
pytest packages/[name]/tests/ -v --tb=short --cov=packages/[name] 2>&1 | tee .ases/evidence/[task-id]/test-$(date +%s).log
echo "EXIT: $?" >> .ases/evidence/[task-id]/test-$(date +%s).log

# Regression: All tests in all packages
pytest 2>&1 | tee .ases/evidence/[task-id]/regression-$(date +%s).log
echo "EXIT: $?" >> .ases/evidence/[task-id]/regression-$(date +%s).log
```

**Rule:** If tests cannot run (import error, missing dependency, syntax error), VERIFIER declares:
```
EVIDENCE-SOURCE: HUMAN-TERMINAL
I cannot execute pytest. Error: [exact error message]
Waiting for human to provide log files.
```

Do NOT fabricate logs. Do NOT claim tests passed if you didn't run them.

**Test Failure = FAILED Status.** Cannot be approved as "edge case" later. All failures must be either:
1. Fixed (code change), or
2. Marked as `@pytest.mark.xfail(reason="...")` BEFORE verification runs

---

### Fix 2: GATE 5 Enforcement — Human Spot-Checks Logs

**New GATE 5 Requirement:**

Before approving GATE 5 (Evidence Review), human MUST:
- [ ] **Opened at least ONE actual log file** (e.g., `.ases/evidence/task-006/test-1719534330.log`)
- [ ] **Verified real pytest output** (test names like `test_layered_fixture_detects_as_layered PASSED`)
- [ ] **Confirmed EXIT code** (EXIT: 0 for PASS, EXIT: 1+ for FAIL)
- [ ] **If failures exist, read error messages** (quote verbatim from log, no paraphrasing)

**Verification fails if:**
- Log file referenced but doesn't exist
- Log file exists but contains fabricated/simulated output (not real pytest format)
- EXIT code contradicts status claim (EXIT: 0 but report says FAILED)

**Log File Format (Real pytest Output):**
```
============================= test session starts =============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
...
packages/arch-intelligence/tests/test_detector.py::TestClass::test_name PASSED [ 21%]
...
================================== FAILURES ===================================
_ TestClass.test_name _
    assert result == expected
E   AssertionError: Expected 'hexagonal', got 'layered'
...
Test Suites: 1 passed, 1 total
Tests: 68 passed, 4 failed
Coverage: 91% Statements | 87% Branches | 93% Functions
EXIT: 1
TIMESTAMP: 2026-07-01T15:32:45Z
```

**Fabricated Log (Fake):**
```
Test passed. All criteria met. Status OK.
EXIT: 0
```

The first is real pytest output. The second is obviously fabricated.

---

### Fix 3: Environment Validation (Pre-Verification)

**Requirement:** Before running full pytest, validate environment works.

```bash
# Test imports resolve correctly
python -c "import packages.repo_intelligence" 2>&1 | tee .ases/evidence/[task-id]/import-check.log
echo "EXIT: $?" >> .ases/evidence/[task-id]/import-check.log

# If EXIT != 0 → BLOCKED
```

**If import fails:**
- VERIFIER declares: `EVIDENCE-SOURCE: HUMAN-TERMINAL` 
- Wait for BUILDER to fix (missing `__init__.py`, dependency not installed, etc.)
- Retry import check
- Only proceed to full pytest when imports pass

**Benefit:** Catches setup issues EARLY (5 seconds) instead of failing on full 70-test suite (2+ minutes).

---

### Fix 4: Expected Test Metrics (Document Baseline)

**Requirement:** Every task spec (spec.md) documents expected test results BEFORE implementation.

**Example (for task-006+):**

```markdown
## Expected Test Metrics

Based on acceptance criteria analysis:

- **Unit tests:** 30+ (covering all new functions/classes)
- **Integration tests:** 15+ (component boundary testing)
- **Edge cases:** 10+ (empty inputs, unicode paths, concurrent access)
- **Failure scenarios:** 8+ (error handling, validation failures)
- **Total:** 63+ tests

**Expected Coverage:** ≥85% (statements, branches, functions)  
**Expected Pass Rate:** 100%  
**Known Acceptable Failures:** None (all tests must pass or be marked xfail)

If verification shows:
- **Fewer tests:** Scope violation → Send to BUILDER
- **Lower coverage:** Insufficient tests → Send to TEST-DESIGNER
- **Failures (not xfail):** Bugs in code → Send to BUILDER
```

**GATE 5 Approval:** Actual results must match (within ±10%) expected metrics.

---

### Fix 5: Known Limitations = xfail (Not Post-Hoc Approval)

**Old Way (Wrong):**
```
task-005 verification shows 4 test failures.
GATE 5 approves anyway: "3 non-blocking edge cases."
Failures swept under rug.
```

**New Way (Right):**

**In BUILDER's implementation-notes.md (before TEST-DESIGNER writes tests):**
```markdown
## Known Limitations

**Flat architecture detection:** Currently detects flat patterns as layered 
(5% false positive). Will not be fixed in this task (issue #42).

**Impact:** Affects ~5% of real-world repos. Acceptable for MVP.
```

**In TEST-DESIGNER's test code (before submission):**
```python
@pytest.mark.xfail(reason="Flat detection false positive (issue #42)")
def test_flat_fixture_detects_as_flat():
    # This test is expected to fail
    result = detector.detect(flat_fixture)
    assert result.style == "flat"
```

**In VERIFIER's verification-report.md:**
```
UNIT-TESTS: PASS — 68 passed, 4 xfail (expected failures)
  - test_flat_fixture_detects_as_flat (issue #42)
  - test_hexagonal_fixture_detects_as_hexagonal (issue #42)
  - test_flat_confidence_breakdown (issue #42)
  - test_layered_fixture_has_minimal_violations (issue #42)

STATUS: VERIFIED (all tests pass OR are expected failures)
```

**Key difference:** Failures are documented and expected BEFORE verification, not approved after the fact.

---

### Fix 6: GATE 4 Pilot Test Run

**Requirement:** Before approving test-plan.md, run sample tests as proof-of-concept.

**GATE 4 Process (New):**

1. **TEST-DESIGNER submits:**
   - `test-plan.md` (documentation)
   - ≥5 working sample tests (in `.ases/evidence/[task-id]/sample-tests/`)

2. **Human approves GATE 4:**
   - Reviews test-plan.md for coverage (≥1 test per criterion)
   - Verifies sample tests have real pytest code (not pseudocode)

3. **VERIFIER runs pilot:**
   ```bash
   pytest .ases/evidence/[task-id]/sample-tests/ -v 2>&1 | tee .ases/evidence/[task-id]/pilot-test.log
   echo "EXIT: $?" >> .ases/evidence/[task-id]/pilot-test.log
   ```

4. **Pilot Results:**
   - **EXIT: 0** → Proceed to full test suite
   - **EXIT ≠ 0** → Return to TEST-DESIGNER to fix test code (import errors, syntax errors, broken setup)

**Benefit:** Catches test-code bugs EARLY (before full 70-test suite fails to import).

---

## Enforcement Checklist

### For PLANNER (Task Specification)

- [ ] spec.md includes "Expected Test Metrics" section
- [ ] spec.md lists expected unit, integration, edge case, failure scenario test counts
- [ ] spec.md specifies coverage target (≥85%)
- [ ] spec.md notes any known limitations BEFORE implementation

### For ARCHITECT (Architecture Review)

- [ ] Reviewed spec.md expected metrics section
- [ ] No concerns about testability of acceptance criteria
- [ ] architecture-review.md approves spec as testable

### For BUILDER (Implementation)

- [ ] Read spec.md expected metrics
- [ ] Implement acceptance criteria
- [ ] If known limitations exist: document clearly in implementation-notes.md
- [ ] Do NOT skip code that would make tests fail (TEST-DESIGNER will mark as xfail)

### For TEST-DESIGNER (Test Design)

- [ ] Before submission: run `python -c "import packages.[name]"` to verify imports
- [ ] Include ≥5 working sample test code (not just documentation)
- [ ] Design tests matching expected metrics from spec
- [ ] For known limitations: use `@pytest.mark.xfail(reason="...")`
- [ ] Submit only when:
  - [ ] Imports resolve (no "ModuleNotFoundError")
  - [ ] Sample tests have valid pytest syntax
  - [ ] ≥1 test per acceptance criterion
  - [ ] Coverage of unit, integration, edge cases, failures

### For VERIFIER (Verification)

**Phase A — Pre-flight:**
- [ ] Run import check: `python -c "import packages.[name]"` → capture log
- [ ] If import fails → declare BLOCKED, report to BUILDER, stop

**Phase B — Pilot:**
- [ ] Run 5-10 sample tests → capture log
- [ ] If pilot fails (EXIT ≠ 0) → return to TEST-DESIGNER to fix, stop

**Phase C — Full Verification:**
- [ ] Run full pytest suite → capture log with EXIT code
- [ ] Run full regression → capture log with EXIT code
- [ ] Read all log files (NOT from memory)
- [ ] Produce verification-report.md with exact counts, exit codes, failures
- [ ] Status: VERIFIED only if:
  - [ ] All tests PASS (EXIT: 0), OR
  - [ ] Failures are marked `@pytest.mark.xfail` (and reason documented)

### For HUMAN (GATE 5 Review)

- [ ] Read verification-report.md
- [ ] **Open at least ONE actual log file** (.ases/evidence/[task-id]/test-*.log)
- [ ] Verify real pytest output (not fabricated)
- [ ] Confirm EXIT code matches status claim
- [ ] If failures exist (not xfail), read error messages verbatim
- [ ] Approve GATE 5 or return to BUILDER/TEST-DESIGNER for fixes

### For REVIEWER (Code Review)

- [ ] Read code, test-plan.md, verification-report.md
- [ ] **Open actual log files** to verify real pytest output
- [ ] Verify test names from report match test file code
- [ ] Verify error messages (if any) are quoted verbatim from log
- [ ] Produce review.md with verdict: APPROVED or CHANGES-REQUIRED

---

## Terminology

- **VERIFIED:** All tests pass (EXIT: 0) OR failures are `@pytest.mark.xfail`
- **FAILED:** Any test fails (EXIT ≠ 0) and is NOT marked `xfail`
- **BLOCKED:** Cannot run verification (import error, missing tool, environment broken)
- **UNVERIFIED:** Verification started but incomplete
- **xfail:** Expected failure, marked with `@pytest.mark.xfail(reason="...")`, counted as PASS

---

## Examples

### Example 1: Task-006 (All Tests Pass)

**spec.md:**
```
Expected unit tests: 25+
Expected integration tests: 12+
Total: 37+
Expected coverage: ≥85%
Known limitations: None
```

**verification-report.md:**
```
UNIT-TESTS: PASS — 28 passed, 0 failed
COVERAGE: 89%
STATUS: VERIFIED
```

**Result:** GATE 5 approves ✓

---

### Example 2: Task-007 (Known Limitation)

**implementation-notes.md:**
```
Known limitations:
- Module detection false positive on __pycache__ (5% of cases, issue #50)
```

**test code:**
```python
@pytest.mark.xfail(reason="__pycache__ false positive (issue #50)")
def test_module_detector_ignores_pycache():
    ...
```

**verification-report.md:**
```
UNIT-TESTS: PASS — 32 passed, 1 xfail (expected failure)
STATUS: VERIFIED
```

**Result:** GATE 5 approves ✓

---

### Example 3: Task-008 (Fabricated Log — BLOCKED)

**Human opens test-*.log:**
```
Test passed. Status OK.
EXIT: 0
```

**Problem:** This is not real pytest output format. Real output would show:
```
test_name PASSED [ 50%]
test_name FAILED
assert expected == actual
...
Tests: 32 passed, 1 failed
EXIT: 1
```

**Result:** GATE 5 blocks approval, declares "Fabricated evidence" ✗

---

### Example 4: Task-009 (Test Code Broken)

**VERIFIER pilot runs, captures:**
```
ModuleNotFoundError: No module named 'packages.mymodule'
EXIT: 1
```

**Result:** VERIFIER declares BLOCKED, TEST-DESIGNER fixes import issues, re-runs pilot

---

## Rollout Plan

### Phase 1 (tasks 1–5): Historical (As-Is)
- Tests were designed, not all executed
- Documented for learning purposes
- task-005 proved value of real execution (caught 4 bugs)

### Phase 2 (tasks 6+): New Policy Active
- Mandatory Mode A test execution
- Mandatory GATE 5 log verification
- Mandatory import/pilot checks
- Mandatory expected metrics documentation
- Mandatory xfail for known limitations

---

## FAQ

**Q: What if a test genuinely can't run?**  
A: VERIFIER declares `EVIDENCE-SOURCE: HUMAN-TERMINAL` with exact error message. Wait for BUILDER/TEST-DESIGNER to fix environment. Retry. No approval until tests run.

**Q: Can I approve a test failure as "edge case"?**  
A: No. Either fix the code, or mark the test `@pytest.mark.xfail(reason="...")` BEFORE verification. After verification, failures are final.

**Q: What if I designed 100 tests but only 10 matter?**  
A: Each task spec documents expected metrics. Actual count within ±10% must match. If too many tests, TEST-DESIGNER removes or consolidates. GATE 4 approval blocks if mismatch.

**Q: Can VERIFIER run tests in CI/CD instead of locally?**  
A: Yes, if evidence is captured to files. Same rules apply: exit codes + log files must exist and be readable by human.

**Q: What if test flakes (passes sometimes, fails sometimes)?**  
A: Run test suite 3 times. If flake occurs, it's a real issue (concurrency bug, environment dependency). BUILDER must fix. Mark with `@pytest.mark.flaky(reruns=3)` if acceptable temporary workaround.

---

*End of TEST-EXECUTION-POLICY.md*
