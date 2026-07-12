# ADR-015: Layer Boundaries & Import Rules

**Status:** Accepted  
**Date:** 2026-07-12  
**Related:** CLEANUP_PLAN.md, packages/ reorganization Phase 3

---

## Context

Ortho v3 has 6 core packages operating across three logical layers:

- **Orchestration** (intent routing, selector, executor)
- **Intelligence** (architecture, impact, repository analysis)
- **Storage** (context hub, token optimizer)

Without explicit import rules, the codebase risks:
- Circular dependencies
- Tight coupling between layers
- Difficult refactoring (moving packages breaks unknown importers)
- Accidental exposure of internal APIs

---

## Decision

Enforce a **one-way, acyclic dependency graph**:

```
apps/*
    ↓
core/*                  (intent-router, selector-engine, workflow-executor)
    ↓
intelligence/*          (arch-intelligence, impact-analysis, repo-intelligence)
    ↓
storage/*               (context-hub, token-optimizer)
    ↓
shared/*                (no internal dependencies)
```

### Layer Definitions

#### Apps Layer
- `apps/cli` — TypeScript CLI (bridges to Python entry points)
- `apps/api-server` — FastAPI server (orchestration + artifact endpoints)
- `apps/dashboard-generator` — Dashboard generation

**Can import from:** Core, Intelligence, Storage, Shared  
**Cannot import from:** Each other (each is independent)

#### Core Layer (Orchestration)
- `packages/orchestration/src/orchestration/intent/router` — Intent classification
- `packages/orchestration/src/orchestration/selector/engine` — Plan building
- `packages/orchestration/src/executor` — Workflow execution + state management

**Can import from:** Storage (for state persistence), Shared  
**Cannot import from:** Intelligence, Apps, each other (only via public __all__)

**Why:** Orchestration must not depend on specific intelligence implementations. It calls interfaces only.

#### Intelligence Layer (Analysis)
- `packages/repo-intelligence` — Symbol extraction, import/call graphs
- `packages/arch-intelligence` — Architecture detection, layers, subsystems
- `packages/impact-analysis` — Dependency health, risk scoring

**Can import from:** Storage (for persistence), Shared  
**Cannot import from:** Core, Apps, each other (only via public __all__)

**Why:** Analysis packages are parallel; each is independent. They write results to storage, not to each other.

#### Storage Layer (Persistence)
- `packages/context-hub` — SQLite store, BM25 search, metadata
- `packages/token-optimizer` — Budget tracking, plan optimization

**Can import from:** Shared only  
**Cannot import from:** Apps, Core, Intelligence

**Why:** Storage is the foundation. No upward dependencies.

#### Shared Layer (Utilities)
- `shared/database` — SQLite helpers
- `shared/types` — Common types (Symbol, ModuleRef, etc., from FRD)
- `shared/utils` — Logging, hashing, math

**Can import from:** Nothing (except stdlib + third-party)  
**Cannot import from:** Any project code

---

## Rules

### 1. Public API Contracts (Enforced via `__all__`)

Each package MUST define `__all__` in its `__init__.py`:

```python
# packages/arch-intelligence/src/arch_intelligence/__init__.py
"""Architectural Intelligence — public API only."""

from .arch_detector import ArchitectureDetector
from .types import ArchStyle, ArchitectureModel

__all__ = ["ArchitectureDetector", "ArchStyle", "ArchitectureModel"]
```

**Rule:** Importers MUST use only `__all__` exports. Direct imports from internal modules break layers.

**Enforcement:** Code review + type checking (mypy will flag undefined names).

### 2. Private Modules (Prefixed with `_`)

Implementation details go into `_internal` submodules:

```
packages/arch-intelligence/src/arch_intelligence/
├── __init__.py          ← Public API (re-exports from below)
├── arch_detector.py     ← Public interface
├── types.py             ← Public types
└── _internal/           ← Private (never import from here)
    ├── __init__.py
    ├── heuristics.py
    └── clustering.py
```

**Rule:** Only `__init__.py` and top-level modules are importable. Private modules get `_` prefix.

### 3. Layer Enforcement Checklist

| From Layer | To Core | To Intelligence | To Storage | To Shared | To Apps |
|----------|---------|-----------------|-----------|----------|---------|
| **Apps** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Core** | ✅ | ❌ | ✅ | ✅ | ❌ |
| **Intelligence** | ❌ | ✅ | ✅ | ✅ | ❌ |
| **Storage** | ❌ | ❌ | ✅ | ✅ | ❌ |
| **Shared** | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Implementation (Current Locations)

**Core (packages/orchestration/)**
```python
from orchestration.intent.router import IntentRouter         # Public
from orchestration.selector.engine import SelectorEngine     # Public
from executor.workflow_executor import WorkflowExecutor      # Public

__all__ = ["IntentRouter", "SelectorEngine", "WorkflowExecutor"]
```

**Intelligence (packages/arch-intelligence/, repo-intelligence/, impact-analysis/)**
Already compliant: `__all__` defined in each.

**Storage (packages/context-hub/, token-optimizer/)**
Already compliant: `__all__` defined in each.

**Shared (shared/)**
✅ No internal dependencies.

---

## Future: Directory Reorganization (Phase 4, Deferred)

Once import rules are established and tested, optionally reorganize directories:

```
ortho/
├── core/                          ← Symlink or copy of orchestration components
├── intelligence/                  ← Reorganized from packages/
├── storage/                       ← Reorganized from packages/
├── packages/                      ← CLI entrypoints, benchmarks, shared
├── apps/
└── docs/
```

This is **not required** for correctness; it's a structural cleanup. Can be deferred.

---

## Verification

### Type Checking
```bash
mypy --strict packages/ apps/ shared/
```

Should report no import errors across layers.

### Code Review
1. **New imports:** Verify they respect layer rules
2. **Moved code:** Ensure imports point to correct layer
3. **Circular imports:** Test with `python -c "import X; import Y"`

### Tests
```bash
pytest packages/ -v
# All tests pass after reorganization
```

---

## Benefits

1. **Clarity:** Developers know which packages are allowed to call which
2. **Refactoring Safety:** Can move/rename packages within a layer without breaking others
3. **Testing Isolation:** Each layer can be tested independently
4. **Microservices Path:** Clear layer boundaries enable service extraction later

---

## Exceptions

**Justified exceptions** (rare):
- `apps/api-server` may import from Core for orchestration endpoints
- `packages/orchestration` may import specific agents/skills registered in registries (not entire Intelligence layer)

All exceptions documented in code comments.

---

## References

- CLEANUP_PLAN.md — Cleanup phases
- CLAUDE.md — Project rules
- FRD — Feature requirements (define types in Shared)
