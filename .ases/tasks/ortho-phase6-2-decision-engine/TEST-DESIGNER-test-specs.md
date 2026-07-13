# Phase 6.2: Decision Engine & CLI Integration — TEST-DESIGNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6.2 (Decision Engine & CLI)  
**Date:** 2026-07-13  
**Methodology:** Hard test design with zero overfitting prevention  

---

## Overview

This document specifies **hard test cases** for Phase 6.2:
- Decision Engine: 20 multi-source scenarios
- CLI Commands: 20 end-to-end workflows
- Integration: 5 full workflow tests
- **Total: 45+ tests**

All tests use real Phase 6.1 components (not mocks).

---

## Part 1: Decision Engine Tests (20 Cases)

### Purpose
Verify decision engine correctly aggregates multi-source recommendations with proper ranking and deduplication.

### Test Fixtures Required
- Real component instances from Phase 6.1 (change-planner, feature-planner, refactoring-advisor, arch-guardrails)
- Mock repositories with realistic data
- Test intents representing common scenarios

### Test Cases

#### Single Source Tests (Tests 1-4)
```
1. single_source_change_planner
   Given: Only change predictions available
   Expect: Options from change planner only
   Verify: Returns valid decisions despite missing other sources
   
2. single_source_feature_planner
   Given: Only feature paths available
   Expect: Options from feature planner only
   
3. single_source_refactoring
   Given: Only refactoring issues available
   Expect: Issues ranked as options
   
4. single_source_guardrails
   Given: Only guardrail violations available
   Expect: Violations presented as actionable options
```

#### Multi-Source Tests (Tests 5-9)
```
5. two_sources_change_feature
   Given: Change predictions + feature paths
   Expect: ≥3 combined options
   Verify: Both sources represented
   
6. two_sources_refactoring_guardrails
   Given: Refactoring issues + guardrail violations
   Expect: Both issue types in options
   
7. three_sources_change_feature_refactoring
   Given: Change + feature + refactoring (no guardrails)
   Expect: Options from all 3 sources
   
8. three_sources_feature_refactoring_guardrails
   Given: Feature + refactoring + guardrails (no change)
   Expect: Well-rounded recommendations
   
9. all_four_sources_combined
   Given: All sources with recommendations
   Expect: ≥3 distinct options combining insights
   Verify: Holistic decision with confidence scores
```

#### Conflict Resolution Tests (Tests 10-12)
```
10. conflicting_recommendations
    Given: Feature planner says "add endpoint" but guardrails says "layer violation"
    Expect: Choose highest confidence option
    Verify: Explain conflict in reasoning
    
11. empty_sources_graceful_degradation
    Given: All 4 sources return no recommendations
    Expect: Empty decision or "no issues found"
    Verify: No crash, meaningful message
    
12. all_low_confidence
    Given: All recommendations have confidence <0.6
    Expect: Return options but flag as low confidence
    Verify: User warned about uncertainty
```

#### Ranking Tests (Tests 13-16)
```
13. high_confidence_consensus
    Given: All sources agree on best option (high confidence)
    Expect: Top ranked option has very high confidence
    Verify: Score reflects agreement
    
14. dispersed_confidence
    Given: Options with confidence 0.5, 0.7, 0.9, 0.6
    Expect: 0.9 ranked highest
    Verify: Ranking function works correctly
    
15. zero_risk_prioritized
    Given: Multiple options, one has zero risk
    Expect: Zero-risk option ranked higher
    Verify: Risk factor included in score
    
16. low_effort_when_equal_confidence
    Given: Two options same confidence, one low effort
    Expect: Low-effort option ranked higher
    Verify: Effort factor applied as tiebreaker
```

#### Deduplication Tests (Tests 17-18)
```
17. similar_recommendations_merged
    Given: Two options "extract interface" and "create abstraction"
    Expect: Merged into single option (high similarity)
    Verify: Confidence averaged, not duplicated
    
18. distinct_recommendations_kept
    Given: "Add caching" and "Add logging" (both cross-cutting)
    Expect: Both kept (low similarity, different recommendations)
    Verify: Deduplication threshold ~0.8
```

#### Edge Cases (Tests 19-20)
```
19. large_option_set_limited
    Given: 20+ recommendations from all sources
    Expect: Return top 5 options (not overwhelming)
    Verify: Limiting works without data loss
    
20. adversarial_contradictory_sources
    Given: Change says "safe", Guardrails says "violation", Refactoring says "bloat"
    Expect: Return all 3 with confidence scores
    Verify: Handle contradictions gracefully
```

### Success Criteria
- ✅ **Multi-source aggregation** (≥3 sources in 9/20 tests)
- ✅ **Proper deduplication** (similar recs merged)
- ✅ **Correct ranking** (highest confidence first)
- ✅ **Graceful degradation** (no crashes on missing sources)
- ✅ **100% test pass rate** (20/20)

---

## Part 2: CLI Commands Tests (20 Cases)

### Purpose
Verify CLI commands execute end-to-end (intent → analysis → recommendations).

### Test Fixtures Required
- Real ortho project (with scan data)
- Test codebase with various issues
- Mock stdin/stdout for CLI testing

### Test Cases

#### Plan Command (Tests 1-3)
```
1. plan_simple_endpoint
   Command: ortho plan "add user search endpoint"
   Expect: ≥3 implementation paths
   Verify: Feature planner results formatted
   
2. plan_background_job
   Command: ortho plan "add notification background job"
   Expect: Service layer paths
   
3. plan_caching_layer
   Command: ortho plan "add caching for expensive queries"
   Expect: Cross-cutting concern paths
```

#### Refactor Command (Tests 4-6)
```
4. refactor_single_file
   Command: ortho refactor src/service.py
   Expect: Issues in that file identified
   
5. refactor_all
   Command: ortho refactor --all
   Expect: Full codebase scan, all issues listed
   Verify: Performance acceptable (<5s)
   
6. refactor_specific_path
   Command: ortho refactor src/api/
   Expect: Issues in api/ subtree only
```

#### Guardrails Command (Tests 7-9)
```
7. guardrails_check_all
   Command: ortho guardrails check
   Expect: All violations listed (errors + warnings)
   
8. guardrails_strict
   Command: ortho guardrails check --strict
   Expect: Only errors (filter warnings)
   
9. guardrails_path
   Command: ortho guardrails check src/models/
   Expect: Violations in specific path
```

#### Decide Command (Tests 10-11)
```
10. decide_feature_implementation
    Command: ortho decide "implement new microservice"
    Expect: Multi-source decision with ≥3 options
    
11. decide_quality_improvement
    Command: ortho decide "improve code quality"
    Expect: Refactoring + architectural recommendations combined
```

#### Output Format Tests (Tests 12-14)
```
12. format_verbose
    Command: ortho refactor --verbose src/service.py
    Expect: Detailed output with evidence
    Verify: Evidence shown for each issue
    
13. format_json
    Command: ortho plan --json "add endpoint"
    Expect: Valid JSON output
    Verify: Machine-parseable
    
14. format_quiet
    Command: ortho guardrails check -q
    Expect: Minimal output (summary only)
```

#### Error Handling Tests (Tests 15-18)
```
15. error_bad_intent
    Command: ortho plan ""
    Expect: Error message "intent required"
    Verify: No crash
    
16. error_missing_file
    Command: ortho refactor nonexistent/file.py
    Expect: Error "file not found"
    
17. error_bad_option
    Command: ortho plan --invalid-flag "something"
    Expect: Usage message
    
18. error_no_context
    Command: ortho decide "something" (on unscanned repo)
    Expect: Error "run ortho scan first"
```

#### Confidence Filtering Tests (Tests 19-20)
```
19. confidence_filter_high
    Command: ortho refactor --confidence 0.8 src/
    Expect: Only high-confidence issues (≥0.8)
    
20. confidence_filter_low
    Command: ortho plan --confidence 0.5 "add feature"
    Expect: More options included (lower threshold)
```

### Success Criteria
- ✅ **All commands execute** (20/20 work end-to-end)
- ✅ **Correct output format** (text, json, quiet)
- ✅ **Error handling** (graceful on bad input)
- ✅ **Performance** (<5s per command)
- ✅ **100% test pass rate**

---

## Part 3: Integration Tests (5 Cases)

### Purpose
Verify full workflows (intent → decision → action).

### Workflows

```
1. FEATURE DEVELOPMENT WORKFLOW
   Intent: "add rate limiting to API"
   Steps:
     a) Feature Planner: 3+ rate limiting strategies
     b) Change Planner: Impact on auth, middleware
     c) Refactoring Advisor: Suggest extraction of cross-cutting
     d) Decision Engine: Combine → best strategy
     e) CLI: Present unified roadmap
   Verify: All steps complete, coherent recommendations

2. REFACTORING WORKFLOW
   Intent: "improve code quality"
   Steps:
     a) Refactoring Advisor: Find issues (coupling, bloat, debt)
     b) Prioritize by impact
     c) Decision Engine: Group related issues
     d) CLI: Show prioritized list
   Verify: Issues actionable, ordered by ROI

3. ARCHITECTURE ENFORCEMENT WORKFLOW
   Intent: "ensure compliance"
   Steps:
     a) Guardrails check: Find violations
     b) Refactoring Advisor: Suggest fixes
     c) Impact: Estimate effort
     d) Decision Engine: Prioritize
     e) CLI: Present remediation roadmap
   Verify: Violations → actionable fixes

4. CHANGE IMPACT WORKFLOW
   Intent: "assess impact of payment service change"
   Steps:
     a) Change Planner: Predict affected modules/functions
     b) Guardrails: Check for layer violations
     c) Refactoring: Identify affected debt areas
     d) Feature Planner: Suggest refactoring paths
     e) Decision: Comprehensive impact report
   Verify: Full change assessment

5. COMBINED WORKFLOW
   Intent: "implement new feature safely"
   Steps:
     a) Feature Planner: Generate implementation paths
     b) Guardrails: Verify all paths are compliant
     c) Refactoring: Identify prerequisite cleanups
     d) Change Planner: Predict impact per path
     e) Decision: Compare paths (compliance, impact, effort)
     f) CLI: Present decision with evidence
   Verify: Holistic feature planning
```

### Success Criteria
- ✅ **All 5 workflows complete**
- ✅ **Coherent recommendations** (not contradictory)
- ✅ **Evidence traceable** (each recommendation justified)
- ✅ **Performance** (<5s per workflow)
- ✅ **100% pass rate**

---

## Part 4: No Overfitting Tests (10 Cases)

### Purpose
Prevent naive solutions; test adversarial/edge cases.

```
1. adversarial_cli_injection
   Input: `ortho plan "$(rm -rf /)"`
   Expect: Safe parsing, command injection prevented
   
2. adversarial_decision_contradiction
   Input: All 4 sources contradict each other
   Expect: Graceful resolution, explain trade-offs
   
3. adversarial_dedup_false_merge
   Input: "Extract interface" and "Add abstraction" (70% similar)
   Expect: NOT merged (below threshold)
   
4. adversarial_empty_codebase
   Input: ortho on project with no source files
   Expect: Graceful "no files to analyze"
   
5. adversarial_huge_project
   Input: Scan 10,000+ file project
   Expect: Commands complete in <10s
   
6. adversarial_conflicting_sources
   Input: Refactoring says "remove module", Feature needs it
   Expect: Flag conflict, let user decide
   
7. adversarial_low_confidence_all
   Input: All recommendations <0.5 confidence
   Expect: Return with warning "low confidence"
   
8. adversarial_missing_dependencies
   Input: Decision Engine can't access Phase 6.1 components
   Expect: Graceful error, not crash
   
9. adversarial_malformed_evidence
   Input: Recommendation with empty evidence list
   Expect: Report without evidence, still valid
   
10. adversarial_circular_suggestions
    Input: Refactoring says "split module", Feature says "merge module"
    Expect: Present both options, explain trade-offs
```

---

## Summary

### Test Counts
- Decision Engine: 20 tests
- CLI Commands: 20 tests
- Integration Workflows: 5 tests
- No Overfitting: 10 tests
- **Total: 55 tests**

### Key Metrics
- **Accuracy:** 100% test pass rate
- **Coverage:** ≥85% code coverage
- **Performance:** <5s per command
- **Robustness:** Adversarial tests confirm handling
- **No Overfitting:** Edge cases explicitly covered

### Execution
```bash
pytest packages/decision-engine \
        packages/cli-commands \
        packages/orchestration/tests/integration \
        -v --tb=short
```

**Expected:** 55/55 tests passing in <30 seconds, coverage ≥85%, zero overfitting.

