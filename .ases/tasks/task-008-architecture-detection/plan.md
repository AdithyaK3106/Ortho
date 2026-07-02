# task-008: Architecture Detection — Plan

**Task ID:** task-008  
**Phase:** Phase 2 (Weeks 9–10)  
**Workflow:** `.ases/workflows/feature.md`  
**FRD Section:** Section 8 (Pillar 3 — Architectural Intelligence)

---

## Feature Summary

Implement architecture pattern detection for Python repositories. Detect and classify architectural styles (layered, hexagonal, mvc, microservices, flat) from call graph and import graph data. Compute confidence scores and evidence justifications for each detection.

---

## Atomic Tasks (30–90 min each)

### Task 1: ArchitectureDetector — Core Pattern Matching
- Implement base class with 5 pattern detectors (layered, hexagonal, mvc, microservices, flat)
- Each detector analyzes import/call graph to extract pattern-specific signals
- Return ArchitectureDetectionResult with style, confidence, evidence list
- **Files:** `packages/arch-intelligence/src/arch_detector.py` (new)
- **Tests:** Unit tests for each detector (happy path + edge cases)

### Task 2: LayerDetector — Topological Layer Extraction
- Extract layers from import graph using topological sort
- Layer numbering: Layer 0 (data/lowest) → Layer 1 (business) → Layer 2 (presentation/highest)
- Semantic naming detection (repository/model → Layer 0, service → Layer 1, controller → Layer 2)
- Layer dependency analysis (layered := acyclic dependencies where each layer only imports lower-numbered layers)
- **Files:** `packages/arch-intelligence/src/layer_detector.py` (new)
- **Tests:** Fixtures with known layer structures; see spec.md for numbering convention details

### Task 3: SubsystemDetector — Clustering & Coupling
- Louvain clustering on call/import graph to identify subsystems
- Compute coupling score per subsystem (intra vs inter-module calls)
- Return subsystem list with files and coupling metrics
- **Files:** `packages/arch-intelligence/src/subsystem_detector.py` (new)
- **Tests:** Graph clustering validation (accuracy on synthetic graphs)

### Task 4: ArchitectureModelStore — Persistence
- Save/load ArchitectureModel to SQLite (new table: architecture_models)
- Versioning: store detected_at timestamp and model_json
- Query: load_latest(repo_id) for current architecture
- **Files:** `packages/arch-intelligence/src/model_store.py` (new)
- **Tests:** CRUD operations, versioning correctness

### Task 5: Integration & CLI Command
- Integrate all 4 components into orchestrated flow
- Add `ortho analyze` command (full architecture report)
- Add `ortho analyze --impact <file>` (blast radius analysis — defer to task-009)
- **Files:** CLI command file (modify `apps/cli/src/commands/analyze.ts`)
- **Tests:** End-to-end: load repo, scan, analyze, display results

---

## Acceptance Criteria

### AC1: Five Pattern Detectors (Layered, Hexagonal, MVC, Microservices, Flat)
- [ ] Each detector correctly identifies its pattern in well-formed test fixtures
- [ ] Confidence scores reflect uncertainty (0.0–1.0, calibrated to pattern clarity)
- [ ] Evidence list justifies confidence (specific rule matches)

### AC2: Layer Detection with Topological Sort
- [ ] Correctly extracts layers from import graph with consistent numbering (Layer 0 = data, Layer 1 = business, Layer 2 = presentation)
- [ ] Semantic naming recognized and matched to correct layers (repository/model files → Layer 0, service files → Layer 1, controller files → Layer 2)
- [ ] Layer dependency validation: layered style = acyclic dependencies (each layer only imports lower-numbered layers)

### AC3: Subsystem Clustering (Louvain)
- [ ] Correctly clusters related modules into subsystems
- [ ] Coupling score accurately reflects inter-module call density
- [ ] Subsystems are stable (same input, same output)

### AC4: Architecture Model Persistence
- [ ] Save/load round-trip: model in = model out
- [ ] Versioning works: multiple detections stored with timestamps
- [ ] Query efficiency: load_latest returns correct model

### AC5: Zero Regressions
- [ ] All existing tests pass (repo-intelligence + context-hub)
- [ ] No broken imports or circular dependencies introduced
- [ ] Code style and type checking pass

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Pattern detection too strict (high false negatives) | Misses real architectures | Pre-calibrate confidence thresholds on 10+ real repos |
| Clustering algorithm instability | Non-deterministic results | Use fixed seed for reproducibility in tests |
| Dependency on unfinished call-graph | Integration failure | Use mock call-graph fixtures if full extraction incomplete |
| Performance degradation | Slow analysis on large repos | Profile on repos >1000 files; optimize if >5s |

---

## Files to Create
- `packages/arch-intelligence/` (new package)
- `packages/arch-intelligence/src/arch_detector.py`
- `packages/arch-intelligence/src/layer_detector.py`
- `packages/arch-intelligence/src/subsystem_detector.py`
- `packages/arch-intelligence/src/model_store.py`
- `packages/arch-intelligence/tests/` (full test suite)
- `apps/cli/src/commands/analyze.ts` (new)

## Files to Modify
- `apps/cli/src/index.ts` (register `ortho analyze` command)
- `.ortho/ortho.db` schema (add architecture_models table)

## Files NOT to Touch
- `packages/repo-intelligence/` (completed; no changes)
- `packages/context-hub/` (completed; no changes)
- `shared/types/` (extend only if new shared type required)

---

## Expected Test Metrics

- **Unit tests:** 40+ (pattern detectors, layer extraction, clustering)
- **Integration tests:** 15+ (full orchestration, CLI end-to-end)
- **Edge cases:** 10+ (empty graphs, single-file repos, cyclic deps)
- **Total:** 65+ tests
- **Expected coverage:** ≥85%
- **Expected pass rate:** 100% (or marked xfail if pre-approved)

---

## Rollback Strategy

**Trigger:** Test failures >10%, regression in repo-intelligence, or architecture review rejection

**Policy:** Use `git revert` for published (committed) work to preserve history and auditability. Use `git reset --hard` only for unpublished local changes.

**See:** `.ases/tasks/task-008-architecture-detection/rollback-plan.md` for complete procedures, step-by-step commands, and verification checklist.

**Quick Reference:**
- If no commits since task-007 (1d7cbec): Use `git reset --hard`
- If commits exist: Use `git revert` (preserves history)
- Verify: Exit code 0 from repo-intelligence + context-hub test suites

---

*Plan prepared by PLANNER role.*  
*Awaiting human review and approval at GATE 1.*
