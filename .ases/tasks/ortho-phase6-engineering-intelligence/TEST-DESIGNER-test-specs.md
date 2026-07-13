# Phase 6: Engineering Intelligence — TEST-DESIGNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6 (Engineering Intelligence)  
**Date:** 2026-07-13  
**Methodology:** Hard test design with zero overfitting prevention  

---

## Overview

This document specifies **hard test cases** designed to:
- Verify correctness through comprehensive coverage
- Prevent overfitting (adversarial + edge cases)
- Achieve 100% pass rate with strict metrics
- Catch bugs before BUILDER delivers code

**Total Test Cases:** 90+ (20 + 15 + 20 + 25 + 10 adversarial)

---

## Part 1: Change Planner Tests (20 Cases)

### Purpose
Verify that impact prediction correctly identifies affected modules/functions with high accuracy.

### Test Fixtures Required
- `simple_project/` — 3-file Python project (main.py imports service.py, service.py imports util.py)
- `circular_project/` — A imports B, B imports A via parent module
- `dynamic_project/` — Uses getattr, __import__, importlib
- `star_import_project/` — Uses `from module import *`
- `deep_call_chain/` — 5+ levels of function calls
- `plugin_project/` — Dynamic plugin discovery system

### Test Cases

#### Straightforward Cases (Tests 1-3)
```
1. simple_single_file_change
   Given: Modify simple_project/main.py (add function call)
   Expect: Only modules/functions in main.py affected
   Verify: No false positives (util.py not affected)
   
2. function_signature_change
   Given: Modify service.py function signature
   Expect: All callers of that function marked as affected
   Verify: Accuracy on hand-verified call sites
   
3. new_import_added
   Given: Add new import to main.py
   Expect: Imported module marked as dependency
   Verify: Reflects actual dependency
```

#### Graph Traversal Cases (Tests 4-7)
```
4. import_graph_traversal
   Given: Change util.py (imported by service.py, service imported by main.py)
   Expect: Both main.py and service.py marked as affected
   Verify: Transitive affects detected
   
5. call_graph_backward_traversal
   Given: Change function F called by G, G called by H
   Expect: All three marked as affected
   Verify: 3-level chain traversal works
   
6. call_graph_forward_traversal
   Given: Change function F that calls G, G calls H
   Expect: All three involved (depends on direction semantics)
   Verify: Forward impacts captured
   
7. mixed_import_and_call_traversal
   Given: Change function in module A, module B imports A and calls function
   Expect: Module B marked as affected
   Verify: Both import + call relationships used
```

#### Edge Cases — Circular Imports (Tests 8-9)
```
8. circular_direct_ab
   Given: A imports B, B imports A (top level)
   Expect: Both marked as affected when either changes
   Verify: Circular deps handled correctly
   
9. circular_transitive_abc
   Given: A imports B, B imports C, C imports A
   Expect: All three marked when any changes
   Verify: Cycle detection in impact prediction
```

#### Edge Cases — Dynamic Imports (Tests 10-12)
```
10. dynamic_getattr_import
   Given: getattr(module, 'func_name', default)
   Expect: Confidence score <0.7 (uncertain)
   Reasoning: Cannot statically determine affected code
   
11. dynamic_importlib
   Given: importlib.import_module('module.name')
   Expect: Detected as import (best effort)
   Verify: Pattern detection works
   
12. eval_import_not_detected
   Given: eval("import module")
   Expect: Not detected as import (too uncertain)
   Verify: Conservative approach
```

#### Edge Cases — Star Imports (Tests 13-15)
```
13. star_import_all_symbols
   Given: from module import * (10 public symbols)
   Expect: All 10 symbols marked as affected when imported module changes
   Verify: Star import expansion works
   
14. star_import_underscore_private
   Given: from module import * (module has _private symbols)
   Expect: Only public symbols marked (respect Python convention)
   Verify: Private symbol filtering
   
15. star_import_with_all_variable
   Given: Module defines __all__ = ['a', 'b']
   Expect: Only a, b marked as affected
   Verify: __all__ respects when present
```

#### Edge Cases — Late Binding (Tests 16-17)
```
16. conditional_import_taken_branch
   Given: if DEBUG: import debug_module
   Expect: When debug_module changes, mark as affected
   Verify: Conditional imports analyzed
   
17. conditional_import_not_taken_branch
   Given: if PRODUCTION: import prod_only_module
   Expect: Changes to prod_only_module DON'T affect non-prod code
   Verify: Conservative: assume condition unknown at analysis time
   Note: Practical tradeoff — mark as affected to be safe
```

#### Complex Cases (Tests 18-20)
```
18. interface_multiple_implementations
   Given: Interface class I, implementations A & B both imported by main
   Expect: Changing I affects main; changing A doesn't affect B
   Verify: Implementation-specific affects
   
19. deep_package_hierarchy
   Given: pkg.sub.module.file.function with 5+ levels
   Expect: Each level correctly identified
   Verify: Package boundary handling
   
20. adversarial_hardcase_tbd
   Placeholder for hardest case identified during design review
   Focus: Maximize accuracy on tricky real-world patterns
```

### Success Criteria
- ✅ **Accuracy ≥90%** (18/20 tests correct)
- ✅ **Zero false positives** (unused imports don't show as affected)
- ✅ **Evidence provided** (each prediction includes reasoning)
- ✅ **All tests deterministic** (same input → same output)

---

## Part 2: Feature Planner Tests (15 Cases)

### Purpose
Verify that feature planner generates ≥3 distinct implementation paths per feature.

### Test Fixtures Required
- `layered_flask_app/` — Flask app with presentation, business, data layers
- `microservices_project/` — 3 services with async workers
- `clean_arch_project/` — Entities, use cases, gateways layers
- `mixed_framework_project/` — FastAPI + Celery + SQLAlchemy

### Test Cases

#### Feature Type: API Endpoints (Tests 1-4)
```
1. add_simple_rest_endpoint_layered
   Given: Feature "add user search endpoint" on layered Flask app
   Expect: ≥3 paths:
     Path A: Add to existing routes blueprint (low effort, low risk)
     Path B: Extract into new microservice (high effort, high risk)
     Path C: Add caching layer wrapper (medium effort, low risk)
   Verify: 3+ paths with different effort/risk profiles
   
2. add_endpoint_with_authentication
   Given: Feature "add admin endpoint with auth" on Flask
   Expect: Paths consider:
     Path A: Reuse existing auth decorator
     Path B: Integrate with OAuth provider
     Path C: Implement custom JWT strategy
   Verify: Multiple auth approaches suggested
   
3. add_endpoint_microservices
   Given: "add search endpoint" on microservices architecture
   Expect: Paths consider service boundaries:
     Path A: Add to API gateway
     Path B: New search microservice
     Path C: Federated search across services
   Verify: Architecture-aware paths
   
4. variety_endpoint_paths_differ
   Given: Same feature request
   Expect: Test verifies paths differ materially (not just reordered)
   Verify: Distinct layers, distinct effort, distinct risk
```

#### Feature Type: Service Layer (Tests 5-8)
```
5. add_background_job_celery
   Given: "add notification background job" on Celery+FastAPI
   Expect: ≥3 paths:
     Path A: Add to existing Celery app (low effort)
     Path B: New Celery worker process (medium effort)
     Path C: Message queue (high abstraction, higher effort)
   Verify: Job architecture options
   
6. add_async_service_asyncio
   Given: "add async data processor" on async Python project
   Expect: Paths consider concurrency:
     Path A: AsyncIO task in main process (simple)
     Path B: Dedicated event loop worker (isolated)
     Path C: Distributed task queue (complex)
   
7. add_caching_layer
   Given: "add caching for expensive queries" on Flask+SQLAlchemy
   Expect: Cache strategies:
     Path A: In-process cache (simple, local only)
     Path B: Redis cache (shared, persistent)
     Path C: Hybrid (hot data in memory, cold in Redis)
   
8. add_rate_limiting
   Given: "add rate limiting to API" on Flask
   Expect: Strategies:
     Path A: Decorator on routes (simple)
     Path B: Middleware wrapper (global)
     Path C: Database-backed limits (shared across instances)
```

#### Feature Type: Data Layer (Tests 9-11)
```
9. add_database_migration
   Given: "add users.role column" on Django project
   Expect: Paths:
     Path A: Simple migration (alter table)
     Path B: Versioned migration (backward compatible)
     Path C: Separate read/write columns (complex)
   
10. add_data_validation_layer
    Given: "add input validation" on API project
    Expect: Validation strategies:
      Path A: Model-level validation (ORM)
      Path B: Dedicated validator classes (separation)
      Path C: GraphQL schema validation (schema-driven)
   
11. add_repository_pattern
    Given: "add abstraction layer for data access" on tightly-coupled project
    Expect: Refactoring paths with different scope:
      Path A: Single repository per entity
      Path B: Generic repository pattern
      Path C: Domain-driven repositories with aggregates
```

#### Feature Type: Cross-Cutting (Tests 12-13)
```
12. add_observability_logging
    Given: "add structured logging" on monolith
    Expect: Logging strategies:
      Path A: Decorator on functions
      Path B: Middleware (global)
      Path C: Context manager (context-aware)
    
13. add_feature_flags
    Given: "add feature flags for A/B testing" on production system
    Expect: Flag system options:
      Path A: Environment variables (simple)
      Path B: Configuration service (dynamic)
      Path C: Multi-tenant flags (complex)
```

#### Meta Tests — Variety Requirement (Tests 14-15)
```
14. feature_planner_returns_multiple_paths
    Test the variety test itself:
    - Parse returned paths
    - Verify all 3+ are distinct (not just reordered same solution)
    - Verify they differ in: layer, effort, or risk
    
15. feature_planner_paths_respect_architecture
    Verify all paths fit detected architecture:
    - Layered app: paths respect layers
    - Microservices: paths consider service boundaries
    - No path violates guardrails
```

### Success Criteria
- ✅ **≥3 paths per feature** (verified in tests)
- ✅ **Variety enforced** (paths differ materially)
- ✅ **Architecture-aware** (respects layer boundaries, subsystems)
- ✅ **All paths valid** (zero guardrail violations)

---

## Part 3: Refactoring Advisor Tests (20 Cases)

### Purpose
Verify that refactoring advisor detects 5 issue types with **zero false positives**.

### Test Fixtures Required
- `tight_coupling_simple/` — 2 modules importing each other
- `tight_coupling_complex/` — 3+ modules in cycle
- `duplication_exact/` — Identical functions in 2 files
- `duplication_similar/` — Similar but not identical (70% match)
- `duplication_test_code/` — Test duplicates (should NOT flag)
- `bloated_module/` — 800-line file
- `bloated_class/` — 60 methods in single class
- `bloated_well_structured/` — 600-line file with perfect structure (should NOT flag)
- `circular_simple/` — A→B→A
- `circular_complex/` — A→B→C→A
- `circular_with_breakpoint/` — A→B→A but includes C that doesn't participate (should NOT flag C)
- `debt_hotspot/` — High churn + high coupling
- `debt_clean/` — High churn but low coupling (should NOT flag)

### Test Cases

#### Tight Coupling Detector (Tests 1-5)
```
1. tight_coupling_bidirectional_ab
   Given: A imports B, B imports A (mutual dependency)
   Expect: Flag tight_coupling at both modules
   Confidence: High (>0.8)
   False Positive Risk: Low (explicit 2-way imports)
   
2. tight_coupling_transitive_abc
   Given: A→B→C→A (3-module cycle)
   Expect: Flag all 3 as tight-coupled
   Verify: Cycle detection in coupling analysis
   
3. tight_coupling_via_interface_not_flagged
   Given: A defines interface I, B implements I, both depend on I
   Expect: DON'T flag (interface-based dep is OK)
   Verify: Zero false positive on interface patterns
   
4. tight_coupling_multiple_issues_same_module
   Given: Module A couples to B, C, D (all bidirectional)
   Expect: Single high-severity issue at A (not 3 separate)
   Verify: Issue aggregation
   
5. tight_coupling_confidence_scoring
   Given: A imports B 1x, B imports A 1x (weak coupling)
   Expect: Flag with confidence 0.6-0.7 (lower confidence)
   Verify: Confidence based on coupling intensity
```

#### Code Duplication Detector (Tests 6-10)
```
6. duplication_exact_functions
   Given: function F in file A.py and file B.py (identical)
   Expect: Flag duplication at both
   Confidence: >0.9 (exact match)
   
7. duplication_similar_70_percent
   Given: function F in A.py, similar function in B.py (70% match)
   Expect: Flag duplication
   Confidence: 0.7-0.8
   
8. duplication_in_test_code_not_flagged
   Given: test_a.py and test_b.py both have setup_fixtures() (identical)
   Expect: DON'T flag (test duplication is normal)
   Verify: Zero false positive on test code
   
9. duplication_identical_class_methods
   Given: Class A and B both have method do_something() (identical)
   Expect: Flag duplication
   Verify: Class method analysis
   
10. duplication_confidence_varies_with_length
    Given: 3-line functions vs 30-line functions (same similarity %)
    Expect: Confidence higher for longer functions (less likely coincidence)
    Verify: Length-aware confidence
```

#### Module Bloat Detector (Tests 11-14)
```
11. bloat_file_800_lines
    Given: src/service.py with 800 lines of code
    Expect: Flag as bloat
    Confidence: 1.0 (deterministic threshold)
    
12. bloat_class_60_methods
    Given: class BigClass with 60 methods
    Expect: Flag as bloat
    Verify: Method count analysis
    
13. bloat_file_well_structured_not_flagged
    Given: src/api.py with 600 lines but perfectly modular (many small functions)
    Expect: DON'T flag (structure matters more than size)
    Verify: Zero false positive on well-factored large files
    Note: This depends on configurable threshold or deeper analysis
    
14. bloat_across_files_single_class
    Given: class_definition.py (10 lines), class_methods_1.py (200), ..._2.py (200)
    Expect: Total class size flagged if analyzed as unit
    Verify: File-level vs class-level analysis granularity
```

#### Circular Dependency Detector (Tests 15-17)
```
15. circular_ab_detected
    Given: A imports B, B imports A
    Expect: Flag circular dependency
    Confidence: 1.0 (deterministic)
    
16. circular_abc_detected
    Given: A→B→C→A
    Expect: Flag all three as participating in cycle
    Verify: Multi-edge cycle detection
    
17. circular_with_non_participant_not_flagged
    Given: A→B→A and C imports A (but not in cycle)
    Expect: Flag A-B cycle, but NOT flag C
    Verify: Precise cycle participation
```

#### Technical Debt Hotspot Detector (Tests 18-20)
```
18. debt_high_churn_high_coupling
    Given: service.py changed in 30 commits, couples to 5 modules
    Expect: Flag as debt hotspot
    Confidence: Based on data freshness
    
19. debt_high_churn_low_coupling_not_flagged
    Given: utils.py changed 25 times but only one module depends on it
    Expect: DON'T flag (not actually a problem)
    Verify: Zero false positive on innocent high-churn modules
    
20. debt_new_module_low_history_not_flagged
    Given: brand new module with 0 history
    Expect: Don't flag (no historical data)
    Verify: Conservative on new code
```

### Success Criteria
- ✅ **Detects all 5 issue types** (at least one test per type)
- ✅ **100% precision** (zero false positives)
- ✅ **Confidence scores** (every issue scored 0.4-1.0)
- ✅ **Evidence provided** (each issue has reasoning)

---

## Part 4: Architecture Guardrails Tests (25 Cases)

### Purpose
Verify that guardrails **catch 100% of violations** with no false negatives.

### Test Fixtures Required
- `valid_layered_app/` — Correct layer boundaries
- `invalid_layer_cross/` — Presentation imports data (violation)
- `valid_dag_graph/` — Acyclic dependency graph
- `invalid_cycle_ab/` — A→B→A (violation)
- `invalid_cycle_abc/` — A→B→C→A (violation)
- `valid_module_size/` — All files <500 lines
- `invalid_module_size/` — One file >1000 lines (violation)
- `flask_correct_pattern/` — Flask app with blueprints (correct)
- `flask_wrong_pattern/` — Flask app without blueprint structure (violation)
- `django_correct_pattern/` — Django with app_label structure (correct)
- `django_wrong_pattern/` — Django app without proper structure (violation)

### Test Cases

#### Layer Boundary Rule (Tests 1-5)
```
1. layer_boundary_presentation_to_data_blocked
   Given: src/presentation/views.py imports src/data/db.py
   Expect: VIOLATION: "Presentation layer cannot import data layer"
   Severity: error
   
2. layer_boundary_service_to_data_allowed
   Given: src/business/service.py imports src/data/repository.py
   Expect: PASS (service → data is allowed direction)
   
3. layer_boundary_data_to_presentation_blocked
   Given: src/data/models.py imports src/presentation/forms.py
   Expect: VIOLATION
   
4. layer_boundary_bidirectional_cascade
   Given: presentation.py imports business.py, business.py imports presentation.py
   Expect: VIOLATION on both (bidirectional)
   
5. layer_boundary_with_exception_allowed
   Given: Violation exists BUT guardrails.layer_boundaries.exceptions includes this import
   Expect: PASS (exception honored)
   Verify: Exception mechanism works
```

#### Dependency Direction Rule (Tests 6-10)
```
6. dag_valid_linear_chain
   Given: A→B→C (linear chain, acyclic)
   Expect: PASS
   
7. dag_invalid_simple_cycle_ab
   Given: A→B→A
   Expect: VIOLATION: "Cycle detected: A→B→A"
   
8. dag_invalid_complex_cycle_abca
   Given: A→B→C→A
   Expect: VIOLATION: "Cycle detected: A→B→C→A"
   
9. dag_invalid_multiple_cycles
   Given: A→B→A and C→D→C
   Expect: TWO VIOLATIONS (each cycle reported)
   Verify: Report all cycles, not just first
   
10. dag_valid_diamond_pattern
    Given: A→B, A→C, B→D, C→D (no cycle, diamond)
    Expect: PASS
```

#### Cyclic Prevention Rule (Tests 11-13)
```
11. cyclic_detection_simple
    Given: A imports B, B imports A
    Expect: VIOLATION
    
12. cyclic_detection_with_parent_module
    Given: pkg/a.py imports pkg.b, pkg/b.py imports pkg (parent)
    Expect: Detect cycle through parent module
    
13. cyclic_detection_masking_attempt
    Given: A imports B as alias, B imports A as different alias
    Expect: VIOLATION (detect despite aliasing)
    Verify: Aliasing doesn't bypass detection
```

#### Module Sizing Rule (Tests 14-18)
```
14. module_size_under_limit
    Given: src/service.py with 400 lines
    Expect: PASS
    
15. module_size_over_line_limit
    Given: src/service.py with 600 lines
    Expect: VIOLATION: "Module exceeds 500 line limit"
    
16. module_size_over_function_limit
    Given: src/handlers.py with 45 functions (under 500 lines)
    Expect: PASS (satisfies both constraints)
    
17. module_size_over_function_limit_violation
    Given: src/handlers.py with 60 functions
    Expect: VIOLATION: "Module exceeds 50 function limit"
    
18. module_size_well_structured_exception
    Given: src/api.py with 600 lines but marked as exception in config
    Expect: PASS (exception honored)
```

#### Framework Consistency Rule (Tests 19-23)
```
19. flask_blueprint_pattern_correct
    Given: Flask app uses blueprint pattern (app.register_blueprint())
    Expect: PASS
    
20. flask_blueprint_pattern_missing_violation
    Given: Flask app with routes defined directly in app.py (no blueprints)
    Expect: VIOLATION (doesn't match expected pattern for large apps)
    Note: Depends on app size threshold
    
21. django_app_label_structure_correct
    Given: Django project with apps/myapp/apps.py (app_label pattern)
    Expect: PASS
    
22. django_without_apps_structure_violation
    Given: Django views/models in root (no proper app_label)
    Expect: VIOLATION
    
23. framework_consistency_mixed_patterns
    Given: Flask app uses both blueprint AND direct routes (mixed)
    Expect: WARNING (inconsistent patterns)
    Severity: warning (not error)
```

#### Multi-Rule Scenarios (Tests 24-25)
```
24. multiple_violations_all_reported
    Given: Code has layer boundary violation AND cyclic import
    Expect: BOTH violations reported in single pass
    Verify: Don't stop at first violation
    
25. adversarial_almost_violates_passes
    Given: Code structure that looks like violation but isn't:
      - A imports B's TYPE (for type hint only, `from typing import TYPE_CHECKING`)
      - OR A imports B's constant (constants are layer-agnostic)
      - OR A imports B's Exception (exceptions often cross layers)
    Expect: PASS
    Verify: Zero false negatives
```

### Success Criteria
- ✅ **100% violation detection** (25/25 violations caught)
- ✅ **Zero false positives** (valid code passes)
- ✅ **All violations reported** (don't stop at first)
- ✅ **Clear error messages** (with suggested fixes)

---

## Part 5: Adversarial & Edge Case Tests (10 Cases)

### Purpose
Prevent overfitting by testing the hardest cases.

### Cases

```
1. adversarial_code_structure_misleading
   Code that looks like a violation but isn't
   (E.g., uses structural patterns that mimic cycles but aren't)
   
2. adversarial_aliased_imports
   Imports with aliases designed to hide dependencies
   Verify: Detection still works
   
3. adversarial_conditional_code
   Imports/dependencies guarded by conditions
   Verify: Analysis handles uncertainty correctly
   
4. adversarial_lazy_imports
   Imports inside functions (not top-level)
   Verify: Detection coverage
   
5. adversarial_string_based_imports
   exec(), eval() based imports
   Verify: Conservative approach (don't crash, low confidence)
   
6. adversarial_plugin_discovery
   Dynamic module loading without explicit imports
   Verify: Limitations documented, doesn't falsely claim coverage
   
7. adversarial_test_vs_production_code
   Test code that violates rules (should be ignored)
   Verify: Separate analysis for test code
   
8. adversarial_generated_code
   Code generated by tools (should be treated differently)
   Verify: Or at least, doesn't crash on weird structures
   
9. adversarial_monkeypatching
   Runtime patches to imports/modules
   Verify: Static analysis limitations respected
   
10. adversarial_mixed_language_boundary
    Python code importing TypeScript, vice versa
    Verify: Cross-language analysis handles boundaries correctly
```

---

## Summary

### Test Counts
- Change Planner: 20 tests
- Feature Planner: 15 tests
- Refactoring Advisor: 20 tests
- Architecture Guardrails: 25 tests
- Adversarial & Edge Cases: 10 tests
- **Total: 90+ tests**

### Key Metrics
- **Accuracy:** ≥90% on hand-verified ground truth
- **Precision (Guardrails):** 100% (no false negatives)
- **Precision (Advisor):** 100% (no false positives)
- **Coverage:** ≥85% of component code
- **Performance:** All tests complete in <30 seconds
- **Determinism:** All tests pass consistently (no flakes)

### No Overfitting Strategies
- ✅ Explicit edge case tests (circular, dynamic, star imports, etc.)
- ✅ Adversarial tests (code designed to trick naive algorithms)
- ✅ False positive prevention tests (benign code that shouldn't flag)
- ✅ Variety tests (multiple solutions, not one hardcoded)
- ✅ Cross-architecture tests (rules work on different patterns)

### Execution
```bash
pytest packages/change-planner \
        packages/feature-planner \
        packages/refactoring-advisor \
        packages/arch-guardrails \
        -v --tb=short --cov=packages --cov-report=term-missing
```

**Expected:** All tests pass in <30 seconds, coverage ≥85%, zero flakes.

