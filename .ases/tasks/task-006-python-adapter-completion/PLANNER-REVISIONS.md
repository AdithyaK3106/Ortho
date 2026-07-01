# PLANNER Revisions: task-006 Planning Documents
**Date:** 2026-07-01  
**Revision:** 1 (Documentation Alignment Pass)  
**Approved by:** PLANNER  
**Purpose:** Align planning documents with ASES principles (behavior-based acceptance, quality metrics separation, confidence semantics definition)

---

## Changes Made

### 1. Replaced xfail-Based Success Metrics with Behavior-Based Criteria

**Changed in:** plan.md (Success Criteria section), spec.md (Acceptance Criteria sections)

**Old approach:**
- "Remove 28 xfail markers"
- "Zero xfail markers needed"
- Success measured by test annotations, not functionality

**New approach (AC1–AC5 in plan.md):**
- AC1: "CallGraphBuilder behavior implemented" — specifies what the feature must DO
- AC2: "ImportGraphBuilder edge cases resolved" — specific behavioral requirements
- AC3: "ModuleDetector complete" — functionality-focused criteria
- AC4: "SymbolExtractor edge cases resolved" — behavior requirements
- AC5: "Zero regressions" — stability requirement

**Rationale:** ASES measures implemented behavior, not test decorators. A feature is complete when it works as specified, regardless of how tests are marked.

---

### 2. Separated Coverage as a Quality Metric (Not a Gate)

**Changed in:** plan.md and spec.md (new "Quality Metrics" sections)

**Old approach:**
- Coverage ≥85% listed as acceptance criterion
- Coverage as part of Definition of Done blocking merge

**New approach:**
- Code coverage tracked and reported (informational)
- Not a gate-blocking metric
- Acceptance depends on AC1–AC5 only
- Quality metrics (coverage, lint, types) monitored but not blocking

**Supporting metrics table (plan.md):**

| Metric | Target | Blocking If |
|--------|--------|------------|
| Code coverage | ≥85% | **No** (informational only) |
| Lint compliance | EXIT 0 | **No** (report but don't block) |
| Type checking | EXIT 0 | **No** (report but don't block) |
| Execution time | Same or faster | **Yes**, only if >2x slower |

**Rationale:** Coverage identifies gaps but doesn't measure correctness. A 100% covered feature can still be wrong; a 70% covered feature can work perfectly. Acceptance is determined by behavioral criteria and regression testing.

---

### 3. Defined Confidence Score Semantics (CallGraphBuilder)

**Added:** spec.md (new "Confidence Score Reference" section)

**Defines:** Clear confidence bands with interpretations

| Band | Range | Meaning | Examples |
|------|-------|---------|----------|
| **Certain** | 1.0 | Exact AST-resolved call | `foo()` where `def foo` found |
| **High** | 0.9–0.8 | Confidently resolved | `self.method()` in class |
| **Moderate** | 0.7–0.6 | Partially inferred | `obj.method()`, type uncertain |
| **Low** | 0.5–0.4 | Ambiguous or builtin | `len()`, `dict()` |
| **Very Low** | Below 0.4 | Dynamic/runtime-dependent | NOT returned |

**Key clarification:** Confidence represents **static analysis certainty**, not runtime correctness. High confidence ≠ guaranteed execution; low confidence ≠ broken call.

**Rationale:** Without clear semantics, confidence scores are meaningless. BUILDER now has guidance on what each range means and when to assign each band.

---

### 4. Consistency Review Completed

**Verified across all three documents:**

✓ No success criteria depend solely on xfail counts  
✓ All acceptance criteria are behavior-based  
✓ Coverage consistently treated as quality metric, not gate  
✓ Confidence terminology used consistently (static analysis, certainty, not runtime correctness)  
✓ Implementation decisions aligned with ASES principles  

**Notable alignment:**
- Plan.md and spec.md use identical AC definitions
- Rollback-plan.md unchanged (already behavior-focused)
- Quality metrics section added to both plan.md and spec.md

---

## Impact on Next Phases

### For ARCHITECT (if not waived):
- Architecture review now focuses on AC1–AC5 completeness, not test metrics
- No architectural concerns regarding this revision

### For BUILDER:
- Clear behavioral criteria to implement against (AC1–AC5)
- Confidence semantics documented to guide CallGraphBuilder implementation
- Quality metrics are informational (report but don't re-engineer for)
- If limitations discovered: document in implementation-notes.md + PLANNER approval needed for xfail

### For TEST-DESIGNER:
- Test coverage measured by AC1–AC5 mapping, not line coverage %
- Coverage reports are informational, not blocking
- Focus on: does the test verify the behavior in AC1–AC5?

### For VERIFIER:
- Acceptance determined by: AC1–AC5 + zero regressions + real pytest results
- Quality metrics reported separately (coverage, lint, types) but not blocking
- Evidence success = AC behaviors verified, not = test count / xfail count

### For REVIEWER:
- Code approval based on: AC1–AC5 implemented correctly, regressions zero, code quality good
- Confidence scores reviewed for reasonableness (0.0–1.0, monotonic ordering) not exact matching
- Quality issues noted but don't block merge if AC + regression criteria met

---

## No Scope, API, or Architecture Changes

This revision is **documentation-only**. No changes to:
- Implementation sequence
- Public interfaces
- Package structure
- Acceptance criteria functionality
- Rollback procedures
- Task dependencies

---

## Verification Checklist (PLANNER)

- [x] All xfail-based metrics replaced with behavior-based criteria
- [x] Coverage moved to quality metrics section (not gate-blocking)
- [x] Confidence score semantics defined with clear bands
- [x] Consistency verified across all three documents
- [x] No scope/API/architecture changes introduced
- [x] Implementation guidance improved without changing requirements
- [x] Rationales documented for all changes

---

*Ready for GATE 1 Human Approval*  
*Status: REVISED (ready for review)*
