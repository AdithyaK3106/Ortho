# task-008: Planning Review — Issues Resolved

**PLANNER Session:** Post-planning consistency pass  
**Date:** 2026-07-02  
**Status:** ✓ ALL ISSUES RESOLVED

---

## Issue 1: Restore Rollback Philosophy (git revert vs git reset --hard)

**Status:** ✓ RESOLVED

**Changes Made:**

**rollback-plan.md:**
- Added "Rollback Policy" section distinguishing local vs. published work
- Documented `git revert` (preserves history, auditability) for published commits
- Documented `git reset --hard` (local recovery only) for unpublished changes
- Added "Rollback Strategy: Local vs. Published" with separate procedures for each
- Added "Step 2: Determine Strategy" to detect which path applies
- Added Phase 3A (local) and Phase 3B (published) execution paths
- Provided copy-paste commands for both strategies

**plan.md:**
- Updated Rollback Strategy to reference the detailed philosophy in rollback-plan.md
- Clarified when each approach is used
- Linked to complete procedures

**Result:** Rollback policy now fully complies with ASES principle of preserving auditability and history for published work.

---

## Issue 2: Resolve Layer Numbering Convention

**Status:** ✓ RESOLVED

**Convention Chosen:** Depth-first numbering (Layer 0 = deepest, lowest-level)

**Specification:**

| Layer | Name | Direction | Examples | Purpose |
|-------|------|-----------|----------|---------|
| 0 | Data | No outgoing dependencies | repository, model, db, dao | Lowest level; other layers depend on this |
| 1 | Business | Depends only on Layer 0 | service, logic, domain, core | Business logic; bridges data and presentation |
| 2 | Presentation | Depends on Layers 0–1 | controller, view, endpoint, handler | Highest level; user-facing |

**Changes Made:**

**spec.md - LayerDetector section:**
- Added comprehensive table showing layer numbers, names, direction, examples, and purpose
- Documented "Layer Numbering Convention (Consistent Throughout)"
- Clarified dependency direction: "Dependencies flow inward: Layer 2 → Layer 1 → Layer 0"
- Added validation rule: "Layered architecture := all dependencies form acyclic dependency chain where each layer only imports from lower-numbered layers"
- Updated algorithm description to align with convention
- Updated output specification

**spec.md - Layered Pattern section:**
- Updated detector description to reference the new layer convention
- Replaced vague "confidence boost/penalty" with detailed scoring model
- Example confidence calculation shows how signals aggregate to 0.5–0.95 range

**plan.md - Task 2:**
- Updated description: "Layer numbering: Layer 0 (data/lowest) → Layer 1 (business) → Layer 2 (presentation/highest)"
- Added semantic naming examples: "repository/model → Layer 0, service → Layer 1, controller → Layer 2"
- Referenced spec.md for detailed convention

**plan.md - AC2:**
- Updated to specify: "Layer 0 = data, Layer 1 = business, Layer 2 = presentation"
- Included semantic naming examples for each layer
- Clarified dependency validation rule

**Result:** Layer numbering is now consistent throughout all planning documents with no ambiguity about what "Layer 0" represents.

---

## Issue 3: Define Confidence Aggregation (Model, Scoring, Winner Selection, Tie Handling)

**Status:** ✓ RESOLVED

**New Section Added:** "Confidence Model (Complete Specification)"

**Contents:**

### Signal Aggregation
- Documented structural signals (import/call graph shape, density, isolation)
- Documented semantic signals (naming patterns, directory organization)
- Documented quality signals (layer acyclicity, subsystem cohesion, boundary clarity)

### Score Normalization
- Explained raw evidence accumulation
- Base score assignment (0.6–0.8 if core signals present)
- Bonus/penalty application (+0.05 to +0.25 bonuses; -0.05 to -0.25 penalties)
- Clamping to [0.0, 1.0] range

### Winner Selection Algorithm
- Step 1: Calculate all 5 detector scores
- Step 2: Select highest score as winner
- Step 3: Identify secondary hypothesis (2nd highest)
- Step 4: Apply margin threshold (if difference <0.15, flag as ambiguous)

### Tie Handling (Deterministic)
- Perfect tie rule: Use priority order (layered → mvc → hexagonal → microservices → flat)
- Close scores rule (difference <0.10): Flag confidence as "low"
- No winner rule (all scores <0.50): Return "flat" with confidence <0.50

### Evidence Justifications
- Provided 3 real examples showing how evidence explains confidence scores
- Demonstrates reproducibility and interpretability

**Pattern Detector Confidence Models Updated:**

Each detector now includes detailed confidence calculation:

**Layered:** Base 0.6, +0.15 for semantic naming, +0.10 for 3–4 layers, penalties for naming/cycles → Range 0.5–0.95

**Hexagonal:** Base 0.65, +0.15 for adapter isolation, +0.10 for semantic naming, penalties for coupling → Range 0.40–0.90

**MVC:** Base 0.70, +0.15 for semantic naming, +0.10 for correct dependency directions, penalties for entanglement → Range 0.35–0.95

**Microservices:** Base 0.60, +0.20 for loose coupling (<0.25), +0.10 for subsystem count, penalties for tight coupling → Range 0.30–0.90

**Flat:** Base 0.55, +0.15 for high coupling, +0.10 for single subsystem, penalties for clear patterns → Range 0.20–0.80

**Result:** Confidence model is now fully specified. Two independent implementations would reach identical decisions given the same evidence.

---

## Issue 4: Expand Validation Strategy with Real Repositories

**Status:** ✓ RESOLVED

**New Section Added:** "Validation Strategy"

**Contents:**

### Synthetic Fixtures (Unit & Regression)
- Purpose: Deterministic validation of algorithm correctness
- Characteristics: Known structure, predictable output, isolated testing
- List of fixtures: Layered DAG, hexagonal, MVC, microservices, flat, edge cases
- Example test code showing deterministic assertions
- Regression value: Catches algorithm breakage early

### Real Repository Fixtures (Robustness & Calibration)
- Purpose: Validate against complex, mixed patterns
- Characteristics: Imperfect patterns, natural complexity, variable sizes
- Fixtures: fastapi, django, layered-example, hexagonal-ddd
- Example test code showing non-deterministic score ranges
- **Critical:** Benchmark values are informational only, not acceptance criteria

### Validation Execution (Timeline)
- **BUILDER phase:** Synthetic tests first, then real-repo tests
- **VERIFIER phase:** Synthetic must pass; real-repo must run without crashes (no score constraints)
- **REVIEWER phase:** Confirm both executed; check for anomalies

**Key Statement:**
> "Repository-specific benchmark values should remain informational and **must not** become acceptance criteria."

**Result:** Validation strategy clearly separates synthetic and real-repository testing. Real repos inform calibration but don't constrain acceptance.

---

## Issue 5: Final Consistency Review

**Status:** ✓ RESOLVED

**Verification Checklist:**

- [x] No contradictory terminology
  - "Layer 0" consistently means "data/lowest level" in all documents
  - "Confidence" consistently defined as 0.0–1.0 aggregated score
  - "Layered" consistently means acyclic dependency chain

- [x] Deterministic confidence behavior
  - Aggregation model fully specified
  - Winner selection deterministic (with tie-breaker rules)
  - Tie-breaking order documented (layered → mvc → hexagonal → microservices → flat)
  - Evidence justifications show reproducibility

- [x] Consistent layer numbering
  - Layer 0 = data, Layer 1 = business, Layer 2 = presentation
  - Semantic naming examples provided for each layer
  - Dependency direction ("flows inward") clear throughout
  - AC2 updated to match convention

- [x] Rollback policy aligns with ASES
  - Git revert (published) vs git reset --hard (local) policy documented
  - Auditability and history preservation emphasized
  - Two separate procedures with clear triggering logic
  - Copy-paste commands provided for both paths

- [x] Validation strategy clearly separates synthetic and real-repo testing
  - Synthetic: deterministic, isolated, regression testing
  - Real-repo: robustness, calibration, complexity handling
  - Benchmark values marked as informational only
  - No score constraints on real-repo tests

---

## Summary of Improvements

| Issue | Before | After | Impact |
|-------|--------|-------|--------|
| Rollback | `git reset --hard` only | `git revert` (published) + `git reset --hard` (local) | Preserves auditability; aligns with ASES |
| Layer numbering | Contradictory (Layer 0 = data AND deepest) | Consistent depth-first (Layer 0 = deepest data) | No ambiguity; deterministic implementation |
| Confidence | Vague ranges per detector | Full aggregation model with signals, scoring, tie-breaking | Reproducible; two implementations reach same result |
| Validation | Synthetic only | Synthetic + real-repo with separate purposes | Catches both algorithm bugs and real-world complexity |
| Consistency | Incomplete | Pass complete; all docs align | Gate-1 ready |

---

## GATE 1 Readiness

**Artifacts Submitted:**

- ✓ plan.md — 5 atomic tasks, risks, rollback strategy (with ASES alignment)
- ✓ spec.md — Complete component contracts, confidence model, validation strategy
- ✓ rollback-plan.md — Detailed procedures, local vs. published strategies, verification

**Consistency Verified:**

- ✓ No contradictory terminology
- ✓ Layer numbering deterministic throughout
- ✓ Confidence model fully specified
- ✓ Rollback aligns with ASES (git revert for published)
- ✓ Validation separates synthetic and real-repo testing
- ✓ All 5 acceptance criteria testable and verifiable

**No Scope Changes:**

- ✓ Architecture unchanged
- ✓ Implementation unchanged
- ✓ APIs unchanged
- ✓ Package structure unchanged
- ✓ 5 atomic tasks unchanged

**Result:** Planning package is now internally consistent, reproducible, and fully aligned with ASES engineering process.

---

*Planning review completed by PLANNER role.*  
*Ready for human review and approval at GATE 1.*
