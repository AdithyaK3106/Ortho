# task-008: Architecture Detection — Specification

**Task ID:** task-008  
**Objective:** Implement Pillar 3 architecture detection: pattern recognition, layer extraction, subsystem clustering with confidence scoring  
**Phase:** Phase 2 (Weeks 9–10)  
**FRD Reference:** Section 8 (Architectural Intelligence)

---

## Overview

Architecture detection analyzes a repository's call graph and import graph to infer structural patterns. Output is an ArchitectureModel with:
- Detected style (layered | hexagonal | mvc | microservices | flat)
- Confidence score (0.0–1.0)
- Extracted layers and subsystems
- Evidence list justifying the detection

---

## Component Contracts

### ArchitectureDetector

```python
class ArchitectureDetector:
    """Analyzes call/import graphs to detect architectural style."""
    
    def detect(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        files: list[File],
    ) -> ArchitectureDetectionResult:
        """
        Analyze graphs and return detected style with confidence.
        
        Returns: ArchitectureDetectionResult
          - style: One of [layered, hexagonal, mvc, microservices, flat]
          - confidence: 0.0–1.0 (higher = more certain)
          - evidence: List of justifications (e.g., "5 layers detected", "acyclic dependencies")
          - alternative: Optional secondary hypothesis
        """
        ...
```

**Input:** Call graph, import graph, symbol registry, file manifest  
**Output:** ArchitectureDetectionResult with style, confidence, evidence  
**Constraints:** Must work on repos 50–5000 files; complete in <5 seconds

---

### LayerDetector

```python
class LayerDetector:
    """Extracts architectural layers from import graph."""
    
    def extract_layers(
        self,
        import_graph: list[ImportEdge],
        files: list[File],
    ) -> list[Layer]:
        """
        Use topological sort to extract layers from import DAG.
        
        Layer numbering convention (depth-first):
        - Layer 0: Data layer (lowest-level, no outgoing dependencies)
        - Layer 1: Business logic layer (depends on Layer 0)
        - Layer 2: Presentation layer (highest-level, depends on Layers 0–1)
        
        Dependencies flow inward: Layer 2 → Layer 1 → Layer 0 (no reverse edges)
        
        Semantic naming: Look for keywords (controller, view, service, repository, model, db)
        - "repository|model|db" → Layer 0
        - "service|business|logic" → Layer 1
        - "controller|view|endpoint|handler" → Layer 2
        
        Returns: Ordered list of layers [Layer 0, Layer 1, Layer 2, ...]
        """
        ...
```

**Layer Numbering Convention (Consistent Throughout):**

| Layer | Name | Example Modules | Dependency Direction |
|-------|------|-----------------|----------------------|
| 0 | Data | repository, model, db, dao | No outgoing (depends on nothing) |
| 1 | Business | service, logic, domain, core | Depends only on Layer 0 |
| 2 | Presentation | controller, view, endpoint, handler | Depends on Layers 0–1 |
| N | (if present) | External interfaces | Depends on Layers 0–(N-1) |

**Algorithm:**
1. Build import DAG from import graph (ignore external imports)
2. Topological sort: assign layer depth where Layer 0 has no incoming edges
3. Semantic naming: categorize files based on naming keywords to infer layer purpose
4. Validate: all dependencies flow toward Layer 0 (no backward edges allowed)
5. Return layers ordered from Layer 0 (deepest) to Layer N (shallowest)

**Validation:** Layered architecture := all dependencies form acyclic dependency chain where each layer only imports from lower-numbered layers.

**Output:** list[Layer] with layer number, name (inferred), file_ids, depends_on (layers this layer imports from)

---

### SubsystemDetector

```python
class SubsystemDetector:
    """Clusters modules into subsystems using Louvain algorithm."""
    
    def detect_subsystems(
        self,
        call_graph: list[CallEdge],
        symbols: list[Symbol],
        files: list[File],
    ) -> list[Subsystem]:
        """
        Apply Louvain clustering to call graph.
        
        Coupling score: measure intra-subsystem vs inter-subsystem calls
          coupling = (inter_calls) / (intra_calls + inter_calls)
          Range: 0.0 (tight cohesion) to 1.0 (loose coupling)
        
        Returns: Subsystems with names (inferred from file paths), 
                 member files, coupling score
        """
        ...
```

**Algorithm:**
1. Convert call graph to NetworkX graph (nodes = symbols, edges = call edges)
2. Run Louvain community detection (networkx.community.louvain_communities)
3. For each community: compute coupling score
4. Infer subsystem name from file paths (common prefix or directory name)

**Output:** list[Subsystem] with id, name, file_ids, coupling_score

---

### ArchitectureModelStore

```python
class ArchitectureModelStore:
    """Persists architecture models to SQLite."""
    
    def save(self, model: ArchitectureModel) -> str:
        """Store model with timestamp. Returns model_id."""
        ...
    
    def load_latest(self, repo_id: str) -> ArchitectureModel | None:
        """Load most recent model for repo."""
        ...
    
    def load_all_versions(self, repo_id: str) -> list[ArchitectureModel]:
        """Load all versions (time-series)."""
        ...
```

**Schema:**
```sql
CREATE TABLE architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    style TEXT NOT NULL,
    style_confidence REAL NOT NULL,
    evidence TEXT NOT NULL,  -- JSON array of strings
    model_json TEXT NOT NULL,  -- Full ArchitectureModel serialized
    detected_at TEXT NOT NULL  -- ISO 8601
);
```

---

## Confidence Model (Complete Specification)

### Overview

Confidence reflects uncertainty in architecture detection. The model aggregates structural evidence into a single score (0.0–1.0) for each candidate architecture, then selects the winner.

---

### Signal Aggregation

Each architecture detector analyzes multiple signals:

**Structural Signals:**
- Import graph shape (DAG, cycles, depth, breadth)
- Call graph density (intra-module vs. inter-module calls)
- Module isolation (coupling score)

**Semantic Signals:**
- File naming patterns (controller, service, repository, etc.)
- Directory organization (flat, nested, separated concerns)
- Module naming conventions matching architecture

**Quality Signals:**
- Layer acyclicity (layered pattern)
- Subsystem cohesion (microservices pattern)
- Clear boundary definition (hexagonal pattern)

### Score Normalization

All detectors produce raw evidence scores. Normalization ensures comparability:

1. **Raw evidence accumulation** — Each detector collects signals (e.g., "3 layers found", "acyclic dependencies", "semantic naming matched")
2. **Base score assignment** — Detector assigns base confidence (0.6–0.8) if core signals present
3. **Bonus/penalty application** — Add bonuses (+0.05 to +0.25) for strong evidence, penalties (-0.05 to -0.25) for weak/contradictory evidence
4. **Clamp to range** — Final score clamped to [0.0, 1.0]

**Result:** Each architecture has a score in [0.0, 1.0]. Scores are directly comparable.

---

### Winner Selection Algorithm

**Step 1: Calculate all detector scores**

For each of the 5 architectures (layered, hexagonal, mvc, microservices, flat):
- Run detector
- Accumulate evidence
- Produce score in [0.0, 1.0]

**Step 2: Identify winner**

Select architecture with highest score.

```
winner = argmax(score[layered], score[hexagonal], score[mvc], score[microservices], score[flat])
winner_confidence = score[winner]
```

**Step 3: Identify secondary hypothesis**

Select second-highest score (if distinct from winner).

```
alternative = architecture with 2nd highest score
alternative_confidence = score[alternative]
```

**Step 4: Apply margin threshold**

If winner and alternative scores differ by <0.15, mark as "ambiguous" (multiple plausible architectures).

---

### Tie Handling (Deterministic)

**Case 1: Perfect Tie (two architectures score identically)**

**Rule:** Deterministic tie-breaking using priority order:
1. Layered (most common, easiest to evolve)
2. MVC (well-established pattern)
3. Hexagonal (explicit boundary pattern)
4. Microservices (requires high separation)
5. Flat (default, least structured)

**Implementation:**
```python
TIE_BREAKER_ORDER = ["layered", "mvc", "hexagonal", "microservices", "flat"]

if len(tied_architectures) > 1:
    for arch in TIE_BREAKER_ORDER:
        if arch in tied_architectures:
            return arch
```

**Case 2: Close Scores (difference < 0.10)**

**Rule:** Report top candidate but flag confidence as "low" in evidence justification.

**Implementation:**
```python
confidence_quality = "high" if (winner_score - alternative_score) >= 0.10 else "low"
evidence.append(f"Confidence: {confidence_quality} (margin: {winner_score - alternative_score:.2f})")
```

**Case 3: No Clear Winner (all scores < 0.50)**

**Rule:** Return "flat" (least structured) with confidence <0.50 and evidence: "no clear architectural pattern detected".

---

### Evidence Justifications

Every detection includes an evidence list explaining the score:

**Examples:**

**Layered (confidence 0.88):**
- "3 acyclic import layers detected (data, business, presentation)"
- "Semantic naming matches layer structure: 12/15 files correctly categorized"
- "No reverse dependencies within import graph"
- "Layer coupling score: 0.15 (high cohesion)"

**Microservices (confidence 0.65):**
- "5 subsystems detected via Louvain clustering"
- "Average inter-subsystem coupling: 0.28"
- "3 subsystems with clear module boundaries"
- "Note: One subsystem tightly coupled (coupling=0.72); impairs confidence"

**Flat (confidence 0.42):**
- "No clear layer structure detected"
- "High import coupling throughout codebase (avg 0.58)"
- "Multiple naming conventions mixed (no semantic signal)"
- "Fallback pattern; low confidence reflects lack of clear structure"

---

## Pattern Detection Rules

### Layered Pattern
**Signal:** Import graph forms clear acyclic dependency layers where each layer only imports lower-numbered layers.

**Detectors:**
- Extract layers via topological sort (Layer 0 = no incoming edges)
- Verify acyclic: no dependencies between same layer, no backward imports to higher layers
- Count distinct layers (3+ layers typical for layered architecture)
- Check semantic naming (data/service/controller keywords match layer numbering)

**Confidence Calculation:**
- **Base:** 0.6 (if acyclic and 3+ layers found)
- **+0.15** if semantic naming matches layers (repository files in Layer 0, controllers in Layer 2, etc.)
- **+0.10** if layer count is 3–4 (typical layered pattern)
- **-0.20** if mixed naming or unclear layer boundaries
- **-0.25** if any backward dependencies detected
- **Result Range:** 0.5–0.95 (after penalties/bonuses applied)

### Hexagonal Pattern (Ports & Adapters)
**Signal:** Clear internal domain separated from external adapters.

**Detectors:**
- Identify core modules (internal subsystem with few external imports)
- Identify adapter modules (high external dependency %, isolated from core)
- Verify adapter isolation (minimal inter-adapter calls)

**Confidence Calculation:**
- **Base:** 0.65 (if core + 2+ adapters identified)
- **+0.15** if adapters isolated (low inter-adapter coupling <0.20)
- **+0.10** if core domain has clear semantic naming (business, domain, core keywords)
- **-0.15** if adapters tightly coupled (interdependencies >0.40)
- **-0.20** if core is unclear (high internal coupling or unclear boundaries)
- **Result Range:** 0.40–0.90

### MVC Pattern
**Signal:** Separation of Model, View, and Controller concerns.

**Detectors:**
- Model modules (data, domain classes; high incoming edges; few outgoing)
- View modules (UI, rendering; few dependencies; consume models)
- Controller modules (business logic; medium coupling; bridge model-view)

**Confidence Calculation:**
- **Base:** 0.70 (if MVC-like subsystems detected)
- **+0.15** if semantic naming matches (model, controller, view keywords)
- **+0.10** if dependency directions correct (controller → model, view → model, no reverse)
- **-0.15** if naming ambiguous or mixed
- **-0.20** if dependencies entangled (circular or unclear)
- **Result Range:** 0.35–0.95

### Microservices Pattern
**Signal:** Multiple independent subsystems with tight cohesion and loose coupling.

**Detectors:**
- Louvain clustering identifies subsystems
- Measure subsystem coupling (intra vs. inter-module calls)
- Verify independence (limited cross-subsystem dependencies)

**Confidence Calculation:**
- **Base:** 0.60 (if 3+ subsystems detected)
- **+0.20** if average inter-subsystem coupling <0.25 (highly independent)
- **+0.10** if subsystem count is 4–8 (typical microservices count)
- **-0.10** if only 3 subsystems (borderline)
- **-0.20** if average coupling >0.40 (too tightly coupled)
- **Result Range:** 0.30–0.90

### Flat Pattern
**Signal:** No clear structure; absence of layering, separation, or subsystems.

**Detectors:**
- Check for lack of layers (single topological level)
- Check for high coupling (>0.50 average)
- Check for no subsystem isolation (Louvain finds single community)

**Confidence Calculation:**
- **Base:** 0.55 (if lack of structure confirmed)
- **+0.15** if confirmed high coupling (>0.60)
- **+0.10** if single subsystem (no natural clustering)
- **-0.15** if clear patterns emerge (contradicts flat)
- **-0.20** if can be classified as another architecture
- **Result Range:** 0.20–0.80
- **Note:** Flat is often a fallback when no other pattern fits. Lower confidence is expected.

---

## Validation Strategy

### Overview

Validation uses two complementary fixture categories: **synthetic graphs** for deterministic testing, and **real repositories** for robustness validation.

---

### Synthetic Fixtures (Unit & Regression)

**Purpose:** Deterministic validation of algorithm correctness and edge cases.

**Characteristics:**
- Known graph structure (DAG, cycles, specific patterns)
- Predictable output (expected layers, subsystems, scores)
- Isolated algorithm testing (no external dependencies)
- Fast execution (<100ms per test)

**Fixtures:**
- Layered DAG (3 layers, acyclic, clearly named)
- Hexagonal graph (core + 2 adapters, clear boundaries)
- MVC structure (models, views, controllers with expected edges)
- Microservices clustering (4–5 subsystems, minimal cross-subsystem calls)
- Flat/undifferentiated (single community, high coupling)
- Edge cases (empty graph, single module, fully connected, cyclic)

**Test Approach:**
```python
def test_layered_detector_on_known_structure():
    # Known graph with 3 layers
    graph = synthetic_layered_3_layer_graph()
    result = arch_detector.detect(call_graph=graph, ...)
    assert result.style == "layered"
    assert result.confidence >= 0.80  # High confidence for clean synthetic case
    assert "3 acyclic layers" in result.evidence[0]
```

**Regression Value:** Catches algorithm breakage early. If synthetic tests pass but real-repo tests fail, the issue is in handling real-world complexity, not core logic.

---

### Real Repository Fixtures (Robustness & Calibration)

**Purpose:** Validate detection against actual codebases with complex, mixed patterns.

**Characteristics:**
- Imperfect patterns (mixed naming, some violations)
- Natural complexity (real import/call graphs)
- Variable sizes (50–1000 files)
- Slower execution (1–5 seconds per analysis)

**Fixtures:** (Stored in `.../tests/fixtures/task-005-arch-detection/` and `.../Repos/`)
- fastapi (microservices-like with layered components)
- django (MVC framework)
- layered application (custom 3-layer project)
- hexagonal domain-driven design example

**Test Approach:**
```python
def test_detection_on_real_repo_fastapi():
    # Load actual repo from Repos/fastapi
    repo = load_repo("Repos/fastapi")
    call_graph = extract_call_graph(repo)
    import_graph = extract_import_graph(repo)
    
    result = arch_detector.detect(call_graph, import_graph, ...)
    
    # Confidence should be reasonable (not zero, not always 1.0)
    assert 0.40 <= result.confidence <= 1.00
    
    # Result should be interpretable
    assert result.style in ["layered", "hexagonal", "mvc", "microservices", "flat"]
    assert len(result.evidence) >= 3  # Multiple signals
```

**Benchmark Values (Informational Only):**

These values are **not** acceptance criteria; they are documented for context and calibration:

| Repository | Expected Style | Typical Confidence Range | Notes |
|------------|---|---|---|
| fastapi | microservices-like | 0.65–0.80 | Multiple subsystems, some cross-coupling |
| django | MVC | 0.70–0.85 | Clear model-view-controller separation |
| layered-example | layered | 0.80–0.95 | Clean 3-layer structure |
| hexagonal-ddd | hexagonal | 0.65–0.80 | Domain core + adapters, some blurring |

**Important:** These values guide calibration but do not constrain the detector. If real repos produce different scores, that is valid data about the patterns present in those repos, not a test failure.

---

### Validation Execution

**During BUILDER phase:**
- Run synthetic tests first (catch algorithm bugs)
- Run real-repo tests second (validate handling of complexity)
- If real-repo scores differ from benchmarks, analyze why (new data, better detector, real complexity)

**During VERIFIER phase:**
- Synthetic tests: must pass (exit 0)
- Real-repo tests: must run and produce results without crashes (no requirement on score values)

**During REVIEWER phase:**
- Confirm both synthetic and real-repo tests executed
- Check error logs for crashes or anomalies
- Verify confidence scores are plausible for given patterns

---

## Integration Points

**Input Sources:**
- `packages/repo-intelligence/src/call_graph.py` — CallGraphBuilder output
- `packages/repo-intelligence/src/import_graph.py` — ImportGraphBuilder output
- `packages/repo-intelligence/src/symbol_registry.py` — Symbol registry

**Output Consumers:**
- `packages/token-optimizer/` — Architecture-aware retrieval (Phase 4)
- `ortho analyze` CLI command

---

## Expected Test Metrics

| Category | Count | Notes |
|----------|-------|-------|
| Pattern detector unit tests | 25+ | 5 per detector × 5 patterns |
| Layer extraction tests | 10+ | Topological sort, naming, acyclic validation |
| Subsystem clustering tests | 10+ | Louvain clustering, coupling score accuracy |
| Persistence tests | 8+ | Save/load/versioning |
| Integration tests | 12+ | Full orchestration, CLI end-to-end |
| **Total** | **65+** | |
| **Expected coverage** | **≥85%** | Code + branch coverage |
| **Expected pass rate** | **100%** | No failures or pre-approved xfail |

---

## Success Criteria

✓ **AC1:** Five pattern detectors identify patterns with calibrated confidence  
✓ **AC2:** Layer detection correctly topologically sorts and names layers  
✓ **AC3:** Subsystem clustering produces stable, accurate results  
✓ **AC4:** Models persist and version correctly  
✓ **AC5:** Zero regressions in existing test suites  

---

## Known Limitations (If Any)

None — all acceptance criteria expected to be fully implemented.

---

*Specification prepared by PLANNER role.*  
*Awaiting human review and approval at GATE 1.*
