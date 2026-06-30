# task-005: Architecture Review
## ARCHITECT — Gate 2 Verdict: APPROVED

**Date:** 2026-06-30  
**Reviewer:** ARCHITECT  
**Status:** ✅ APPROVED — ready for BUILDER

---

## Review Summary

Specification aligns with FRD §8 (Pillar 3 — Architectural Intelligence). No conflicts with existing packages or types. Architecture is sound, dependencies are minimal, scope is appropriate for Week 9–10.

---

## Detailed Review

### 1. Alignment with FRD §8

**FRD requirement:** Architecture detector, layer detector, subsystem detector with confidence scores.

**Spec delivers:** ✅
- `ArchitectureDetector` with 5 style classifications (layered, hexagonal, MVC, microservices, flat)
- Confidence scoring 0.0–1.0 + evidence lists
- `LayerDetector` extracts layers from import patterns (topological sort)
- `SubsystemDetector` clusters modules by coupling (Louvain algorithm)
- Alternative style detection for ambiguous cases

**No deviations.** Spec is conservative and follows FRD precisely.

---

### 2. Shared Types Verification

**Types checked against shared/types/src/architecture.ts:**

```typescript
// Spec uses these from shared/types — already defined ✅
interface ArchitectureModel { ... }  // 8 fields
interface Layer { ... }              // 5 fields
interface Subsystem { ... }          // 4 fields
type ArchStyle = 'layered' | 'hexagonal' | 'mvc' | 'microservices' | 'flat' | 'unknown'
```

**Internal types defined in arch-intelligence/src/types.py:**
- `DetectionResult` — new, no conflicts
- `DetectionMetrics` — new, no conflicts

**Verdict:** ✅ No breaking changes. Shared types are sufficient.

---

### 3. Package Structure Review

**New package:**
```
packages/arch-intelligence/
├── src/
│   ├── detector.py
│   ├── layer_detector.py
│   ├── subsystem_detector.py
│   ├── graph_utils.py
│   ├── types.py
│   └── models.py
├── tests/
├── README.md
└── pyproject.toml
```

**Assessment:**
- Clean separation from other pillars (repo-intelligence, context-hub, token-optimizer)
- Single responsibility: architecture reasoning only
- No circular imports (depends on: repo-intelligence, context-hub, shared/storage)
- ✅ Follows FRD monorepo dependency rules

---

### 4. Algorithm Review

**ArchitectureDetector.detect():**
- Scores 5 patterns against metrics (layering, cohesion, modularity)
- Picks highest-confidence style
- Flags alternative if ambiguous (top 2 within 0.15 confidence)
- Returns evidence list (human-readable reasons)
- ✅ Approach is sound. Scoring weights are reasonable (not magic).

**LayerDetector:**
- Uses topological sort on file dependency graph (DAG assumption)
- Assigns layers by longest-path distance
- Assigns semantic names (presentation, business, data, infrastructure)
- Detects cross-layer violations
- ✅ Mathematically sound. Handles layer violations correctly.

**SubsystemDetector:**
- Uses Louvain community detection (via networkx)
- Computes coupling score within communities
- Auto-names from module prefixes or keywords
- ✅ Louvain is industry-standard clustering. Appropriate for this use case.

---

### 5. Dependencies Review

**New Python package required:**
- `networkx` — graph algorithms (community detection, shortest paths)

**Check FRD §13:**
```
| Package | Python deps |
|---------|-------------|
| arch-intelligence | networkx (graph analysis) | —
```

✅ **`networkx` is already listed in FRD as approved dependency.** No new deps needed.

**Existing dependencies leveraged:**
- `shared/storage` — OrthoDatabase for persistence
- `shared/types` — ArchitectureModel, Layer, Subsystem
- task-003 data: call graph, import graph (loaded from DB)
- task-004 data: ContextHub (for future reference lookups)

✅ All dependency relationships are forward (arch-intelligence depends on earlier tasks, never vice versa).

---

### 6. Schema Review

**New table:**
```sql
CREATE TABLE architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT FOREIGN KEY,
    style TEXT,
    style_confidence REAL,
    evidence TEXT (JSON),
    model_json TEXT (full model as JSON),
    detected_at TEXT
);
```

**Assessment:**
- Follows existing schema patterns (artifact-style storage)
- Backward-compatible (new table, no schema changes to existing)
- Appropriate for versioning (timestamp + JSON blob)
- ✅ Correct design

---

### 7. Test Strategy Review

**Coverage:**
- 25+ unit tests (5 patterns × 3–4 cases each + layer/subsystem edge cases)
- 8+ integration tests (end-to-end on fixture repos)
- Fixtures: layered repo, microservices repo, flat repo

**Assessment:**
- Good breadth (all 5 architecture patterns tested)
- Good depth (each pattern has 3–4 variants)
- Fixtures are essential (community detection is empirical)
- ✅ Test strategy is comprehensive

---

### 8. CLI Integration

**Command:** `ortho analyze`

**Design:**
- Calls ArchitectureDetector.detect()
- Prints human-readable report (style, confidence, evidence, layers, subsystems)
- Integration point: orchestration package will call this in Phase 3

**Assessment:**
- ✅ Simple, clean interface
- ✅ Output format is clear and informative

---

### 9. Potential Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Large repos (1000+ files) slow detection | Medium | Cache results; pre-compute metrics on scan |
| Ambiguous architectures (low confidence) | Low | Return confidence < 0.5; flag as "unknown" |
| Circular dependencies break topological sort | Low | DAG assumption documented; handle cycles gracefully |
| Subsystem naming collisions | Low | Auto-number fallback (subsystem_0, subsystem_1) |

✅ **All risks have documented mitigations.**

---

### 10. Architecture Decision Records (ADRs)

**No new ADRs required for task-005.**

FRD §17 asks for ADR when deciding on:
- Package boundaries (already defined in FRD)
- Storage backends (SQLite already chosen in task-001)
- Library selection (networkx already in FRD)
- Interface contracts (ArchitectureModel already in shared/types)

✅ **No architectural decisions requiring ADR documentation.**

---

## Verdict

### ✅ APPROVED FOR BUILDER

Specification is:
- ✅ Aligned with FRD §8 (Pillar 3 — Architectural Intelligence)
- ✅ No conflicts with shared types or existing packages
- ✅ Appropriate scope for Week 9–10 (4 atomic tasks, 33+ tests)
- ✅ Dependencies already approved in FRD
- ✅ Test strategy is comprehensive
- ✅ Risk mitigations documented
- ✅ Ready to implement

---

## Guidance for BUILDER

**Before implementing:**
1. Review spec.md carefully — ArchitectureDetector scoring functions are critical
2. Ensure networkx is in pyproject.toml (poetry add networkx)
3. Create fixture repos early (essential for testing community detection)
4. Test on sample-python-project (from tests/fixtures/)

**During implementation:**
1. Implement DetectionMetrics calculation first (foundation for all scoring)
2. Implement ArchitectureDetector.detect() second (core logic)
3. Implement LayerDetector and SubsystemDetector in parallel (independent)
4. Persistence (models.py) last (depends on all detectors)

**Atomic commits:**
- Commit 1: graph_utils.py + networkx integration
- Commit 2: ArchitectureDetector + tests
- Commit 3: LayerDetector + tests
- Commit 4: SubsystemDetector + models.py + CLI command

---

**Prepared by:** ARCHITECT  
**Date:** 2026-06-30 23:50 UTC  
**Status:** GATE 2 APPROVED ✅
