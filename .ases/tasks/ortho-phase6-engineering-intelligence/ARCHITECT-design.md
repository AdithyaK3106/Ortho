# Phase 6: Engineering Intelligence — ARCHITECT Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6 (Engineering Intelligence)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 — Architecture & ADR Design  

---

## 1. Architecture Overview

Phase 6 introduces four new packages that sit above the existing Pillar 3 (Architectural Intelligence). They consume architecture data and produce high-level engineering guidance.

```
User Intent
    ↓
Orchestrator Agent
    ↓
┌─────────────────────────────────────────────┐
│  PHASE 6: ENGINEERING INTELLIGENCE LAYER   │
├─────────────────────────────────────────────┤
│ Change Planner        → Impact Prediction  │
│ Feature Planner       → Implementation Paths│
│ Refactoring Advisor   → Issue Detection    │
│ Architecture Guardrails→ Violation Blocking │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  PHASE 5: ARCHITECTURAL INTELLIGENCE        │
├─────────────────────────────────────────────┤
│ Architecture Detector  (8 styles)           │
│ Layer & Subsystem Analysis                  │
│ Blast Radius Calculator                     │
│ Circular Dependency Detector                │
│ Technical Debt Scorer                       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  PHASE 2-3: REPO INTELLIGENCE               │
├─────────────────────────────────────────────┤
│ Symbol Extraction       (AST-based)         │
│ Call Graph              (function level)    │
│ Import Graph            (module level)      │
│ Dependency Analysis                         │
└─────────────────────────────────────────────┘
```

---

## 2. Component Design

### 2.1 Change Planner (`change-planner`)

**Purpose:** Given a file change, predict which modules/functions are affected.

**Inputs:**
- Changed file path
- Call graph (from Pillar 2)
- Import graph (from Pillar 2)
- Architecture model (from Pillar 3)

**Algorithm:**
```
1. Identify changed symbols in file (functions, classes, constants)
2. Traverse call graph backward:
   - Find all functions calling changed symbols
   - Find all modules importing changed module
3. Traverse forward (optional):
   - Find all functions/modules called by changed code
4. Score confidence based on:
   - Directness (direct call vs transitive)
   - Certainty (explicit import vs dynamic)
   - Distance (same module vs cross-module)
5. Return ImpactPrediction with evidence
```

**Edge Cases (Hard):**
- Circular imports (A imports B, B imports A via parent)
- Dynamic imports (getattr, __import__)
- Star imports (from module import *)
- Late binding (runtime resolution)
- Plugin systems (discovery-based)
- Conditional imports (if DEBUG: import X)

**Key Decision:** Conservative on confidence. Low confidence (<0.6) for uncertain impacts.

**No Overfitting:** Tests explicitly check that missing edges don't show up as impacts.

---

### 2.2 Feature Planner (`feature-planner`)

**Purpose:** Given a feature intent, suggest 3+ implementation paths with architecture guidance.

**Inputs:**
- Feature description (natural language or structured)
- Architecture model (style, layers, subsystems)
- Codebase context (existing patterns, frameworks)
- Constraints (performance, security, etc.)

**Algorithm:**
```
1. Parse feature intent (identify type: endpoint, service, utility, etc.)
2. For each known pattern:
   a. Check if pattern fits this architecture style
   b. Identify affected layers/subsystems
   c. Estimate effort + risk
   d. Validate against guardrails
3. Rank paths by:
   - Fit to architecture (higher = better)
   - Risk level (lower = better for safe paths)
   - Effort (varied paths, not just easiest)
4. Return top 3+ paths with rationale
```

**Feature Types:**
- API Endpoint (add route, handler, validation)
- Service Layer (new async service, batch processor)
- Data Layer (new schema, migration, repository)
- Cross-cutting (auth, logging, caching)
- Infrastructure (deployment, monitoring)

**Variety Requirement:** Paths must differ materially (different layers, different effort levels, different risk profiles). Not just sorted by effort.

**No Overfitting:** Tests verify that multiple paths exist and are returned, not hardcoded to one solution.

---

### 2.3 Refactoring Advisor (`refactoring-advisor`)

**Purpose:** Identify 5 issue types and recommend refactoring actions.

**Issue Detectors (5 Modules):**

**1. Tight Coupling Detector**
- Identifies modules with high bidirectional dependencies
- Algorithm: Count edges in both directions, flag if count > threshold
- Edge case: Interfaces/contracts (should not flag)
- Confidence: Count of problematic imports / total imports

**2. Code Duplication Detector**
- Identifies similar code patterns across files
- Algorithm: Compare function signatures + AST structure (Jaccard similarity)
- Edge case: Test code (often duplicates by design)
- Confidence: Similarity score (0.8+ = high confidence)

**3. Module Bloat Detector**
- Identifies oversized files/classes
- Thresholds: >500 lines or >50 functions or >5000 cyclomatic complexity
- Edge case: Well-structured large files (should not flag)
- Confidence: Based on ratio to threshold

**4. Circular Dependency Detector**
- Reuses Phase 5's circular dependency engine
- Detects A→B→A patterns
- Confidence: 1.0 (deterministic)

**5. Technical Debt Hotspot Detector**
- Identifies high-churn, high-coupling modules
- Algorithm: (churn_score * 0.6) + (coupling_score * 0.4)
- Edge case: New projects (low historical churn)
- Confidence: Based on data freshness + sample size

**Zero False Positives Requirement:**
- Every issue must have clear evidence
- Tests adversarially check for false positives
- If uncertain, confidence < 0.6

**No Overfitting:** Tests include benign code that looks suspicious but shouldn't be flagged.

---

### 2.4 Architecture Guardrails (`arch-guardrails`)

**Purpose:** Enforce 5 architectural rules with 100% detection rate.

**Rules (5 Modules):**

**1. Layer Boundaries Rule**
- Data layer cannot import presentation layer
- Service layer cannot import presentation layer
- Each layer defined by file/module path patterns
- Algorithm: For each import, check import direction against layer hierarchy
- Confidence: 1.0 (deterministic)

**2. Dependency Direction Rule**
- Dependencies must flow in one direction (DAG, acyclic)
- Detects cycles of any length
- Algorithm: Topological sort + cycle detection
- Confidence: 1.0 (deterministic)

**3. Cyclic Prevention Rule**
- Same as #2, but allows explicit exceptions (with documentation)
- Reuses Phase 5 circular dependency detector
- Confidence: 1.0

**4. Module Sizing Rule**
- Configurable thresholds (default: 500 lines, 50 functions)
- Prevents bloat
- Algorithm: Line count + function count
- Confidence: 1.0 (deterministic)

**5. Framework Consistency Rule**
- Enforces consistent use of framework patterns
- Examples: Flask apps use blueprint pattern, Django apps use app_label pattern
- Algorithm: Scan for framework fingerprints + expected patterns
- Confidence: Based on pattern detection (0.7-1.0)

**100% Block Rate Requirement:**
- All violations must be caught
- Tests design adversarial violations that try to evade detection
- Report all violations in single pass (don't miss secondary violations)

**No Overfitting:** Adversarial tests include near-violations that should pass.

---

## 3. Data Flow & Integration

### 3.1 Inputs from Existing Pillars

**From Pillar 2 (Repo Intelligence):**
- `CallGraph` → vertices (functions), edges (calls)
- `ImportGraph` → vertices (modules), edges (imports)
- `SymbolRegistry` → function/class definitions + locations
- `ModuleRegistry` → module boundaries

**From Pillar 3 (Arch Intelligence):**
- `ArchitectureModel` → detected style (layered, microservices, etc.)
- `LayerModel` → layers + file patterns
- `SubsystemModel` → subsystems + boundaries
- `CircularDependencies` → list of cycles
- `DebtScores` → per-module debt

**From ContextHub (Pillar 2):**
- FRD, ADRs → feature context + architectural decisions
- Git metadata → churn history
- Artifact search → code patterns + examples

### 3.2 Outputs

**Change Planner:**
```python
ImpactPrediction(
    changed_file="src/auth/service.py",
    affected_modules=["src/auth", "src/api/routes"],
    affected_functions=["authenticate", "validate_token"],
    cascade_risk="medium",
    confidence=0.87,
    reasoning="...",
    evidence=[
        "auth/service.py exports authenticate",
        "api/routes.py imports auth/service",
        "api/routes.py calls authenticate in 3 places"
    ]
)
```

**Feature Planner:**
```python
ImplementationPath(
    name="API Gateway Pattern",
    description="Add new route handler in existing blueprint",
    affected_layers=["presentation", "business"],
    effort="low",
    risk="low",
    dependencies_to_add=[],
    rationale="Fits existing Flask blueprint architecture"
)
```

**Refactoring Advisor:**
```python
RefactoringIssue(
    issue_type="tight_coupling",
    location="src/payment/service.py ↔ src/order/service.py",
    severity="high",
    recommendation="Extract shared Ledger interface",
    estimated_effort="4 hours",
    confidence=0.92,
    false_positive_risk="Low (explicit 2-way imports verified)"
)
```

**Architecture Guardrails:**
```python
GuardrailViolation(
    rule_id="layer_boundaries",
    severity="error",
    location="src/presentation/views.py:42",
    message="Presentation layer imports data layer (src/data/db.py)",
    suggested_fix="Use repository pattern or service layer instead"
)
```

---

## 4. ADRs

### ADR-016: Phase 6 Package Structure & Dependencies

**Status:** Proposed  
**Decision:** Each Phase 6 component is a separate package with clear responsibilities.

**Rationale:**
- Follows YAGNI (each package solves one problem)
- Enables independent testing and upgrades
- Allows selective inclusion in orchestrator workflows

**Alternatives Considered:**
1. Single monolithic package (rejected: bloat, harder to test)
2. Plugins registry (rejected: overengineering for 4 components)

**Consequences:**
- ✅ Clear package boundaries
- ✅ Parallel test + build work possible
- ✅ Each component upgradeable independently
- ⚠️ Coordination overhead (manage shared types)

**Mitigation:** Shared types in `packages/shared-types/`.

---

### ADR-017: Confidence Scoring Strategy

**Status:** Proposed  
**Decision:** All components return confidence scores (0.0-1.0) based on evidence.

**Rationale:**
- Enables downstream filtering (only act on high-confidence recommendations)
- Makes uncertainty explicit
- Helps identify where more analysis is needed

**Scoring Rules:**
- 1.0 = Deterministic (e.g., cycle detection)
- 0.8-0.99 = High confidence (multiple sources agree)
- 0.6-0.79 = Medium confidence (single source or heuristic)
- 0.4-0.59 = Low confidence (uncertain, may be false positive)
- <0.4 = Not reported (too uncertain)

**Consequences:**
- ✅ Explicit uncertainty handling
- ✅ Orchestrator can make informed decisions
- ⚠️ Low-confidence results may be missed

---

### ADR-018: Zero False Positives Philosophy

**Status:** Proposed  
**Decision:** Refactoring Advisor and Guardrails prioritize precision over recall.

**Rationale:**
- False positives create noise and erode trust
- Better to miss an issue than report wrong ones
- Engineers should act on recommendations with confidence

**Implementation:**
- Refactoring Advisor: Only report high-confidence issues (>0.8)
- Guardrails: Report all violations (deterministic)
- Tests explicitly verify zero false positives (adversarial cases)

**Consequences:**
- ✅ High trust in reported issues
- ⚠️ May miss some real issues (acceptable tradeoff)

---

### ADR-019: Feature Planner Variety Requirement

**Status:** Proposed  
**Decision:** Feature Planner must return ≥3 distinct implementation paths.

**Rationale:**
- One solution is luck; multiple solutions show understanding
- Different paths serve different priorities (speed vs safety)
- Humans should decide, not AI

**Definition of Distinct:**
- Different effort levels OR
- Different risk profiles OR
- Different affected layers OR
- Different technology choices

**Consequences:**
- ✅ Users see options
- ✅ Prevents hardcoded solutions
- ⚠️ More computation needed

---

### ADR-020: Guardrails Configurability

**Status:** Proposed  
**Decision:** Guardrail rules are configurable (per-project settings).

**Rationale:**
- Different projects have different constraints
- Framework patterns vary by codebase
- Some teams tolerate certain violations

**Configuration:**
```toml
[guardrails]
layer_boundaries = true
dependency_direction = true
cyclic_prevention = true
module_sizing = true
framework_consistency = true

[guardrails.module_sizing]
max_lines = 500
max_functions = 50

[guardrails.layer_boundaries]
exception_imports = [
    "src/presentation -> src/shared"
]
```

**Consequences:**
- ✅ Flexibility for diverse projects
- ✅ Explicit exceptions documented
- ⚠️ Risk of disabling important rules

---

## 5. No Overfitting Strategies

### Test Design Principles

1. **Explicit Edge Cases**
   - Circular imports tested
   - Dynamic imports tested
   - Star imports tested
   - Late-binding imports tested

2. **Adversarial Tests**
   - Code that *looks* like an issue but isn't
   - Code that *almost* violates but doesn't
   - Code with intentional obfuscation

3. **False Positive Prevention**
   - Every test verifies NOT reporting non-issues
   - Advisors tested for overcounting
   - Guardrails tested for overly strict rules

4. **Variety Tests**
   - Feature planner returns multiple distinct paths
   - Impact predictor handles different path lengths
   - Refactoring advisor covers different issue types

5. **Cross-Architecture Tests**
   - Rules work on layered AND microservices
   - Rules work on Python AND TypeScript
   - Rules work on small AND large projects

### Concrete Examples

**Change Planner — No Overfitting:**
- Test that unused imports DON'T show up as affected
- Test that comments mentioning a function DON'T count as usage
- Test that conditional imports only count when conditions are met

**Feature Planner — No Overfitting:**
- Test that multiple distinct paths are returned (not just reordered same path)
- Test that paths differ in layers, effort, or risk (not just names)

**Refactoring Advisor — No Overfitting:**
- Test that benign large files don't trigger bloat warning
- Test that test duplication doesn't trigger duplication warning
- Test that interface-based tight coupling doesn't trigger coupling warning

**Guardrails — No Overfitting:**
- Test that aliased imports still trigger violations
- Test that conditional violations on non-taken branches don't trigger
- Test that exceptions actually work (don't ignore them)

---

## 6. Integration Points

### With Orchestrator

**Change Planner:**
- Triggered by: `analyze --impact <file>` command
- Agent: Analyst
- Skills: impact-analyzer (shared with Phase 5)

**Feature Planner:**
- Triggered by: `feature_development` intent
- Agent: Architect
- Skills: impact-analyzer, adr-writer

**Refactoring Advisor:**
- Triggered by: `refactor` intent
- Agent: Analyst, Reviewer
- Skills: debt-analyzer

**Architecture Guardrails:**
- Triggered by: Before any code change
- Agent: Reviewer
- Skills: architecture-aware-retrieval

### Storage

- Results stored in ContextHub as artifacts (type: `engineering_recommendation`)
- Evidence artifacts link back to code locations
- Git-tracked in `.ases/evidence/`

---

## 7. Performance Targets

| Component | Operation | Target |
|-----------|-----------|--------|
| **Change Planner** | Predict impact (1 file) | <100ms |
| **Feature Planner** | Generate 3+ paths | <500ms |
| **Refactoring Advisor** | Scan all issues | <2s |
| **Guardrails** | Validate all rules | <500ms |

---

## 8. Testing Strategy Summary

### TEST-DESIGNER Approach

**Hard Test Cases (Not Easy Mocks):**
- Real call graphs with actual cyclic patterns
- Real import structures from test fixtures
- Real architectural patterns from known repos
- Adversarial cases designed to trick naive algorithms

**No Flakes (Deterministic Tests):**
- No randomization
- No time-based tests
- No external dependencies
- All tests use local fixtures

**High Coverage (≥85%):**
- Unit tests per function
- Integration tests per component
- End-to-end tests per package
- Adversarial tests for edge cases

---

## 9. Definition of Done (GATE 2)

✅ All 4 component designs complete (with ADRs)  
✅ Data models defined (shared types)  
✅ Integration points identified  
✅ No circular dependencies between packages  
✅ ADRs reviewed and approved  
✅ No external dependencies without justification  
✅ Performance targets set and achievable  

---

## Next Phase (BUILDER)

Implement all 4 packages in parallel:
- BUILDER 1: change-planner (predictor + types)
- BUILDER 2: feature-planner (planner + types)
- BUILDER 3: refactoring-advisor (detectors + advisor)
- BUILDER 4: arch-guardrails (enforcer + rules)

With parallel TEST-DESIGNER building comprehensive test suites.

