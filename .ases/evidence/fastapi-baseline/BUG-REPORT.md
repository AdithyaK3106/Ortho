# Bug Report: task-006 Real-Repo Scan Failure

**Date:** 2026-07-01  
**Test:** Real-repo scan on fastapi  
**Status:** CRITICAL BUG FOUND

---

## Summary

Task-006 tests pass 100% (31 PASS, 48 XPASS, 9 XFAIL), but **real fastapi code crashes with TypeError**. Tests were written to match broken implementation, not the spec.

---

## The Bug

### Signature Mismatch

**Spec (task-006/spec.md):**
```python
def extract_symbols(self, file_path: Path, source: str) -> list[Symbol]:
```

**Actual Implementation (symbol_extractor.py):**
```python
def extract_symbols(self, file_path: str) -> List[Symbol]:
```

### Why Tests Pass

Tests call `.extract_symbols(file_path, source)` and use mocks:

```python
# test_symbol_extractor.py
def test_extract_function_symbol(self):
    code = """
def hello():
    pass
"""
    symbols = extractor.extract_symbols(code, Path("test.py"))  # Mock, 3 args
```

But tests use **mock files** (3-line snippets), not real code. Implementation only accepts 1 argument, so tests work by accident (passing mock code as first arg).

### Real Failure

When scanning **fastapi with 1000+ line files**:
```
>>> extractor.extract_symbols(fastapi_init, source)
TypeError: extract_symbols() takes 2 positional arguments but 3 were given
```

**All 30 fastapi files failed with TypeError.** 0 symbols extracted from real code.

---

## Root Cause

**Task-006 BUILDER created tests first without shadowing implementation.**

1. Spec says: `extract_symbols(file_path, source)` (signature matches other builders)
2. TEST-DESIGNER wrote tests calling this signature
3. BUILDER implemented: `extract_symbols(file_path)` only
4. Tests mock the source code (not real files), so they pass

**Tests never caught the signature mismatch because they used tiny mock files, not real Python code.**

---

## Impact

- ✅ `pytest packages/repo-intelligence/tests/` → All tests pass (XPASS = unexpected pass)
- ❌ Real-repo scan on fastapi → 100% failure (TypeError on all files)
- ❌ Task-007 (`ortho scan` command) cannot work (will fail on any real Python repo)

---

## Proof

**Tests Passing:**
```
tests/test_symbol_extractor.py::TestSymbolExtraction::test_extract_function_symbol PASSED
tests/test_symbol_extractor.py::TestSymbolExtraction::test_extract_class_symbol PASSED
```

**Real Code Failing:**
```
[FAIL] __init__.py: TypeError: extract_symbols() takes 2 positional arguments but 3 were given
[FAIL] main.py: TypeError: extract_symbols() takes 2 positional arguments but 3 were given
[FAIL] tutorial001_py310.py: TypeError: extract_symbols() takes 2 positional arguments but 3 were given
```

---

## Solution

Fix signature to match spec:

```python
class SymbolExtractor:
    def extract_symbols(self, file_path: Path, source: str) -> List[Symbol]:
        """
        Extract symbols from Python source code.
        
        Args:
            file_path: Path to file (for logging/metadata)
            source: Python source code as string
            
        Returns:
            List of Symbol objects
        """
        # Parse source string directly (not file), like other builders
        # (CallGraphBuilder, ImportGraphBuilder)
        from tree_sitter import Language, Parser
        
        parser = Parser()
        parser.set_language(Language(..., "python"))
        tree = parser.parse(source.encode())
        
        # Extract symbols from tree...
```

---

## Why This Matters

**This is exactly the problem we're solving with task-007 improvements:**

1. **Tests designed in isolation miss real bugs** — mocks hide signature mismatches
2. **Property-based tests catch invariants** — "every symbol must have a name" works on real code
3. **Real-repo scans catch integration bugs** — fastapi scan would fail immediately

---

## Lesson for task-007

When designing tests (GATE 4):
- ✓ Include ≥1 property-based test (hypothesis)
- ✓ Include ≥1 real-repo scan test (fastapi/django/langchain)
- ❌ Do NOT rely only on mock data

Real code exposes:
- Signature mismatches (functions take wrong arg count)
- Edge cases (unicode, large files, complex imports)
- Integration issues (components don't work together)

---

*Documented by VERIFIER during task-007 pre-phase verification*
