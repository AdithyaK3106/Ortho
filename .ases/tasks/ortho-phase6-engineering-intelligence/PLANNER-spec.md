# Phase 6: Engineering Intelligence — PLANNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6 (Engineering Intelligence)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 with parallel BUILDER + TEST-DESIGNER  
**Duration:** 2 weeks (Phase 6.1 MVP)

---

## Executive Summary

Phase 6 introduces the **Engineering Intelligence layer** — high-level planning and analysis that sits above architecture detection. This phase delivers:

1. **Change Planner** — Predict impact before code generation
2. **Feature Planner** — Suggest implementation paths  
3. **Refactoring Advisor** — Recommend improvements
4. **Architecture Guardrails** — Enforce patterns and constraints

**Phase 6.1 MVP focuses on:**
- Change Impact Prediction (extension of Phase 5 blast radius)
- Feature Planning (using architecture + context)
- Refactoring Opportunity Detection
- Guardrail Violation Detection

**Success Criteria (Hard Metrics):**
- ✅ 90%+ accuracy on impact prediction (20 test cases, hand-verified ground truth)
- ✅ Feature planner suggests ≥3 implementation paths per feature (variety)
- ✅ Refactoring advisor identifies 5+ types of issues (with zero false positives in test suite)
- ✅ Guardrails block 100% of architectural violations in adversarial tests
- ✅ Tests pass with 100% rate (zero flakes)
- ✅ Zero overfitting (edge cases explicitly tested)

---

## Current State (End of Phase 5.3)

### What Phase 5 Built
- ✅ **Architecture Detection:** 8 frameworks, 100% accuracy on 8/8 repos
- ✅ **Blast Radius Analysis:** Change impact (files, functions, modules affected)
- ✅ **Layer & Subsystem Analysis:** Dependency boundaries
- ✅ **Debt Scoring:** Multi-factor (churn, coupling, complexity)
- ✅ **Circular Dependency Detection:** Graph-based analysis

### Missing (Phase 6 Inputs)
- Feature planning (what to build + where)
- Refactoring guidance (what to improve + how)
- Guardrails (what NOT to do)
- Engineering recommendations (actionable insights)

---

## Phase 6.1 Architecture

### Package Structure
```
packages/
├── change-planner/          [NEW]
│   ├── src/change_planner/
│   │   ├── predictor.py       # Impact prediction engine
│   │   ├── types.py           # ImpactPrediction, PlanStep dataclasses
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_predictor.py  # Hard impact cases
│   │   ├── test_edge_cases.py # Overfitting prevention
│   │   └── fixtures/
│   └── README.md
│
├── feature-planner/         [NEW]
│   ├── src/feature_planner/
│   │   ├── planner.py         # Implementation path suggester
│   │   ├── types.py           # FeaturePlan, ImplementationPath
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_planner.py
│   │   ├── test_variety.py    # Multiple paths per feature
│   │   └── fixtures/
│   └── README.md
│
├── refactoring-advisor/     [NEW]
│   ├── src/refactoring_advisor/
│   │   ├── advisor.py         # Issue detection + recommendations
│   │   ├── detectors/
│   │   │   ├── tight_coupling.py
│   │   │   ├── code_duplication.py
│   │   │   ├── module_bloat.py
│   │   │   ├── circular_deps.py
│   │   │   └── debt_hotspots.py
│   │   ├── types.py           # RefactoringIssue, Recommendation
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_advisor.py
│   │   ├── test_zero_false_positives.py
│   │   ├── test_coverage_5_issue_types.py
│   │   └── fixtures/
│   └── README.md
│
└── arch-guardrails/         [NEW]
    ├── src/arch_guardrails/
    │   ├── enforcer.py        # Violation detection
    │   ├── rules/
    │   │   ├── layer_boundaries.py
    │   │   ├── dependency_direction.py
    │   │   ├── cyclic_prevention.py
    │   │   ├── module_sizing.py
    │   │   └── framework_consistency.py
    │   ├── types.py           # GuardrailViolation
    │   └── __init__.py
    ├── tests/
    │   ├── test_enforcer.py
    │   ├── test_100_percent_block_rate.py
    │   ├── test_adversarial_violations.py
    │   └── fixtures/
    └── README.md
```

### Data Models (Shared Types)

**ImpactPrediction:**
```python
@dataclass
class ImpactPrediction:
    changed_file: str
    affected_modules: list[str]      # Modules directly affected
    affected_functions: list[str]    # Functions calling changed code
    cascade_risk: str                # low | medium | high
    confidence: float                # 0.0-1.0
    reasoning: str                   # Explain the prediction
    evidence: list[str]              # Which paths/edges led to this
```

**ImplementationPath:**
```python
@dataclass
class ImplementationPath:
    name: str                        # e.g., "API Gateway Pattern"
    description: str
    affected_layers: list[str]       # Which layers to modify
    effort: str                      # low | medium | high
    risk: str                        # low | medium | high
    dependencies_to_add: list[str]   # New packages needed
    rationale: str                   # Why this path fits the architecture
```

**RefactoringIssue:**
```python
@dataclass
class RefactoringIssue:
    issue_type: str                  # tight_coupling | duplication | bloat | circular | debt
    location: str                    # File, module, or function
    severity: str                    # low | medium | high
    recommendation: str
    estimated_effort: str            # hours
    confidence: float
    false_positive_risk: str         # Explain risk of this being wrong
```

**GuardrailViolation:**
```python
@dataclass
class GuardrailViolation:
    rule_id: str
    severity: str                    # error | warning
    location: str
    message: str
    suggested_fix: str
```

---

## Acceptance Criteria (GATE 3 scope)

### AC1: Change Planner MVP ✅

**Definition:**
- Predicts which modules/functions are affected by a code change
- Extends Phase 5 blast radius with function-level granularity
- Returns confidence scores and evidence

**Acceptance Criteria:**
- ✅ Accuracy ≥90% on 20 test cases (hand-verified ground truth)
- ✅ Handles edge cases: circular imports, dynamic imports, cross-file affects
- ✅ Returns structured ImpactPrediction with evidence
- ✅ Tests cover: single-file changes, multi-file refactors, library updates
- ✅ Zero overfitting (edge case tests explicitly prevent hardcoding)

**Test Cases (20 total):**
1. Simple single-file change (straightforward impact)
2. Function signature change (cascading impacts)
3. Import graph traversal (transitive affects)
4. Circular dependency handling
5. Dynamic import edge case
6. Module rename (cross-references)
7. Interface change (multiple implementations)
8. Shared utility modification
9. Deep call chain (5+ levels)
10. Parallel dependency paths
11. Conditional imports (not always loaded)
12. Late-binding imports (runtime resolution)
13. Star imports (implicit affects)
14. Vendored code (external but local)
15. Plugin architecture (dynamic loading)
16. TypeScript cross-language affects
17. Multi-layer traversal (presentation → data)
18. Package boundary crossing
19. Configuration-driven affects
20. Adversarial: intentionally hard case (TBD after arch review)

---

### AC2: Feature Planner MVP ✅

**Definition:**
- Given a feature intent, suggests 3+ implementation paths
- Each path respects architectural constraints
- Recommends layer modifications, new modules, dependencies

**Acceptance Criteria:**
- ✅ Generates ≥3 distinct paths per feature
- ✅ Each path includes: layers, effort, risk, rationale
- ✅ Zero paths violate guardrails (architecture rules)
- ✅ Tests cover: feature types (endpoint, service, utility), architecture styles
- ✅ Variety tests ensure paths differ meaningfully

**Test Cases (15 total):**
1. Add API endpoint (layered arch)
2. Add service layer (clean arch)
3. Add caching layer (microservices)
4. Add background job (async patterns)
5. Add database migration (data layer)
6. Add authentication (cross-cutting)
7. Add monitoring (observability)
8. Refactor feature into microservice
9. Consolidate features into monolith
10. Add configuration system
11. Add feature flag system
12. Add multi-tenancy
13. Separate presentation from logic
14. Add testing utilities
15. Add validation framework

---

### AC3: Refactoring Advisor MVP ✅

**Definition:**
- Identifies 5+ issue types in code
- Recommends concrete refactoring actions
- Zero false positives (all issues must be real)

**Issue Types:**
1. **Tight Coupling** — Modules tightly depend on each other
2. **Code Duplication** — Similar patterns across multiple files
3. **Module Bloat** — Functions/files over size thresholds
4. **Circular Dependencies** — Explicit cycles
5. **Debt Hotspots** — High churn + low modularity

**Acceptance Criteria:**
- ✅ Detects all 5 issue types with 100% precision (no false positives)
- ✅ Each issue includes: location, severity, recommendation, effort
- ✅ Tests verify zero false positives (adversarial tests)
- ✅ Coverage: single issues, multi-issue scenarios

**Test Cases (20 total):**
1. Tight coupling (simple 2-module case)
2. Tight coupling (3+ module chain)
3. Tight coupling with interfaces (should not flag)
4. Duplication (identical functions)
5. Duplication (similar but not identical)
6. Duplication in tests (should not flag)
7. Module bloat (>500 lines)
8. Module bloat (>50 functions)
9. Module bloat with good structure (should not flag)
10. Circular dependency (A→B→A)
11. Circular dependency (A→B→C→A)
12. Circular dependency with break point (should not flag)
13. Debt hotspot (high churn + high coupling)
14. Debt hotspot (high churn but low coupling, should not flag)
15. Multiple issues in same module
16. Issue in well-tested code (vs untested)
17. Issue in vendored code (should flag differently)
18. Issue across language boundaries (Python + TypeScript)
19. False positive prevention: similar but not duplicate code
20. Adversarial: intentionally confusing structure

---

### AC4: Architecture Guardrails MVP ✅

**Definition:**
- Enforces 5 architectural rules
- Blocks violations with 100% detection rate
- Prevents layer-crossing, circular deps, pattern violations

**Rules:**
1. **Layer Boundaries** — Data layer cannot import presentation layer
2. **Dependency Direction** — Dependencies flow in one direction (acyclic)
3. **Cyclic Prevention** — No cycles in module graph
4. **Module Sizing** — Modules under threshold (configurable)
5. **Framework Consistency** — Consistent use of framework patterns

**Acceptance Criteria:**
- ✅ 100% detection rate on adversarial violations
- ✅ Zero false negatives (all violations caught)
- ✅ Tests include: single violations, multi-rule scenarios
- ✅ Clear error messages with suggested fixes

**Test Cases (25 total):**
1. Layer boundary cross (data→presentation, should fail)
2. Layer boundary cross (presentation→data, should pass)
3. Dependency direction correct (follows DAG)
4. Dependency direction wrong (creates cycle)
5. Circular: A→B→A
6. Circular: A→B→C→A
7. Circular: A→B→A→C (multi-path cycle)
8. Module size OK (<500 lines)
9. Module size violation (>500 lines)
10. Framework pattern: Flask app structure (correct)
11. Framework pattern: Flask app structure (incorrect)
12. Framework pattern: Django app structure (correct)
13. Framework pattern: Django app structure (incorrect)
14. Multi-rule: Both layer + framework violations
15. Multi-rule: Layer + size violations
16. Adversarial: Almost violates but doesn't (should pass)
17. Adversarial: Masked violation (import aliased, should still catch)
18. Adversarial: Conditional import (only sometimes violates)
19. Adversarial: Dynamic import (getattr-based, best effort)
20. Violation with exception rule (should respect exceptions)
21. New rule integration (extensibility)
22. Rule priority (which violation reported first?)
23. Cross-language rule (Python imports TypeScript)
24. Vendor/external code (should not flag)
25. Configuration-driven rules (custom guardrails)

---

## Parallel Execution Plan (TEST-DESIGNER + BUILDER)

### BUILDER Tasks (Sequential)
1. Implement `change-planner` package (predictor engine + types)
2. Implement `feature-planner` package (suggestion engine + types)
3. Implement `refactoring-advisor` package (detectors + advisor engine)
4. Implement `arch-guardrails` package (enforcer + rules)
5. Integration: Wire all 4 packages into orchestrator

### TEST-DESIGNER Tasks (Parallel with BUILDER)
1. Create comprehensive test suite for change-planner (20 tests, hard cases)
2. Create comprehensive test suite for feature-planner (15 tests, variety)
3. Create comprehensive test suite for refactoring-advisor (20 tests, zero false positives)
4. Create comprehensive test suite for arch-guardrails (25 tests, 100% block rate)
5. Create adversarial tests (10 tests designed to break implementations)
6. Create edge-case tests (overfitting prevention)

**Synchronization Points:**
- BUILDER 1 → TEST-DESIGNER 1 (tests ready, then implementation)
- BUILDER 2 → TEST-DESIGNER 2 (same)
- BUILDER 3 → TEST-DESIGNER 3 (same)
- BUILDER 4 → TEST-DESIGNER 4 (same)
- Final: Adversarial + edge-case tests run on completed implementation

---

## Success Metrics (GATE 5)

### Quality Gates
| Metric | Target | Evidence |
|--------|--------|----------|
| **Accuracy (Impact Prediction)** | ≥90% | 18/20 tests passing on hand-verified truth |
| **Feature Path Variety** | ≥3 paths/feature | Test suite verifies distinct paths |
| **Refactoring Precision** | 100% (no false positives) | Adversarial tests confirm all issues real |
| **Guardrail Block Rate** | 100% | 25/25 violation tests caught |
| **Test Pass Rate** | 100% | All 90+ tests pass |
| **Type Safety** | mypy --strict | Zero type violations |
| **Code Coverage** | ≥85% | pytest-cov report |

### No Overfitting Tests
- ✅ Edge cases explicitly tested (circular imports, dynamic code, etc.)
- ✅ Adversarial tests designed to break naive solutions
- ✅ False positive prevention tests (ensure no overcounting)
- ✅ Variety tests (multiple valid solutions, not one hardcoded)
- ✅ Cross-architecture tests (rules work across layered, microservices, etc.)

### Test Execution
- **Command:** `pytest packages/change-planner packages/feature-planner packages/refactoring-advisor packages/arch-guardrails -v --tb=short`
- **Expected:** All tests pass in <10 seconds total
- **CI Integration:** Must pass before merge

---

## Rollback Plan

If any component fails GATE 5:
1. Revert package to empty skeleton (keep interfaces)
2. Move failing tests to `tests/deferred/` (document why)
3. Create ADR explaining deferral to Phase 6.2
4. Phase 6.1 ships with 3/4 components (accept partial completion)
5. Phase 6.2 completes remaining component

---

## Next Phase (6.2)

- Decision Engine (structured decision support)
- Integration with orchestrator workflows
- CLI commands: `ortho plan`, `ortho refactor-advice`, `ortho guardrails`
- Interactive approval gates with recommendations

---

## Definition of Done

✅ All 4 packages implemented + tested  
✅ GATE 1: Plan approved (this document)  
✅ GATE 2: Architecture approved (ADRs, no circular deps)  
✅ GATE 3: Scope review (no unauthorized changes)  
✅ GATE 4: Test coverage (90+ tests, 100% pass, hard edge cases)  
✅ GATE 5: Verification (metrics met, zero overfitting)  
✅ Code reviewed + merged to main

