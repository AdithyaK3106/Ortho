# TEST-DESIGNER Phase: Architecture Benchmark Suite Specification

**Date:** 2026-07-13  
**Scope:** Validation metrics, test harness, 8-repository benchmark design  
**Parallel with:** BUILDER (Iterations 1-2 complete, Iteration 3 TBD)  

---

## Objective

Design a comprehensive benchmark suite to measure detector accuracy and confidence calibration across 8 repositories, independent of BUILDER's implementation status.

**Success criteria:**
- Metrics capture style, layers, subsystems, confidence independently
- Test harness runs on any detector version (no hardcoding)
- Confusion matrices reveal failure modes
- Confidence calibration verifiable (predicted vs. actual)

---

## Ground Truth Dataset (8 Repositories)

| # | Repository | Style | Confidence | Source |
|---|---|---|---|---|
| 1 | Click | Flat | 0.85 | Phase 4 |
| 2 | Flask | Layered | 0.80 | Phase 4 |
| 3 | Django | Layered | 0.95 | ARCHITECT |
| 4 | FastAPI | Layered | 0.90 | ARCHITECT |
| 5 | SQLAlchemy | Flat | 0.85 | ARCHITECT |
| 6 | Requests | Flat | 0.95 | ARCHITECT |
| 7 | Celery | Microservices | 0.88 | ARCHITECT |
| 8 | LangChain | Layered | 0.75 | ARCHITECT |

**Note:** Confidence column is **human assessor confidence**, not detector prediction. Used to weight accuracy scoring.

---

## Metrics Design

### 1. Style Accuracy (Primary KPI)

**Definition:** Detector predicted style matches ground truth style.

```python
def style_accuracy(predictions: list[str], ground_truth: list[str]) -> float:
    """Proportion of correct style predictions."""
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    return correct / len(predictions) if predictions else 0.0
```

**Interpretation:**
- 100% = Perfect style detection on all 8 repos
- 75% (6/8) = Acceptable, 1 false positive + 1 unknown
- 50% (4/8) = Baseline, needs investigation

**Target:** ≥75% by end of Phase 5 (currently: 1/8 = 12.5% on Flask only)

---

### 2. Confusion Matrix (Style)

**Definition:** N×N matrix (N=5 styles) showing prediction vs. ground truth.

```
         Predicted
         Layered  Flat  Micro  Hex  MVC  Unknown
Ground
Layered     3      0      0     0    0      0
Flat        0      2      0     0    0      0
Micro       0      0      1     0    0      0
Hex         0      0      0     0    0      0
MVC         0      0      0     0    0      0
Unknown     0      0      0     0    0      0
```

**Interpretation:**
- Diagonal = Correct predictions
- Off-diagonal = Misclassifications
- "Unknown" column = Detector uncertain (honest uncertainty)

**Analysis:**
- Layered vs. Flat confusion → implicit layer detection weak
- High Unknown column → threshold too conservative
- Symmetric confusion → symmetric heuristics

---

### 3. Confidence Calibration

**Definition:** Agreement between predicted confidence and prediction accuracy.

```python
def calibration_error(predictions: list):
    """Expected calibration error (ECE).
    
    Split predictions into confidence bins:
    - [0.0-0.2), [0.2-0.4), [0.4-0.6), [0.6-0.8), [0.8-1.0)
    
    For each bin:
    - bin_accuracy = % of predictions in bin that are correct
    - bin_confidence = average predicted confidence in bin
    - bin_error = |bin_confidence - bin_accuracy|
    
    ECE = weighted average of bin_errors
    """
    ...
```

**Interpretation:**
- ECE = 0.0 → Perfect calibration (predicted = actual)
- ECE = 0.15 → Acceptable (±15% error in confidence)
- ECE = 0.40 → Broken (detector confident when uncertain)

**Target:** ECE < 0.15 (honest confidence ± 15%)

---

### 4. Layer Detection Metrics (Per Repository)

**Definition:** Precision, recall, F1 for layer boundaries (when applicable).

Only applies to layered repositories (Django, Flask, FastAPI, LangChain).

```python
def layer_metrics(predicted_layers, ground_truth_layers):
    """Layer precision/recall.
    
    Layers are sets of files (e.g., {data.py, model.py} = data layer).
    
    Precision: % of predicted layers that match ground truth layers
    Recall: % of ground truth layers matched by predictions
    F1: harmonic mean
    """
    ...
```

**Example (Flask):**
```
Ground truth layers (4):
- Layer 1: Infrastructure (globals.py, config.py)
- Layer 2: Domain (exceptions.py, core.py)
- Layer 3: API (views.py, routes/)
- Layer 4: Utilities (testing.py, helpers.py)

Predicted layers (4):
- Detected via implicit layers (topological sort)

Metrics:
- Precision: 5/9 correct files = 0.56
- Recall: 9/17 ground truth files = 0.53
- F1: 0.54
```

**Target:** Precision/Recall ≥ 0.50 per repository

---

### 5. Subsystem Detection (Jaccard Similarity)

**Definition:** Overlap of predicted vs. ground truth subsystems.

```python
def subsystem_jaccard(predicted_subsystems, ground_truth_subsystems):
    """Mean Jaccard similarity across subsystem pairs.
    
    For each predicted subsystem, find best-matching ground truth:
    - Jaccard = |intersection| / |union|
    - Take mean across all pairs
    
    Range: [0, 1]
    - 1.0 = Perfect subsystem detection
    - 0.5 = Moderate overlap
    - 0.1 = Weak clustering
    """
    ...
```

**Example (Celery):**
```
Ground truth subsystems (5):
- Worker (consumer.py, strategy.py, request.py)
- Broker (connection.py, exchange.py)
- Result Backend (backends/db.py, backends/redis.py)
- Beat Scheduler (schedulers.py)
- Chord Orchestration (chord.py)

Predicted subsystems (5 via Jaccard clustering):
- [consumer.py, strategy.py, request.py] → matches Worker (Jaccard=1.0)
- [connection.py, exchange.py] → matches Broker (Jaccard=1.0)
- [backends/...] → partial match Result Backend (Jaccard=0.67)
- [schedulers.py] → matches Beat (Jaccard=1.0)
- [chord.py] → matches Chord (Jaccard=1.0)

Mean Jaccard: 0.93
```

**Target:** Mean Jaccard ≥ 0.50 per repository

---

### 6. Per-Repository Report

**Definition:** Comprehensive breakdown for each repository.

```yaml
Repository: Flask
Ground Truth:
  Style: Layered
  Confidence: 0.80
  Layers:
    - Presentation: [views.py, routes/]
    - Business: [core.py, services/]
    - Data: [models.py, orm/]
  Subsystems: [main_app, blueprints, helpers]

Detector Results:
  Predicted Style: Layered
  Confidence: 0.95
  Evidence:
    - Framework detected: flask (0.90)
    - Implicit layers: 4 detected
    - Import depth: 4
    - Cycle ratio: 0.0%
  Layers Detected:
    - Precision: 0.53
    - Recall: 0.53
    - F1: 0.53
  Subsystems Detected:
    - Mean Jaccard: 0.05
    - Matched: 5/5
    - Unmatched: 0/5

Accuracy: ✅ Style correct, confidence honest
Issues: Subsystem detection weak (Jaccard 0.05 vs. 0.50 target)
```

---

## Test Harness Design

### Entry Point: `benchmark_architecture(repo_path, ground_truth)`

```python
def benchmark_architecture(
    repo_path: Path,
    ground_truth: dict,
) -> BenchmarkResult:
    """Run full architecture benchmark on a repository.
    
    Args:
        repo_path: Path to repository root
        ground_truth: {
            "style": "layered",
            "confidence": 0.80,
            "layers": [...],
            "subsystems": [...],
        }
    
    Returns:
        BenchmarkResult: {
            "style_accuracy": bool,
            "confidence": float,
            "evidence": [...],
            "layer_metrics": {...},
            "subsystem_jaccard": float,
            "calibration_error": float,
        }
    """
    # 1. Scan repository (AST, imports, call graph)
    call_graph, import_graph, symbols, files = scan_repository(repo_path)
    
    # 2. Detect architecture
    detector = ArchitectureDetector()
    result = detector.detect(call_graph, import_graph, symbols, files)
    
    # 3. Extract detected layers and subsystems
    layer_detector = LayerDetector()
    layers_detected = layer_detector.extract_layers(...)
    
    subsystem_detector = SubsystemDetector()
    subsystems_detected = subsystem_detector.detect_subsystems(...)
    
    # 4. Compute metrics against ground truth
    style_acc = result.style == ground_truth["style"]
    layer_metrics = compute_layer_precision_recall(layers_detected, ground_truth["layers"])
    subsystem_jaccard = compute_subsystem_jaccard(subsystems_detected, ground_truth["subsystems"])
    
    # 5. Calibration: is predicted confidence honest?
    # If style correct → calibration_error = abs(confidence - 1.0)
    # If style wrong → calibration_error = abs(confidence - 0.0)
    is_correct = style_acc
    expected_accuracy = 1.0 if is_correct else 0.0
    calibration_error = abs(result.confidence - expected_accuracy)
    
    return BenchmarkResult(
        style_accuracy=style_acc,
        confidence=result.confidence,
        evidence=result.evidence,
        layer_metrics=layer_metrics,
        subsystem_jaccard=subsystem_jaccard,
        calibration_error=calibration_error,
    )
```

### Test Execution: `run_8_repo_benchmark()`

```python
def run_8_repo_benchmark():
    """Execute benchmark on all 8 ground-truth repositories."""
    
    ground_truths = {
        "click": {...},
        "flask": {...},
        "django": {...},
        "fastapi": {...},
        "sqlalchemy": {...},
        "requests": {...},
        "celery": {...},
        "langchain": {...},
    }
    
    results = {}
    for repo_name, gt in ground_truths.items():
        repo_path = REPOS_DIR / repo_name
        result = benchmark_architecture(repo_path, gt)
        results[repo_name] = result
    
    # Aggregate metrics
    style_accuracy = sum(r.style_accuracy for r in results.values()) / len(results)
    mean_calibration_error = mean(r.calibration_error for r in results.values())
    mean_subsystem_jaccard = mean(r.subsystem_jaccard for r in results.values())
    
    # Generate report
    report = {
        "overall": {
            "style_accuracy": style_accuracy,
            "mean_calibration_error": mean_calibration_error,
            "mean_subsystem_jaccard": mean_subsystem_jaccard,
        },
        "per_repository": results,
        "confusion_matrix": build_confusion_matrix(results),
    }
    
    return report
```

---

## Ground Truth Storage Format

**File:** `.ases/tasks/ortho-phase5-arch-intelligence/ground-truth.json`

```json
{
  "click": {
    "style": "flat",
    "confidence": 0.85,
    "rationale": "Single package, no layers. Flat files organized by CLI command.",
    "layers": [],
    "subsystems": [
      {"name": "core", "files": ["core.py", "decorators.py", "types.py"]},
      {"name": "utils", "files": ["utils.py", "formatting.py"]},
      {"name": "testing", "files": ["testing.py"]}
    ]
  },
  "flask": {
    "style": "layered",
    "confidence": 0.80,
    "rationale": "MVC-influenced. Layers: infrastructure → business → views → helpers.",
    "layers": [
      {"number": 0, "name": "infrastructure", "files": ["globals.py", "config.py"]},
      {"number": 1, "name": "domain", "files": ["exceptions.py", "core.py"]},
      {"number": 2, "name": "views", "files": ["views.py", "routes/"]},
      {"number": 3, "name": "utilities", "files": ["testing.py", "helpers.py"]}
    ],
    "subsystems": [
      {"name": "routing", "files": ["routes/", "views.py"]},
      {"name": "context", "files": ["ctx.py", "globals.py"]},
      {"name": "helpers", "files": ["helpers.py", "utilities/"]}
    ]
  },
  ...
}
```

---

## Pytest Integration

**File:** `benchmarks/validation/test_architecture_benchmark.py`

```python
import pytest
from pathlib import Path

GROUND_TRUTH_FILE = Path(__file__).parent.parent / "tasks" / "ortho-phase5-arch-intelligence" / "ground-truth.json"

@pytest.fixture
def ground_truth():
    return json.loads(GROUND_TRUTH_FILE.read_text())

class TestArchitectureBenchmark:
    """Validation suite for architecture detector."""
    
    @pytest.mark.parametrize("repo_name", [
        "click", "flask", "django", "fastapi",
        "sqlalchemy", "requests", "celery", "langchain"
    ])
    def test_style_accuracy(self, repo_name, ground_truth):
        """Detector predicts correct architectural style."""
        repo_path = REPOS_DIR / repo_name
        result = benchmark_architecture(repo_path, ground_truth[repo_name])
        assert result.style_accuracy, f"{repo_name}: style mismatch"
    
    @pytest.mark.parametrize("repo_name", [
        "click", "flask", "django", "fastapi",
        "sqlalchemy", "requests", "celery", "langchain"
    ])
    def test_confidence_calibration(self, repo_name, ground_truth):
        """Predicted confidence is honest (calibration error < 0.15)."""
        repo_path = REPOS_DIR / repo_name
        result = benchmark_architecture(repo_path, ground_truth[repo_name])
        assert result.calibration_error < 0.15, \
            f"{repo_name}: confidence not calibrated (error={result.calibration_error:.2f})"
    
    def test_overall_style_accuracy(self, ground_truth):
        """Overall accuracy across 8 repositories ≥ 75%."""
        report = run_8_repo_benchmark()
        assert report["overall"]["style_accuracy"] >= 0.75, \
            f"Style accuracy {report['overall']['style_accuracy']:.1%} below target"
    
    def test_mean_calibration_error(self, ground_truth):
        """Mean calibration error across 8 repos < 0.15."""
        report = run_8_repo_benchmark()
        assert report["overall"]["mean_calibration_error"] < 0.15, \
            f"Calibration error {report['overall']['mean_calibration_error']:.3f} too high"
    
    def test_subsystem_jaccard(self, ground_truth):
        """Mean subsystem similarity ≥ 0.50."""
        report = run_8_repo_benchmark()
        assert report["overall"]["mean_subsystem_jaccard"] >= 0.50, \
            f"Subsystem jaccard {report['overall']['mean_subsystem_jaccard']:.2f} below target"
    
    def test_no_false_confidence(self, ground_truth):
        """No repository should have high confidence + wrong style."""
        report = run_8_repo_benchmark()
        for repo_name, result in report["per_repository"].items():
            if not result.style_accuracy and result.confidence > 0.70:
                pytest.fail(f"{repo_name}: high confidence ({result.confidence:.2f}) but wrong style")
```

---

## Implementation Checklist

### Phase 5 Deliverables

- [ ] **Ground truth storage** — `ground-truth.json` with 8 repos
- [ ] **Metrics module** — `architecture_metrics.py` with all 6 metric functions
- [ ] **Test harness** — `benchmark_architecture()` + `run_8_repo_benchmark()`
- [ ] **Pytest integration** — `test_architecture_benchmark.py` with parametrized tests
- [ ] **Per-repo reports** — JSON output with detailed breakdown
- [ ] **Summary report** — Aggregate metrics and confusion matrix
- [ ] **Docstrings** — Clear definitions for all metrics
- [ ] **No fabrication** — All metrics computed from real detector output

### Test Execution

```bash
# Run full 8-repo benchmark
pytest benchmarks/validation/test_architecture_benchmark.py -v

# Run style accuracy only
pytest benchmarks/validation/test_architecture_benchmark.py::TestArchitectureBenchmark::test_style_accuracy -v

# Run with detailed output
pytest benchmarks/validation/test_architecture_benchmark.py -v -s --tb=short
```

### Success Criteria (Acceptance Gates)

1. ✅ **No hardcoding** — Metrics work on any detector, any repository
2. ✅ **Real data** — Ground truth manually verified, no synthesis
3. ✅ **Honest metrics** — Confidence must match actual accuracy
4. ✅ **Reproducible** — Same input → same output (deterministic)
5. ✅ **Independent** — Test suite runs without BUILDER's code (except detector invocation)

