# Phase 5.3: Extended Coverage — BUILDER Phase (Parallel with TEST-DESIGNER)

**Date:** 2026-07-13  
**Goal:** Implement all 4 acceptance criteria  
**Parallel:** TEST-DESIGNER running simultaneously, test-driven implementation  

---

## AC1: Complete 8-Repository Benchmark

### Task: Clone SQLAlchemy and Celery

**Current state:**
- 6/8 repos cloned (Flask, Click, Django, FastAPI, LangChain, Requests)
- Missing: SQLAlchemy, Celery

**Action:**

1. Clone SQLAlchemy
   ```bash
   cd repos/
   git clone https://github.com/sqlalchemy/sqlalchemy.git
   cd sqlalchemy && git log --oneline | head -1
   ```

2. Clone Celery
   ```bash
   cd repos/
   git clone https://github.com/celery/celery.git
   cd celery && git log --oneline | head -1
   ```

3. Run indexer on both
   ```bash
   python benchmarks/run_benchmark.py --repo=sqlalchemy
   python benchmarks/run_benchmark.py --repo=celery
   ```

4. Classify ground truth (from ARCHITECT phase)
   - SQLAlchemy: flat (0.70 confidence)
   - Celery: microservices (0.80 confidence)

**Deliverable:** 8/8 repos indexed, predictions logged

---

## AC2: Fix Requests Misclassification

### Root Cause (from ARCHITECT phase)
File `api.py` contains stem "api" → matches PRESENTATION_TOKENS → 50% penalty → score 0.39 < threshold → UNKNOWN

### Solution: Separate File Stems from Directory Tokens

**Current (broken):** Both file stems and directory names contribute to layer vocabulary detection

**Proposed (fixed):** Only directory names (not file stems) should contribute to layer vocabulary

#### Implementation Steps

**File:** `packages/arch-intelligence/src/arch_intelligence/arch_detector.py`

**Step 1: Update token collection (line 311-330)**

Current:
```python
def _extract_tokens(self):
    """Extract directory and file tokens."""
    self.dir_tokens = set()  # Current: mixed file stems and dirs
    for file_id, path in self.symbols.files.items():
        parts = Path(path).parts
        for part in parts:
            if part not in {"..", ".", "src", "lib"}:
                self.dir_tokens.add(part)  # INCLUDES file stems
```

Changed to:
```python
def _extract_tokens(self):
    """Extract directory and file tokens."""
    self.dir_tokens = set()  # Directory names only
    self.file_stem_tokens = set()  # File stems separately
    for file_id, path in self.symbols.files.items():
        parts = Path(path).parts
        # Directory parts (all but last)
        for part in parts[:-1]:  # Skip filename
            if part not in {"..", ".", "src", "lib"}:
                self.dir_tokens.add(part)
        # File stem (last part, without extension)
        filename = parts[-1]
        if filename.endswith(".py"):
            stem = filename[:-3]
            self.file_stem_tokens.add(stem)
```

**Step 2: Update bands_present() to use only dir_tokens (line 372)**

Current:
```python
def bands_present(self):
    return [i for i, band in enumerate(LAYER_BANDS) 
            if set(self.dir_tokens) & band]  # Includes file stems
```

Changed to:
```python
def bands_present(self):
    # Only directory tokens (not file stems) for layer detection
    return [i for i, band in enumerate(LAYER_BANDS) 
            if set(self.dir_tokens) & band]  # Same code, but dir_tokens cleaned
```

**Step 3: Optional — preserve file stem analysis for debugging (line ~380)**

```python
def stem_vocabulary_strength(self):
    """Compute file stem vocabulary (for information only)."""
    token_strength = {}
    for band_name, band_tokens in zip(LAYER_NAMES, LAYER_BANDS):
        count = len(set(self.file_stem_tokens) & band_tokens)
        token_strength[band_name] = count
    return token_strength
```

#### Impact on Requests

**Before:**
- `api.py` → stem "api" → matches PRESENTATION_TOKENS
- `no_layer_vocab = False` → 50% penalty
- Score: 0.78 * 0.5 = 0.39 → UNKNOWN (0.31 confidence)

**After:**
- `api.py` → stem "api" ignored (not a directory)
- No directory-level layer vocabulary → no penalty
- Score: 0.78 → FLAT (0.75+ confidence) ✅

#### Regression Check

**Django:** Has `django/` with models/, views/, admin/ subdirectories
- Before: models/ detected as layer → LAYERED ✅
- After: Same (models/ is directory, not stem) ✅

**Flask:** Has `src/flask/` with app.py, routing/, templates/
- Before: Detected as LAYERED ✅
- After: Same (routing/ is directory) ✅

**Click:** Flat structure, no layers
- Before: FLAT ✅
- After: Same (no directories match LAYER_TOKENS) ✅

**Deliverable:** Requests detected as flat (>0.75 confidence), zero regressions on other repos

---

## AC3: Call Graph Integration

### Current State
- Call graph extracted in `IndexResult.calls`
- Not used in `ArchitectureDetector`
- Opportunity: Call patterns reveal implicit layering

### Implementation

**File:** `packages/arch-intelligence/src/arch_intelligence/arch_detector.py`

**Add method _score_call_graph_signals (after line 510)**

```python
def _score_call_graph_signals(self, calls: list[CallEdge]) -> dict:
    """
    Analyze call graph for architecture patterns.
    
    Returns:
    {
        'is_layered': score (0-1),
        'is_flat': score (0-1),
        'is_microservices': score (0-1),
        'evidence': str
    }
    """
    if not calls or len(calls) < 5:  # Too few calls → neutral
        return {
            'is_layered': 0.0,
            'is_flat': 0.0,
            'is_microservices': 0.0,
            'evidence': 'Insufficient call data'
        }
    
    # Build adjacency for analysis
    call_graph = {}  # source_file_id -> set of target_file_ids
    for call in calls:
        if call.source_file_id not in call_graph:
            call_graph[call.source_file_id] = set()
        call_graph[call.source_file_id].add(call.target_file_id)
    
    # Analyze directionality
    bidirectional = 0
    total_pairs = 0
    for src, targets in call_graph.items():
        for tgt in targets:
            total_pairs += 1
            if tgt in call_graph and src in call_graph[tgt]:
                bidirectional += 1
    
    bidirectional_ratio = bidirectional / total_pairs if total_pairs > 0 else 0
    
    # Layered: low bidirectionality (<0.2)
    # Flat: high bidirectionality (>0.5)
    # Microservices: low density, isolated clusters
    
    is_layered = 1.0 if bidirectional_ratio < 0.2 else max(0, 1.0 - (bidirectional_ratio * 2))
    is_flat = 1.0 if bidirectional_ratio > 0.5 else max(0, (bidirectional_ratio * 2) - 0.2)
    
    # Microservices: detect isolated call islands
    n_files = len(self.symbols.files)
    n_files_with_calls = len(call_graph)
    isolation_ratio = 1.0 - (n_files_with_calls / n_files) if n_files > 0 else 0
    is_microservices = 0.3 if isolation_ratio > 0.5 else 0.0
    
    return {
        'is_layered': is_layered,
        'is_flat': is_flat,
        'is_microservices': is_microservices,
        'evidence': f'bidirectional_ratio={bidirectional_ratio:.2f}, isolation={isolation_ratio:.2f}'
    }
```

**Integrate into detector (modify line 422-440)**

Current:
```python
scores = {
    'layered': self._score_layered(sig),
    'flat': self._score_flat(sig),
    'microservices': self._score_microservices(sig),
}
```

Changed to:
```python
scores = {
    'layered': self._score_layered(sig),
    'flat': self._score_flat(sig),
    'microservices': self._score_microservices(sig),
}

# Integrate call graph signals (weight: 0.15)
if hasattr(self, 'calls') and self.calls:
    cg_signals = self._score_call_graph_signals(self.calls)
    for style in ['layered', 'flat', 'microservices']:
        call_signal = cg_signals.get(f'is_{style}', 0.0)
        scores[style] = scores[style] + (call_signal * 0.15)
```

**Pass calls to detector:**

Current:
```python
result = indexer.index(repo_path)
detector = ArchitectureDetector(result.symbols)
```

Changed to:
```python
result = indexer.index(repo_path)
detector = ArchitectureDetector(result.symbols)
detector.calls = result.calls  # Pass call graph
```

**Deliverable:** Call graph integrated (0.15 weight), no regressions on accuracy

---

## AC4: Extended Framework Coverage

### Current Frameworks (8)
Flask, Django, FastAPI, Click, Celery, Starlette, Pyramid, FastStream

### Add 2-3 New Frameworks

**File:** `packages/arch-intelligence/src/arch_intelligence/arch_detector.py`

**Candidates (in priority order):**

1. **Tornado** (LAYERED)
   - Large async web framework
   - Canonical: app.py, main.py, tornado/web.py imports
   - Imports: tornado.web, tornado.ioloop, tornado.httpserver
   - Decorators: web.get, web.post, web.route

2. **Aiohttp** (LAYERED)
   - Modern async web framework
   - Canonical: app.py, main.py, aiohttp/web.py imports
   - Imports: aiohttp, aiohttp.web
   - Decorators: app.router, web.get, web.post

3. **FastAPI** (already added in Phase 5.2)

**Add to FRAMEWORK_FINGERPRINTS (line 122-160):**

```python
'tornado': {
    'architecture': LAYERED,
    'confidence': 0.85,
    'canonical_files': frozenset({'app.py', 'main.py', '__main__.py'}),
    'imports': frozenset({'tornado.web', 'tornado.ioloop', 'tornado.httpserver'}),
    'decorator_tokens': frozenset({'get', 'post', 'route', 'handler'}),
},
'aiohttp': {
    'architecture': LAYERED,
    'confidence': 0.85,
    'canonical_files': frozenset({'app.py', 'main.py', '__main__.py'}),
    'imports': frozenset({'aiohttp', 'aiohttp.web'}),
    'decorator_tokens': frozenset({'get', 'post', 'route'}),
},
```

**Update decorator detection (line 374-390):**

Add tornado/aiohttp to decorator pattern matching.

**Deliverable:** 10-12 frameworks total, fingerprints tested on real repos

---

## Implementation Checklist

### AC1: Repository Coverage
- [ ] Clone SQLAlchemy
- [ ] Clone Celery
- [ ] Index both
- [ ] Classify ground truth
- [ ] Log predictions

### AC2: Requests Fix
- [ ] Separate file stems from directory tokens
- [ ] Update bands_present() logic
- [ ] Test Requests detection (>0.75 confidence)
- [ ] Verify no regressions (Flask, Click, Django, FastAPI, LangChain)

### AC3: Call Graph Integration
- [ ] Add _score_call_graph_signals()
- [ ] Integrate into detector (0.15 weight)
- [ ] Pass calls to detector
- [ ] Validate accuracy maintained

### AC4: Framework Coverage
- [ ] Add Tornado fingerprints
- [ ] Add Aiohttp fingerprints
- [ ] Test detections
- [ ] No false positives

---

## Commits

Each task will be committed atomically:
1. `feat(phase-5.3): complete 8-repo benchmark (SQLAlchemy, Celery)`
2. `fix(phase-5.3): separate file stems from directory tokens for Requests fix`
3. `feat(phase-5.3): integrate call graph signals into architecture detector`
4. `feat(phase-5.3): add Tornado and Aiohttp framework fingerprints`

---

## Status

**Ready to execute:** All tasks planned, TEST-DESIGNER running in parallel writing hard tests.

**Blocking TEST-DESIGNER for:** Edge case discovery and regression validation.
