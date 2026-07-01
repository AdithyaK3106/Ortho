# Revision Requirements Mapping: task-006 Planning

This document maps each of the four PLANNER improvement requirements to the specific changes made in the planning documents.

---

## Requirement 1: Replace xfail-Based Success Metrics (REQUIRED)

### Requirement Statement
> Replace metrics that count test annotations with behavior-oriented criteria.

### Implementation

**File: plan.md**
- **Old Section:** "Acceptance Criteria (Binary & Testable)" — Lines measured success by xfail removal
- **New Section:** "Acceptance Criteria (Binary & Testable)" + "Success Criteria (Behavior-Based)"
  - Replaced: "All tests pass via pytest → EXIT 0, 88 PASSED, 0 FAILED"
  - With: AC1–AC5 behavior statements:
    1. CallGraphBuilder implements required behavior (8 bullet points)
    2. ImportGraphBuilder edge cases resolved (2 specific behaviors)
    3. ModuleDetector complete (5 specific behaviors)
    4. SymbolExtractor edge cases resolved (3 specific behaviors)
    5. Zero regressions

**File: spec.md**
- **New Sections:** AC1–AC5 rewritten to focus on behavior, not test counts
  - Example AC1 old: "18 tests covering function calls"
  - Example AC1 new: "Simple function call detection", "Method call detection", "Nested call detection", etc.
  - Each AC lists the specific behavior that must be implemented
  - Verification moved to "Test Verification Strategy" (separate section)

**Success Criteria (plan.md):**
Replaced:
- ~~"88/88 tests passing (no xfail)"~~
- ~~"Zero xfail markers"~~

With:
- "All atomic task behavior implemented as specified in AC1–AC4"
- "All tests execute via pytest (no design-only tests)"
- "No regressions in other packages"

**Verification:** ✓ Requirement satisfied — all xfail-based metrics removed, replaced with behavior-based criteria

---

## Requirement 2: Reclassify Coverage as a Quality Metric (REQUIRED)

### Requirement Statement
> Move coverage into a dedicated **Quality Metrics** section. Clarify that coverage is monitored but doesn't determine completion.

### Implementation

**File: plan.md**
- **New Section:** "Quality Metrics (Monitored, Not Gate-Blocking)"
  - Covers: Coverage, lint, types, performance
  - Clear table showing what metric blocks vs. what is informational:
    | Metric | Blocking If |
    |--------|------------|
    | Coverage | **No** |
    | Lint | **No** |
    | Types | **No** |
    | Performance | Yes only if >2x |

**File: spec.md**
- **New Section:** "Quality Metrics (Monitored, Not Gate-Blocking)"
  - Coverage: "Target ≥85% (informational)"
  - Lint: "Target EXIT 0 (not a hard gate)"
  - Types: "Target EXIT 0 (not a hard gate)"
  - Performance: "Only blocks if >2x slower"

**Definition of Done (spec.md):**
- Removed: "Code quality checks pass (lint, types, coverage)"
- Added: "Quality metrics reviewed and documented (even if not all targets met)"

**Acceptance Criteria (AC6 removed):**
- Old: AC6 "Code Quality" with coverage/lint/types as gates
- New: AC5 "Zero regressions" — gates are behavioral only

**Verification:** ✓ Requirement satisfied — coverage moved to dedicated Quality Metrics section, clearly marked as non-blocking

---

## Requirement 3: Define Confidence Score Semantics (REQUIRED)

### Requirement Statement
> Document clear confidence bands. Every confidence value should have a documented interpretation.

### Implementation

**File: spec.md**
- **New Section:** "Confidence Score Reference (CallGraphBuilder)"
  - Defines 5 confidence bands with numeric ranges and meanings:
    | Band | Range | Meaning |
    |------|-------|---------|
    | **Certain** | 1.0 | Exact AST-resolved call |
    | **High** | 0.9–0.8 | Confidently resolved |
    | **Moderate** | 0.7–0.6 | Partially inferred |
    | **Low** | 0.5–0.4 | Ambiguous or builtin |
    | **Very Low** | Below 0.4 | Dynamic/runtime-dependent |
  
  - Examples for each band (e.g., "High: self.method() within a class")
  - Key clarification: "Confidence represents static analysis certainty, not runtime correctness"

**File: spec.md (CallGraphBuilder docstring)**
- Updated docstring to include confidence semantics:
  ```
  Confidence Score Semantics:
  - 1.0: Exact AST-resolved call
  - 0.9–0.8: Confidently resolved method call
  - 0.7–0.6: Partially inferred call
  - 0.5–0.4: Ambiguous or builtin call
  - Below 0.4: Dynamic/runtime-dependent calls not included
  ```

**BUILDER Implementation Guidance (added):**
- Document when to assign each confidence band
- Start with 1.0 for simple cases
- Reduce confidence for ambiguous receivers
- Never return confidence below 0.4

**VERIFIER Validation (added):**
- Confidence scores do not need exact numeric matches
- Focus on: presence, range (0.0–1.0), reasonable ordering
- Confidence disagreements do not block merge

**Verification:** ✓ Requirement satisfied — confidence semantics fully defined with bands, examples, and implementation guidance

---

## Requirement 4: Consistency Review (REQUIRED)

### Requirement Statement
> Perform final pass to ensure all success criteria are behavior-based, quality metrics clearly separated, confidence terminology consistent, no dependencies on coverage/xfail.

### Implementation

**Consistency Verified:**

1. **No xfail-dependent criteria**
   - Plan.md: AC1–AC5 all behavior-based ✓
   - Spec.md: AC1–AC5 all behavior-based ✓
   - Rollback-plan.md: Already behavior-focused ✓

2. **Quality metrics clearly separated**
   - Plan.md: New "Quality Metrics" section ✓
   - Spec.md: New "Quality Metrics" section ✓
   - Definition of Done: Updated to exclude coverage/lint as gates ✓
   - VERIFIER notes: Quality metrics reported separately, don't block merge ✓

3. **Confidence terminology consistent**
   - Spec.md CallGraphBuilder docstring: Uses "static analysis certainty" ✓
   - Confidence Score Reference: Clarifies NOT runtime correctness ✓
   - BUILDER guidance: Consistent language about AST resolution ✓
   - VERIFIER validation: Consistent interpretation ✓

4. **No implementation decisions depend on coverage/xfail**
   - Atomic task 8: Changed to "verify no regressions" (not "pass 88 tests") ✓
   - Success criteria: All refer to AC1–AC5 completion ✓
   - Test strategy: Behavior verification, not metric counting ✓

5. **Cross-document alignment**
   - Plan.md and spec.md AC definitions identical ✓
   - All three documents use same quality metric definitions ✓
   - Terminology ("static analysis", "confidence", "behavior") used consistently ✓

**Verification:** ✓ Requirement satisfied — comprehensive consistency review completed

---

## Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| 1. Replace xfail metrics | ✓ COMPLETE | AC1–AC5 behavior-based, no xfail references in success criteria |
| 2. Reclassify coverage | ✓ COMPLETE | Quality Metrics section added, coverage marked non-blocking |
| 3. Define confidence semantics | ✓ COMPLETE | 5-band table, examples, BUILDER/VERIFIER guidance |
| 4. Consistency review | ✓ COMPLETE | All four areas verified across three documents |

---

## Constraint Verification

No changes made to:
- ✓ Architecture
- ✓ Implementation sequence
- ✓ Public interfaces
- ✓ Package layout
- ✓ Task scope
- ✓ Acceptance criteria functionality

Only planning documentation improved for clarity, rigor, and ASES alignment.

---

*Verified by PLANNER*  
*Date: 2026-07-01*  
*Status: REVISION COMPLETE — Ready for GATE 1*
