---
name: task-009-impact-analysis
display_name: "Task-009: Impact Analysis + Debt Scoring (Phase 2, Week 11–12)"
workflow: feature.md
phase: Phase 2 (Reasoning)
week: 11–12
estimated_duration_hours: 40
architecture_impact: MEDIUM
dependencies:
  - task-003 (call/import graphs)
  - task-007 (incremental indexer)
  - task-008 (architecture detection)
---

# Task-009: Impact Analysis + Debt Scoring

## Objective

Implement Pillar 3 capabilities for change impact analysis and technical debt scoring. Engineers answer: "If I change this file, what breaks?" and "Which modules have the highest tech debt?"

---

## Atomic Tasks (4 tasks)

### Task 1: ImpactAnalyzer — Blast Radius Computation

**Scope:** Build component that traverses call/import graphs from a changed file to compute affected downstream dependencies.

**Inputs:**
- Changed file ID
- Call graph (from CallGraphBuilder, task-003)
- Import graph (from ImportGraphBuilder, task-003)
- Depth parameter (default 3 hops)

**Outputs:**
```python
@dataclass
class ImpactReport:
    changed_file_id: str
    direct_dependents: list[str]          # Files that directly import/call this file
    transitive_dependents: list[str]      # Reachable within `depth` hops
    risk_score: float                     # 0.0–1.0 based on centrality
    blast_radius: int                     # Count of affected files
    evidence: list[str]                   # Human-readable justifications
```

**Implementation:**
- BFS traversal of import/call edges
- Centrality scoring (fan-in + fan-out ratio)
- Cycle detection (ignore cycles in risk computation)
- Query by file_id or symbol_id

**Tests:** Unit (6+), integration (4+), edge cases (3+)

---

### Task 2: DebtScorer — Multi-Dimensional Scoring

**Scope:** Compute technical debt score per module using 5 dimensions.

**Inputs:**
- Call graph (task-003)
- Import graph (task-003)
- File metadata (size, age, churn from git)
- Symbol registry (task-002)

**Scoring dimensions:**
```python
@dataclass
class DebtScore:
    module_id: str
    total_score: float          # 0.0 (clean) — 1.0 (critical), weighted average
    coupling_score: float       # (fan-in + fan-out) / (module_files * 2), capped at 1.0
    churn_score: float          # Git commits last 30 days, log scale
    complexity_score: float     # AST depth / avg function length
    test_coverage_score: float  # Heuristic: test file presence + imports
    evidence: list[str]         # Justifications per dimension
```

**Formulas:**
- **Coupling:** `(fan_in + fan_out) / (2 * num_files)`, capped at 1.0
- **Churn:** `min(1.0, commits_30d / 20)` (20 commits = high churn)
- **Complexity:** `min(1.0, avg_depth / 8)` (depth > 8 = complex)
- **Test coverage:** 0.0 if `test_*.py` exists, 0.5 if uncertain, 1.0 if none
- **Total:** `0.3*coupling + 0.2*churn + 0.2*complexity + 0.2*test_coverage + 0.1*other`

**Tests:** Unit (8+), property-based (hypothesis, 10+ cases), integration (3+)

---

### Task 3: DependencyHealthAnalyzer — Tightly Coupled Detection

**Scope:** Flag modules with high fan-in (depended-on by many), high fan-out (depends-on many), or circular dependencies.

**Inputs:**
- Call graph
- Import graph
- Architecture model (from task-008)

**Outputs:**
```python
@dataclass
class DependencyHealthReport:
    module_id: str
    high_fan_in: bool           # > 10 dependents
    high_fan_out: bool          # > 15 dependencies
    is_hub: bool                # Fan-in > 8 AND fan-out > 8
    cycles_involved: list[list[str]]  # Circular dependency chains
    recommendations: list[str]  # Action items (e.g., "extract interface")
```

**Algorithm:**
- Fan-in/fan-out from import edges
- Cycle detection (DFS, track visited nodes)
- Hub detection (both high in and high out)
- Recommend extraction/refactoring based on pattern

**Tests:** Unit (6+), integration with architecture (4+)

---

### Task 4: Integration + CLI Command

**Scope:** Integrate all three components, expose via `ortho analyze` subcommands.

**New CLI commands:**
```bash
ortho analyze --impact src/auth.py              # Blast radius for a file
ortho analyze --impact-symbol auth.get_user     # Blast radius for a symbol
ortho analyze --debt                             # Full debt report
ortho analyze --health                           # Dependency health report
```

**CLI options:**
- `--format json|text` (default: text)
- `--depth N` (for impact, default 3)
- `--module PATH` (for debt/health, scopes to module)

**Implementation:**
- Load architecture model from task-008
- Query graphs and compute scores
- Format output (table for text, JSON for parsing)
- Cache results in SQLite (optional, for large repos)

**Tests:** CLI integration (5+), end-to-end (3+)

---

## Architecture & Dependencies

```
task-009/
├── ImpactAnalyzer
│   ├── Inputs: call_edges, import_edges, file_id, depth
│   └── Outputs: ImpactReport
├── DebtScorer
│   ├── Inputs: call_edges, import_edges, symbols, git_metadata
│   └── Outputs: DebtScore[]
├── DependencyHealthAnalyzer
│   ├── Inputs: call_edges, import_edges, architecture_model
│   └── Outputs: DependencyHealthReport[]
└── CLI integration (analyze.py + analyze.ts enhancements)

Dependencies:
  - packages/repo-intelligence/ (graphs, symbols)
  - packages/arch-intelligence/ (architecture model)
  - shared/storage/ (SQLite for caching, optional)
  - gitpython (for churn analysis)
```

**No circular dependencies.** All flow downward to shared/.

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cycle detection expensive on large graphs | Medium | Limit DFS depth to 100 nodes; memoize results |
| Churn heuristic depends on git history | Medium | Fall back to 0.0 if git unavailable; document assumption |
| Debt scoring weights are arbitrary | Low | Make weights tunable via config; log evidence per dimension |
| Impact analysis gives false positives (indirect deps) | Medium | Use `confidence` field; mark static-analysis limitations in output |

---

## Acceptance Criteria (AC)

**AC1: ImpactAnalyzer correctly computes blast radius**
- Traverses call/import graphs up to depth N
- Returns direct and transitive dependents
- Risk score correlates with centrality (higher for hub modules)
- Handles cycles without infinite loops

**AC2: DebtScorer produces consistent, explainable scores**
- Scores are 0.0–1.0 (normalized)
- Evidence list justifies each dimension
- Identical inputs → identical outputs (deterministic)
- All 5 dimensions computed and weighted

**AC3: DependencyHealthAnalyzer identifies problematic patterns**
- High fan-in detection (>10 dependents)
- High fan-out detection (>15 dependencies)
- Circular dependency detection
- Recommends refactoring actions

**AC4: CLI commands work end-to-end**
- `ortho analyze --impact FILE` returns blast radius
- `ortho analyze --debt` returns module scores
- `ortho analyze --health` returns dependency report
- JSON output parseable

**AC5: Zero regressions in repo-intelligence, arch-intelligence**
- All existing tests pass
- No changes to public APIs of other packages

---

## Expected Test Metrics

- **Unit tests:** 25+
- **Integration tests:** 15+
- **Property-based tests (hypothesis):** 10+ cases
- **CLI tests:** 8+
- **Edge cases:** 6+ (cycles, missing git, large graphs)
- **Total:** 64+ tests
- **Expected coverage:** ≥85%
- **Expected pass rate:** 100% (or pre-approved xfail)

---

## Known Limitations (To Document Before GATE 4)

1. **Static analysis:** CallEdge confidence < 1.0 (cannot resolve dynamic calls)
2. **Churn scoring:** Requires git history; falls back to neutral if unavailable
3. **Debt weights:** Tuned for general Python repos; may not fit all domains
4. **Graph size:** Performance degrades beyond 10k nodes; document O(n) limits

---

## Rollback Plan

**If implementation fails:**

1. **Local rollback (branch):** `git reset --hard HEAD~[N]`
2. **Published rollback:** Create ADR-XXX documenting why, then `git revert [commit]` on main
3. **Data cleanup:** Delete `.ases/tasks/task-009-*` and `.ases/evidence/task-009/`
4. **Restart:** File issue, review plan, replan if needed

---

## Success Criteria (Definition of Done)

- ✅ GATE 1 (Plan): This document approved by human
- ✅ GATE 2 (Architecture): Reviewed against FRD, all circular deps resolved
- ✅ GATE 3 (Implementation): All 4 tasks implemented, no scope violations
- ✅ GATE 4 (Tests): 64+ tests written, pilot tests pass
- ✅ GATE 5 (Verification): All tests pass (pytest), coverage ≥85%
- ✅ GATE 6 (Review): Code quality approved, no security issues
- ✅ Evidence: All logs in `.ases/evidence/task-009/`
- ✅ Committed: Single squash commit or granular commits with rollback-safe granularity

---

*Created by PLANNER, 2026-07-02*
*Awaiting GATE 1 approval to proceed to ARCHITECT phase*
