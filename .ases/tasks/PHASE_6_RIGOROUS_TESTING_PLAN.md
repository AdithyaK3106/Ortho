# Phase 6: Rigorous Testing & Bug Hunt

**Date:** 2026-07-13  
**Objective:** Find and fix ALL bugs, edge cases, and issues  
**Methodology:** Exhaustive testing + verification + fixes  
**Scope:** All 6 packages (change-planner, feature-planner, refactoring-advisor, arch-guardrails, decision-engine, cli-commands)

---

## Test Strategy: EXHAUSTIVE COVERAGE

### Tier 1: Boundary Testing (Input Edge Cases)

**Change Planner Edge Cases:**
- [ ] Empty file change
- [ ] File with only comments
- [ ] File with only whitespace
- [ ] 1-line file
- [ ] 10,000-line file
- [ ] Circular imports A→B→A
- [ ] Circular A→B→C→A
- [ ] Circular A→B→A→C→A (nested)
- [ ] Star imports: from X import *
- [ ] Star imports with __all__ = []
- [ ] Star imports with __all__ = None
- [ ] Dynamic: getattr(module, name)
- [ ] Dynamic: __import__("module")
- [ ] Dynamic: importlib.import_module()
- [ ] Conditional: if DEBUG: import X
- [ ] Conditional: if sys.version > 3.8: import X
- [ ] Late binding: import inside function
- [ ] Late binding: import inside lambda
- [ ] Null/None handling
- [ ] Missing symbols

**Feature Planner Edge Cases:**
- [ ] Empty intent ""
- [ ] Whitespace-only intent "   "
- [ ] Very long intent (10K chars)
- [ ] Special chars: !@#$%^&*()
- [ ] Unicode: emoji, CJK
- [ ] SQL injection attempt: "'; DROP TABLE--"
- [ ] Command injection: "$(rm -rf /)"
- [ ] Null intent None
- [ ] Integer intent 123
- [ ] Boolean intent True/False
- [ ] List/dict intent as string

**Refactoring Advisor Edge Cases:**
- [ ] Empty repository (0 modules)
- [ ] Single file (1 module)
- [ ] 10,000 modules (scale test)
- [ ] Identical functions in 2 files (merge)
- [ ] Similar functions (70% match)
- [ ] Dissimilar functions (30% match)
- [ ] Test files (should not flag)
- [ ] Generated code (should skip)
- [ ] Vendor code (should exclude)
- [ ] Circular deps A→B→A
- [ ] Circular A→B→C→D→A (deep)
- [ ] Self-reference A→A
- [ ] Module with 0 functions
- [ ] Module with 1000+ functions
- [ ] File with 0 lines
- [ ] File with 1M lines

**Arch Guardrails Edge Cases:**
- [ ] No layers defined
- [ ] Single layer (monolith)
- [ ] 10 layers (deep)
- [ ] No dependencies
- [ ] All modules depend on all (complete graph)
- [ ] No modules
- [ ] Module not assigned to layer
- [ ] Layer boundary with TYPE_CHECKING import
- [ ] Layer boundary with exception rule
- [ ] Cyclic A→B→A
- [ ] Cyclic all-to-all
- [ ] Module size: 0 bytes
- [ ] Module size: 1GB
- [ ] Module functions: 0
- [ ] Module functions: 10K

**Decision Engine Edge Cases:**
- [ ] No sources have data
- [ ] All sources empty
- [ ] One source crashes
- [ ] All sources crash
- [ ] Confidence: all 0.0
- [ ] Confidence: all 1.0
- [ ] Confidence: NaN
- [ ] Confidence: Infinity
- [ ] Option dedup: 100% match
- [ ] Option dedup: 0% match
- [ ] 1000 options
- [ ] 0 options
- [ ] Contradictory sources (A vs not-A)
- [ ] Cyclic recommendations (A→B→A)
- [ ] Null options
- [ ] Missing required fields

**CLI Commands Edge Cases:**
- [ ] Empty intent: `ortho plan ""`
- [ ] Whitespace: `ortho plan "   "`
- [ ] Very long: 100K char intent
- [ ] Shell injection: `ortho plan "$(malicious)"`
- [ ] Path traversal: `ortho refactor ../../../etc/passwd`
- [ ] Symlink path: `ortho refactor /path/to/symlink`
- [ ] Non-existent path: `ortho refactor /nonexistent/path`
- [ ] Permission denied: `/root/private/`
- [ ] Unicode path: `ortho refactor /café/café/`
- [ ] Circular symlinks: infinite loop
- [ ] Mount point: cross filesystem
- [ ] Lock file exists (concurrent access)
- [ ] Database locked
- [ ] Missing .ortho/ directory
- [ ] Corrupted config file
- [ ] Invalid JSON in config

---

### Tier 2: Logic Correctness Testing

**Change Planner Logic:**
- [ ] Impact: direct vs. transitive calls
- [ ] Impact: import vs. call precedence
- [ ] Impact: star import expansion correct
- [ ] Confidence: decreases with distance
- [ ] Cascade risk: assessed correctly
- [ ] Evidence: includes all edges
- [ ] No duplicates in results
- [ ] Handles missing graph data

**Feature Planner Logic:**
- [ ] Feature type classification (all 5 types)
- [ ] Path variety: 3+ distinct returned
- [ ] Effort/risk: correctly assigned
- [ ] Layers: matches architecture
- [ ] Rationale: non-empty
- [ ] Dependencies: realistic
- [ ] Duplicate detection: actual vs. false positives

**Refactoring Advisor Logic:**
- [ ] Coupling: symmetric detection
- [ ] Duplication: Jaccard similarity correct
- [ ] Bloat: thresholds applied
- [ ] Circular: all cycles found
- [ ] Debt: churn × coupling calculated
- [ ] Confidence: reflects evidence
- [ ] Severity: high/medium/low correct
- [ ] False positive prevention working

**Arch Guardrails Logic:**
- [ ] Layer boundaries: direction enforced
- [ ] Dependency DAG: acyclic check
- [ ] Module size: both thresholds applied
- [ ] Framework patterns: detected correctly
- [ ] Exception rules: honored
- [ ] All violations reported (no truncation)
- [ ] Suggested fixes: actionable

**Decision Engine Logic:**
- [ ] Source conversion: all 4 handled
- [ ] Deduplication: threshold (0.8) applied
- [ ] Ranking: confidence × fit formula
- [ ] Graceful degradation: missing sources
- [ ] Top N selection: capped at 5
- [ ] Reasoning: explains top choice
- [ ] Confidence aggregation: correct

**CLI Commands Logic:**
- [ ] plan: calls feature-planner
- [ ] refactor: calls refactoring-advisor
- [ ] guardrails: calls arch-guardrails
- [ ] decide: calls decision-engine
- [ ] Output formatting: valid structure
- [ ] Error messages: clear
- [ ] Exit codes: correct (0 = success)

---

### Tier 3: Integration Testing

**Component Chains:**
- [ ] Change → Feature (impact → plan)
- [ ] Change → Refactoring (impact → issues)
- [ ] Change → Guardrails (impact → violations)
- [ ] Feature → Guardrails (plan → compliance)
- [ ] Refactoring → Guardrails (fix → validation)
- [ ] All → Decision (aggregate all)
- [ ] Decision → CLI (format output)

**Conflict Resolution:**
- [ ] Contradictory sources (A vs ¬A)
- [ ] Consensus (all agree)
- [ ] Dispersion (all different confidence)
- [ ] Degenerate (all low confidence)
- [ ] Missing evidence (partial data)

**Data Flow:**
- [ ] Recommendations pass through correctly
- [ ] Evidence preserved through pipeline
- [ ] Confidence scores maintained
- [ ] No data loss/corruption

---

### Tier 4: Performance Testing

**Load Testing:**
- [ ] 1000-module project
- [ ] 10,000-module project
- [ ] 1M-line codebase
- [ ] Deep call graphs (1000 levels)
- [ ] Wide graphs (1000 branches)
- [ ] Dense graphs (complete connectivity)

**Timing Tests:**
- [ ] Change planner: <100ms
- [ ] Feature planner: <500ms
- [ ] Refactoring advisor: <2s
- [ ] Guardrails: <500ms
- [ ] Decision engine: <1s
- [ ] CLI commands: <5s
- [ ] All together: <10s

---

### Tier 5: Type Safety & Memory

**Python Strict Mode:**
- [ ] No `Any` types
- [ ] All return types specified
- [ ] All param types specified
- [ ] No implicit None
- [ ] No missing error handling

**Memory:**
- [ ] No memory leaks (large project)
- [ ] No unbounded data structures
- [ ] Proper cleanup
- [ ] No circular references

---

## Execution Plan

1. **Run all existing tests** (verify baseline)
2. **Create exhaustive test file** for each component
3. **Run new tests** (find failures)
4. **Fix identified bugs** immediately
5. **Re-run full suite** (verify fixes)
6. **Document findings** (bug report)

---

## Progress Tracking

Component | Unit Tests | Edge Cases | Integration | Perf | Status
-----------|-----------|-----------|------------|------|--------
Change Planner | ✅ | 🔄 | 🔄 | 🔄 | Testing
Feature Planner | ✅ | 🔄 | 🔄 | 🔄 | Testing
Refactoring | ✅ | 🔄 | 🔄 | 🔄 | Testing
Guardrails | ✅ | 🔄 | 🔄 | 🔄 | Testing
Decision Engine | ✅ | 🔄 | 🔄 | 🔄 | Testing
CLI Commands | ✅ | 🔄 | 🔄 | 🔄 | Testing

---

## Bug Fixes Applied

[To be updated as bugs are found and fixed]

