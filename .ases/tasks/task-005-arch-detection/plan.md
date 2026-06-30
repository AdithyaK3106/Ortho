# task-005: Architecture Detection
## PLANNER — Gate 1 Approval Request

**Date:** 2026-06-30  
**Phase:** 2 (Reasoning) — Week 9–10  
**Task:** Arch-Intelligence Pillar 3 — Architecture style detection + layer extraction  
**Workflow:** feature.md (ASES v1.2 optimized)

---

## Intent

Detect software architecture patterns (layered, hexagonal, MVC, microservices, flat) with confidence scores. Identify logical layers from import/call patterns. Build foundational architecture model that subsequent tasks (risk analysis, debt scoring) depend on.

---

## Business Value

- **Architecture visibility:** Answer "what architectural style is this repo?"
- **Layer detection:** Automatically identify (presentation, business logic, data access, etc.)
- **Confidence scoring:** All detections include 0.0–1.0 confidence + evidence
- **Foundation for Phase 2:** Enables impact analysis, debt scoring, subsystem detection in subsequent tasks

---

## Scope — 4 Atomic Implementations

1. **ArchitectureDetector** — Style classification (layered, hexagonal, MVC, flat, microservices)
2. **LayerDetector** — Identify logical layers from import/call graph patterns
3. **SubsystemDetector** — Cluster related modules into named subsystems
4. **ArchitectureModel** — Persist detected style, layers, subsystems, evidence

**New package:** `packages/arch-intelligence/` (Python)  
**CLI command:** `ortho analyze`  
**Dependencies:** `networkx` (graph algorithms)

---

## Acceptance Criteria (12 total)

### ArchitectureDetector (4 AC)
- [ ] AC1: Classify style as layered | hexagonal | mvc | microservices | flat with confidence 0.0–1.0
- [ ] AC2: Provide evidence list (why layered? which layers matched?)
- [ ] AC3: Identify alternative style + confidence if ambiguous
- [ ] AC4: Handle repos with no detectable pattern (confidence < 0.5)

### LayerDetector (4 AC)
- [ ] AC5: Extract layers from import dependency patterns (upward deps = layer boundary)
- [ ] AC6: Assign semantic names (presentation, business, data, infrastructure)
- [ ] AC7: Detect layer violations (cross-layer dependencies)
- [ ] AC8: Return layers with file membership + confidence per layer

### SubsystemDetector (2 AC)
- [ ] AC9: Cluster modules by coupling (high internal coupling = subsystem)
- [ ] AC10: Assign subsystem names (auth, payment, inventory, etc.) or auto-number

### ArchitectureModel (2 AC)
- [ ] AC11: Store model in SQLite (architecture_models table)
- [ ] AC12: Retrieve model by repo + timestamp

---

## Atomic Task Breakdown

| Task | Depends On | Est. LOC | Effort |
|------|-----------|----------|--------|
| 1. Graph analysis utils (networkx) | call/import graphs | 200 | 1h |
| 2. ArchitectureDetector class | graph utils | 400 | 2h |
| 3. LayerDetector class | graph utils | 350 | 1.5h |
| 4. SubsystemDetector class | graph utils | 250 | 1.5h |

**Total: ~1200 LOC, ~6h work**

---

## Architecture Sketch

```
packages/arch-intelligence/
├── src/
│   ├── __init__.py
│   ├── detector.py           # ArchitectureDetector
│   ├── layer_detector.py     # LayerDetector
│   ├── subsystem_detector.py # SubsystemDetector
│   ├── graph_utils.py        # networkx helpers
│   ├── types.py              # ArchStyle, Layer, Subsystem, etc.
│   └── models.py             # Persistence logic
├── tests/
│   ├── conftest.py
│   ├── test_detector.py
│   ├── test_layer_detector.py
│   ├── test_subsystem_detector.py
│   └── integration_test.py
├── README.md
└── pyproject.toml
```

---

## Schema Changes

**New table:**
- `architecture_models` — detected style, layers, subsystems, evidence, timestamp

**Migrations:** Add `0006_architecture.sql` to shared/storage/migrations/

---

## Test Strategy

**Unit tests (25+):**
- Detector: layered pattern detection, hexagonal pattern, MVC, flat
- Detector: confidence scoring, alternative detection
- LayerDetector: layer extraction, naming, violations
- SubsystemDetector: clustering, naming

**Integration tests (8+):**
- End-to-end: analyze fixture repo → detect architecture → verify style
- Real repo: scan sample-python-project → detect architecture

**Fixtures:**
- Fixture repo with clear layered architecture (web layer, business logic, data access)
- Fixture repo with flat structure
- Fixture repo with microservices (multiple independent modules)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| No clear pattern detected | Return confidence < 0.5, flag as "unknown" |
| Ambiguous patterns | Detect top 2 styles, return alternative |
| Large repos slow | Cache results, only re-detect on significant change |
| Naming collision (subsystem names) | Auto-number if collision: subsystem_0, subsystem_1 |

---

## Definition of Done

- [ ] All 4 atomic tasks implemented
- [ ] 33+ tests passing
- [ ] 0 lint errors, mypy --strict clean
- [ ] `ortho analyze` command functional
- [ ] Confidence scores on all detections
- [ ] README documents architecture model
- [ ] No breaking changes to shared types
- [ ] Integration test passes
- [ ] REVIEWER approval

---

## Rollback Plan

**If rejected at any gate:** `git reset --hard` to commit before task-005 branch. Delete `.ases/tasks/task-005-arch-detection/`.

---

**Prepared by:** PLANNER  
**Status:** Gate 1 complete — awaiting human approval
