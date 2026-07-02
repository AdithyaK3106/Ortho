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

**Architecture:** Stateless analyzer matching task-008 pattern (no constructor state, all data passed as arguments).

**Inputs:**
- Call graph (from CallGraphBuilder, task-003)
- Import graph (from ImportGraphBuilder, task-003)
- Changed file ID
- Depth parameter (default 3 hops)

**Outputs:**
```python
@dataclass
class ImpactReport:
    changed_file_id: str
    direct_dependents: list[str]          # Files that directly import/call this file
    transitive_dependents: list[str]      # Reachable within `depth` hops
    risk_score: float                     # 0.0–1.0 based on centrality
    analysis_confidence: float            # 0.0–1.0 based on resolution quality
    blast_radius: int                     # Count of affected files
    evidence: list[str]                   # Human-readable justifications
```

**Implementation:**
- BFS traversal of import/call edges (stateless)
- Risk scoring: (fan_in + fan_out) / (2 * num_symbols), clamped to [0.0, 1.0]
- Confidence scoring: 1.0 - (unresolved_symbols / total_symbols)
- Cycle detection (ignore cycles in risk computation)
- Query by file_id or symbol_id

**Tests:** Unit (6+), integration (4+), edge cases (3+)

---

### Task 2: DebtScorer — Multi-Dimensional Scoring

**Scope:** Compute technical debt score per module using 5 dimensions.

**Architecture:** Stateless analyzer matching task-008 pattern (no constructor state, all data passed as arguments).

**Inputs:**
- Call graph (task-003)
- Import graph (task-003)
- Symbols (task-002)
- Git metadata (commits_30d, last_modified, size_bytes per file)

**Configuration (Phase 1 Defaults):**
- Coupling weight: 0.30
- Churn weight: 0.20
- Complexity weight: 0.20
- Test coverage weight: 0.20
- Other weight: 0.10

**Scoring dimensions:**
```python
@dataclass
class DebtScore:
    module_id: str
    total_score: float          # 0.0 (clean) — 1.0 (critical), weighted average
    coupling_score: float       # (fan_in + fan_out) / (module_files * 2), capped at 1.0
    churn_score: float          # min(1.0, commits_30d / 20), default threshold
    complexity_score: float     # min(1.0, avg_ast_depth / 8), default threshold
    test_coverage_score: float  # Heuristic: test file presence in package
    evidence: list[str]         # Justifications per dimension
```

**Formulas:**
- **Coupling:** `(fan_in + fan_out) / (2 * num_files)`, capped at 1.0
- **Churn:** `min(1.0, commits_30d / 20)` (default: 20 commits = high churn)
- **Complexity:** `min(1.0, avg_ast_depth / 8)` (default: depth > 8 = complex)
- **Test coverage:** 0.0 if `test_*.py` exists, 0.5 if uncertain, 1.0 if none
- **Total:** Apply default weights: `0.3*coupling + 0.2*churn + 0.2*complexity + 0.2*coverage + 0.1*other`

Note: Default thresholds (20 commits, depth 8) work well for typical Python repos. Larger codebases may need calibration.

**Tests:** Unit (8+), property-based (hypothesis, 10+ cases), integration (3+)

---

### Task 3: DependencyHealthAnalyzer — Tightly Coupled Detection

**Scope:** Flag modules with high fan-in (depended-on by many), high fan-out (depends-on many), or circular dependencies.

**Architecture:** Stateless analyzer matching task-008 pattern (no constructor state, all data passed as arguments).

**Configuration (Phase 1 Defaults):**
- High fan-in threshold: > 10 dependents
- High fan-out threshold: > 15 dependencies
- Hub detection: fan-in > 8 AND fan-out > 8

Note: These are practical defaults for typical Python repos. Larger codebases may need calibration.

**Inputs:**
- Call graph
- Import graph
- Architecture model (from task-008, optional)

**Outputs:**
```python
@dataclass
class DependencyHealthReport:
    module_id: str
    fan_in: int                 # Count of incoming dependencies
    fan_out: int                # Count of outgoing dependencies
    high_fan_in: bool           # fan_in exceeds threshold (default: > 10)
    high_fan_out: bool          # fan_out exceeds threshold (default: > 15)
    is_hub: bool                # Both thresholds exceeded (default: > 8 each)
    cycles_involved: list[list[str]]  # Circular dependency chains
    recommendations: list[str]  # Action items (e.g., "extract interface")
```

**Algorithm:**
- Fan-in/fan-out from import edges (stateless)
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

### Stateless Design (Consistent with Task-008)

All three analyzers follow the stateless pattern of task-008:
- No constructor-based state
- All data passed as function arguments
- Deterministic outputs for identical inputs
- Pure functions enabling parallel processing and testing

### Component Structure

```
task-009/
├── ImpactAnalyzer (stateless)
│   ├── Inputs: call_graph, import_graph, file_id, depth
│   └── Output: ImpactReport (includes risk_score + analysis_confidence)
├── DebtScorer (stateless)
│   ├── Inputs: call_graph, import_graph, symbols, git_metadata
│   ├── Config: DEFAULT_WEIGHTS (0.30, 0.20, 0.20, 0.20, 0.10)
│   └── Output: DebtScore[]
├── DependencyHealthAnalyzer (stateless)
│   ├── Inputs: call_graph, import_graph, architecture_model (optional)
│   ├── Config: DEFAULT_THRESHOLDS (10, 15, 8, 8)
│   └── Output: DependencyHealthReport[]
└── CLI integration (analyze.py + analyze.ts enhancements)
```

### Dependencies

```
Inputs from:
  - packages/repo-intelligence/ (call_edges, import_edges, symbols)
  - packages/arch-intelligence/ (architecture model)
  - git metadata (via gitpython)

Optional:
  - shared/storage/ (SQLite for result caching)
  - packages/arch-intelligence/model_store (for architecture model)
```

**No circular dependencies.** All flow downward to shared/.

---

## Architectural Consistency (Task-008 Alignment)

### Stateless Pattern
Task-009 analyzers match the stateless architecture of task-008 (ArchitectureDetector, LayerDetector, SubsystemDetector).
This ensures consistent API design across Pillar 3.

**Pattern applied:**
- No constructor state (e.g., NOT `ImpactAnalyzer(call_graph, import_graph)`)
- All data passed as arguments (e.g., `analyzer.analyze(call_graph, import_graph, file_id)`)
- Deterministic, pure functions
- Enables testing, parallelization, and dependency injection

### Configuration vs Architecture
Task-009 distinguishes between algorithm (immutable) and configuration (tunable defaults).

**Default configuration (Phase 1):**
- Debt weights: 0.30 coupling, 0.20 churn, 0.20 complexity, 0.20 coverage, 0.10 other
- Dependency thresholds: fan_in > 10, fan_out > 15, hub > 8/8
- Churn threshold: 20 commits/30 days
- Complexity threshold: AST depth > 8

**Key principle:** Changing configuration does not change the architecture or algorithm.
Implementation uses documented defaults; future versions may expose configuration via files or CLI.

### Metrics Separation
Task-009 clearly separates risk_score (engineering impact) from analysis_confidence (analysis certainty).

**Risk Score** — Derived from: Dependency centrality, blast radius, graph connectivity
**Analysis Confidence** — Limited by: Dynamic dispatch, unresolved symbols, incomplete graphs

These are never interchangeable and are reported separately in all outputs.

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cycle detection expensive on large graphs | Medium | Limit DFS depth to 100 nodes; memoize results |
| Churn heuristic depends on git history | Medium | Fall back to 0.0 if git unavailable; document assumption |
| Debt configuration weights | Low | Document as Phase 1 defaults; algorithm is immutable; future versions may expose tuning |
| Impact analysis confidence | Medium | Separate analysis_confidence from risk_score; mark static-analysis limitations in output |
| Dependency thresholds | Medium | Document as Phase 1 defaults for typical repos; larger codebases may need calibration |

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
