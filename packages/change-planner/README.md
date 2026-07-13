# Change Planner

**Purpose:** Predict the impact of code changes across a repository.

Given a changed file, Change Planner identifies all affected modules and functions using call graph and import graph analysis.

## Responsibilities

- Extract changed symbols from a file
- Traverse call graphs (who calls what)
- Traverse import graphs (who imports what)
- Score confidence based on edge types and distances
- Report impacts with evidence

## API

```python
from change_planner import ChangePredictor, ImpactPrediction

predictor = ChangePredictor(
    call_graph=graph,
    import_graph=graph,
    symbol_registry=registry,
    arch_model=model
)

result: ImpactPrediction = predictor.predict_impact("src/auth/service.py")

print(f"Affected modules: {result.affected_modules}")
print(f"Affected functions: {result.affected_functions}")
print(f"Cascade risk: {result.cascade_risk}")
print(f"Confidence: {result.confidence:.2%}")
```

## Data Models

### ImpactPrediction
- `changed_file`: File that was changed
- `affected_modules`: Modules that import this file
- `affected_functions`: Functions that call changed functions
- `cascade_risk`: low | medium | high
- `confidence`: 0.0-1.0 based on evidence quality
- `reasoning`: Human-readable explanation
- `evidence`: List of ImpactEdge (source, target, type, distance)

### ImpactEdge Types
- `DIRECT_CALL`: Direct function call (confidence: 1.0)
- `TRANSITIVE_CALL`: Call through intermediaries (confidence: 0.9/distance)
- `IMPORT`: Direct import (confidence: 0.8)
- `STAR_IMPORT`: from module import * (confidence: 0.6)
- `DYNAMIC_IMPORT`: getattr/importlib (confidence: 0.4)
- `CONDITIONAL_IMPORT`: Guarded by if statement (confidence: 0.7)

## Confidence Scoring

Confidence is computed as average edge confidence:
- Direct edges: High confidence (0.8-1.0)
- Transitive edges: Decreases with distance
- Dynamic/conditional: Lower confidence (<0.7)

## Edge Cases Handled

- ✅ Circular imports (A→B→A)
- ✅ Dynamic imports (getattr, importlib)
- ✅ Star imports (from X import *)
- ✅ Late-binding imports (runtime resolution)
- ✅ Plugin systems (discovery-based loading)
- ✅ Conditional imports (if DEBUG: import X)

## Testing

```bash
pytest packages/change-planner -v --cov=src/change_planner
```

20 hard test cases covering:
- Straightforward single-file changes
- Graph traversal (call & import)
- Circular dependencies
- Dynamic code patterns
- Star imports
- Late-binding scenarios
- Complex multi-edge cases
- Accuracy metrics (90% target)

## Notes

- Conservative on confidence (prefers false negatives to false positives)
- Handles dynamic code with limited static analysis
- Respects Python privacy conventions (_private symbols)
- Works with any call graph + import graph implementation

