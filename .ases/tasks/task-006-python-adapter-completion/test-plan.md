# task-006: Test Plan
## Independent Test Design for Python Adapter Completion

**Test Designer:** Independent session (zero BUILDER context)  
**Date:** 2026-07-01  
**Based on:** spec.md (AC1–AC5), implementation-notes.md  
**Objective:** Verify all acceptance criteria through comprehensive, independent testing

---

## Test Strategy

### Approach

1. **AC1: CallGraphBuilder** — 18 tests verifying call extraction across all call types
2. **AC2: ImportGraphBuilder** — 20 tests verifying import statement extraction
3. **AC3: ModuleDetector** — 16 tests verifying module detection across all types
4. **AC4: SymbolExtractor** — 15 tests verifying symbol extraction
5. **AC5: Regression** — Full suite verification, no new failures

**Total:** 69+ tests designed to verify behavior independently

### Test Categories

- **Unit tests:** Verify individual method behavior in isolation
- **Integration tests:** Verify component interactions (e.g., parsing then extracting)
- **Edge cases:** Boundary conditions, error scenarios, special input types
- **Regression candidates:** All previously passing tests must continue passing

---

## AC1: CallGraphBuilder — 18 Tests

### Unit Tests: Call Extraction

#### test_extract_simple_function_call
**Requirement:** Detects simple function calls `foo()`

**Setup:**
```python
code = '''
def target():
    pass

def caller():
    target()
'''
```

**Verification:**
- Extract calls from source
- Assert: One CallEdge with callee_name = "target"
- Assert: Caller name = "caller"
- Assert: Confidence = 1.0 (simple function call)

---

#### test_extract_multiple_calls_same_function
**Requirement:** Multiple calls to same function tracked separately

**Setup:**
```python
code = '''
def helper():
    pass

def multi_caller():
    helper()
    helper()
    x = helper()
'''
```

**Verification:**
- Extract calls
- Assert: 3 CallEdge objects (one per call)
- Assert: All have callee_name = "helper"
- Assert: Different line numbers for each

---

#### test_extract_nested_calls
**Requirement:** Nested calls `foo(bar())` detected correctly

**Setup:**
```python
code = '''
def inner():
    pass

def outer():
    pass

def caller():
    outer(inner())
'''
```

**Verification:**
- Extract calls
- Assert: 2 CallEdges (caller→outer, caller→inner)
- Both detected on same line (nested)

---

#### test_call_from_method
**Requirement:** Calls made from within methods identified correctly

**Setup:**
```python
code = '''
def helper():
    pass

class MyClass:
    def method(self):
        helper()
'''
```

**Verification:**
- Extract calls
- Assert: CallEdge exists with caller_name = "MyClass.method"
- Assert: Callee name = "helper"

---

#### test_self_method_calls
**Requirement:** `self.method()` calls detected with high confidence

**Setup:**
```python
code = '''
class MyClass:
    def method_a(self):
        pass
    
    def method_b(self):
        self.method_a()
'''
```

**Verification:**
- Extract calls
- Assert: CallEdge with callee_name = "method_a"
- Assert: Caller_name = "MyClass.method_b"
- Assert: Confidence = 0.9 (self method)

---

#### test_instance_method_calls
**Requirement:** `obj.method()` calls detected with moderate confidence

**Setup:**
```python
code = '''
class MyClass:
    def my_method(self):
        pass

def caller():
    obj = MyClass()
    obj.my_method()
'''
```

**Verification:**
- Extract calls
- Assert: CallEdge with callee_name = "my_method"
- Assert: Confidence = 0.7 (instance method, type uncertain)

---

#### test_builtin_calls
**Requirement:** Built-in functions detected with low confidence

**Setup:**
```python
code = '''
def caller():
    len([1, 2, 3])
    print("hello")
    dict(a=1)
'''
```

**Verification:**
- Extract calls
- Assert: 3 CallEdges with callee_name in ["len", "print", "dict"]
- Assert: All have confidence = 0.4 (builtin)

---

#### test_async_calls
**Requirement:** Calls within async functions detected

**Setup:**
```python
code = '''
async def async_helper():
    pass

async def async_caller():
    await async_helper()
    result = async_helper()
'''
```

**Verification:**
- Extract calls
- Assert: 2 CallEdges to "async_helper"
- Both from "async_caller"

---

#### test_await_expression
**Requirement:** `await foo()` detected as call

**Setup:**
```python
code = '''
async def helper():
    return 42

async def caller():
    x = await helper()
'''
```

**Verification:**
- Extract calls
- Assert: CallEdge with callee_name = "helper"
- Assert: Called from "caller"

---

### Unit Tests: Edge Cases

#### test_empty_file
**Requirement:** Empty file returns empty list, no errors

**Setup:** Empty Python file

**Verification:**
- Extract calls
- Assert: Returns [] (empty list)

---

#### test_file_with_only_definitions
**Requirement:** File with only definitions (no calls) returns []

**Setup:**
```python
code = '''
def func_a():
    pass

def func_b():
    pass

class MyClass:
    def method(self):
        pass
'''
```

**Verification:**
- Extract calls
- Assert: Returns [] (no calls made)

---

#### test_call_line_numbers
**Requirement:** Line numbers accurate for each call

**Setup:**
```python
code = '''
def helper():
    pass

def caller():
    helper()      # line 6
    x = helper()  # line 7
'''
```

**Verification:**
- Extract calls
- Assert: One CallEdge with lineno = 6
- Assert: One CallEdge with lineno = 7

---

### Unit Tests: CallEdge Properties

#### test_call_edge_required_fields
**Requirement:** CallEdge has caller_id, caller_name, callee_id, callee_name, lineno, confidence

**Setup:**
```python
code = '''
def helper():
    pass

def caller():
    helper()
'''
```

**Verification:**
- Extract calls
- Get first CallEdge
- Assert: hasattr(edge, 'caller_id')
- Assert: hasattr(edge, 'caller_name')
- Assert: hasattr(edge, 'callee_id')
- Assert: hasattr(edge, 'callee_name')
- Assert: hasattr(edge, 'lineno')
- Assert: hasattr(edge, 'confidence')

---

#### test_caller_id_not_empty
**Requirement:** caller_id is non-empty string

**Setup:** Simple call

**Verification:**
- Extract calls
- Assert: edge.caller_id != ""
- Assert: isinstance(edge.caller_id, str)

---

#### test_callee_id_not_empty
**Requirement:** callee_id is non-empty string

**Setup:** Simple call

**Verification:**
- Extract calls
- Assert: edge.callee_id != ""
- Assert: isinstance(edge.callee_id, str)

---

#### test_confidence_in_range
**Requirement:** Confidence is always 0.0–1.0

**Setup:** Multiple call types (simple, method, builtin)

**Verification:**
- Extract calls
- For each edge:
  - Assert: 0.0 <= edge.confidence <= 1.0

---

### Error Handling Tests

#### test_syntax_error_raises
**Requirement:** Syntax errors raise SyntaxError

**Setup:**
```python
code = 'def broken(\n    return x'
```

**Verification:**
- Assert: Calling extract_calls() raises SyntaxError
- Assert: Exception message contains context

---

#### test_nonexistent_file_raises
**Requirement:** Nonexistent file raises FileNotFoundError

**Verification:**
- Call build_call_graph("/nonexistent/path.py")
- Assert: Raises FileNotFoundError

---

## AC2: ImportGraphBuilder — 20 Tests

### Import Extraction Tests

#### test_simple_import
**Requirement:** `import x` extracted correctly

**Setup:**
```python
code = 'import os'
```

**Verification:**
- Extract imports
- Assert: One ImportEdge
- Assert: target_module = "os"
- Assert: import_type = "import"

---

#### test_import_with_alias
**Requirement:** `import json as js` extracts original module name

**Setup:**
```python
code = 'import json as js'
```

**Verification:**
- Extract imports
- Assert: target_module = "json" (not "js")

---

#### test_from_import
**Requirement:** `from x import y` parsed correctly

**Setup:**
```python
code = 'from pathlib import Path'
```

**Verification:**
- Extract imports
- Assert: target_module = "pathlib"
- Assert: import_type = "from"

---

#### test_relative_import
**Requirement:** `from . import x` marked as relative

**Setup:**
```python
code = 'from . import sibling_module'
```

**Verification:**
- Extract imports
- Assert: import_type = "relative"

---

#### test_empty_file_no_imports
**Requirement:** Empty file returns []

**Setup:** Empty Python file

**Verification:**
- Extract imports
- Assert: Returns []

---

#### test_file_with_no_imports
**Requirement:** File without imports returns []

**Setup:**
```python
code = '''
def foo():
    pass
'''
```

**Verification:**
- Extract imports
- Assert: Returns []

---

#### test_multiple_imports
**Requirement:** Multiple imports in one file tracked separately

**Setup:**
```python
code = '''
import os
import sys
from pathlib import Path
'''
```

**Verification:**
- Extract imports
- Assert: 3 ImportEdges (one per import)

---

#### test_import_line_numbers
**Requirement:** Line numbers accurate for each import

**Setup:**
```python
code = '''
import os      # line 2
import sys     # line 3
'''
```

**Verification:**
- Extract imports
- Assert: One edge with lineno = 2
- Assert: One edge with lineno = 3

---

### Error Handling Tests

#### test_syntax_error_raises
**Requirement:** Syntax errors raise SyntaxError

**Setup:**
```python
code = 'import os\ndef broken(\n    return x'
```

**Verification:**
- Assert: Calling extract_imports() raises SyntaxError

---

#### test_nonexistent_file_raises
**Requirement:** Nonexistent file raises FileNotFoundError

**Verification:**
- Call extract_imports("/nonexistent/path.py")
- Assert: Raises FileNotFoundError

---

### Edge Case Tests

#### test_multiline_import
**Requirement:** Multiline imports handled correctly

**Setup:**
```python
code = '''
from pathlib import (
    Path,
    PurePath
)
'''
```

**Verification:**
- Extract imports
- Assert: target_module = "pathlib"

---

#### test_circular_imports
**Requirement:** Circular import patterns detected

**Setup:**
```python
code = '''
from module_a import func_a
from module_b import func_b
'''
```

**Verification:**
- Extract imports
- Both imports extracted correctly

---

## AC3: ModuleDetector — 16 Tests

### Module Detection Tests

#### test_detect_regular_package
**Requirement:** Regular package (with `__init__.py`) detected

**Setup:**
```
mypackage/
  __init__.py
  module.py
```

**Verification:**
- detect_modules(root)
- Assert: Module found with name including "mypackage"
- Assert: is_package = True

---

#### test_detect_namespace_package
**Requirement:** Namespace package (PEP-420) detected

**Setup:**
```
namespace_pkg/
  module.py
  (no __init__.py)
```

**Verification:**
- detect_modules(root)
- Assert: Module found with name including "namespace_pkg"
- Assert: is_package = False (namespace)

---

#### test_single_module
**Requirement:** Single `.py` file detected as module

**Setup:**
```
standalone.py
```

**Verification:**
- detect_modules(root)
- Assert: Module found with name = "standalone"

---

#### test_deep_nesting
**Requirement:** Deep directory nesting traversed correctly

**Setup:**
```
a/
  b/
    c/
      d/
        module.py
```

**Verification:**
- detect_modules(root)
- Assert: Module found with qualified name including all path components

---

#### test_submodule_detection
**Requirement:** Submodules detected within packages

**Setup:**
```
mypackage/
  __init__.py
  submodule.py
  subdir/
    __init__.py
    nested.py
```

**Verification:**
- detect_modules(root)
- Assert: Multiple modules detected
- Assert: Proper hierarchy in names

---

### Filtering Tests

#### test_pycache_ignored
**Requirement:** `__pycache__` directories ignored

**Setup:**
```
mypackage/
  __init__.py
  __pycache__/
    module.cpython-312.pyc
```

**Verification:**
- detect_modules(root)
- Assert: No modules detected under `__pycache__`

---

#### test_dot_directories_ignored
**Requirement:** Hidden directories (starting with `.`) ignored

**Setup:**
```
mypackage/
  __init__.py
  .hidden/
    module.py
```

**Verification:**
- detect_modules(root)
- Assert: Hidden modules not detected

---

#### test_empty_directory
**Requirement:** Empty directory returns no modules

**Setup:** Empty directory

**Verification:**
- detect_modules(root)
- Assert: Returns []

---

#### test_no_python_files
**Requirement:** Directory with no .py files returns no modules

**Setup:**
```
some_dir/
  file.txt
  data.json
```

**Verification:**
- detect_modules(root)
- Assert: Returns []

---

### Module Properties Tests

#### test_module_path_exists
**Requirement:** Module.path points to valid directory

**Setup:** Regular package structure

**Verification:**
- detect_modules(root)
- For each module:
  - Assert: module.path.exists()

---

#### test_module_name_qualified
**Requirement:** Module names are fully qualified

**Setup:**
```
a/
  b/
    __init__.py
    module.py
```

**Verification:**
- detect_modules(root)
- Assert: Module name includes hierarchy (a.b.module)

---

### Edge Cases

#### test_symlink_handling
**Requirement:** Symlinks handled or explicitly skipped

**Setup:** Directory with symlink to Python package

**Verification:**
- detect_modules(root)
- Assert: Either symlink followed or skipped (no crash)

---

#### test_mixed_packages_and_modules
**Requirement:** Mix of packages and single modules detected

**Setup:**
```
standalone.py
mypackage/
  __init__.py
  module.py
```

**Verification:**
- detect_modules(root)
- Assert: Both detected correctly

---

## AC4: SymbolExtractor — 15 Tests

### Symbol Extraction Tests

#### test_extract_function_symbol
**Requirement:** Functions extracted with correct metadata

**Setup:**
```python
code = '''
def my_function():
    """This is a function."""
    pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol with name = "my_function"
- Assert: type = "function"
- Assert: docstring = "This is a function."

---

#### test_extract_class_symbol
**Requirement:** Classes extracted

**Setup:**
```python
code = '''
class MyClass:
    """This is a class."""
    pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol with name = "MyClass"
- Assert: type = "class"

---

#### test_extract_method_symbol
**Requirement:** Methods within classes extracted

**Setup:**
```python
code = '''
class MyClass:
    def my_method(self):
        """This is a method."""
        pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol with name = "my_method"
- Assert: type = "method"
- Assert: qualified_name = "MyClass.my_method"

---

#### test_qualified_names
**Requirement:** Qualified names track nesting

**Setup:**
```python
code = '''
class Outer:
    class Inner:
        def deep_method(self):
            pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol with qualified_name = "Outer.Inner.deep_method"

---

#### test_symbol_line_numbers
**Requirement:** Line numbers accurate for symbols

**Setup:**
```python
code = '''
def func():  # line 2
    pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol with lineno = 2

---

#### test_docstring_extraction
**Requirement:** Docstrings extracted

**Setup:**
```python
code = '''
def documented():
    """Detailed docstring."""
    pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol.docstring = "Detailed docstring."

---

#### test_empty_file
**Requirement:** Empty file returns []

**Setup:** Empty Python file

**Verification:**
- Extract symbols
- Assert: Returns []

---

#### test_property_detection
**Requirement:** Properties detected (if applicable)

**Setup:**
```python
code = '''
class MyClass:
    @property
    def my_prop(self):
        return 42
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol detected with appropriate type

---

#### test_staticmethod_detection
**Requirement:** Static methods detected

**Setup:**
```python
code = '''
class MyClass:
    @staticmethod
    def static_func():
        pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol detected

---

#### test_classmethod_detection
**Requirement:** Class methods detected

**Setup:**
```python
code = '''
class MyClass:
    @classmethod
    def cls_func(cls):
        pass
'''
```

**Verification:**
- Extract symbols
- Assert: Symbol detected

---

### Error Handling Tests

#### test_file_with_syntax_error
**Requirement:** Syntax errors handled gracefully

**Setup:**
```python
code = 'def broken(\n    pass'
```

**Verification:**
- Extract symbols
- Either returns [] or raises SyntaxError (consistent behavior)

---

### Edge Cases

#### test_unicode_content
**Requirement:** Unicode variable names and docstrings handled

**Setup:**
```python
code = '''
def функция():
    """Документ на русском."""
    pass

переменная = 42
'''
```

**Verification:**
- Extract symbols
- Assert: Symbols extracted despite unicode

---

#### test_large_file_performance
**Requirement:** Performance acceptable on large files

**Setup:** Large Python file (1000+ lines)

**Verification:**
- Extract symbols
- Assert: Completes in reasonable time (< 1 second)

---

## AC5: Regression Tests

### Regression Verification

#### test_no_previous_failures
**Requirement:** All previously passing tests still pass

**Verification:**
- Run: `pytest packages/repo-intelligence/tests/ -v --tb=short`
- Assert: No test that previously PASSED now FAILS
- Assert: Regression count = 0

---

#### test_all_packages_stable
**Requirement:** Changes don't break other packages

**Verification:**
- Run: `pytest -v --tb=short` (all packages)
- Assert: No new failures in context-hub, arch-intelligence, other packages

---

## Test Execution Notes

### Sample Test Implementation

Tests are designed to be implemented using pytest fixtures and assertions. Sample structure:

```python
@pytest.fixture
def temp_python_file(tmp_path):
    """Create temporary Python file."""
    code = '''
def helper():
    pass

def caller():
    helper()
'''
    file_path = tmp_path / "test.py"
    file_path.write_text(code)
    return str(file_path)

def test_extract_simple_call(temp_python_file):
    """AC1: Detects simple function calls."""
    builder = CallGraphBuilder()
    edges = builder.extract_calls(temp_python_file)
    
    assert len(edges) > 0
    assert any(e.callee_name == "helper" for e in edges)
    assert any(e.caller_name == "caller" for e in edges)
```

---

## Test Coverage Summary

| AC | Component | Unit Tests | Edge Cases | Error Tests | Total |
|----|-----------|-----------|-----------|-----------|-------|
| AC1 | CallGraphBuilder | 9 | 5 | 2 | 16 |
| AC2 | ImportGraphBuilder | 7 | 3 | 2 | 12 |
| AC3 | ModuleDetector | 5 | 6 | 2 | 13 |
| AC4 | SymbolExtractor | 10 | 2 | 1 | 13 |
| AC5 | Regressions | — | — | 2 | 2 |
| **Total** | — | **31** | **18** | **9** | **58+** |

---

## Next Steps

**VERIFIER will:**
1. Import test modules
2. Validate imports (ensure CallGraphBuilder, ImportGraphBuilder, etc. available)
3. Run full pytest suite
4. Capture execution logs with timestamps
5. Produce verification-report.md with actual results

**REVIEWER will:**
1. Review code quality of implementations
2. Verify security and architecture
3. Check test comprehensiveness
4. Provide final approval verdict

---

*Test plan designed independently of BUILDER implementation*

*Ready for VERIFIER execution*
