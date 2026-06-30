# task-005: Architecture Detection — Specification
## Gate 1 Artifact

**Date:** 2026-06-30  
**Scope:** Pillar 3 — Architecture style detection, layer identification, subsystem clustering  
**Dependencies:** task-001 (shared storage), task-002 (python adapter), task-003 (call graph), task-004 (context hub)

---

## 1. Data Types

**From FRD §8 (already in shared/types):**
```python
ArchitectureModel
  repo_id: str
  style: ArchStyle  # 'layered' | 'hexagonal' | 'mvc' | 'microservices' | 'flat' | 'unknown'
  style_confidence: float  # 0.0 - 1.0
  layers: list[Layer]
  subsystems: list[Subsystem]
  detected_at: str  # ISO8601

ArchStyle = Literal['layered', 'hexagonal', 'mvc', 'microservices', 'flat', 'unknown']

Layer
  id: str
  name: str  # 'presentation', 'business', 'data', 'infrastructure', etc.
  file_ids: list[str]
  depends_on: list[str]  # Layer.id references (upward deps)
  confidence: float

Subsystem
  id: str
  name: str  # 'auth', 'payment', 'inventory', etc.
  file_ids: list[str]
  layer_id: str | None  # which layer does this subsystem belong to
  coupling_score: float  # 0.0 (loose) - 1.0 (tight internal coupling)
```

**New internal types (arch-intelligence/src/types.py):**
```python
@dataclass
class DetectionResult:
    style: ArchStyle
    confidence: float  # 0.0 - 1.0
    evidence: list[str]  # ["found 3 layers", "upward-only deps", ...]
    alternative: ArchStyle | None
    alternative_confidence: float | None

@dataclass
class DetectionMetrics:
    layering_score: float  # How much upward-only vs cross-layer deps
    cohesion_score: float  # Within-module coupling vs between-module
    modularity_score: float  # Overall module independence
    pattern_matches: dict[ArchStyle, float]  # Scores for each style
```

---

## 2. ArchitectureDetector Class

**Purpose:** Classify overall architecture style.

**Constructor:**
```python
class ArchitectureDetector:
    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self.call_graph = None  # Loaded from CallGraphBuilder (task-003)
        self.import_graph = None  # Loaded from ImportGraphBuilder (task-002)
```

**Public API:**

```python
def detect(self) -> DetectionResult:
    """
    Classify architecture style by analyzing:
    1. Import dependency patterns (upward-only = layered)
    2. Cyclic structures (hubs with spokes = hexagonal)
    3. Three-tier pattern (MVC)
    4. Independent subsystems (microservices)
    5. Everything connected (flat)
    
    Returns DetectionResult with confidence + evidence.
    """

def detect_confidence_breakdown(self) -> dict[ArchStyle, float]:
    """Return score for each style: {'layered': 0.85, 'mvc': 0.4, ...}"""
```

**Algorithm sketch:**

```python
def detect(self) -> DetectionResult:
    metrics = self._compute_metrics()
    
    # Score each pattern
    scores = {
        'layered': self._score_layered(metrics),
        'hexagonal': self._score_hexagonal(metrics),
        'mvc': self._score_mvc(metrics),
        'microservices': self._score_microservices(metrics),
        'flat': self._score_flat(metrics),
    }
    
    # Pick winner
    best_style = max(scores, key=scores.get)
    best_confidence = scores[best_style]
    
    # Pick alternative if ambiguous (top 2 within 0.1)
    sorted_styles = sorted(scores.items(), key=lambda x: -x[1])
    alternative = None
    if len(sorted_styles) > 1 and abs(sorted_styles[0][1] - sorted_styles[1][1]) < 0.15:
        alternative = sorted_styles[1][0]
    
    return DetectionResult(
        style=best_style,
        confidence=best_confidence,
        evidence=[...],  # List reasons
        alternative=alternative,
        alternative_confidence=scores.get(alternative) if alternative else None
    )
```

**Scoring functions:**

```python
def _score_layered(self, metrics: DetectionMetrics) -> float:
    """
    Layered if:
    - High upward-dependency (dependencies point down layers)
    - Low cross-layer deps
    - Clear layer structure
    """
    return (
        metrics.layering_score * 0.7 +  # Most important
        (1.0 - metrics.pattern_matches.get('microservices', 0.0)) * 0.2 +
        metrics.cohesion_score * 0.1
    )

def _score_hexagonal(self, metrics: DetectionMetrics) -> float:
    """
    Hexagonal (ports & adapters) if:
    - Core module with inbound + outbound adapters
    - Clear separation of domain from infrastructure
    """
    # High cohesion + low external coupling
    return metrics.cohesion_score * 0.8 + (1.0 - metrics.modularity_score) * 0.2

def _score_mvc(self, metrics: DetectionMetrics) -> float:
    """
    MVC if:
    - Three distinct layers (view, controller, model)
    - Upward deps (view → controller → model)
    """
    return metrics.layering_score * 0.6 + self._detect_mvc_pattern() * 0.4

def _score_microservices(self, metrics: DetectionMetrics) -> float:
    """
    Microservices if:
    - Multiple independent subsystems
    - Minimal cross-subsystem coupling
    """
    return metrics.modularity_score * 0.7 + self._detect_service_boundaries() * 0.3

def _score_flat(self, metrics: DetectionMetrics) -> float:
    """
    Flat if:
    - Everything imports everything
    - No clear layer/subsystem structure
    """
    layering = metrics.layering_score
    modularity = metrics.modularity_score
    # High score if NOT layered and NOT modular
    return (1.0 - layering) * 0.5 + (1.0 - modularity) * 0.5
```

---

## 3. LayerDetector Class

**Purpose:** Identify logical layers from import/call patterns.

```python
class LayerDetector:
    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id

    def detect_layers(self) -> list[Layer]:
        """
        1. Build dependency graph (files as nodes)
        2. Compute topological levels (DFS, longest path)
        3. Cluster files by level (same layer = same topo level)
        4. Assign semantic names based on module paths + analysis
        5. Return ordered layers (top → bottom)
        """

    def detect_layer_violations(self) -> list[str]:
        """Return list of cross-layer dependencies (violations)."""

    def _assign_semantic_names(self, layers_by_level: list[list[str]]) -> dict[int, str]:
        """
        Map level → human name:
        - Top level → 'presentation' | 'api' | 'handlers'
        - Middle → 'business' | 'domain' | 'logic'
        - Bottom → 'data' | 'repository' | 'storage'
        - Infrastructure → 'config' | 'utils' | 'infrastructure'
        """
```

**Algorithm:**

```python
def detect_layers(self) -> list[Layer]:
    graph = self._build_file_dependency_graph()
    
    # Topological sort with level assignment
    levels = {}  # file_id → level
    for file_id in topo_sort(graph):
        if not graph[file_id]:  # No incoming deps
            levels[file_id] = 0
        else:
            # Level = 1 + max(level of dependencies)
            levels[file_id] = 1 + max(levels[dep] for dep in graph[file_id])
    
    # Cluster by level
    layers_by_level = defaultdict(list)
    for file_id, level in levels.items():
        layers_by_level[level].append(file_id)
    
    # Assign names
    names = self._assign_semantic_names(sorted(layers_by_level.items()))
    
    # Build Layer objects (sorted top → bottom)
    layers = []
    for level in sorted(layers_by_level.keys(), reverse=True):
        file_ids = layers_by_level[level]
        layer = Layer(
            id=f"layer_{level}",
            name=names.get(level, f"level_{level}"),
            file_ids=file_ids,
            depends_on=[],  # Will be populated below
            confidence=self._compute_layer_confidence(file_ids, level)
        )
        layers.append(layer)
    
    # Find cross-layer dependencies (depends_on)
    for i, layer in enumerate(layers):
        for file_id in layer.file_ids:
            for dep_file_id in graph[file_id]:
                # Which layer does dep belong to?
                for j, dep_layer in enumerate(layers):
                    if dep_file_id in dep_layer.file_ids:
                        if j < i and dep_layer.id not in layer.depends_on:
                            layer.depends_on.append(dep_layer.id)
    
    return layers
```

---

## 4. SubsystemDetector Class

**Purpose:** Cluster related modules into subsystems.

```python
class SubsystemDetector:
    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id

    def detect_subsystems(self) -> list[Subsystem]:
        """
        1. Build coupling matrix (files × files)
        2. Cluster by high internal coupling (e.g., Louvain algorithm via networkx)
        3. Auto-name clusters (from common module prefix or domain keywords)
        4. Return Subsystem objects with coupling scores
        """

    def _compute_coupling_score(self, subsystem_files: list[str]) -> float:
        """
        Coupling = internal_edges / (size * (size - 1) / 2)
        where internal_edges = edges within subsystem.
        Returns 0.0 (loose) to 1.0 (tightly coupled).
        """

    def _suggest_subsystem_name(self, file_ids: list[str]) -> str:
        """
        From file paths: auth/, payment/, inventory/ → use dir name.
        From keywords: extract_* + load_* functions → 'data_pipeline'.
        Fallback: auto-number 'subsystem_0', 'subsystem_1'.
        """
```

**Algorithm:**

```python
def detect_subsystems(self) -> list[Subsystem]:
    graph = self._build_file_dependency_graph()
    
    # Community detection (Louvain)
    communities = community.louvain_communities(graph)
    
    subsystems = []
    for i, community_files in enumerate(communities):
        name = self._suggest_subsystem_name(community_files)
        coupling = self._compute_coupling_score(community_files, graph)
        
        subsystems.append(Subsystem(
            id=f"subsystem_{i}",
            name=name,
            file_ids=community_files,
            layer_id=None,  # Will be filled by LayerDetector if needed
            coupling_score=coupling
        ))
    
    return subsystems
```

---

## 5. ArchitectureModel Persistence

**Location:** `arch-intelligence/src/models.py`

```python
class ArchitectureModelStore:
    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
    
    def save(self, model: ArchitectureModel) -> str:
        """Insert/update architecture_models table. Return model_id."""
    
    def load(self, model_id: str) -> ArchitectureModel | None:
        """Retrieve by ID."""
    
    def load_latest(self) -> ArchitectureModel | None:
        """Retrieve most recent detection."""
```

**Schema:**
```sql
CREATE TABLE architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    style TEXT NOT NULL,
    style_confidence REAL NOT NULL,
    evidence TEXT NOT NULL,  -- JSON array
    model_json TEXT NOT NULL,  -- Full ArchitectureModel as JSON
    detected_at TEXT NOT NULL
);
```

---

## 6. CLI Command

**`ortho analyze`**
```bash
ortho analyze                  # Detect architecture + print report
```

**Output:**
```
Architecture Detection Report
==============================
Style: Layered (confidence: 0.87)
Alternative: MVC (confidence: 0.52)

Evidence:
  - Clear upward dependencies (95% of imports point down)
  - 3 distinct layers detected
  - Low cross-layer coupling

Layers:
  Layer 1 (presentation): 8 files
    - depends_on: business
  Layer 2 (business): 12 files
    - depends_on: data
  Layer 3 (data): 6 files

Subsystems:
  auth (coupling: 0.89)
    - 4 files
  payment (coupling: 0.78)
    - 6 files
```

---

## 7. Tests

**Unit tests (25+):**
- Detector: layered pattern (3 test cases)
- Detector: hexagonal pattern (2 test cases)
- Detector: MVC pattern (2 test cases)
- Detector: microservices pattern (2 test cases)
- Detector: flat pattern (2 test cases)
- Detector: confidence scoring + alternatives (3 test cases)
- LayerDetector: layer extraction (4 test cases)
- LayerDetector: layer naming (2 test cases)
- LayerDetector: violation detection (2 test cases)
- SubsystemDetector: clustering (3 test cases)
- SubsystemDetector: naming (2 test cases)

**Integration tests (8+):**
- Analyze fixture repo → detect layered architecture
- Analyze fixture repo → detect microservices
- Analyze fixture repo → flat (no structure)
- Persistence: save + load architecture model
- CLI: `ortho analyze` produces readable output

**Fixtures:**
- `tests/fixtures/layered-repo/` — clear 3-tier layered structure
- `tests/fixtures/microservices-repo/` — independent modules
- `tests/fixtures/flat-repo/` — everything imports everything

---

## 8. Acceptance Criteria Mapping

| AC | Implemented By |
|----|-------|
| AC1 | ArchitectureDetector.detect() → style + confidence |
| AC2 | ArchitectureDetector.detect() → evidence list |
| AC3 | DetectionResult.alternative + alternative_confidence |
| AC4 | ArchitectureDetector handles low-confidence cases |
| AC5 | LayerDetector.detect_layers() |
| AC6 | LayerDetector._assign_semantic_names() |
| AC7 | LayerDetector.detect_layer_violations() |
| AC8 | Layer object with confidence |
| AC9 | SubsystemDetector.detect_subsystems() |
| AC10 | SubsystemDetector._suggest_subsystem_name() |
| AC11 | ArchitectureModelStore.save() |
| AC12 | ArchitectureModelStore.load() + load_latest() |

---

**Prepared by:** PLANNER  
**Status:** Gate 1 complete
