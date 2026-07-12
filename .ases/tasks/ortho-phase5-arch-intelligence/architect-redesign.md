# ARCHITECT Phase: Detector Redesign Strategy

**Scope:** Multi-evidence architecture detection with framework fingerprinting  
**Date:** 2026-07-13  
**Target Accuracy:** 75%+ on 8-repository corpus  

---

## Current Detector: Single-Evidence Problem

**Current flow:**
1. Extract directory/stem vocabulary
2. Measure import graph (depth, cycles, shallow ratio)
3. Score 5 style scorers using vocabulary only
4. Threshold 0.45 → "unknown"

**Problem:** Vocabulary alone is weak. Flask/Click have no "services" or "models" directories, so scorers fail despite having clear architectures.

---

## Redesigned Detector: Three-Evidence Integration

### Evidence #1: Directory Vocabulary (Weight: 0.25)

**Current:** Find `services`, `models`, `data`, etc.

**Improved:**

```python
LAYERED_VOCAB = {
    'models', 'entities', 'domain',
    'services', 'service', 'use_cases',
    'data', 'database', 'db', 'repositories', 'repository',
    'api', 'handlers', 'handlers', 'views', 'controllers',
    'middleware', 'config', 'infrastructure',
    'schemas', 'dtos',
    'layers', 'application', 'presentation'
}

MICROSERVICES_VOCAB = {
    'service', 'worker', 'broker', 'gateway',
    'orchestrator', 'coordinator',
    'admin', 'console', 'dashboard',
    'services'
}

FLAT_VOCAB = {
    'utils', 'helpers', 'core',
    'lib', 'tools', 'common'
}
```

**Logic:**
- Count tokens in vocabulary buckets
- Layered score ↑ if layered_vocab_ratio > 0.20
- Microservices score ↑ if microservices_vocab_ratio > 0.15
- Flat score ↑ if flat_vocab_ratio > 0.25 AND no layered tokens

---

### Evidence #2: Import Graph Analysis (Weight: 0.50)

**Current:** Only dag_depth, cycle_ratio, shallow_ratio.

**New metrics:**

1. **Layer Detection (Implicit)**
   ```python
   # Partition import graph into layers by fan-in degree
   # Files with high fan-in (many dependents) = lower layer
   # Files with high fan-out (many imports) = upper layer
   # If partition forms acyclic DAG → likely layered
   
   def detect_implicit_layers(graph):
       """Assign layer numbers based on import dependencies."""
       layers = {}
       for node in topo_sort(graph):
           # Layer = max(predecessor layers) + 1
           pred_layers = [layers[p] for p in graph.predecessors(node)]
           layers[node] = max(pred_layers) if pred_layers else 0
       return len(set(layers.values()))  # Number of layer bands
   ```

2. **Coupling Metrics**
   ```python
   def measure_coupling(graph):
       """Measure internal vs external coupling."""
       total_edges = len(graph.edges)
       cyclic_edges = sum(1 for u, v in graph.edges if has_path(v, u, graph))
       
       # Layered: low cyclic_edges, acyclic DAG
       # Microservices: low coupling per module, high subsystem boundaries
       # Flat: high cyclic_edges, dense graph
       
       return {
           'cycle_ratio': cyclic_edges / total_edges if total_edges else 0,
           'density': total_edges / (len(graph.nodes) * (len(graph.nodes) - 1)),
           'avg_fan_in': sum(g.in_degree(n) for n in g) / len(g),
           'avg_fan_out': sum(g.out_degree(n) for n in g) / len(g),
       }
   ```

3. **Subsystem Clustering**
   ```python
   # Partition graph into cohesive subsystems (already using Jaccard)
   # Count number of distinct clusters
   # Microservices: 4-8 clusters, low inter-cluster coupling
   # Layered: 2-4 layers (different metric)
   # Flat: 1-2 clusters (everything interconnected)
   ```

**Scoring logic:**

```python
def score_layered_from_graph(graph):
    implicit_layers = detect_implicit_layers(graph)
    coupling = measure_coupling(graph)
    
    score = 0.0
    if 2 <= implicit_layers <= 5:
        score += 0.35  # Clear layer structure
    if coupling['cycle_ratio'] < 0.10:
        score += 0.30  # Acyclic → layered
    if coupling['avg_fan_in'] > coupling['avg_fan_out']:
        score += 0.20  # Pyramid structure (fanout to center)
    
    return min(score, 0.85)  # Cap at 0.85 (not certain)
```

---

### Evidence #3: Framework Fingerprinting (Weight: 0.25)

**Current:** No framework detection.

**New framework signatures:**

```python
FRAMEWORK_SIGNATURES = {
    'flask': {
        'decorators': ['@app.route', '@app.before_request', '@app.after_request'],
        'imports': ['flask.Flask', 'flask.Blueprint'],
        'files': ['app.py', 'wsgi.py'],
        'style': 'layered'  # Flask encourages layered if using blueprints
    },
    'django': {
        'files': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
        'imports': ['django.db.models', 'django.views'],
        'style': 'layered'  # Django enforces layered (MTV pattern)
    },
    'fastapi': {
        'decorators': ['@app.get', '@app.post', '@app.dependency'],
        'imports': ['fastapi', 'pydantic'],
        'files': ['main.py', 'schemas.py'],
        'style': 'layered'
    },
    'click': {
        'decorators': ['@click.command', '@click.option', '@click.group'],
        'files': ['cli.py', 'commands.py'],
        'style': 'flat'  # Click CLIs are flat (no layers)
    },
    'celery': {
        'imports': ['celery', 'celery.Task'],
        'files': ['celery.py', 'tasks.py'],
        'style': 'microservices'  # Celery tasks are service-oriented
    }
}

def fingerprint_framework(repo_root):
    """Scan repo for framework patterns."""
    found_frameworks = []
    for framework, sig in FRAMEWORK_SIGNATURES.items():
        score = 0.0
        
        # Check for decorators in source (via regex scan)
        for decorator in sig['decorators']:
            if grep(repo_root, decorator):
                score += 0.25
        
        # Check for imports in source
        for import_pattern in sig['imports']:
            if grep(repo_root, f'import.*{import_pattern}'):
                score += 0.25
        
        # Check for canonical file names
        for filename in sig['files']:
            if Path(repo_root).rglob(filename):
                score += 0.25
        
        if score > 0.50:
            found_frameworks.append((framework, score, sig['style']))
    
    return found_frameworks  # [(framework_name, confidence, style), ...]
```

**Scoring logic:**

```python
def score_from_framework(frameworks):
    """Boost style scores based on framework detection."""
    if not frameworks:
        return {}  # No framework → use graph evidence
    
    # Take highest-confidence framework
    best_framework, confidence, style = max(frameworks, key=lambda x: x[1])
    
    # Framework boosts the detected style
    return {
        style: confidence * 0.50  # Framework votes with 50% weight
    }
```

---

## Integrated Scoring

**Pseudocode:**

```python
def detect_style(repo_root):
    """Multi-evidence architecture detection."""
    
    # Evidence 1: Vocabulary (weight 0.25)
    vocab_scores = score_vocabulary(repo_root)  # {layered: 0.60, flat: 0.20, ...}
    
    # Evidence 2: Import graph analysis (weight 0.50)
    import_graph = build_import_graph(repo_root)
    graph_scores = score_from_graph(import_graph)  # {layered: 0.70, ...}
    
    # Evidence 3: Framework fingerprinting (weight 0.25)
    frameworks = fingerprint_framework(repo_root)
    framework_scores = score_from_framework(frameworks)  # {layered: 0.50, ...}
    
    # Weighted combination
    final_scores = {}
    for style in STYLES:
        final_scores[style] = (
            0.25 * vocab_scores.get(style, 0.0) +
            0.50 * graph_scores.get(style, 0.0) +
            0.25 * framework_scores.get(style, 0.0)
        )
    
    # Apply threshold (0.45)
    best_style, best_score = max(final_scores.items(), key=lambda x: x[1])
    
    if best_score < 0.45:
        return 'unknown', best_score
    else:
        return best_style, best_score
```

---

## Expected Improvements

### On Current Test Cases

| Repo | Current | Predicted | Evidence |
|---|---|---|---|
| Click | unknown (0.40) | flat (0.70) | Framework fingerprint (Click) + shallow graph |
| Flask | unknown (0.40) | layered (0.65) | Framework fingerprint (Flask) + implicit layers |
| Django | unknown (0.40) | layered (0.90) | Vocab (models, views, etc.) + framework |
| FastAPI | unknown (0.40) | layered (0.80) | Vocab (schemas, routes) + framework |
| Requests | unknown (0.40) | flat (0.85) | Shallow graph + flat vocab |
| SQLAlchemy | unknown (0.40) | flat (0.75) | High coupling + flat vocab |
| Celery | unknown (0.40) | microservices (0.70) | Subsystem clustering + microservices vocab |
| LangChain | unknown (0.40) | layered (0.68) | Implicit layers + abstractions in schema/ |

**Overall target:** 7/8 correct (88% accuracy), all scores > 0.60 (confident predictions).

---

## Implementation Plan

### Iteration 1: Graph-Based Implicit Layer Detection
- Add `detect_implicit_layers()` function
- Measure coupling metrics
- Update scorers to use graph evidence
- **Expected impact:** Click, Flask → layered/flat (not unknown)

### Iteration 2: Framework Fingerprinting
- Add `FRAMEWORK_SIGNATURES` dict
- Implement pattern matching (decorators, imports, files)
- Update scorers to integrate framework evidence
- **Expected impact:** Flask, Django, FastAPI, Click boost to confident predictions

### Iteration 3: Evidence Weighting & Calibration
- Combine three evidence sources (weights 0.25/0.50/0.25)
- Re-test on 8-repository corpus
- Adjust thresholds based on false-positive/negative rates
- **Expected impact:** Balanced accuracy, honest confidence

### Iteration 4: Generalization Validation
- Run on all 8 repos + 2 holdout repos (if available)
- Measure precision/recall per style
- Document failure modes
- **Expected impact:** Confident release of improved detector

---

## Constraints & Guardrails

❌ **Do NOT:**
- Hardcode repository names
- Use synthetic ground truth
- Lower threshold below 0.40 (keeps confidence honest)
- Add ML/LLM dependency

✅ **Must:**
- Test on all 8 ground-truth repos
- Preserve all 883 passing tests
- Document framework signatures (maintainable)
- Measure accuracy before/after

---

## Handoff to BUILDER

**Deliverables from ARCHITECT phase:**
1. ✅ Root-cause forensic audit (planner-audit.md)
2. ✅ Ground truth expansion for 6 repos (architect-ground-truth.md)
3. ✅ Redesign strategy with implementation plan (this doc)

**Next step:** BUILDER implements Iterations 1-2 (graph analysis + framework detection).

