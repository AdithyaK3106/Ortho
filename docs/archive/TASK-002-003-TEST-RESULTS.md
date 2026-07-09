# Task-002-003: Python Adapter Test Results

**Date:** 2026-07-01  
**Status:** 16/88 passing (18%), 37 failed, 35 errors  
**Root Cause:** API mismatches + missing implementations  

---

## Test Summary

| Category | Count | Status |
|----------|-------|--------|
| PASSED | 16 | ✅ Working |
| FAILED | 37 | ❌ API mismatch |
| ERROR | 35 | ❌ Constructor/import error |
| **TOTAL** | **88** | **18% pass rate** |

---

## What's Passing (16 tests)

### Imports & Basic Setup (7/13 basic tests pass)
```
✅ test_import_python_adapter
✅ test_import_symbol_extractor
✅ test_import_import_graph_builder
✅ test_adapter_has_required_methods
✅ test_parse_simple_file
✅ test_parse_handles_missing_file
✅ test_adapter_initialization
✅ test_adapter_is_callable
✅ test_adapter_has_parse_method
✅ test_extractor_has_extract_method (2 tests)
```

**What works:** Core imports work, PythonAdapter initializes correctly (dependency fix helped!)

---

## Critical Failures (37 failed, 35 errors)

### Error Type 1: Constructor Signature Mismatch (35 errors)

**Pattern:**
```python
# Test does this:
builder = CallGraphBuilder()
detector = ModuleDetector()
edges = builder.extract_calls(file)

# But code expects:
builder = CallGraphBuilder(repo_root, python_files)
detector = ModuleDetector(repo_root)
edges = builder.extract_calls_from_tree(tree)
```

**Affected Tests (35 total errors):**
- `test_call_graph.py` — All 20 tests (CallGraphBuilder expects args)
- `test_module_detector.py` — All 20 tests (ModuleDetector expects repo_root)
- `test_symbol_extractor.py` — No direct errors but method names don't match

### Error Type 2: Method Name Mismatches (17 failed)

**Pattern:**
```python
# Tests call:
builder.extract_imports(file_path)
builder.extract_calls(file_path)
extractor.extract(file_path)

# But actual methods are:
builder.build()  # takes no args in constructor
builder.get_call_graph()
extractor.extract_symbols(tree)  # expects AST tree, not file path
```

**Affected Tests (17 failures):**
- `test_import_graph.py` — 14 tests fail on `extract_imports` (doesn't exist)
- `test_symbol_extractor.py` — 14 tests fail on method signatures

### Error Type 3: Syntax Error Handling (1 failure)

```python
test_adapters.py::TestPythonAdapterBasics::test_syntax_error_file
E   AssertionError: DID NOT RAISE <class 'Exception'>
```

Code doesn't raise on syntax errors; returns None instead.

---

## Root Causes

### 1. **API Mismatch Between Design & Implementation**

Tests were designed as if the API was:
```python
adapter = PythonAdapter()
tree = adapter.parse(file_path)  # File path → AST

builder = ImportGraphBuilder()
edges = builder.extract_imports(file_path)  # File path → edges

detector = ModuleDetector()
modules = detector.detect_modules(root)  # String root → modules
```

But actual implementation is:
```python
adapter = PythonAdapter()
tree = adapter.parse(file_path)  # ✅ This part is correct

builder = ImportGraphBuilder()
builder.build()  # Takes nothing, builds internally
# or requires: builder = ImportGraphBuilder(repo_root, python_files)

detector = ModuleDetector()
# Actually requires: detector = ModuleDetector(repo_root)
detector.detect_modules(root)  # Different signature
```

### 2. **Constructor Requirements Not Documented**

From looking at actual code:
- `CallGraphBuilder(repo_root, python_files)` — needs both
- `ModuleDetector(repo_root)` — needs repo root
- Tests written to `CallGraphBuilder()` — constructor with no args

### 3. **Missing Method Implementations**

Tests call:
- `builder.extract_imports(file)` → doesn't exist
- `builder.extract_calls(file)` → doesn't exist
- `extractor.extract(file)` → might be `extract_symbols(tree)`

---

## What Needs Fixing

### Fix 1: Update Test Constructor Calls (35 errors)

**Example:**
```python
# Current (WRONG):
def test_extract_simple_call(self):
    builder = CallGraphBuilder()
    
# Fixed:
def test_extract_simple_call(self):
    builder = CallGraphBuilder("/test/repo", ["/test/repo/file.py"])
```

**Affected files:**
- `test_call_graph.py` — update all 20 tests
- `test_module_detector.py` — update all 20 tests

### Fix 2: Update Method Names (17 failures)

**Example:**
```python
# Current (WRONG):
edges = builder.extract_imports(file_path)

# Fixed (check actual method):
edges = builder.build_graph()  # or whatever it's actually called
```

**Affected files:**
- `test_import_graph.py` — update all 14 tests
- `test_symbol_extractor.py` — update method calls

### Fix 3: Update Error Handling (1 failure)

**Current:**
```python
with pytest.raises(Exception):
    adapter.parse(bad_file)
```

**Fixed:**
```python
result = adapter.parse(bad_file)
assert result is None or result.has_error
```

---

## Why This Happened

**Timeline:**
1. Phase 1: Tests designed (assumed simple API)
2. Implementation built: Actual API more complex (needs repo context, etc.)
3. Tests never executed: Gap hidden
4. Now (2026-07-01): Running tests reveals API mismatch

**This is exactly why Phase 2+ enforces test execution during BUILDER stage** — mismatch caught immediately, not weeks later.

---

## Fix Effort

| Item | Effort | Impact |
|------|--------|--------|
| Fix constructor calls (35 errors) | 1 hour | Unblocks 35 tests |
| Fix method names (17 failures) | 1.5 hours | Fixes 17 tests |
| Fix error handling (1 failure) | 15 min | Fixes 1 test |
| **TOTAL** | **2.75 hours** | **53/88 tests → pass** |

**Estimated result after fixes:** 53/88 passing (60%)

---

## Next Steps

1. **Read actual source code** (not test code) to find real method names
2. **Update test signatures** to match actual constructor params
3. **Update test method calls** to use actual method names
4. **Re-run pytest** to verify improvements

Want me to start fixing these now? Or document them in BUGS.md first?

---

## Evidence Files

- `.ases/evidence/task-002-003/test-run-fixed.log` — Full pytest output

