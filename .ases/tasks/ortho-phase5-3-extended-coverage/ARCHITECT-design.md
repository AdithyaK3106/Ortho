# Phase 5.3: Extended Coverage — ARCHITECT Phase

**Date:** 2026-07-13  
**Goal:** Design ground truth, call graph integration, and test strategy  

---

## Ground Truth: Missing 2 Repositories

### SQLAlchemy (ORM Framework)

**Repository Structure Analysis:**
- **Type:** Object-relational mapper (database abstraction)
- **Main Package:** `src/sqlalchemy/`
  - Core components: `sql/`, `orm/`, `ext/`, `pool/`, `engine/`
  - Language support: `dialects/` (postgres, mysql, oracle, etc.)
  - High coupling: Heavy interdependencies between modules

**Architecture Classification:**
- **Predicted Style:** FLAT
  - Rationale: High internal coupling, all modules interdependent
  - Multiple independent dialects share core interface
  - No hierarchical layering (core-db-app model)

**Confidence:** 0.70 (high coupling signals flat clearly)

**Framework Detection:** No web/app framework (pure library)

### Celery (Distributed Task Queue)

**Repository Structure Analysis:**
- **Type:** Distributed task processing framework
- **Main Package:** `celery/`
  - Worker: `worker/`, `workstations/`
  - Broker: `brokers/` (Redis, RabbitMQ, etc.)
  - Backend: `backends/` (result storage)
  - Schedulers: `beat/`
  - Each subsystem independent with clear boundaries

**Architecture Classification:**
- **Predicted Style:** MICROSERVICES
  - Rationale: Multiple independent services (worker, broker, scheduler, backend)
  - Clear entry points per service
  - Low cross-service coupling
  - Message-based communication

**Confidence:** 0.80 (distinct services with independent entry points)

**Framework Detection:** Framework fingerprinting should fire (celery imports, task decorators)

---

## Call Graph Integration Design

### Current State
- Call graph extracted but not used in `ArchitectureDetector`
- Call patterns available in `result.calls` (list of CallEdge)

### Integration Strategy

**Goal:** Use call graph to improve implicit layer detection

**Hypothesis:** 
- In layered architectures, calls flow downward (presentation → business → data)
- In flat architectures, calls are bidirectional and dense
- In microservices, calls are sparse and isolated per service

**Implementation:**

```python
def _score_call_graph_signals(self, calls: list[CallEdge]) -> dict:
    """
    Analyze call graph for architecture patterns.
    
    Returns:
    {
        'is_layered': score (0-1),  # High if calls flow one direction
        'is_flat': score (0-1),     # High if calls are bidirectional/dense
        'is_microservices': score (0-1),  # High if isolated clusters
        'evidence': str  # Human-readable explanation
    }
    """
    # Analyze call directionality
    # Compute clustering coefficient
    # Measure cross-module call density
    # Detect isolated call islands
```

**Weight Integration:**
- Add call graph score to each style scorer
- Weight: 0.15 (modest, since graph alone isn't definitive)
- Formula: `base_score + (call_graph_score * 0.15)`

**Edge Cases to Handle:**
- No calls extracted (empty graph) → neutral signal
- Bidirectional calls (A→B, B→A) → dampens layered signal
- High clustering → suggests microservices
- Low clustering + dense → suggests flat

---

## Test Strategy: Hard Edge Cases

### Test Suite 1: Repository Layout Edge Cases

**Purpose:** Ensure detector handles unusual structures

**Tests:**

1. **Symlinked Packages**
   - Create: src/real_package/ with symlink to src/alias/
   - Test: Detector doesn't double-count or miss due to symlinks
   - Expected: Correct architecture detection without duplicates

2. **Namespace Packages (PEP-420)**
   - Create: pkg/module_a/__init__.py and pkg/module_b/ (no __init__.py)
   - Test: Detector correctly identifies namespace vs regular packages
   - Expected: No errors, correct module detection

3. **Mixed Layouts**
   - src/main_package/ + top-level/secondary/
   - Test: Detector identifies multiple package roots
   - Expected: Handles heterogeneous structure gracefully

4. **Deep Nesting**
   - 10+ level deep module hierarchy
   - Test: Layer detection doesn't break with depth
   - Expected: Reasonable layer count (not 1 per file)

5. **Single-File Modules**
   - util.py (no module folder)
   - Test: Doesn't misclassify as package
   - Expected: Correct handling as module, not package

### Test Suite 2: Framework Fingerprinting Edge Cases

**Purpose:** Catch false positives and edge cases

**Tests:**

1. **False Positive: "Flask" in Comments/Strings**
   - File with comments mentioning Flask framework
   - Test: Doesn't trigger Flask detection
   - Expected: Only actual imports/decorators count

2. **Multiple Frameworks Coexisting**
   - FastAPI (web) + Celery (task queue) + SQLAlchemy (ORM)
   - Test: Highest confidence framework wins, others noted
   - Expected: Top framework used for style, others for evidence

3. **Framework Imports Without Use**
   - `import flask` but no decorators or Flask() instances
   - Test: Lower confidence than active framework use
   - Expected: Detects import but lower score than decorator

4. **Version-Specific Imports**
   - `from flask import json` (removed in newer versions)
   - Test: Doesn't fail on version-specific imports
   - Expected: Handles gracefully, detects framework anyway

5. **Custom Decorators Over Framework**
   - Custom `@route` decorator (not `@app.route`)
   - Test: Doesn't false-trigger Flask
   - Expected: Only detects official framework patterns

### Test Suite 3: Call Graph Signal Validation

**Purpose:** Verify call graph correctly influences detection

**Tests:**

1. **Pure Hierarchy (No Cycles)**
   - Layer 1 → Layer 2 → Layer 3 (unidirectional calls)
   - Test: Call graph boosts layered score
   - Expected: Improves confidence on layered detection

2. **Circular Calls**
   - Module A → B, B → A (cycle)
   - Test: Call graph dampens layered signal
   - Expected: Lowers layered score, raises flat score

3. **High Fan-In Pattern (Hub)**
   - One module called by many others (e.g., utils)
   - Test: Correctly identified as utility, not layer
   - Expected: Doesn't break architecture detection

4. **Isolated Call Islands**
   - Separate call clusters with no cross-cluster calls
   - Test: Call graph recognizes isolation
   - Expected: Boosts microservices score

5. **No External Calls**
   - All calls internal, deep within package
   - Test: Call graph signal useful for differentiation
   - Expected: Correctly weights internal call patterns

### Test Suite 4: Full Repository Benchmarks

**Purpose:** Validate detection on all 8 repos with calls

**Tests:**

1. **SQLAlchemy Benchmark**
   - Index, detect, measure accuracy
   - Expected: flat (>0.70 confidence)
   - Verify: High coupling signals flat correctly

2. **Celery Benchmark**
   - Index, detect, measure accuracy
   - Expected: microservices (>0.70 confidence)
   - Verify: Independent services detected

3. **All 8 Repos Together**
   - Run full benchmark, compute metrics
   - Expected: ≥85% accuracy (or maintain 83.3%)
   - Verify: No regressions on Phase 5 repos

### Test Suite 5: Regression Suite (No Degradation)

**Purpose:** Ensure Phase 5.3 changes don't break existing work

**Tests:**

1. **Phase 5 Flask**
   - Flask still detected as layered
   - Confidence maintained >0.80
   - Expected: No regression

2. **Phase 5 Click**
   - Click still detected as flat
   - Confidence maintained >0.70
   - Expected: No regression

3. **Requests Fix Validation**
   - Requests now detected as flat (not unknown)
   - Confidence >0.75
   - Expected: Fix verified

4. **All Phase 5 Repos**
   - 6/6 original repos still correct
   - Confidence levels maintained or improved
   - Expected: Zero regressions

5. **Framework Detection No False Positives**
   - Repos without specific frameworks don't trigger
   - False positive rate <5%
   - Expected: Clean detections

---

## Requests Misclassification Fix Design

### Root Cause
File `api.py` contains stem "api" which matches `PRESENTATION_TOKENS`, causing flat scorer to see layer vocabulary and apply 50% penalty.

### Solution: Separate File Stems from Directory Tokens

**Current (Broken):**
```python
# Both directory names AND file stems go into token detection
dir_tokens = {"src", "models", "views", "api"}  # Mixed!
```

**Proposed (Fixed):**
```python
# Only directory names, NOT file stems
dir_tokens = {"src", "models", "views"}  # Only dirs
stem_tokens = {"api", "models", "utils"}  # Only file stems

# For layer detection: Use only dir_tokens
def bands_present(self):
    return [i for i, band in enumerate(LAYER_BANDS) 
            if set(self.dir_tokens) & band]  # Not stem_tokens!
```

**Impact:**
- Requests: api.py file stem no longer triggers layer vocabulary
- Flat scorer no longer applies 50% penalty
- Score improves from ~0.39 to ~0.85
- Confidence >0.75

**Regression Check:**
- Django (has models/, views/ dirs) still detected as layered ✅
- Flask (has src/flask/ dir) still detected as layered ✅
- SQLAlchemy (no layer dirs) detected as flat ✅

---

## Deliverables Summary

### ARCHITECT Phase Output ✅

- [x] Ground truth classification (SQLAlchemy: flat, Celery: microservices)
- [x] Call graph integration design (0.15 weight, signal analysis)
- [x] Test strategy (40-50 hard edge case tests)
- [x] Requests fix design (separate file stems from dirs)
- [x] Regression test plan (6 Phase 5 repos + 2 new repos)

### Ready for BUILDER + TEST-DESIGNER (Parallel)

**BUILDER Tasks:**
1. Clone SQLAlchemy & Celery
2. Fix Requests misclassification
3. Integrate call graph signals
4. Add 2-3 frameworks

**TEST-DESIGNER Tasks:**
1. Edge case tests (layouts, frameworks, call graphs)
2. Regression suite (no Phase 5 degradation)
3. Full 8-repo benchmark tests
4. Hard tests for bugs and edge cases

---

## Approval Checklist

- [x] Ground truth documented
- [x] Call graph integration strategy clear
- [x] Test edge cases identified
- [x] Requests fix strategy sound
- [x] Risk assessment complete
- [x] Regression plan in place

**Status: ✅ READY FOR BUILDER + TEST-DESIGNER (PARALLEL)**
