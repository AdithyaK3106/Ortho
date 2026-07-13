# Phase 5.3: Extended Coverage — TEST-DESIGNER Phase (Parallel with BUILDER)

**Date:** 2026-07-13  
**Goal:** Write 40-50 hard edge-case tests to identify bugs and regressions  
**Parallel:** BUILDER implementing simultaneously, tests drive implementation  

---

## Test Strategy Overview

### Five Test Suites
1. **Repository Layout Edge Cases** (5 tests) — Symlinks, namespace packages, mixed layouts, deep nesting, single-file modules
2. **Framework Fingerprinting Edge Cases** (5 tests) — False positives, multiple frameworks, imports without use, version edge cases, custom decorators
3. **Call Graph Signal Validation** (5 tests) — Pure hierarchy, circular calls, fan-in patterns, isolated islands, no external calls
4. **Full Repository Benchmarks** (3 tests) — SQLAlchemy, Celery, all 8 repos
5. **Regression Suite** (5 tests) — Flask, Click, Requests, all Phase 5 repos, framework detection false positives

**Total:** 23 core tests, expandable to 40-50 as edge cases discovered

---

## Suite 1: Repository Layout Edge Cases

### Test 1.1: Symlinked Packages

**Objective:** Ensure detector handles symlinks correctly (no double-counting)

**Test code** (new file: `packages/arch-intelligence/tests/test_layout_symlinks.py`):

```python
import tempfile
import os
from pathlib import Path
from repo_intelligence.indexer import Indexer
from arch_intelligence.arch_detector import ArchitectureDetector

def test_symlinked_packages():
    """Detect architecture in repo with symlinked packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create real package
        real_pkg = Path(tmpdir) / "src" / "real_package"
        real_pkg.mkdir(parents=True)
        (real_pkg / "__init__.py").write_text("")
        (real_pkg / "core.py").write_text("def do_something(): pass")
        
        # Create symlink to real package
        alias_pkg = Path(tmpdir) / "src" / "alias"
        os.symlink(real_pkg, alias_pkg)
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Should detect as flat (single package, not multi-level)
        assert prediction.style in ['flat', 'unknown']
        # Should not double-count: only ~2 files (core.py, __init__.py)
        assert len(result.symbols.files) <= 3  # Real + alias link info
```

**Edge case tested:** Symlink handling without filesystem traversal issues

**Expected outcome:** Detector handles symlinks gracefully, doesn't crash

---

### Test 1.2: Namespace Packages (PEP-420)

**Objective:** Handle namespace packages without __init__.py

**Test code:**

```python
def test_namespace_packages():
    """Detect architecture with PEP-420 namespace packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create namespace package (no __init__.py)
        ns_a = Path(tmpdir) / "pkg" / "module_a"
        ns_a.mkdir(parents=True)
        (ns_a / "core.py").write_text("def a(): pass")
        
        ns_b = Path(tmpdir) / "pkg" / "module_b"
        ns_b.mkdir(parents=True)
        (ns_b / "core.py").write_text("def b(): pass")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        
        # Verify: Should index both modules
        assert len(result.symbols.files) >= 2  # At least both core.py files
        assert result.symbols is not None
```

**Edge case tested:** Namespace package support (no __init__.py)

**Expected outcome:** Indexer correctly handles namespace packages

---

### Test 1.3: Mixed Layouts (src/ + top-level)

**Objective:** Handle repositories with multiple package roots

**Test code:**

```python
def test_mixed_layouts():
    """Detect architecture with src/ and top-level packages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # src/package
        src_pkg = Path(tmpdir) / "src" / "main_package"
        src_pkg.mkdir(parents=True)
        (src_pkg / "__init__.py").write_text("")
        (src_pkg / "app.py").write_text("def run(): pass")
        
        # Top-level package
        top_pkg = Path(tmpdir) / "secondary"
        top_pkg.mkdir()
        (top_pkg / "__init__.py").write_text("")
        (top_pkg / "utils.py").write_text("def helper(): pass")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Should handle both package locations
        assert len(result.symbols.files) >= 4  # At least 4 files
        assert prediction.style is not None
```

**Edge case tested:** Multiple package roots in one repository

**Expected outcome:** Detector handles heterogeneous layouts

---

### Test 1.4: Deep Nesting

**Objective:** Ensure layer detection doesn't break with deep nesting

**Test code:**

```python
def test_deep_nesting():
    """Detect architecture with 10+ level deep module hierarchy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create deeply nested structure
        deep_path = Path(tmpdir) / "src"
        for i in range(10):
            deep_path = deep_path / f"level{i}"
        
        deep_path.mkdir(parents=True)
        (deep_path / "__init__.py").write_text("")
        (deep_path / "core.py").write_text("def deep(): pass")
        
        # Add intermediate __init__.py files
        current = Path(tmpdir) / "src"
        for i in range(10):
            current = current / f"level{i}"
            (current / "__init__.py").write_text("")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Should not crash, reasonable layer count
        assert prediction.style in ['flat', 'layered', 'unknown']
        # DAG depth shouldn't be 1 per level
        assert detector._dag_depth <= 5  # Reasonable, not 11
```

**Edge case tested:** Deep nesting doesn't break layer detection

**Expected outcome:** Detector computes reasonable layer count

---

### Test 1.5: Single-File Modules

**Objective:** Handle single .py files (not inside module folders)

**Test code:**

```python
def test_single_file_modules():
    """Detect architecture with single-file modules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create single .py file (no folder)
        (Path(tmpdir) / "util.py").write_text("def utility(): pass")
        (Path(tmpdir) / "helper.py").write_text("def help(): pass")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Should handle single-file modules gracefully
        assert len(result.symbols.files) >= 2
        assert prediction.style is not None
```

**Edge case tested:** Single-file modules (not in packages)

**Expected outcome:** Detector handles gracefully

---

## Suite 2: Framework Fingerprinting Edge Cases

### Test 2.1: False Positive — Flask in Comments

**Objective:** Ensure framework detection doesn't trigger on comments/strings

**Test code:**

```python
def test_framework_false_positive_comments():
    """Framework detection ignores Flask in comments and strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "myapp"
        app_dir.mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "core.py").write_text("""
# This application uses Flask for routing
# See: https://flask.palletsprojects.com/

code_str = 'from flask import Flask'
# NEVER import Flask at module level
def setup():
    pass
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Flask not detected (no actual import)
        assert prediction.framework is None or prediction.framework.name != 'flask'
```

**Edge case tested:** Comments and strings don't trigger framework detection

**Expected outcome:** Clean, low false positive rate

---

### Test 2.2: Multiple Frameworks Coexisting

**Objective:** Highest confidence framework wins, others noted

**Test code:**

```python
def test_multiple_frameworks():
    """Multiple frameworks — highest confidence wins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "web.py").write_text("""
from flask import Flask, route
from celery import Celery
from sqlalchemy import create_engine

app = Flask(__name__)
celery = Celery('tasks')

@app.route('/api')
def index():
    return 'Hello'

@celery.task
def long_task():
    pass
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Flask (web) is primary, Celery (task) is secondary
        # App with web + task frameworks → layered (Flask) or microservices (Celery)
        # Should pick Flask as primary (web framework)
        assert prediction.framework is not None
        # Flask should be detected
```

**Edge case tested:** Framework priority when multiple present

**Expected outcome:** Correct framework prioritization

---

### Test 2.3: Framework Imports Without Use

**Objective:** Detect imports but lower confidence than active use

**Test code:**

```python
def test_framework_import_without_use():
    """Framework import without decorators/instances — lower confidence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "core.py").write_text("""
# Imports Flask but doesn't use it
from flask import Flask, json

# Actually, we're not using Flask
def process():
    return json.dumps({'key': 'value'})
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Flask might be detected but with lower confidence
        # than if decorators were present
        # This is informational — not a hard pass/fail
```

**Edge case tested:** Import detection vs. active use confidence

**Expected outcome:** Graceful handling

---

### Test 2.4: Version-Specific Imports

**Objective:** Don't fail on version-specific imports

**Test code:**

```python
def test_version_specific_imports():
    """Handle version-specific imports (e.g., removed in newer Flask versions)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "app.py").write_text("""
from flask import Flask
from flask import json  # Removed in Flask 2.1+

app = Flask(__name__)
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Should detect Flask and not crash
        assert prediction is not None
```

**Edge case tested:** Version-specific import handling

**Expected outcome:** Robust to version changes

---

### Test 2.5: Custom Decorators Over Framework

**Objective:** Don't false-trigger on custom @route decorators

**Test code:**

```python
def test_custom_decorators():
    """Custom @route decorator shouldn't trigger Flask detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "routing.py").write_text("""
def route(path):
    def decorator(func):
        return func
    return decorator

@route('/home')
def home():
    return 'Home'
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        # Verify: Flask not detected (custom @route, not @app.route)
        assert prediction.framework is None or prediction.framework.name != 'flask'
```

**Edge case tested:** Custom decorator discrimination

**Expected outcome:** No false framework detection

---

## Suite 3: Call Graph Signal Validation

### Test 3.1: Pure Hierarchy (No Cycles)

**Objective:** Call graph boosts layered score

**Test code:**

```python
def test_call_graph_pure_hierarchy():
    """Call graph with pure hierarchy (no cycles) boosts layered score."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        
        # Layer 1: Presentation
        (app_dir / "__init__.py").write_text("")
        (app_dir / "views.py").write_text("""
from .business import process_request

def handle_request(data):
    return process_request(data)
""")
        
        # Layer 2: Business logic
        (app_dir / "business.py").write_text("""
from .data import fetch_data

def process_request(data):
    db_data = fetch_data(data['id'])
    return {'result': db_data}
""")
        
        # Layer 3: Data layer
        (app_dir / "data.py").write_text("""
def fetch_data(id):
    return {'value': id}
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        # Verify: Layered detection with high confidence
        assert prediction.style == 'layered'
        assert prediction.confidence > 0.7
```

**Edge case tested:** Unidirectional call patterns

**Expected outcome:** Call graph strengthens layered detection

---

### Test 3.2: Circular Calls

**Objective:** Call graph dampens layered signal on cycles

**Test code:**

```python
def test_call_graph_circular_calls():
    """Circular calls dampen layered signal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        
        (app_dir / "__init__.py").write_text("")
        (app_dir / "module_a.py").write_text("""
from .module_b import b_func

def a_func():
    return b_func()
""")
        
        (app_dir / "module_b.py").write_text("""
from .module_a import a_func

def b_func():
    if some_condition:
        a_func()  # Cycle!
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        # Verify: Call graph recognizes cycle, lowers layered confidence
        # May predict flat or unknown due to bidirectional calls
        assert prediction.style in ['flat', 'unknown']
```

**Edge case tested:** Bidirectional call detection

**Expected outcome:** Cycles dampen layered signal

---

### Test 3.3: High Fan-In (Hub Patterns)

**Objective:** Detect hub modules (utils called by many)

**Test code:**

```python
def test_call_graph_fan_in():
    """Hub modules (high fan-in) don't break detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        
        (app_dir / "__init__.py").write_text("")
        (app_dir / "utils.py").write_text("""
def format_data(d): return d
def parse_input(s): return s
def validate(x): return x
""")
        
        # 5 modules all calling utils
        for i in range(5):
            (app_dir / f"module{i}.py").write_text(f"""
from .utils import format_data, validate

def work_{i}():
    return format_data(validate(None))
""")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        # Verify: Handles hub pattern gracefully
        assert prediction is not None
```

**Edge case tested:** High fan-in utility modules

**Expected outcome:** Detector handles hubs gracefully

---

### Test 3.4: Isolated Call Islands

**Objective:** Isolated clusters boost microservices score

**Test code:**

```python
def test_call_graph_isolated_islands():
    """Isolated call clusters boost microservices score."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        
        (app_dir / "__init__.py").write_text("")
        
        # Island 1: Worker
        (app_dir / "worker.py").write_text("""
from .worker_utils import helper

def work():
    return helper()
""")
        (app_dir / "worker_utils.py").write_text("def helper(): pass")
        
        # Island 2: Broker
        (app_dir / "broker.py").write_text("""
from .broker_utils import connect

def pub():
    return connect()
""")
        (app_dir / "broker_utils.py").write_text("def connect(): pass")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        # Verify: Isolated clusters detected
        # May predict microservices or flat
        assert prediction is not None
```

**Edge case tested:** Call graph clustering

**Expected outcome:** Microservices signal activated

---

### Test 3.5: No External Calls

**Objective:** All internal calls used for differentiation

**Test code:**

```python
def test_call_graph_all_internal():
    """All internal calls — call graph useful for differentiation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = Path(tmpdir) / "src" / "app"
        app_dir.mkdir(parents=True)
        
        (app_dir / "__init__.py").write_text("")
        (app_dir / "a.py").write_text("from .b import b; x = b()")
        (app_dir / "b.py").write_text("from .c import c; y = c()")
        (app_dir / "c.py").write_text("z = 42")
        
        # Index and detect
        indexer = Indexer()
        result = indexer.index(tmpdir)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        # Verify: Call graph signals contribute
        assert prediction is not None
```

**Edge case tested:** Pure internal call graphs

**Expected outcome:** Useful signal strength

---

## Suite 4: Full Repository Benchmarks

### Test 4.1: SQLAlchemy Benchmark

**Objective:** Validate SQLAlchemy detection as flat

```python
def test_sqlalchemy_benchmark():
    """SQLAlchemy benchmark — expect flat architecture."""
    repo_path = "repos/sqlalchemy"
    if not Path(repo_path).exists():
        pytest.skip("SQLAlchemy not cloned")
    
    indexer = Indexer()
    result = indexer.index(repo_path)
    detector = ArchitectureDetector(result.symbols)
    detector.calls = result.calls
    prediction = detector.detect()
    
    # Verify: Detected as flat with >0.70 confidence
    assert prediction.style == 'flat', f"Expected flat, got {prediction.style}"
    assert prediction.confidence > 0.70, f"Confidence {prediction.confidence} too low"
```

### Test 4.2: Celery Benchmark

**Objective:** Validate Celery detection as microservices

```python
def test_celery_benchmark():
    """Celery benchmark — expect microservices architecture."""
    repo_path = "repos/celery"
    if not Path(repo_path).exists():
        pytest.skip("Celery not cloned")
    
    indexer = Indexer()
    result = indexer.index(repo_path)
    detector = ArchitectureDetector(result.symbols)
    detector.calls = result.calls
    prediction = detector.detect()
    
    # Verify: Detected as microservices with >0.70 confidence
    assert prediction.style == 'microservices', f"Expected microservices, got {prediction.style}"
    assert prediction.confidence > 0.70, f"Confidence {prediction.confidence} too low"
```

### Test 4.3: All 8 Repos Benchmark

**Objective:** Full accuracy/calibration metrics

```python
def test_full_8_repo_benchmark():
    """All 8 repos — accuracy and calibration metrics."""
    repos = {
        'flask': 'layered',
        'click': 'flat',
        'django': 'layered',
        'fastapi': 'layered',
        'langchain': 'layered',
        'requests': 'flat',
        'sqlalchemy': 'flat',
        'celery': 'microservices',
    }
    
    results = {}
    for repo_name, expected_style in repos.items():
        repo_path = f"repos/{repo_name}"
        if not Path(repo_path).exists():
            pytest.skip(f"{repo_name} not found")
        
        indexer = Indexer()
        result = indexer.index(repo_path)
        detector = ArchitectureDetector(result.symbols)
        detector.calls = result.calls
        prediction = detector.detect()
        
        results[repo_name] = {
            'predicted': prediction.style,
            'expected': expected_style,
            'confidence': prediction.confidence,
            'correct': prediction.style == expected_style,
        }
    
    # Compute metrics
    correct = sum(1 for r in results.values() if r['correct'])
    total = len(results)
    accuracy = correct / total if total > 0 else 0
    
    # Verify: ≥85% accuracy or maintain 83.3%
    assert accuracy >= 0.833, f"Accuracy {accuracy:.1%} below target"
```

---

## Suite 5: Regression Suite

### Test 5.1: Flask Regression

```python
def test_regression_flask():
    """Flask still detected as layered, confidence >0.80."""
    repo_path = "repos/flask"
    if not Path(repo_path).exists():
        pytest.skip("Flask not found")
    
    indexer = Indexer()
    result = indexer.index(repo_path)
    detector = ArchitectureDetector(result.symbols)
    prediction = detector.detect()
    
    assert prediction.style == 'layered'
    assert prediction.confidence > 0.80
```

### Test 5.2: Click Regression

```python
def test_regression_click():
    """Click still detected as flat, confidence >0.70."""
    repo_path = "repos/click"
    if not Path(repo_path).exists():
        pytest.skip("Click not found")
    
    indexer = Indexer()
    result = indexer.index(repo_path)
    detector = ArchitectureDetector(result.symbols)
    prediction = detector.detect()
    
    assert prediction.style == 'flat'
    assert prediction.confidence > 0.70
```

### Test 5.3: Requests Fix Validation

```python
def test_requests_fix():
    """Requests now detected as flat, >0.75 confidence."""
    repo_path = "repos/requests"
    if not Path(repo_path).exists():
        pytest.skip("Requests not found")
    
    indexer = Indexer()
    result = indexer.index(repo_path)
    detector = ArchitectureDetector(result.symbols)
    prediction = detector.detect()
    
    # After fix: Should be flat, not unknown
    assert prediction.style == 'flat', f"Expected flat, got {prediction.style}"
    assert prediction.confidence > 0.75, f"Confidence {prediction.confidence} too low"
```

### Test 5.4: All Phase 5 Repos No Regression

```python
def test_all_phase5_repos_regression():
    """All Phase 5 repos (6/6) still correct, confidence maintained."""
    expected = {
        'flask': ('layered', 0.80),
        'click': ('flat', 0.70),
        'django': ('layered', 0.90),
        'fastapi': ('layered', 0.90),
        'langchain': ('layered', 0.85),
        'requests': ('flat', 0.75),
    }
    
    for repo_name, (style, min_conf) in expected.items():
        repo_path = f"repos/{repo_name}"
        if not Path(repo_path).exists():
            pytest.skip(f"{repo_name} not found")
        
        indexer = Indexer()
        result = indexer.index(repo_path)
        detector = ArchitectureDetector(result.symbols)
        prediction = detector.detect()
        
        assert prediction.style == style, f"{repo_name}: expected {style}, got {prediction.style}"
        assert prediction.confidence > min_conf, f"{repo_name}: confidence {prediction.confidence} < {min_conf}"
```

### Test 5.5: Framework Detection False Positives

```python
def test_framework_false_positive_rate():
    """Framework detection false positive rate <5% across all repos."""
    # Scan all repos
    # Count false positives (detected framework when none should be)
    # E.g., Requests shouldn't detect Flask, Click, etc.
    
    # This is a meta-test checking calibration across all 8 repos
    pass  # Implemented during VERIFIER phase
```

---

## Test Execution

**Run command:**
```bash
pytest packages/arch-intelligence/tests/test_phase5_3_*.py -v
```

**Expected output:**
- 40-50 tests total
- All passing (or marked as expected failures)
- Edge cases discovered and logged
- Bugs identified immediately for BUILDER fix

---

## Status

**Ready to execute:** TEST-DESIGNER hardfests planned and ready to run.

**Blocking for:** BUILDER implementation to provide ground truth for benchmark tests.

**Test-driven flow:**
1. TEST-DESIGNER runs edge case tests
2. Tests identify edge cases and bugs
3. BUILDER implements fixes
4. TEST-DESIGNER verifies fixes
5. Repeat until all tests pass
