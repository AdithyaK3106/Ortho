# task-005: Cycle Handling — Deterministic Behavior
## Architectural Clarification (ARCHITECT)

**Date:** 2026-06-30  
**Purpose:** Document deterministic behavior for circular dependencies in architecture detection  
**Scope:** Cycles in import graph, cycles in call graph, layer detection fallback

---

## Problem Statement

The current documentation contains:
- "Architecture analysis should handle cycles gracefully"
- "Layer detection assumes a DAG"

These statements are contradictory without explicit resolution. This document specifies exact behavior.

---

## Execution Flow: Circular Dependency Handling

### Phase 1: Cycle Detection (Deterministic)

**When:** Before any analysis begins (in ArchitectureDetector.detect())

```python
# Pseudocode — exact order
1. Build file dependency graph from import edges
2. Call FileGraph.detect_cycles() → returns list[list[file_id]]
3. If cycles found:
   a. Log all cycles with file paths
   b. Store cycle_count in analysis metadata
   c. Reduce confidence score by 0.15 (see confidence adjustment below)
   d. Add evidence: "N circular dependencies detected (see full report)"
4. Continue to phase 2 (do not abort)
```

**Output:** cycles: list[list[str]] (list of all cycles found)

**Deterministic:** Same repo always produces same cycles in same order (topological enumeration).

---

### Phase 2: Metrics Computation (Tolerates Cycles)

**When:** After cycle detection (MetricsCalculator._compute_metrics())

**Behavior:**
- Layering score: Computed on full graph (cycles included)
  - Cyclic edges count as "same-level" dependencies (neither upward nor downward)
  - Formula: layering_score = upward_edges / (upward_edges + same_level + downward)
  - Cycles reduce layering_score (expected: lower confidence)

- Cohesion score: Uses density metric (handles cycles naturally)
  - Cycles increase internal connectivity
  - Expected: higher cohesion in cycle-rich repos

- Modularity score: Community detection (Louvain) handles cycles
  - Cyclic modules cluster together
  - Expected: modularity unchanged (algorithm is robust)

**Deterministic:** Same graph always produces same metrics (networkx algorithms are deterministic).

---

### Phase 3: Architecture Style Scoring (Degraded Confidence)

**When:** After metrics computed (ArchitectureDetector._score_*)

**Behavior for each style:**

| Style | Cycle Impact | Adjusted Score |
|-------|--------------|-----------------|
| **layered** | Cycles break layer hierarchy | base_score - 0.15 |
| **hexagonal** | Cycles in adapters acceptable | base_score - 0.05 |
| **mvc** | Cycles break tier isolation | base_score - 0.20 |
| **microservices** | Cycles = bad coupling | base_score - 0.25 |
| **flat** | Cycles expected | base_score (no adjustment) |

**Application:**
```python
# In ArchitectureDetector.detect()
if cycles_found:
    cycle_penalties = {
        'layered': 0.15,
        'hexagonal': 0.05,
        'mvc': 0.20,
        'microservices': 0.25,
        'flat': 0.0,
    }
    for style, base_score in scores.items():
        scores[style] = max(0.0, base_score - cycle_penalties[style])
```

**Deterministic:** Same cycles produce same score adjustments.

---

### Phase 4: Layer Detection (Fallback Mode)

**When:** LayerDetector.detect_layers() is called

**Normal case (no cycles or DAG-like):**
1. Compute topological_levels() via longest-path algorithm
2. Assign each file to a level (0 = no dependencies, N = deepest)
3. Cluster files by level → layers
4. Assign semantic names (presentation, business, data, infrastructure)

**Degraded case (cycles present):**
1. Compute topological_levels() with cycle-aware fallback
   - Cyclic nodes get level = 1 + max(level of non-cyclic predecessors)
   - If all predecessors are cyclic, level = 0
2. Cluster files by level → layers (same as normal)
3. Confidence score per layer reduced (see Layer.confidence computation)
4. Layer.depends_on includes cyclic edges (marked as "cyclic" in evidence)

**Deterministic:** Same graph always produces same layer assignments (level assignment is deterministic).

**Key property:** Layer detection NEVER FAILS. It produces layers even with cycles, but with reduced confidence.

---

### Phase 5: Subsystem Detection (Cycle-Agnostic)

**When:** SubsystemDetector.detect_subsystems() is called

**Behavior:** Louvain community detection is independent of cycle structure.
- Cycles are edges like any other
- Cyclic edges increase community cohesion
- Algorithm continues unchanged

**Deterministic:** Same graph produces same communities (Louvain seeds are reproducible with fixed random state).

---

### Phase 6: Final Result (Reduced Confidence, Still Valid)

**When:** ArchitectureDetector.detect() returns DetectionResult

**Structure:**
```python
DetectionResult(
    style='layered',                 # Still assigned even with cycles
    confidence=0.72,                 # Reduced from 0.87 (e.g., -0.15 penalty)
    evidence=[
        "Clear upward dependencies (88% upward-only imports)",
        "3 detected layers",
        "⚠ WARNING: 2 circular dependencies found (auth ↔ config, model ↔ utils)",
        "Cycles reduce confidence in layer isolation",
        "Consider breaking cycles for cleaner architecture",
    ],
    alternative='mvc',
    alternative_confidence=0.51,
)
```

**Key properties:**
- Result is never None or partial
- Confidence is reduced, not zeroed
- Cycles explicitly listed in evidence
- Architecture detection continues
- Style is still actionable (layers still identified, subsystems still clustered)

---

## Confidence Adjustments (Cycle Penalties)

**Table of penalties** (cumulative within a single detection):

| Penalty Source | Amount | Rationale |
|---|---|---|
| Each unique cycle detected | -0.03 | Cycles indicate non-layered design |
| Cyclic edge count > 5% of total | -0.10 | Significant violation of DAG assumption |
| Cycle in core module (high centrality) | -0.05 | Central cycles are more impactful |
| **Maximum total reduction** | -0.25 | (Never below 0.0) |

**Example:**
```
Base layered score: 0.87
- 3 cycles detected: -0.09
- Cycles > 5%: -0.10
- Core module involved: -0.05
= 0.87 - 0.24 = 0.63 (valid, reduced confidence)
```

---

## Testing Expectations for Cycles

### Test fixture: circular-deps-repo

```
packages/
  auth/
    service.py → imports config
  config/
    manager.py → imports auth (CYCLE!)
```

**Expected behavior:**
- detect_cycles() returns [['auth/service.py', 'config/manager.py']]
- layering_score = reduced but non-zero
- LayerDetector assigns both to same level
- Confidence = 0.70-0.75 (reduced from ~0.85)
- evidence includes: "1 circular dependency found"
- Result still assigns architecture style (not "unknown")

### Test fixture: heavily-cyclic-repo

```
20 modules, 50% edges are cyclic (unusual but valid)
```

**Expected behavior:**
- detect_cycles() returns 15+ cycles
- layering_score ≈ 0.1 (mostly same-level edges)
- Architecture style = "flat" (high confidence, penalized less)
- Result is valid and deterministic

---

## Determinism Guarantee

**For any fixed repository state:**

1. Cycle detection is deterministic (DFS order is consistent)
2. Metrics computation is deterministic (networkx is deterministic)
3. Score adjustments are deterministic (formula is fixed)
4. Layer assignments are deterministic (topological levels are unique)
5. Subsystem assignments are deterministic (Louvain with fixed seed)

**Consequence:** Running detect() twice on same repo produces identical results.

---

## Failure Cases (Do Not Occur)

| Case | Behavior |
|------|----------|
| Dense graph with many cycles | Reduced confidence, still valid result |
| Strongly connected component | Assigned to same layer, reduced confidence |
| Completely cyclic graph | Assigned architecture='flat' (correct), confidence ≈ 0.5 |
| **No architecture can cause FAILURE** | Layer detection uses fallback; subsystem detection tolerates cycles |

---

## Summary

| Aspect | Behavior |
|--------|----------|
| **Cycle detection** | Deterministic, before analysis |
| **Cycle impact** | Reduced confidence via fixed penalties |
| **Layer detection** | Uses fallback topological assignment, never fails |
| **Subsystem detection** | Cycle-agnostic (Louvain handles naturally) |
| **Final result** | Always valid ArchitectureModel, never None |
| **Confidence** | Adjusted downward, never zeroed |
| **Determinism** | Guaranteed for fixed repo state |

---

**Prepared by:** ARCHITECT  
**Status:** Refinement — Ready for TEST-DESIGNER to validate with adversarial fixtures
