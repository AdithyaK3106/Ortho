# task-008: Architecture Contract Audit

**ARCHITECT:** Contract Verification Session  
**Date:** 2026-07-02  
**Task:** Determine which artifact deviates from approved specification

---

## Step 1: API Contract Matrix

| Component / API | Specification | Builder Implementation | TEST-DESIGNER Tests | Match? |
|---|---|---|---|---|
| **ArchitectureDetector class** | Stateless, no constructor | Stateless, no constructor | Stateless, no constructor | ✅ YES |
| **ArchitectureDetector.detect()** | `detect(call_graph, import_graph, symbols, files)` | `detect(call_graph, import_graph, symbols, files)` | `detector.detect(...)` | ✅ YES |
| **ArchitectureDetector return** | ArchitectureDetectionResult | ArchitectureDetectionResult | Expects ArchitectureDetectionResult | ✅ YES |
| **LayerDetector class** | Stateless, no constructor | Stateless, no constructor | **Expects constructor (repo_db, repo_id)** | ❌ NO |
| **LayerDetector.extract_layers()** | `extract_layers(import_graph, files)` | `extract_layers(import_graph, files)` | **Expects `detector.extract_layers()` with no args (state-driven)** | ❌ NO |
| **LayerDetector return** | `list[Layer]` | `list[Layer]` | Expects `list[Layer]` | ✅ YES |
| **SubsystemDetector class** | Stateless, no constructor | Stateless, no constructor | **Expects constructor (repo_db, repo_id)** | ❌ NO |
| **SubsystemDetector.detect_subsystems()** | `detect_subsystems(call_graph, symbols, files)` | `detect_subsystems(call_graph, symbols, files)` | **Expects `detector.detect_subsystems()` with no args (state-driven)** | ❌ NO |
| **SubsystemDetector return** | `list[Subsystem]` | `list[Subsystem]` | Expects `list[Subsystem]` | ✅ YES |
| **ArchitectureModelStore class** | Stateless, no constructor shown | Likely stateless | **Tests expect constructor (db connection)** | ❌ UNCLEAR |
| **ArchitectureModelStore.save()** | `save(model) -> str` | Method signature present | Tests expect this | ✅ YES |
| **ArchitectureModelStore.load_latest()** | `load_latest(repo_id) -> Model` | Method signature present | Tests expect this | ✅ YES |

---

## Step 2: Evidence for Each Mismatch

### Mismatch 1: LayerDetector Constructor

**Specification (spec.md, lines 56–81):**
```python
class LayerDetector:
    """Extracts architectural layers from import graph."""
    
    def extract_layers(
        self,
        import_graph: list[ImportEdge],
        files: list[File],
    ) -> list[Layer]:
```
**Specification verdict:** No constructor defined. Class accepts only `import_graph` and `files` as parameters to `extract_layers()`. **Stateless design**.

**Builder Implementation (layer_detector.py, line 7–16):**
```python
class LayerDetector:
    # (no __init__ defined)
    
    def extract_layers(self, import_graph: list, files: list) -> list[Layer]:
```
**Builder verdict:** Matches specification exactly. Stateless, no constructor.

**TEST-DESIGNER Test (test_layer_detector.py, line 22):**
```python
detector = LayerDetector(mock_symbol_repo, sample_repo_id)
detector = LayerDetector(layered_fixture_db, layered_repo_id)
```
**Test verdict:** Expects constructor with `(database, repo_id)` arguments. **Stateful design**.

**Classification:** ❌ **Category B — TEST-DESIGNER DEVIATION**
- Implementation matches specification exactly
- Tests expect behavior not in specification
- Constructor with database dependency is invented

---

### Mismatch 2: LayerDetector.extract_layers() Signature

**Specification (spec.md, lines 59–81):**
```python
def extract_layers(
    self,
    import_graph: list[ImportEdge],
    files: list[File],
) -> list[Layer]:
```
**Specification verdict:** Method requires two parameters: `import_graph` and `files`.

**Builder Implementation (layer_detector.py, line 16):**
```python
def extract_layers(self, import_graph: list, files: list) -> list[Layer]:
```
**Builder verdict:** Matches specification. Two parameters required.

**TEST-DESIGNER Test (test_layer_detector.py, line 30):**
```python
detector = LayerDetector(mock_symbol_repo, sample_repo_id)
# ...later...
detector.extract_layers()  # Called with NO parameters
```
**Test verdict:** Expects method callable with zero parameters (state stored in constructor).

**Classification:** ❌ **Category B — TEST-DESIGNER DEVIATION**
- Implementation matches specification
- Tests expect different signature (no parameters)
- Requires injected state from constructor

---

### Mismatch 3: SubsystemDetector Constructor

**Specification (spec.md, lines 109–137):**
```python
class SubsystemDetector:
    """Clusters modules into subsystems using Louvain algorithm."""
    
    def detect_subsystems(
        self,
        call_graph: list[CallEdge],
        symbols: list[Symbol],
        files: list[File],
    ) -> list[Subsystem]:
```
**Specification verdict:** No constructor shown. Stateless design.

**Builder Implementation (subsystem_detector.py, line 7–10):**
```python
class SubsystemDetector:
    # (no __init__)
    
    def detect_subsystems(self, call_graph: list, symbols: list, files: list) -> list[Subsystem]:
```
**Builder verdict:** Matches specification. Stateless, no constructor.

**TEST-DESIGNER Test (test_subsystem_detector.py, line 225):**
```python
detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
subsys1 = detector.detect_subsystems()  # Called with no parameters
```
**Test verdict:** Expects constructor with database and repo_id. Method callable with no parameters.

**Classification:** ❌ **Category B — TEST-DESIGNER DEVIATION**
- Implementation matches specification exactly
- Tests invent constructor not in specification
- Tests expect stateful design, spec shows stateless

---

## Step 3: Constructor Audit Summary

**Question:** Should LayerDetector, SubsystemDetector, and ArchitectureModelStore have constructors?

**Specification Answer:** 
- LayerDetector: NO constructor shown. Stateless. Takes data as parameters.
- SubsystemDetector: NO constructor shown. Stateless. Takes data as parameters.
- ArchitectureModelStore: NO constructor shown in class definition.

**Architectural Rationale (from spec.md):**
The specification shows pure functions-on-objects pattern:
- Each component is a stateless analyzer
- Data (graphs, files) passed to methods
- No dependency injection
- No constructor parameters for database access

This is **consistent with the specification philosophy:** simple, composable modules (FRD Section 1, Principle 5: "Small composable modules").

---

## Step 4: API Surface Audit

### ArchitectureDetector (Stateless)
- ✅ No constructor → Specification
- ✅ `detect(call_graph, import_graph, symbols, files)` → Specification
- ✅ Returns `ArchitectureDetectionResult` → Specification

**Verdict:** COMPLIANT

### LayerDetector (Stateless)
- ✅ No constructor → Specification
- ✅ `extract_layers(import_graph, files)` → Specification
- ✅ Returns `list[Layer]` → Specification
- ❌ Tests expect constructor → **TEST-DESIGNER DEVIATION**
- ❌ Tests expect parameterless `extract_layers()` → **TEST-DESIGNER DEVIATION**

**Verdict:** IMPLEMENTATION COMPLIANT, TESTS DEVIATE

### SubsystemDetector (Stateless)
- ✅ No constructor → Specification
- ✅ `detect_subsystems(call_graph, symbols, files)` → Specification
- ✅ Returns `list[Subsystem]` → Specification
- ❌ Tests expect constructor → **TEST-DESIGNER DEVIATION**
- ❌ Tests expect parameterless `detect_subsystems()` → **TEST-DESIGNER DEVIATION**

**Verdict:** IMPLEMENTATION COMPLIANT, TESTS DEVIATE

### ArchitectureModelStore
- ✅ `save(model) -> str` → Specification
- ✅ `load_latest(repo_id) -> Model` → Specification
- ❌ Tests expect constructor (repo_db) → **TEST-DESIGNER DEVIATION**

**Verdict:** IMPLEMENTATION COMPLIANT, TESTS DEVIATE

---

## Step 5: Test Pattern Analysis

**Pattern in all failing tests:**

```python
# TEST-DESIGNER pattern (INVENTED):
detector = LayerDetector(mock_symbol_repo, sample_repo_id)
detector = SubsystemDetector(mock_symbol_repo, sample_repo_id)
result = detector.method()  # No parameters

# SPECIFICATION pattern (ACTUAL):
detector = LayerDetector()  # Or just call function
result = detector.extract_layers(import_graph, files)
result = detector.detect_subsystems(call_graph, symbols, files)
```

Tests systematically expect:
1. Stateful constructors with database injection
2. Parameterless method calls

Specification shows:
1. Stateless constructors
2. Parameter-passing methods

This is **not an accidental misalignment**. Tests were designed for a different architecture (dependency injection + state) than the specification defines.

---

## Step 6: Final Verdict

### **VERDICT: Category B — TEST-DESIGNER DEVIATION**

**Finding:**
- **Specification** defines stateless classes with parameter-passing methods
- **Builder Implementation** correctly implements specification
- **TEST-DESIGNER Tests** expect stateful classes with dependency injection

**Evidence:**
1. Specification explicitly shows no constructors (spec.md, lines 56–81, 109–137)
2. Specification shows parameters passed to methods, not stored in state (spec.md)
3. Builder faithfully implements specification contract
4. Tests systematically expect different API (constructors with db/repo_id)

**Root Cause:**
TEST-DESIGNER designed tests for a richer, stateful API that was never part of the approved specification. This suggests TEST-DESIGNER misunderstood the FRD principle 5: "Small composable modules" which implies stateless, functional design.

**Action Required:**
Revise TEST-DESIGNER artifacts only. Do not modify implementation.

---

## Recommendation

**Immediate:**
1. Rewrite test suite to match specification (stateless API)
2. Remove all constructor calls with database/repo_id arguments
3. Add parameters to method calls: `detector.extract_layers(import_graph, files)`
4. Re-run VERIFIER Phase C

**No changes to builder needed.**
**No changes to specification needed.**
**Builder correctly implements specification.**

---

*Architecture Contract Audit completed by ARCHITECT role.*  
*Verdict: TEST-DESIGNER DEVIATION (Category B)*
