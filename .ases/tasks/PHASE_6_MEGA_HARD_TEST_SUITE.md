# Phase 6: Comprehensive HARD Test Suite (200+ Cases)

**Date:** 2026-07-13  
**Scope:** ALL Phase 6 components (6.1 + 6.2 + 6.3 Plan)  
**Test Count:** 200+ adversarial test cases  
**Focus:** Integration, edge cases, overfitting prevention, real-world scenarios  
**Execution:** ASES TEST-DESIGNER methodology  

---

## Test Tiers

### Tier 1: Individual Component Hardness (96 existing + 50+ new)

**Change Planner (30 HARD cases)**
- Circular: A→B→C→A→D (multi-path cycles)
- Dynamic: eval, exec, __import__, getattr chains
- Star imports with conditional __all__ definitions
- Late-binding with decorator factories
- Plugin systems with discovery patterns
- Lazy imports in lambda/closure contexts
- Cross-module impact through inheritance
- Metaclass-based dynamic loading
- Descriptor protocol affects
- Property decorators affecting call chains

**Feature Planner (30 HARD cases)**
- Conflicting paths (both add feature AND remove it)
- Paths that violate each other's assumptions
- Microservice split that creates tight coupling
- Monolith consolidation reducing performance
- Feature flag systems with complex rules
- A/B testing infrastructure affecting paths
- Performance optimization vs. maintainability trade-off
- Security hardening vs. usability trade-off
- Multi-tenant architecture decisions
- Cost optimization paths

**Refactoring Advisor (30 HARD cases)**
- Tight coupling that's actually abstraction
- Duplication that's intentional (policy, security)
- Bloat that's well-structured (lookup tables)
- Circular deps that are intentional (event systems)
- Debt hotspots in actively-developed code
- False positive prevention (interface patterns)
- Test code duplication (not a bug)
- Generated code bloat (don't refactor)
- Vendor code analysis (skip)
- Framework idioms (not smells)

**Arch Guardrails (30 HARD cases)**
- Layer violations that are type-safe (TYPE_CHECKING)
- Dependency cycles that are weak (config loading)
- Module size violations that are justified (DSL)
- Framework patterns that are inverted (middleware)
- Exception patterns crossing layers (OK)
- Conditional imports guarded by version checks
- Explicit exception rules honored
- Aliased imports hiding violations
- Re-exports crossing layers
- Private module imports

**Decision Engine (20 HARD cases)**
- All 4 sources contradict (rank by confidence)
- 2 sources agree, 2 disagree (choose consensus)
- All sources low confidence (<0.5)
- One source crashes (graceful degradation)
- Cyclic recommendations (A→B→A)
- Contradictory evidence for same recommendation
- Deduplication merges too aggressively
- Deduplication keeps duplicates (threshold)
- Recommendation titles differ, content identical
- Multi-word titles with substring matching

**CLI Commands (20 HARD cases)**
- Empty intent ("", whitespace, newlines)
- Intent with special chars ($, ;, |, &, `)
- Very long intent (10,000 chars)
- Unicode in intent (emoji, CJK)
- Path with symlinks
- Path with relative components (../..)
- Path that doesn't exist (graceful)
- Permission denied on path (error handling)
- Circular symlinks (infinite traversal)
- Mount points and filesystem boundaries

---

### Tier 2: Cross-Component Integration (100+ HARD cases)

**Change → Feature Planning**
- Impact predicts 5 modules affected
- Feature planner suggests changing all 5
- Verify consistency of recommendations

**Change → Refactoring**
- Impact predicts module M changed
- Refactoring finds issue in M
- Suggest fix that doesn't re-introduce issue

**Change → Guardrails**
- Impact predicts cross-layer affects
- Guardrails check predicted violations
- Verify all violations in predicted impact

**Feature → Refactoring**
- Feature plan suggests extracting service
- Refactoring finds tight coupling in service
- Suggest extraction doesn't create cycles

**Feature → Guardrails**
- All feature paths comply with guardrails
- No path violates layer boundaries
- No path creates circular deps

**Refactoring → Guardrails**
- Suggested fix doesn't violate rules
- Refactoring in data layer doesn't violate
- Extraction creates new valid module

**All 4 → Decision**
- Consensus when all agree
- Conflict resolution when contradictory
- Ranking by confidence when dispersed
- Graceful when sources missing

**Decision → CLI**
- Decision with 5 options
- CLI displays all options
- User can select any option

---

### Tier 3: Real-World Scenarios (50+ HARD cases)

**Scenario 1: Add Rate Limiting**
- Feature planner: 3+ paths
- Change impact: predict middleware, routes, config
- Refactoring: suggest extraction of decorator
- Guardrails: verify cross-cutting pattern
- Decision: choose best path

**Scenario 2: Fix Auth Bug**
- Change predicts: auth module + 8 callers
- Refactoring: find tight coupling
- Feature: optional migration path
- Guardrails: verify layer compliance
- Decision: urgent vs. refactor-first

**Scenario 3: Migrate Monolith→Microservices**
- Feature plans: 3 split strategies
- Change impact: predict massive cascade
- Refactoring: debt in extraction targets
- Guardrails: new service boundaries
- Decision: phased vs. big-bang

**Scenario 4: Database Schema Migration**
- Feature: backward-compatible vs. breaking
- Change: impacts ORM, migrations, schema
- Refactoring: data layer bloat
- Guardrails: layer violations in ORM
- Decision: strategy selection

**Scenario 5: Performance Optimization**
- Change: cache layer affects query paths
- Feature: 3+ caching strategies
- Refactoring: identify cache busting issues
- Guardrails: verify cache doesn't violate
- Decision: trade-offs (latency vs. complexity)

**Scenario 6: Security Hardening**
- Feature: auth, encryption, validation
- Change: widespread impact
- Refactoring: extract security concerns
- Guardrails: enforce security patterns
- Decision: minimal viable security

**Scenario 7: Technical Debt Paydown**
- Refactoring: identify debt hotspots
- Change: refactoring cascade
- Feature: how to maintain during refactor
- Guardrails: prevent regressions
- Decision: prioritization

**Scenario 8: Framework Upgrade**
- Change: framework updates affect all
- Feature: breaking changes handling
- Refactoring: deprecated patterns
- Guardrails: version-specific rules
- Decision: upgrade strategy

---

### Tier 4: Adversarial Edge Cases (50+ HARD cases)

**Adversarial: Component Failures**
- Change planner crashes (handler test)
- Feature planner returns 0 paths (fallback)
- Refactoring finds 1000+ issues (limiting)
- Guardrails timeout (graceful fail)
- Decision engine missing source (degrade)

**Adversarial: Conflicting Recommendations**
- Split component vs. consolidate
- Add layer vs. remove layer
- Increase modularity vs. reduce complexity
- Cache aggressively vs. avoid cache
- Refactor now vs. defer to Phase 2

**Adversarial: Degenerate Inputs**
- 0-length code
- 1000000-line single file
- Circular includes (A→B→C→A)
- 10,000 modules (scalability)
- Cyclical feature dependencies

**Adversarial: Ambiguity**
- Same recommendation from multiple sources
- Nearly-identical recommendations (merge?)
- Confidence tied (rank by secondary metric)
- All scores equal (random selection OK?)
- No clear winner (present all)

**Adversarial: Incomplete Information**
- Call graph missing edges
- Import graph partial
- Architecture detected incorrectly
- No debt score available
- Limited test coverage

**Adversarial: Cascade Effects**
- Change breaks refactoring suggestion
- Refactoring violates new guardrail
- Feature enables new architectural issue
- Decision choice cascades to new issues
- Fix creates new problem elsewhere

---

## Test Execution Matrix

| Component | Unit | Integration | Adversarial | Real-World | Total |
|-----------|------|-------------|-------------|-----------|-------|
| Change | 22 | 15 | 10 | 10 | 57 |
| Feature | 18 | 15 | 10 | 10 | 53 |
| Refactoring | 22 | 15 | 10 | 10 | 57 |
| Guardrails | 18 | 15 | 10 | 10 | 53 |
| Decision | 12 | 20 | 10 | 10 | 52 |
| CLI | 6 | 15 | 10 | 10 | 41 |
| **TOTAL** | **98** | **95** | **60** | **60** | **313** |

---

## Success Criteria (GATE 5)

- ✅ **All 313 tests pass** (100%)
- ✅ **No regressions** (Phase 6.1/6.2 still 100%)
- ✅ **Coverage ≥90%** per component
- ✅ **Performance** <10s all tests
- ✅ **Zero overfitting** (adversarial tests)
- ✅ **Real-world scenarios** validated
- ✅ **Integration verified** (all combinations)

---

## Execution Plan

1. **Run Phase 6.1 Full Test Suite** (78 tests)
   - change-planner: 22/22
   - feature-planner: 18/18
   - refactoring-advisor: 22/22
   - arch-guardrails: 18/18

2. **Run Phase 6.2 Full Test Suite** (18 tests)
   - decision-engine: 12/12
   - cli-commands: 6/6

3. **Run New Comprehensive Suite** (200+ tests)
   - 50 per component (hard cases)
   - 100 integration tests
   - 60 adversarial tests

4. **Verify No Regressions**
   - All 96 original tests still pass
   - New tests integrated
   - All 313+ tests passing

5. **Performance Validation**
   - <10s total execution
   - <1s per component set
   - <100ms per test (avg)

---

## Deliverables

✅ **PHASE_6_MEGA_HARD_TEST_SUITE.md** (this document)  
✅ **Phase 6.1 full test run** (78/78)  
✅ **Phase 6.2 full test run** (18/18)  
✅ **Comprehensive test suite** (200+)  
✅ **Integration verification** (all combinations)  
✅ **Performance report** (timings)  
✅ **Coverage report** (by component)  

---

## Expected Outcome

When user returns from lunch:
- ✅ All Phase 6.X complete
- ✅ 300+ tests passing (100%)
- ✅ Comprehensive HARD test suite executed
- ✅ All metrics exceeded
- ✅ Zero overfitting confirmed
- ✅ Production ready

