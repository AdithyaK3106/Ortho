task: [task-id]
title: [task-title]
verified: [YYYY-MM-DD HH:MM:SS UTC]
tier: ITERATION | COMMIT-GATE
evidence_source: CLAUDE-CLI | HUMAN-TERMINAL | CI-CD

summary:
  build: PASS | FAIL | NOT-RUN — [log file reference]
  lint: PASS | FAIL | NOT-RUN — [log file reference]
  types: PASS | FAIL | NOT-RUN — [log file reference]
  unit_tests: PASS | FAIL | NOT-RUN — [X/Y passed] — [log file reference]
  coverage: [percentage] | NOT-MEASURED
  regression: PASS | FAIL | NOT-RUN — [X new failures] — [log file reference]
  android_ui: NOT-APPLICABLE | MANUAL-REQUIRED | [status]

detailed_results:

### BUILD: PASS ✓

**Log file:** `.ases/evidence/[task-id]/build-1719534330.log`

**Output:**
```
Type checking complete. No errors detected.
EXIT: 0
TIMESTAMP: 2026-06-27T23:55:30Z
```

**Analysis:**
- TypeScript compilation successful
- No type errors
- All files in scope compile correctly
- Ready for next stage

---

### LINT: PASS ✓

**Log file:** `.ases/evidence/[task-id]/lint-1719534330.log`

**Output:**
```
✓ src/controllers/CategoryController.ts
✓ src/services/CategoryService.ts
✓ src/repositories/CategoryRepository.ts
✓ src/schemas/Category.ts

All files pass ESLint checks.
EXIT: 0
TIMESTAMP: 2026-06-27T23:56:00Z
```

**Analysis:**
- All linting rules pass
- No style violations
- Code follows project conventions

---

### TYPE-CHECK: PASS ✓

**Log file:** `.ases/evidence/[task-id]/types-1719534330.log`

**Output:**
```
Type checking with strict mode enabled...
✓ All type checks pass
0 errors, 0 warnings
EXIT: 0
TIMESTAMP: 2026-06-27T23:56:30Z
```

**Analysis:**
- All types are correct
- No `any` types used
- Type safety verified

---

### UNIT-TESTS: PASS ✓

**Log file:** `.ases/evidence/[task-id]/test-1719534330.log`

**Output:**
```
PASS  src/controllers/CategoryController.test.ts (1234 ms)
PASS  src/services/CategoryService.test.ts (567 ms)
PASS  src/repositories/CategoryRepository.test.ts (891 ms)

Test Suites: 3 passed, 3 total
Tests:       42 passed, 42 total
Coverage:    87% Statements | 84% Branches | 89% Functions | 86% Lines
```

**Analysis:**
- 42 tests passed, 0 failed
- Coverage exceeds 80% target
- All acceptance criteria have tests
- Edge cases covered

---

### COVERAGE: 87% ✓

**Breakdown:**
- Statements: 87%
- Branches: 84%
- Functions: 89%
- Lines: 86%

**Gap Analysis:**
- Missing coverage in error path: `if (database.connection.closed)` (line 156 of CategoryService.ts)
  - This is acceptable — error handling for rare failures
  - If needed, can be covered with error injection test

---

### REGRESSION: PASS ✓

**Log file:** `.ases/evidence/[task-id]/regression-1719534330.log`

**Output:**
```
PASS  src/routes.test.ts (2345 ms)
PASS  src/database.test.ts (1567 ms)
PASS  src/types.test.ts (456 ms)

Test Suites: 3 passed, 3 total (50 other test suites also passed)
Tests:       165 passed, 165 total
New tests:   +42 (from this task)
Previously passing: 123 → still 123 passing
```

**Analysis:**
- No regression detected
- All previously passing tests still pass
- No new failures introduced

---

### REGRESSION-DELTA

```
Tests before:       123
Tests after:        165
Net change:         +42 (all new, from this task)

Newly failing:      0
Newly passing:      0 (all 42 new tests written with this task)
```

---

## FAILURES

[If any check failed, copy exact error text from log files. Never summarize.]

**[If PASS on all checks, write:]**

No failures detected in any verification gate.

---

## STATUS: VERIFIED ✓

**Summary:** All verification gates passed. Code compiles, lints, tests pass (42 tests, 87% coverage), no regressions.

**Confidence Level:** EVIDENCE-BACKED

---

## Verification Checklist

- ✓ Build passes (EXIT 0)
- ✓ Lint passes (EXIT 0)
- ✓ Type check passes (EXIT 0)
- ✓ Unit tests pass (42 passed, 0 failed)
- ✓ Coverage ≥80% (87%)
- ✓ Regression suite passes (0 new failures)
- ✓ All acceptance criteria have tests
- ✓ Edge cases tested
- ✓ Failure scenarios tested

---

## Evidence Files Created

All evidence files timestamped and stored in `.ases/evidence/[task-id]/`:
- `build-1719534330.log` — Type checking output
- `lint-1719534330.log` — Linting output
- `types-1719534330.log` — Type checking output (if separate)
- `test-1719534330.log` — Unit test output with coverage
- `regression-1719534330.log` — Full regression suite output

**Evidence Source Declaration:**
```
EVIDENCE-SOURCE: CLAUDE-CLI

All commands executed in Claude CLI environment using Node.js 18+ and npm 8+.
Commands run: tsc, eslint, jest
All output captured to timestamped log files.
No output fabricated or summarized from memory.
```

---

## Next Steps

1. ✓ Verification complete
2. Send to REVIEWER for code review
3. If REVIEWER approves, commit to git
4. Update CLAUDE.md with completion

---

*End of verification-report.md template*
