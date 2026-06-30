# task-005: Evidence Model — Structured & Explainable
## Architecture Detection Output Documentation (ARCHITECT)

**Date:** 2026-06-30  
**Purpose:** Make every architecture decision explainable and reviewable  
**Scope:** DetectionResult structure, evidence fields, metadata

---

## Current DetectionResult Structure

```python
@dataclass
class DetectionResult:
    style: ArchStyle                          # Selected style
    confidence: float                         # 0.0 - 1.0
    evidence: list[str]                      # Human-readable justifications
    alternative: ArchStyle | None
    alternative_confidence: float | None
```

**Assessment:** Current structure is human-friendly but lacks structured metrics. This document extends explainability without changing the API.

---

## Enhanced Evidence Model (Proposed)

### Extended DetectionResult Output (in practice)

The public API remains unchanged. The evidence list is enriched with structured data:

```python
# What gets returned to users:
result = DetectionResult(
    style='layered',
    confidence=0.87,
    evidence=[
        # Structured metrics (parseable, not just text)
        "[METRIC] layering_score: 0.92",
        "[METRIC] cohesion_score: 0.56",
        "[METRIC] modularity_score: 0.34",
        "[METRIC] node_count: 127",
        "[METRIC] edge_count: 487",
        "[METRIC] cycle_count: 0",
        "[METRIC] layer_count: 3",
        "[METRIC] subsystem_count: 8",
        
        # Style confidence breakdown
        "[CONFIDENCE] layered: 0.87",
        "[CONFIDENCE] hexagonal: 0.52",
        "[CONFIDENCE] mvc: 0.41",
        "[CONFIDENCE] microservices: 0.31",
        "[CONFIDENCE] flat: 0.15",
        
        # Human-readable analysis
        "Clear upward dependencies (92% upward-only imports)",
        "3 distinct layers detected (presentation, business, data)",
        "Low cross-layer coupling (8% cross-layer edges)",
        "8 subsystems with average coupling 0.67",
        "0 circular dependencies detected",
        
        # Reasoning
        "Layered scoring: 0.7 * 0.92 (layering) + 0.2 * (1 - 0.34) + 0.1 * 0.56 = 0.87",
        "High confidence due to clear layer structure and minimal violations",
    ],
    alternative='mvc',
    alternative_confidence=0.52,
)
```

### Structured Evidence Tags (Proposed)

Evidence list items can be categorized by prefix:

| Prefix | Purpose | Example |
|--------|---------|---------|
| `[METRIC]` | Numeric graph property | `[METRIC] edge_count: 487` |
| `[CONFIDENCE]` | Style score | `[CONFIDENCE] layered: 0.87` |
| `[ANALYSIS]` | Human interpretation | `Clear upward dependencies...` |
| `[REASONING]` | Score calculation trace | `Layered scoring: 0.7 * 0.92 + ...` |
| `[WARNING]` | Risk or degradation | `⚠ [WARNING] 3 circular dependencies reduce confidence` |

---

## Comprehensive Evidence Fields

### 1. Detected Architecture Style

```
[STYLE] layered
[CONFIDENCE] 0.87
[ALTERNATIVE] mvc (0.52)
```

**Meaning:** Selected style is "layered" with 87% confidence. MVC is a close alternative at 52%.

---

### 2. Confidence Breakdown (All Candidates)

```
[CONFIDENCE] layered: 0.87
[CONFIDENCE] hexagonal: 0.52
[CONFIDENCE] mvc: 0.41
[CONFIDENCE] microservices: 0.31
[CONFIDENCE] flat: 0.15
```

**Meaning:** Shows relative scores for all 5 patterns. Helps users understand robustness of the result.

---

### 3. Dependency Graph Statistics

```
[METRIC] node_count: 127          # Files in repo
[METRIC] edge_count: 487          # Import relationships
[METRIC] cycle_count: 0           # Circular dependencies
[METRIC] avg_in_degree: 3.8       # Average fan-in
[METRIC] avg_out_degree: 3.8      # Average fan-out
[METRIC] max_in_degree: 24        # Most imported file
[METRIC] max_out_degree: 18       # Heaviest importer
[METRIC] graph_density: 0.030     # Sparsity indicator
```

**Meaning:** Characterizes the structure being analyzed. Helps reviewers gauge complexity.

---

### 4. Architecture-Specific Metrics

```
[METRIC] layering_score: 0.92       # How much follows upward deps (0.0-1.0)
[METRIC] cohesion_score: 0.56       # Internal coupling density (0.0-1.0)
[METRIC] modularity_score: 0.34     # Independence of modules (0.0-1.0)
```

**Meaning:** Core inputs to scoring. Reviewable at detail level.

---

### 5. Layer Analysis

```
[LAYER_COUNT] 3
[LAYER] presentation (8 files, confidence 0.94)
  - depends_on: business
  - violations: 0
[LAYER] business (12 files, confidence 0.89)
  - depends_on: data
  - violations: 1 (auth → data)
[LAYER] data (6 files, confidence 1.0)
  - depends_on: (none)
  - violations: 0
```

**Meaning:** Detailed layer breakdown. Shows violations and confidence per layer.

---

### 6. Subsystem Analysis

```
[SUBSYSTEM_COUNT] 8
[SUBSYSTEM] auth (4 files, coupling 0.89)
[SUBSYSTEM] payment (6 files, coupling 0.78)
[SUBSYSTEM] inventory (5 files, coupling 0.64)
[SUBSYSTEM] reporting (3 files, coupling 0.55)
[SUBSYSTEM] util (2 files, coupling 0.10)
...
[SUBSYSTEM_AVG_COUPLING] 0.67
```

**Meaning:** Subsystem membership and internal coupling. High coupling = tightly bound module.

---

### 7. Cycle Analysis

```
[CYCLE_COUNT] 0
```

or (if cycles exist):

```
[CYCLE_COUNT] 3
[CYCLE] auth ↔ config (2 files, edge_count: 2)
[CYCLE] model ↔ utils ↔ model (3 files, edge_count: 3)
[CYCLE] service → cache → service (2 files, edge_count: 2)
[CONFIDENCE_PENALTY] 0.15 (due to cycles)
```

**Meaning:** Explicit cycle reporting. Shows penalty applied to confidence.

---

### 8. Scoring Trace (Reasoning)

```
[REASONING] Layered score calculation:
  base = 0.7 * layering(0.92) + 0.2 * (1 - modularity(0.34)) + 0.1 * cohesion(0.56)
  base = 0.7 * 0.92 + 0.2 * 0.66 + 0.1 * 0.56
  base = 0.644 + 0.132 + 0.056 = 0.832
  [No cycles → no penalty]
  final_confidence = 0.832 ≈ 0.83

[REASONING] Hexagonal score:
  base = 0.8 * cohesion(0.56) + 0.2 * (1 - modularity(0.34))
  base = 0.448 + 0.132 = 0.580
  [Low confidence → alternative]
  final_confidence = 0.580 ≈ 0.58
```

**Meaning:** Fully transparent scoring. Reviewers can audit every decision.

---

### 9. Human-Readable Analysis

```
[ANALYSIS] Clear upward dependencies
  92% of import edges point to lower-level modules.
  This is the hallmark of layered architecture.

[ANALYSIS] Distinct layer structure
  Topological analysis identifies 3 layers:
  - Layer 0 (top): presentation handlers, API routes
  - Layer 1 (mid): business logic, domain services
  - Layer 2 (bottom): data access, repositories

[ANALYSIS] Low cross-layer coupling
  Only 8% of edges cross layer boundaries.
  This indicates strong architectural discipline.

[ANALYSIS] Moderate internal coupling
  Cohesion score 0.56 suggests modules are loosely coupled.
  No evidence of god objects or tangled classes.

[ANALYSIS] Low modularity
  Modularity score 0.34 indicates subsystems are not perfectly isolated.
  This is consistent with tightly-layered design (expected).

[ANALYSIS] No circular dependencies
  The graph is acyclic. No coupling cycles detected.
```

**Meaning:** Human-friendly explanation. Auditable by non-technical reviewers.

---

### 10. Warnings & Limitations

```
[WARNING] Modularity score is low (0.34)
  The detection algorithm found weak module boundaries.
  This may indicate: (a) tight integration by design, (b) poor modularization.
  Recommend code review of high-coupling subsystems.

[WARNING] 1 layer violation detected
  The 'auth' layer imports 'data' layer, skipping 'business' layer.
  This violates clean architecture principles.
  Recommend refactoring auth → business → data call chain.

[LIMITATION] Hexagonal pattern requires manual validation
  The detector scores hexagonal architecture at 0.52.
  This is below the confidence threshold (0.7).
  Manual review required to confirm ports & adapters pattern.
```

**Meaning:** Actionable warnings. Flagged issues for code review.

---

## Usage Examples (What TEST-DESIGNER Tests)

### Example 1: Clear Layered Architecture

```python
result = detector.detect()
# result.confidence = 0.87
# evidence includes [METRIC], [CONFIDENCE], [LAYER], [ANALYSIS], [REASONING]
# Reviewable at every level
```

### Example 2: Ambiguous Architecture + Cycles

```python
result = detector.detect()
# result.confidence = 0.54 (reduced from 0.69 by cycle penalty)
# evidence includes:
#   [CYCLE_COUNT] 3
#   [CONFIDENCE_PENALTY] 0.15
#   [REASONING] ...explains why confidence is lower
# Fully transparent degradation
```

### Example 3: Low-Confidence Result

```python
result = detector.detect()
# result.style = 'flat'  (highest, but still low)
# result.confidence = 0.42
# result.alternative = None  (all styles scored low)
# evidence includes [WARNING] "No clear architectural pattern detected"
# User knows: this repo needs architectural analysis by humans
```

---

## Evidence Format Guarantees

### What TEST-DESIGNER Must Verify

1. **Completeness:** Every detection produces evidence with all 10 categories (where applicable)
2. **Parsability:** Evidence strings with `[TAG]` prefix can be programmatically extracted
3. **Accuracy:** Metrics in evidence match actual graph measurements (verified by test)
4. **Consistency:** Same repo always produces same evidence (determinism check)
5. **Explainability:** Every metric and score is justified in reasoning section
6. **Auditability:** Code reviewers can trace from confidence score back to raw metrics

---

## Evidence Storage (Existing API, No Changes)

```python
# Current storage in ArchitectureModelStore
model_json = {
    "style": "layered",
    "style_confidence": 0.87,
    "evidence": [
        "[METRIC] layering_score: 0.92",
        "[METRIC] cohesion_score: 0.56",
        ...  # Full evidence list stored as-is
    ],
    "layers": [...],
    "subsystems": [...],
}
```

**No API changes.** Evidence is stored in existing `evidence` field as list[str].

---

## Summary: Explainability Checklist

For task-005 to be considered fully explainable:

- [x] Every architecture detection produces a confidence score (0.0–1.0)
- [x] Confidence breakdown shows all 5 style scores
- [x] Metrics (layering, cohesion, modularity) are included in evidence
- [x] Layer structure is documented with per-layer confidence
- [x] Subsystem membership and coupling is documented
- [x] Cycles (if any) are explicitly listed and penalty explained
- [x] Scoring formula is traced step-by-step in reasoning section
- [x] Warnings flag limitations and recommended actions
- [x] Result is deterministic (same repo → same evidence)
- [x] Reviewers can audit every decision via evidence list

---

**Prepared by:** ARCHITECT  
**Status:** Refinement — Evidence model documented, API unchanged
