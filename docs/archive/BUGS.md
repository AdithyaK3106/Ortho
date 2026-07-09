# Ortho Bug Report

**Date:** 2026-07-07  
**Status:** Active Testing  
**Found During:** End-to-End Testing on FastAPI & LangChain

---

## Bug Tracker

### BUG-001: CLI Path Resolution Issue (CRITICAL)

**Severity:** CRITICAL  
**Component:** `apps/cli/src/commands/scan.ts`  
**Status:** CONFIRMED  

**Description:**
When running `ortho scan` from a different directory (e.g., `Repos/fastapi`), the CLI cannot find the Python script path because `__dirname` resolves relative to the compiled module location, not the current working directory.

**Error:**
```
python: can't open file 'C:\Users\urbra\OneDrive\Desktop\Projects\ortho\apps\cli\python\scan_cli.py': [Errno 2] No such file or directory
```

**Root Cause:**
In `scan.ts` line 26-29, the path calculation uses `__dirname`:
```typescript
const pythonScript = path.join(
  __dirname,
  "../../../../packages/repo-intelligence/src/repo_intelligence/scan_cli.py"
);
```

When compiled, `__dirname` points to `dist/commands/`, but the relative path calculation assumes it's relative to `src/commands/`. This works when running from the Ortho root but fails from other directories.

**Expected Behavior:**
- CLI should find Python scripts regardless of current working directory
- Path resolution should be absolute or relative to the CLI installation

**Fix Approach:**
1. Use `process.env.ORTHO_ROOT` (if set) or
2. Use `require.main.filename` to get the entry point and calculate from there
3. Or hardcode the absolute path to the installed Ortho location

**Similar Issues:**
- `index.ts` (analyze.ts, index.ts commands likely have same issue)

**Test Case:**
```bash
cd C:/Users/urbra/OneDrive/Desktop/Projects/ortho/Repos/fastapi
node ../../apps/cli/dist/index.js scan
# Expected: Success
# Actual: "can't open file" error
```

---

### BUG-002: Module Import Structure (HIGH)

**Severity:** HIGH  
**Component:** `packages/repo-intelligence`, all packages  
**Status:** CONFIRMED

**Description:**
Python modules cannot be imported as `from packages.repo_intelligence import X` because the package structure doesn't match the import path. Tests that directly import modules fail.

**Error:**
```python
ModuleNotFoundError: No module named 'packages.repo_intelligence'
```

**Root Cause:**
The `packages/` directory is not a proper Python package. The `__init__.py` files either don't exist or don't properly export submodules.

**Expected Behavior:**
```python
from packages.repo_intelligence import SymbolExtractor
from packages.arch_intelligence import ArchitectureDetector
```

**Current Behavior:**
Requires full path:
```python
from packages.repo_intelligence.src.repo_intelligence.symbol_extractor import SymbolExtractor
```

**Fix Approach:**
1. Add proper `__init__.py` to `packages/` with `__path__` declaration
2. Or install packages via Poetry: `pip install -e .`
3. Or document the correct import paths in README

---

### BUG-003: Python Script Path Mismatch in CLI (HIGH)

**Severity:** HIGH  
**Component:** `apps/cli/src/commands/`  
**Status:** CONFIRMED

**Description:**
CLI looks for Python scripts in wrong locations. The actual scripts are in `packages/repo_intelligence/src/repo_intelligence/scan_cli.py` but the CLI searches in `apps/cli/python/` or other locations.

**Error:**
```
python: can't open file 'C:\Users\urbra\...\apps\cli\python\scan_cli.py'
```

**Expected Behavior:**
CLI should find scripts in their actual locations within the `packages/` directory.

**Fix Approach:**
1. Update all path calculations in CLI commands to point to correct locations
2. Or copy/symlink scripts to a standard location

---

### BUG-004: Unicode Encoding Issue in Python Output (MEDIUM)

**Severity:** MEDIUM  
**Component:** Python CLI scripts  
**Status:** CONFIRMED

**Description:**
When printing symbols like `✓`, `✗` from Python, Windows console (cp1252 encoding) fails to encode Unicode characters.

**Error:**
```
UnicodeEncodeError: 'charmap' codec can't encode character '✗' in position 0
```

**Fix Approach:**
1. Add `export PYTHONIOENCODING=utf-8` before running
2. Or use ASCII fallback: `[OK]` instead of `✓`

---

### BUG-005: Missing CLI Commands in Index (MEDIUM)

**Severity:** MEDIUM  
**Component:** `apps/cli/src/index.ts`  
**Status:** SUSPECTED

**Description:**
The new task-013 commands (`run`, `status`, `approve`, `reject`, `history`) may not be registered in the main CLI entry point.

**Error:**
Likely `Unknown command` when trying `ortho run`

**Expected Behavior:**
```bash
ortho run "analyze architecture"
ortho status
ortho approve
ortho reject
ortho history
```

**Test Case:**
```bash
node apps/cli/dist/index.js help
# Should list: run, status, approve, reject, history
```

---

### BUG-006: Python Module Path in Compiled CLI (MEDIUM)

**Severity:** MEDIUM  
**Component:** `apps/cli/dist/commands/`  
**Status:** CONFIRMED

**Description:**
The compiled JavaScript files may have incorrect path calculations due to TypeScript compilation. The `__dirname` context is lost during compilation.

**Expected Behavior:**
CLI works from any directory after being built.

**Fix Approach:**
1. Use `path.resolve(__dirname, ...)` with proper testing
2. Or update paths dynamically based on `process.env.ORTHO_ROOT`

---

## Summary Table

| Bug ID | Component | Severity | Status | Blocker |
|--------|-----------|----------|--------|---------|
| BUG-001 | CLI scan.ts | CRITICAL | CONFIRMED | YES |
| BUG-002 | Package imports | HIGH | CONFIRMED | YES |
| BUG-003 | CLI script paths | HIGH | CONFIRMED | YES |
| BUG-004 | Unicode output | MEDIUM | CONFIRMED | NO |
| BUG-005 | CLI commands | MEDIUM | SUSPECTED | MAYBE |
| BUG-006 | Path resolution | MEDIUM | CONFIRMED | YES |

---

## Blockers for Testing

**Current Status:** ❌ **BLOCKED**

Cannot proceed with end-to-end testing due to:
1. ✗ CLI path resolution broken (BUG-001, BUG-003, BUG-006)
2. ✗ Python imports broken (BUG-002)
3. ✗ Cannot run `ortho scan` or `ortho analyze` from test repos

**Required Fixes Before Testing:**
1. Fix `scan.ts` path calculation
2. Fix `analyze.ts` path calculation  
3. Fix `index.ts` path calculation
4. Verify all task-013 commands are registered
5. Test CLI works from external directories

**Recommended Fix Order:**
1. **FIRST:** Fix BUG-001 (CLI path resolution) - blocks all scanning
2. **SECOND:** Fix BUG-003 (Python script paths) - blocks command execution
3. **THIRD:** Fix BUG-005 (CLI command registration) - verify new commands work
4. **FOURTH:** Fix BUG-002 (Python imports) - allows direct Python testing
5. **FIFTH:** Fix BUG-004 (Unicode) - output formatting

---

## Test Environment

**OS:** Windows 11  
**Python:** 3.12.3  
**Node.js:** 11.14.1  
**Test Repos:**
- FastAPI (98MB)
- LangChain (623MB)

**Test Date:** 2026-07-07

---

*Last updated: 2026-07-07 during end-to-end testing*
