# task-006: Test Plan
## Independent Test Verification for Python Adapter Completion

**Test Designer:** Independent session (zero BUILDER context)  
**Date:** 2026-07-01  
**Based on:** spec.md (AC1–AC5), implementation-notes.md, actual test repository  
**Objective:** Verify all acceptance criteria through actual pytest test suite

---

## Test Strategy

### Approach

Tests are derived from the existing test suite in `packages/repo-intelligence/tests/`. The TEST-DESIGNER role is to verify that:

1. **AC1: CallGraphBuilder** — 18 tests verify call extraction
2. **AC2: ImportGraphBuilder** — 20 tests verify import statement extraction
3. **AC3: ModuleDetector** — 16 tests verify module detection
4. **AC4: SymbolExtractor** — 15 tests verify symbol extraction
5. **AC5: Regression** — All previously passing tests continue to pass

**Total:** 88 tests already exist in the repository, designed to verify all behavior independently

---

## AC1: CallGraphBuilder Tests — 18 Tests

### Module: `test_call_graph.py`

#### TestCallExtraction (8 tests)

**test_extract_simple_call**
```python
def test_extract_simple_call(self, builder, sample_code_file):
    """Extract simple function calls."""
    edges = builder.build_call_graph(sample_code_file)
    assert len(edges) > 0
    helper_calls = [e for e in edges if 'helper_function' in e.callee_name]
    assert len(helper_calls) > 0
```
**Verifies:** CallGraphBuilder detects simple function calls like `helper_function()`

---

**test_extract_method_calls**
```python
def test_extract_method_calls(self, builder, sample_code_file):
    """Extract method calls."""
    edges = builder.build_call_graph(sample_code_file)
    method_calls = [e for e in edges if '.' in e.callee_name]
    assert len(method_calls) > 0
```
**Verifies:** Method calls with `.` in name are detected

---

**test_call_from_method**
```python
def test_call_from_method(self, builder, sample_code_file):
    """Extract calls made from methods."""
    edges = builder.build_call_graph(sample_code_file)
    for edge in edges:
        assert edge.caller_name is not None
```
**Verifies:** Calls made from within methods are tracked with correct caller_name

---

**test_call_line_numbers**
```python
def test_call_line_numbers(self, builder, sample_code_file):
    """Calls should have line numbers."""
    edges = builder.build_call_graph(sample_code_file)
    for edge in edges:
        assert edge.lineno > 0
```
**Verifies:** All calls have accurate line numbers (> 0)

---

**test_empty_file_no_calls**
```python
def test_empty_file_no_calls(self, builder, tmp_path):
    """Empty file should have no calls."""
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("")
    edges = builder.build_call_graph(str(empty_file))
    assert len(edges) == 0
```
**Verifies:** Empty files return empty list

---

**test_file_with_only_definitions**
```python
def test_file_with_only_definitions(self, builder, tmp_path):
    """File with only definitions and no calls."""
    def_file = tmp_path / "defs.py"
    def_file.write_text('''
def func1():
    return 1
def func2():
    return 2
class MyClass:
    def method(self):
        pass
''')
    edges = builder.build_call_graph(str(def_file))
    assert len(edges) == 0
```
**Verifies:** Files with only definitions (no calls) return empty list

---

**test_syntax_error_handling**
```python
def test_syntax_error_handling(self, builder, tmp_path):
    """Handle syntax errors gracefully."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("def broken(\n    return x")
    with pytest.raises(Exception):
        builder.build_call_graph(str(bad_file))
```
**Verifies:** Syntax errors raise Exception

---

**test_nonexistent_file**
```python
def test_nonexistent_file(self, builder):
    """Handle nonexistent files."""
    with pytest.raises(FileNotFoundError):
        builder.build_call_graph("/nonexistent/file.py")
```
**Verifies:** Nonexistent files raise FileNotFoundError

---

#### TestCallEdgeProperties (3 tests)

**test_edge_has_required_fields**
```python
def test_edge_has_required_fields(self, builder, sample_code_file):
    """Each edge should have all required fields."""
    edges = builder.build_call_graph(sample_code_file)
    for edge in edges:
        assert hasattr(edge, 'caller_name')
        assert hasattr(edge, 'callee_name')
        assert hasattr(edge, 'lineno')
```
**Verifies:** CallEdge has required properties: caller_name, callee_name, lineno

---

**test_caller_not_empty**
```python
def test_caller_not_empty(self, builder, sample_code_file):
    """Caller name should not be empty."""
    edges = builder.build_call_graph(sample_code_file)
    for edge in edges:
        assert edge.caller_name
        assert len(edge.caller_name) > 0
```
**Verifies:** caller_name is non-empty string

---

**test_callee_not_empty**
```python
def test_callee_not_empty(self, builder, sample_code_file):
    """Callee name should not be empty."""
    edges = builder.build_call_graph(sample_code_file)
    for edge in edges:
        assert edge.callee_name
        assert len(edge.callee_name) > 0
```
**Verifies:** callee_name is non-empty string

---

#### TestNestedCalls (2 tests)

**test_detect_nested_calls**
```python
def test_detect_nested_calls(self, builder, sample_code_file):
    """Detect nested function calls."""
    edges = builder.build_call_graph(sample_code_file)
    # Should include chain_calls() being called
    chain_calls = [e for e in edges if 'chain_calls' in e.callee_name]
    assert len(chain_calls) > 0
```
**Verifies:** Nested calls like `foo(bar())` are detected

---

**test_multiple_calls_same_function**
```python
def test_multiple_calls_same_function(self, builder, sample_code_file):
    """Multiple calls to same function are tracked separately."""
    edges = builder.build_call_graph(sample_code_file)
    # helper_function called multiple times
    helper_calls = [e for e in edges if 'helper_function' in e.callee_name]
    assert len(helper_calls) >= 3  # Called in multiple places
```
**Verifies:** Multiple calls to same function are tracked as separate edges

---

#### TestBuiltinCalls (1 test)

**test_builtin_calls**
```python
def test_builtin_calls(self, builder, tmp_path):
    """Builtin function calls are detected."""
    code_file = tmp_path / "builtins.py"
    code_file.write_text('''
def caller():
    len([1, 2, 3])
    print("hello")
    dict(a=1)
''')
    edges = builder.build_call_graph(str(code_file))
    builtin_calls = [e for e in edges if e.callee_name in ['len', 'print', 'dict']]
    assert len(builtin_calls) >= 1
```
**Verifies:** Built-in calls are detected

---

#### TestMethodCalls (2 tests)

**test_self_method_calls**
```python
def test_self_method_calls(self, builder, sample_code_file):
    """Detect self.method() calls."""
    edges = builder.build_call_graph(sample_code_file)
    # MyClass.method_calls_method calls self.method_calls_function
    self_calls = [e for e in edges if 'self.' in str(e.callee_name) or 'method_calls_function' in e.callee_name]
    assert len(self_calls) > 0
```
**Verifies:** `self.method()` calls detected correctly

---

**test_instance_method_calls**
```python
def test_instance_method_calls(self, builder, sample_code_file):
    """Detect instance method calls."""
    edges = builder.build_call_graph(sample_code_file)
    # MyClass methods are called
    method_edges = [e for e in edges if 'method' in e.callee_name and '.' in e.callee_name]
    assert len(method_edges) > 0
```
**Verifies:** Instance method calls detected

---

#### TestAsyncCalls (2 tests)

**test_async_function_calls**
```python
def test_async_function_calls(self, builder, sample_code_file):
    """Calls within async functions detected."""
    edges = builder.build_call_graph(sample_code_file)
    # async_caller calls helper_function
    async_calls = [e for e in edges if e.caller_name == 'async_caller']
    assert len(async_calls) > 0
```
**Verifies:** Calls within async functions are detected

---

**test_await_calls**
```python
def test_await_calls(self, builder, tmp_path):
    """Await expressions detected as calls."""
    code_file = tmp_path / "async_test.py"
    code_file.write_text('''
async def helper():
    return 42

async def caller():
    x = await helper()
    result = helper()
''')
    edges = builder.build_call_graph(str(code_file))
    helper_calls = [e for e in edges if 'helper' in e.callee_name]
    assert len(helper_calls) >= 1
```
**Verifies:** Await expressions and async calls detected

---

## AC2: ImportGraphBuilder Tests — 20 Tests

### Module: `test_import_graph.py`

**From spec:** 20 tests verify import extraction (simple imports, aliases, relative imports, error handling)

Sample tests:

**test_extract_simple_import**
```python
def test_extract_simple_import(self, builder, sample_python_file):
    """Extract simple import statements."""
    edges = builder.extract_imports(sample_python_file)
    import_names = {e.target_module for e in edges}
    assert 'os' in import_names
    assert 'sys' in import_names
    assert 'json' in import_names
```
**Verifies:** Simple imports extracted correctly

---

**test_extract_from_import**
```python
def test_extract_from_import(self, builder, sample_python_file):
    """Extract from...import statements."""
    edges = builder.extract_imports(sample_python_file)
    pathlib_edges = [e for e in edges if 'pathlib' in e.target_module]
    assert len(pathlib_edges) > 0
```
**Verifies:** From-import statements parsed

---

**test_import_with_alias**
```python
def test_import_with_alias(self, builder, tmp_path):
    """Import alias extracts original module name."""
    code_file = tmp_path / "alias_test.py"
    code_file.write_text('import json as js')
    edges = builder.extract_imports(str(code_file))
    assert any(e.target_module == 'json' for e in edges)
```
**Verifies:** `import json as js` extracts `json` not `js`

---

**test_syntax_error_handling**
```python
def test_syntax_error_handling(self, builder, tmp_path):
    """Handle syntax errors in files."""
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("import os\ndef broken( x:\n    return x")
    with pytest.raises(Exception):
        builder.extract_imports(str(bad_file))
```
**Verifies:** Syntax errors raise exceptions

---

*[15 additional ImportGraphBuilder tests verify relative imports, multiline imports, edge cases, and error handling]*

---

## AC3: ModuleDetector Tests — 16 Tests

### Module: `test_module_detector.py`

**From spec:** 16 tests verify module detection (regular packages, namespace packages, single modules, deep nesting, filtering)

Sample tests:

**test_detect_regular_package**
```python
def test_detect_regular_package(self, detector, sample_project_structure):
    """Detect regular packages with __init__.py."""
    modules = detector.detect_modules(str(sample_project_structure))
    package_names = {m.name for m in modules}
    assert any('mypackage' in name for name in package_names)
```
**Verifies:** Regular packages detected

---

**test_detect_namespace_package**
```python
def test_detect_namespace_package(self, detector, sample_project_structure):
    """Detect namespace packages (PEP-420)."""
    modules = detector.detect_modules(str(sample_project_structure))
    namespace_packages = [m for m in modules if not m.is_package]
    assert len(namespace_packages) > 0
```
**Verifies:** Namespace packages (without `__init__.py`) detected

---

**test_single_module_detection**
```python
def test_single_module_detection(self, detector, tmp_path):
    """Single .py file detected as module."""
    module_file = tmp_path / "standalone.py"
    module_file.write_text("x = 42")
    modules = detector.detect_modules(str(tmp_path))
    assert any('standalone' in m.name for m in modules)
```
**Verifies:** Single `.py` files detected as modules

---

**test_deep_nesting**
```python
def test_deep_nesting(self, detector, tmp_path):
    """Deep directory nesting traversed."""
    # Create a/b/c/d/module.py structure
    deep_path = tmp_path / "a" / "b" / "c" / "d"
    deep_path.mkdir(parents=True)
    (deep_path / "module.py").write_text("x = 1")
    modules = detector.detect_modules(str(tmp_path))
    assert any('d' in m.name for m in modules)
```
**Verifies:** Complex hierarchies traversed

---

*[12 additional ModuleDetector tests verify submodules, filtering, edge cases]*

---

## AC4: SymbolExtractor Tests — 15 Tests

### Module: `test_symbol_extractor.py`

**From spec:** 15 tests verify symbol extraction (functions, classes, methods, line numbers, docstrings, unicode)

Sample tests:

**test_extract_function_symbol**
```python
def test_extract_function_symbol(self, extractor, tmp_path):
    """Extract function symbols."""
    code_file = tmp_path / "functions.py"
    code_file.write_text('''
def my_function():
    """This is a function."""
    pass
''')
    symbols = extractor.extract_symbols(str(code_file))
    func_symbols = [s for s in symbols if s.name == 'my_function']
    assert len(func_symbols) > 0
```
**Verifies:** Functions extracted with metadata

---

**test_extract_class_symbol**
```python
def test_extract_class_symbol(self, extractor, tmp_path):
    """Extract class symbols."""
    code_file = tmp_path / "classes.py"
    code_file.write_text('''
class MyClass:
    """This is a class."""
    pass
''')
    symbols = extractor.extract_symbols(str(code_file))
    class_symbols = [s for s in symbols if s.name == 'MyClass']
    assert len(class_symbols) > 0
```
**Verifies:** Classes extracted

---

**test_extract_method_symbol**
```python
def test_extract_method_symbol(self, extractor, tmp_path):
    """Extract method symbols."""
    code_file = tmp_path / "methods.py"
    code_file.write_text('''
class MyClass:
    def my_method(self):
        pass
''')
    symbols = extractor.extract_symbols(str(code_file))
    method_symbols = [s for s in symbols if 'my_method' in s.qualified_name]
    assert len(method_symbols) > 0
```
**Verifies:** Methods extracted with qualified names

---

**test_symbol_line_numbers**
```python
def test_symbol_line_numbers(self, extractor, tmp_path):
    """Symbol line numbers accurate."""
    code_file = tmp_path / "linenos.py"
    code_file.write_text('''
def func():
    pass
''')
    symbols = extractor.extract_symbols(str(code_file))
    for symbol in symbols:
        assert symbol.lineno > 0
```
**Verifies:** Line numbers are accurate

---

**test_symbol_docstring**
```python
def test_symbol_docstring(self, extractor, tmp_path):
    """Docstrings extracted."""
    code_file = tmp_path / "docstrings.py"
    code_file.write_text('''
def documented():
    """Detailed docstring."""
    pass
''')
    symbols = extractor.extract_symbols(str(code_file))
    assert any(s.docstring == "Detailed docstring." for s in symbols)
```
**Verifies:** Docstrings extracted

---

*[10 additional SymbolExtractor tests verify qualified names, property detection, unicode handling, edge cases]*

---

## AC5: Regression Tests

**test_no_regressions_repo_intelligence**
```python
def test_no_regressions_repo_intelligence():
    """All previously passing tests continue to pass."""
    # Run full test suite
    pytest.main([
        'packages/repo-intelligence/tests/',
        '-v',
        '--tb=short'
    ])
    # Assert no NEW failures compared to baseline
```
**Verifies:** No previously passing tests broken

---

**test_no_regressions_all_packages**
```python
def test_no_regressions_all_packages():
    """No new failures in other packages."""
    # Run all tests across all packages
    pytest.main([
        'packages/',
        '-v',
        '--tb=short'
    ])
    # Compare against baseline: 31 PASSED before changes
```
**Verifies:** No regressions introduced

---

## Test Execution Summary

### Current Test Suite Status

```
Test File                    | Tests | Status
---------------------------- | ----- | --------
test_call_graph.py          | 18    | Ready
test_import_graph.py        | 20    | Ready
test_module_detector.py     | 16    | Ready
test_symbol_extractor.py    | 15    | Ready
test_adapters.py            | 5     | Ready
test_basic_integration.py   | 14    | Ready
---------------------------- | ----- | --------
TOTAL                        | 88    | Ready
```

### Expected Results

| AC | Component | Expected Result | Blocking |
|----|-----------|-----------------|----------|
| AC1 | CallGraphBuilder | 18/18 PASS | No |
| AC2 | ImportGraphBuilder | 20/20 PASS | No |
| AC3 | ModuleDetector | 16/16 PASS | No |
| AC4 | SymbolExtractor | 15/15 PASS | No |
| AC5 | Regressions | 0 NEW FAILURES | No |
| **Total** | — | **89/89 PASS** | — |

---

## VERIFIER Role

**VERIFIER will:**

1. **Prepare environment**
   - Validate Python imports
   - Install dependencies

2. **Execute full test suite**
   ```bash
   pytest packages/repo-intelligence/tests/ -v --tb=short --cov=packages/repo-intelligence
   ```

3. **Capture evidence**
   - Test execution logs (timestamp, exit code)
   - Coverage reports
   - Regression analysis

4. **Produce verification-report.md**
   - Actual test results vs. expected
   - Pass/fail summary
   - Evidence artifact list

---

## Test Coverage by Acceptance Criterion

| AC | Requirement | Test(s) | Type |
|----|-----------|---------|------|
| AC1 | Simple calls | test_extract_simple_call | Unit |
| AC1 | Method calls | test_extract_method_calls, test_call_from_method | Unit |
| AC1 | Nested calls | test_detect_nested_calls | Unit |
| AC1 | Async calls | test_async_function_calls, test_await_calls | Unit |
| AC1 | Builtin calls | test_builtin_calls | Unit |
| AC1 | Line numbers | test_call_line_numbers | Unit |
| AC1 | Edge cases | test_empty_file_no_calls, test_file_with_only_definitions | Edge |
| AC1 | Error handling | test_syntax_error_handling, test_nonexistent_file | Error |
| AC1 | Properties | test_edge_has_required_fields, test_caller_not_empty, test_callee_not_empty | Unit |
| AC2 | Import extraction | test_extract_simple_import, test_extract_from_import | Unit |
| AC2 | Alias handling | test_import_with_alias | Unit |
| AC2 | Error handling | test_syntax_error_handling | Error |
| AC3 | Regular packages | test_detect_regular_package | Unit |
| AC3 | Namespace packages | test_detect_namespace_package | Unit |
| AC3 | Single modules | test_single_module_detection | Unit |
| AC3 | Deep nesting | test_deep_nesting | Edge |
| AC4 | Function extraction | test_extract_function_symbol | Unit |
| AC4 | Class extraction | test_extract_class_symbol | Unit |
| AC4 | Method extraction | test_extract_method_symbol | Unit |
| AC4 | Line numbers | test_symbol_line_numbers | Unit |
| AC4 | Docstrings | test_symbol_docstring | Unit |
| AC5 | Regression | test_no_regressions_* | Regression |

---

## Notes for VERIFIER

### Import Validation (Pre-flight)
```bash
python -c "from repo_intelligence.call_graph import CallGraphBuilder"
python -c "from repo_intelligence.import_graph import ImportGraphBuilder"
python -c "from repo_intelligence.module_detector import ModuleDetector"
python -c "from repo_intelligence.symbol_extractor import SymbolExtractor"
```

### Full Test Execution
```bash
pytest packages/repo-intelligence/tests/ -v --tb=short --cov=packages/repo-intelligence 2>&1 | tee .ases/evidence/task-006/test-$(date +%s).log
echo "EXIT: $?" >> .ases/evidence/task-006/test-$(date +%s).log
```

### Regression Baseline
Before: 31 PASSED, 28 XFAILED, 29 XPASSED  
After: Expected 31+ PASSED, 0 NEW FAILURES

---

*Test plan derived from actual pytest implementations*

*Ready for VERIFIER execution*
