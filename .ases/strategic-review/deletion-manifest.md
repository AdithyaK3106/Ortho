# Code Deletion & Refactoring Manifest

**Date:** 2026-07-01  
**Purpose:** Identify what to remove, archive, or refactor as GitNexus integration proceeds

---

## Executive Summary

**DON'T DELETE YET.** Keep all Ortho Python code during transition phase. Archive only after GitNexusAdapter proven stable in production (1+ months).

| Status | Component | Reason | Timeline |
|--------|-----------|--------|----------|
| **KEEP NOW** | PythonAdapter | Fallback during transition | Keep until Phase 3 (6+ months) |
| **DEPRECATE LATER** | Python parsing code | Replaced by GitNexus | Archive after 3 months production |
| **KEEP FOREVER** | ContextHub | Unique to Ortho | Never delete |
| **KEEP FOREVER** | Architecture detection | Unique to Ortho | Never delete |
| **KEEP FOREVER** | ASES artifacts | Audit trail | Never delete |

---

## What To Delete (Eventually)

### 1. Python AST Parsing Code

**Files to archive (NOT delete yet):**
- `packages/repo-intelligence/adapters/python_adapter.py`
- `packages/repo-intelligence/symbol_extractor.py`
- `packages/repo-intelligence/import_graph_python.py` (if language-specific)

**Status:** DEPRECATE after Phase 2 production validation (3+ months)

**Timeline:**
- Week 10-11: GitNexusAdapter implemented
- Weeks 12-15: Testing and production transition
- Weeks 16-28: Keep as fallback
- Week 29+: Archive to `.ases/deprecated/python-adapter-v1/`

**Archiving procedure:**
```bash
# Create archive directory
mkdir -p .ases/deprecated/python-adapter-v1

# Move files
git mv packages/repo-intelligence/adapters/python_adapter.py \
         .ases/deprecated/python-adapter-v1/
git mv packages/repo-intelligence/symbol_extractor.py \
       .ases/deprecated/python-adapter-v1/

# Update imports to remove dependencies
# Create README explaining why this was removed
echo "Replaced by GitNexusAdapter in Phase 2. See architecture-decision.md" \
     > .ases/deprecated/python-adapter-v1/README.md

# Commit with explanation
git commit -m "Archive: Python adapter v1 (replaced by GitNexus, Week 29)"
```

**Why archive instead of delete:**
- Preserve commit history
- Enable rollback if needed
- Document decision for future reference

---

### 2. Call Graph Implementation

**Files to archive:**
- `packages/repo-intelligence/call_graph.py` (custom AST implementation)

**Status:** DEPRECATE after GitNexus call graph proven better (Weeks 12-15)

**Reason:** GitNexus has higher confidence (0.9+ vs 0.8), better OOP dispatch handling

**Keep only:** `packages/repo-intelligence/call_graph.py` interface/schema (abstract types)

**Timeline:** Same as Python adapter (archive Week 29+)

---

### 3. Dependency Graph Parser

**Files to archive:**
- `packages/repo-intelligence/dependency_graph.py` (if Python-specific implementation)

**Status:** DEPRECATE if GitNexus covers all manifest types

**Reason:** GitNexus supports package.json, go.mod, Cargo.toml, etc. Ortho only supports pyproject.toml

**Note:** If Ortho's implementation has custom logic, keep it and make it language-aware

**Timeline:** Week 29+ (after TypeScript support proven)

---

### 4. Module Detector

**Files to archive:**
- `packages/repo-intelligence/module_detector.py` (if regex-based)

**Status:** DEPRECATE if GitNexus detection is more reliable

**Reason:** GitNexus uses language-native detection (more accurate)

**Timeline:** Week 29+ (after multi-language testing)

---

## What NOT To Delete (Never)

### 1. Shared Storage Layer

**Files:** `shared/storage/database.py`, `vector_store.py`, `config.py`

**Why:**
- Foundation for ALL pillars (ContextHub, Architecture, Orchestration)
- Removing would require rewriting everything
- SQLite schema is production data (must preserve)

**Status:** KEEP FOREVER

---

### 2. Type Definitions

**Files:** `shared/types/src/adapter.ts`, `symbol.ts`, `repository.ts`, `artifact.ts`

**Why:**
- Canonical data models
- Define contracts between pillars
- Must match GitNexus output format

**Status:** KEEP FOREVER (may need to extend for GitNexus metadata)

---

### 3. ContextHub

**Files:** `packages/context-hub/src/store.py`, `ingestion.py`, `versioning.py`, `search/*`, etc.

**Why:**
- Unique to Ortho (GitNexus doesn't have this)
- Long-term artifact storage (not code-focused)
- Core differentiator of Engineering Intelligence

**Status:** KEEP FOREVER

---

### 4. Architecture Detection

**Files:** `packages/arch-intelligence/detector.py`, `layer_detector.py`, `subsystem_detector.py`

**Why:**
- Unique to Ortho (GitNexus has no equivalent)
- Core differentiator vs. repo scanning
- Part of Architectural Intelligence pillar

**Status:** KEEP FOREVER

---

### 5. ASES Artifacts & Evidence

**Files:** `.ases/tasks/`, `.ases/evidence/`, `CLAUDE.md`, ADRs

**Why:**
- Audit trail (proof that work was done correctly)
- Decision history (enables rollback)
- Governance (ASES workflows are non-negotiable)

**Status:** KEEP FOREVER (grows over time)

---

### 6. Incremental Indexer

**Files:** `packages/repo-intelligence/incremental_indexer.py`

**Why:**
- Works at graph level (not parser level)
- GitNexus incremental is at parser level
- Need adaptation layer between them

**Status:** KEEP FOREVER (enhance to work with GitNexus)

---

## What To Refactor (Later)

### 1. LanguageAdapter Hierarchy

**Current:**
```
LanguageAdapter (interface)
  └── PythonAdapter (concrete)
  └── TypeScriptAdapterStub (stub, never completed)
  └── GoAdapterStub (stub, never completed)
```

**Refactored (Phase 2):**
```
LanguageAdapter (interface)
  └── GitNexusAdapter (concrete, multi-language)
      └── _translate_symbol() (helper)
      └── _translate_import() (helper)
      └── _translate_call() (helper)
  └── PythonAdapter (concrete, DEPRECATED, fallback)
```

**Effort:** 2 hours (file reorganization only)

**Acceptance criteria:**
- Adapters inherit from LanguageAdapter
- Old stubs are deleted (never completed anyway)
- Gitignore updated

---

### 2. Tests Organization

**Current:** Tests mixed in each package

**Refactored (Phase 2):** Adapter tests separated:
```
packages/repo-intelligence/tests/
  ├── test_python_adapter.py (deprecated, kept as reference)
  ├── test_gitnexus_adapter.py (new)
  ├── test_symbol_extraction.py (language-agnostic)
  ├── test_import_graph.py (language-agnostic)
  └── conftest.py (shared fixtures)
```

**Effort:** 3 hours

**Acceptance criteria:**
- Tests organized by adapter
- No duplicated test logic
- Clear which tests are deprecated

---

### 3. Configuration Files

**Current:** Hardcoded defaults favor PythonAdapter

**Refactored (Phase 2):** Config-driven adapter selection:

```toml
# config.toml
[repository_intelligence]
adapter = "gitnexus"  # or "python"

[repository_intelligence.gitnexus]
languages = ["python", "typescript", "go"]
cache = true
```

**Effort:** 2 hours

**Acceptance criteria:**
- Config can select adapter
- Defaults make sense (GitNexus if available, Python fallback)

---

### 4. Import Statements

**Current:** Some modules import PythonAdapter directly

**Refactored (Phase 2):** Factory pattern for adapter creation:

```python
# BEFORE (hardcoded)
from adapters.python_adapter import PythonAdapter
adapter = PythonAdapter()

# AFTER (configurable)
adapter = create_adapter(config.adapter, repo_path)
```

**Effort:** 4 hours

**Acceptance criteria:**
- No hardcoded adapter imports in main code
- Factory pattern used everywhere
- Tests can inject mock adapters

---

## What To Move / Restructure

### 1. Language-Specific Helpers

**Current:** Some code is Python-specific but not in adapter class

**Move:** Extract Python-specific logic into `packages/repo-intelligence/adapters/python_helpers.py`

**Example:**
- AST traversal helpers
- Python syntax patterns
- Decorator parsing

**Effort:** 3 hours

**Timeline:** Phase 2, Task 4 cleanup

---

### 2. Test Fixtures

**Current:** Test files are scattered

**Restructure:**
- Central test data directory: `packages/repo-intelligence/tests/fixtures/`
- Sample Python files: `fixtures/python/`
- Sample TypeScript files: `fixtures/typescript/`
- Sample Go files: `fixtures/go/`

**Effort:** 2 hours

**Timeline:** Phase 2, Task 5

---

## Deletion Timeline

### Week 8 (End of Phase 1)
- ✅ No deletions
- ✅ Prepare Python adapter for deprecation (document usage)

### Weeks 10-11 (Phase 2, Task 4)
- ✅ No deletions
- ✅ Implement GitNexusAdapter alongside PythonAdapter
- ✅ Refactor imports to use factory pattern

### Weeks 12-15 (Phase 2, Tasks 5-6)
- ✅ No deletions
- ✅ Test both adapters in parallel
- ✅ Keep PythonAdapter as fallback

### Week 16+ (Phase 2, Task 7)
- ✅ No deletions
- ✅ Add TypeScript/Go adapters
- ✅ Mark PythonAdapter as deprecated in code comments

### Weeks 17-28 (Phase 3 start)
- ✅ No deletions
- ✅ Monitor GitNexus in production
- ✅ Collect feedback

### Week 29 (After 3+ months production use)
- 🗑️ Archive Python adapter code
- 🗑️ Archive call graph custom implementation
- 🗑️ Archive dependency graph Python implementation
- 🗑️ Archive module detector Python implementation
- ✅ Keep as git history (can resurrect if needed)

### Week 30+
- 🗑️ Clean up old test files
- 🗑️ Remove deprecated imports from main code
- ✅ Update ADRs to reference archived code

---

## File Deletion Checklist (Week 29+, only if approved)

Before deleting any Python adapter code:

- [ ] GitNexusAdapter has been in production for 3+ months
- [ ] Zero issues reported with GitNexus
- [ ] Test coverage is 100% with GitNexus backend
- [ ] No commits in last 2 weeks to PythonAdapter code
- [ ] ADR-XXX (GitNexus integration) is written and approved
- [ ] `.ases/deprecated/` directory exists with README
- [ ] Git history preserved (files archived, not deleted)
- [ ] Team agrees (consensus, not unilateral)

---

## What Never Gets Deleted

```
.ases/                    ← History, decision trail, evidence
  ├── tasks/              ← Task artifacts (never delete)
  ├── evidence/           ← Test logs (never delete)
  └── deprecated/         ← Archived code (reference only)

shared/storage/           ← Foundation layer (never delete)
shared/types/             ← Contracts (never delete)

packages/context-hub/     ← Unique feature (never delete)
packages/arch-intelligence/ ← Unique feature (never delete)

CLAUDE.md                 ← Project context (never delete)
ortho-v3-frd.md          ← Requirements (never delete)
```

---

## Summary

**Phase 1-2 (Weeks 1-15):** NO DELETIONS. Build new, keep old, test in parallel.

**Phase 3 (Weeks 16-28):** Monitor and validate. Prepare for cleanup.

**Phase 3+ (Week 29+):** Archive only if GitNexus proven stable. Keep everything in git history.

**Rule:** Never delete unique Ortho features. Only remove duplicate code after replacement is proven superior.

---

*Deletion manifest prepared by ARCHITECT*  
*Guidelines: Archive, don't delete. Move fast, clean up slow. Preserve history.*
