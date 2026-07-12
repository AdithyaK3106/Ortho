# Safe Cleanup & Reorganization Plan

**Date:** 2026-07-12  
**Status:** REVISED — Python CLI files are ACTIVE, do not delete

---

## Phase 1: P0 Cleanup (Safe Deletions Only)

### ✅ 1.1 Delete `./apps/api_server/` (SAFE — orphaned directory)

**Verification:** No imports found
```bash
grep -r "api_server" ./apps ./packages ./benchmarks 2>/dev/null
# Result: 0 matches
```

**Action:** Delete
```bash
rm -rf ./apps/api_server/
```

**Files removed:**
- `./apps/api_server/src/routers/orchestration.py` (264 lines)

---

### ✅ 1.2 Delete Empty `__init__.py` Files (SAFE — Python 3.3+ supports implicit namespaces)

**Files to delete:**
```
./packages/token-optimizer/tests/__init__.py (0 lines)
./packages/arch-intelligence/src/__init__.py (1 line, empty)
./packages/arch-intelligence/tests/__init__.py (1 line, empty)
./packages/context-hub/tests/__init__.py (1 line, empty)
./packages/impact-analysis/tests/__init__.py (1 line, empty)
./packages/orchestration/tests/__init__.py (1 line, empty)
./packages/repo-intelligence/src/repo_intelligence/adapters/__init__.py (1 line, empty)
```

**Action:** Delete all

---

### ✅ 1.3 Update `.gitignore` (SAFE — adds cache exclusions)

Add:
```
.mypy_cache/
.hypothesis/
.ruff_cache/
*.coverage
.coverage.*
```

---

### ❌ 1.4 DO NOT DELETE Python CLI files

**Correction:** Files like `analyze.py`, `context.py`, `workflow_cli.py` are **ACTIVE**.

They are called via TypeScript via `runPython()` / `runPythonCapture()` bridge.

**Action:** Keep as-is; will reorganize in Phase 2.

---

## Phase 2: P1 Improvements (Non-Breaking Refactoring)

### ✅ 2.1 Move Python CLI Entry Points to `packages/` (Safe reorganization)

**Problem:** CLI commands are scattered across `apps/cli/src/commands/`

**Solution:** Create dedicated `packages/cli-entrypoints/` to house Python CLI entry points

```
packages/cli-entrypoints/
├── src/cli_entrypoints/
│   ├── __init__.py
│   ├── analyze_cmd.py       ← from apps/cli/src/commands/analyze.py
│   ├── context_cmd.py       ← from apps/cli/src/commands/context.py
│   └── workflow_cmd.py      ← from apps/cli/src/commands/workflow_cli.py
└── pyproject.toml
```

**Benefits:**
- Clear separation: TypeScript CLI frontend vs. Python logic backend
- Single source of truth for CLI entry points
- Easier to test and version

---

### ✅ 2.2 Delete Stub API Endpoints (Safe deletion)

**File:** `./apps/api-server/src/main.py`

**Lines to remove:** Lines 14–27 (empty `/api/v1/search` and `/api/v1/artifacts`)

**Reason:** These endpoints return stubs or errors; no active usage.

---

### ✅ 2.3 Add `__all__` to Package `__init__.py` Files (Safe addition)

**Pattern:**
```python
# packages/{pkg}/src/{pkg}/__init__.py
from .main_module import MainClass
from .types import TypeA, TypeB

__all__ = ["MainClass", "TypeA", "TypeB"]
```

**Affected packages:**
- `packages/arch-intelligence/`
- `packages/context-hub/`
- `packages/impact-analysis/`
- `packages/orchestration/`
- `packages/repo-intelligence/`
- `packages/token-optimizer/`
- `packages/cli-entrypoints/` (new)

---

## Phase 3: Reorganization (Full Restructuring)

### ✅ 3.1 Create Layer-Based Directory Structure

```
ortho/
├── core/                            ← Orchestration (new)
│   ├── intent-router/               ← from packages/orchestration/src/orchestration/intent
│   ├── selector-engine/             ← from packages/orchestration/src/orchestration/selector
│   ├── workflow-executor/           ← from packages/orchestration/src/executor
│   ├── __init__.py
│   └── types.py                     ← Shared orchestration types
│
├── intelligence/                    ← Analysis (reorganized)
│   ├── repo-intelligence/           ← unchanged
│   ├── arch-intelligence/           ← unchanged
│   ├── impact-analysis/             ← unchanged
│   ├── __init__.py
│   └── types.py                     ← Shared analysis types
│
├── storage/                         ← Persistence (reorganized)
│   ├── context-hub/                 ← unchanged
│   ├── token-optimizer/             ← unchanged
│   ├── __init__.py
│   └── types.py                     ← Shared storage types
│
├── apps/
│   ├── cli/                         ← TypeScript CLI (unchanged)
│   ├── api-server/                  ← Single FastAPI server (consolidated)
│   └── dashboard-generator/         ← unchanged
│
├── packages/
│   ├── cli-entrypoints/             ← Python CLI entry points (NEW)
│   ├── shared/                      ← Common utilities (pruned)
│   └── benchmarks/                  ← Testing & validation
│
├── docs/
│   ├── architecture/                ← Layer diagrams, ADRs
│   ├── frd/                         ← Functional requirements
│   └── guides/                      ← Onboarding
│
└── .gitignore                       ← Updated
```

### ✅ 3.2 Update All Import Paths

**Pattern:**
```python
# OLD: from packages.arch_intelligence import ...
# NEW: from intelligence.arch_intelligence import ...

# OLD: from packages.orchestration.intent import ...
# NEW: from core.intent_router import ...
```

**Affected files:**
- `apps/api-server/` (imports from storage, core)
- `apps/cli/` pybridge calls (paths to new locations)
- `benchmarks/` (imports from intelligence, storage, core)
- All `__init__.py` files

---

## Phase 4: Testing & Validation

### ✅ 4.1 Run Type Checking

```bash
mypy --strict packages/ core/ intelligence/ storage/
```

### ✅ 4.2 Run All Tests

```bash
pytest packages/ benchmarks/ -v --tb=short
```

### ✅ 4.3 Verify CLI Works

```bash
npm run build --prefix apps/cli
node apps/cli/dist/index.js analyze --help
node apps/cli/dist/index.js context --help
```

### ✅ 4.4 Run API Server

```bash
python -m apps.api_server.src.main
curl http://localhost:8000/health
```

---

## Execution Order (Safe, With Rollback Points)

1. **Commit 1:** Delete `api_server/` + empty `__init__.py` + update `.gitignore`
   - Safe, isolated change
   - Tests should still pass

2. **Commit 2:** Delete stub API endpoints
   - Minimal change
   - Tests should still pass

3. **Commit 3:** Add `__all__` to all `__init__.py` files
   - No functional change
   - Type checkers will validate

4. **Commit 4:** Create `core/`, `intelligence/`, `storage/` directories
   - Move (don't copy) packages into new structure
   - Update all imports
   - Run full test suite

5. **Commit 5:** Create `packages/cli-entrypoints/`
   - Move Python CLI files from `apps/cli/src/commands/`
   - Update `pybridge.ts` to call new paths
   - Run CLI tests

6. **Commit 6:** Consolidate `api_server/` (merge router into main)
   - Already mostly done in Commit 1
   - Just merge any remaining code

---

## Safe Points (Rollback If Tests Fail)

| Commit | Tests Pass? | Action |
|--------|------------|--------|
| 1 | ✅ No | Rollback, investigate |
| 2 | ✅ No | Rollback, fix stub API endpoints first |
| 3 | ✅ No | Rollback, fix import issues |
| 4 | ✅ No | Major issue; investigate import errors carefully |
| 5 | ✅ No | Fix pybridge paths, retest |
| 6 | ✅ No | Verify API server startup |

---

## Timeline

| Phase | Commits | Time | Risk |
|-------|---------|------|------|
| 1 | 1–3 | 1 hour | Low (deletions only) |
| 2 | 4–5 | 2 hours | Medium (imports) |
| 3 | 6 | 1 hour | Low (consolidation) |
| **Total** | **6** | **~4 hours** | **Medium** |

---

## Key Safety Rules

1. ✅ **Keep `repos/` — it's for benchmarking**
2. ✅ **Keep `ortho-demo/` — separate project**
3. ✅ **Keep all Python CLI entry points — they're active**
4. ✅ **Run tests after each commit**
5. ✅ **Use git branches for Phases 3+ (reorganization)**
6. ✅ **Verify imports before committing**
7. ✅ **Document all changes in commit messages**

---

## Ready to Execute?

**Proceed with Phases 1–6 above with full verification.**
