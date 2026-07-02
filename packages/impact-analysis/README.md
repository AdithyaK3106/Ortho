# Impact Analysis & Debt Scoring

Part of Ortho's **Pillar 3 (Architectural Intelligence)**.

## Purpose

Answer three key architectural questions:

1. **Impact Analysis:** "If I change this file, what breaks?"
2. **Debt Scoring:** "Which modules have the highest technical debt?"
3. **Dependency Health:** "Which dependencies are problematic?"

## Architecture

All components follow a **stateless analyzer pattern** (matching task-008):
- No constructor state
- All data passed as function arguments
- Deterministic, pure functions
- Enables testing, injection, and parallelization

## Components

### ImpactAnalyzer

Computes the blast radius of changing a file or symbol.

```python
from impact_analysis import ImpactAnalyzer

analyzer = ImpactAnalyzer()
report = analyzer.analyze(
    call_graph=call_edges,
    import_graph=import_edges,
    changed_file_id="src/auth.py",
    symbols=symbols,
    depth=3,
)

print(f"Risk: {report.risk_score:.1%}")
print(f"Confidence: {report.analysis_confidence:.1%}")
print(f"Blast radius: {report.blast_radius} files")
```

**Output: ImpactReport**
- `changed_file_id`: The file being analyzed
- `direct_dependents`: Files that directly import/call this file
- `transitive_dependents`: All reachable dependents within depth hops
- `risk_score`: 0.0–1.0 (engineering impact from centrality)
- `analysis_confidence`: 0.0–1.0 (certainty of analysis)
- `blast_radius`: Count of affected files
- `evidence`: Human-readable justifications

### DebtScorer

Computes technical debt per module using 5 dimensions.

```python
from impact_analysis import DebtScorer

scorer = DebtScorer()
score = scorer.score_module(
    file_id="src/api.py",
    call_graph=call_edges,
    import_graph=import_edges,
    symbols=symbols,
    git_metadata=metadata,
)

print(f"Total debt: {score.total_score:.1%}")
print(f"Coupling: {score.coupling_score:.1%}")
print(f"Churn: {score.churn_score:.1%}")
print(f"Complexity: {score.complexity_score:.1%}")
print(f"Test coverage: {score.test_coverage_score:.1%}")
```

**Scoring Dimensions (Phase 1 Defaults):**
- **Coupling (30%):** `(fan_in + fan_out) / 2`, measures dependency centrality
- **Churn (20%):** `min(1.0, commits_30d / 20)`, measures change frequency
- **Complexity (20%):** `min(1.0, avg_ast_depth / 8)`, measures nesting depth
- **Test Coverage (20%):** `0.0 if tests exist, 1.0 if none`, measures test presence
- **Other (10%):** Reserved for future metrics

**Output: DebtScore**
- All five dimension scores (0.0–1.0)
- `total_score`: Weighted average
- `evidence`: Justifications per dimension

### DependencyHealthAnalyzer

Detects problematic dependency patterns.

```python
from impact_analysis import DependencyHealthAnalyzer

analyzer = DependencyHealthAnalyzer()
report = analyzer.analyze_module(
    file_id="src/core.py",
    call_graph=call_edges,
    import_graph=import_edges,
)

if report.is_hub:
    print("WARNING: Hub module detected!")
    for rec in report.recommendations:
        print(f"  - {rec}")
```

**Pattern Detection (Phase 1 Defaults):**
- **High fan-in:** >10 dependents (core module)
- **High fan-out:** >15 dependencies (too many deps)
- **Hub:** Both high fan-in AND high fan-out
- **Circular dependencies:** Cycles in import graph

**Output: DependencyHealthReport**
- `fan_in`, `fan_out`: Dependency counts
- `high_fan_in`, `high_fan_out`, `is_hub`: Pattern flags
- `cycles_involved`: List of cycle chains
- `recommendations`: Actionable refactoring suggestions
- `evidence`: Justifications for findings

## Configuration

**Phase 1 Defaults** (documented, not hardcoded):

```python
# Debt weights
DebtScorer.DEFAULT_WEIGHTS = {
    "coupling": 0.30,
    "churn": 0.20,
    "complexity": 0.20,
    "test_coverage": 0.20,
    "other": 0.10,
}

# Dependency thresholds
DependencyHealthAnalyzer.DEFAULT_THRESHOLDS = {
    "high_fan_in": 10,
    "high_fan_out": 15,
    "hub_fan_in": 8,
    "hub_fan_out": 8,
}

# Churn threshold
DebtScorer.CHURN_THRESHOLD = 20  # commits in 30 days
DebtScorer.COMPLEXITY_THRESHOLD = 8  # AST depth
```

All values are Phase 1 defaults. Future versions may expose configuration via files or CLI.

## Key Design Decisions

### Stateless Pattern
All analyzers are functions that accept data as arguments. No state is stored in constructors.
This matches the architecture of task-008 and enables:
- Easy testing (no setup/teardown)
- Dependency injection (pass test doubles)
- Parallelization (no shared state)

### Metrics Separation
- **Risk Score:** Engineering impact from dependency centrality
- **Analysis Confidence:** Certainty that static analysis is correct

These are never interchangeable. A file can have:
- High risk + high confidence (central, well-analyzed)
- High risk + low confidence (central, calls unresolved)
- Low risk + high confidence (isolated, well-analyzed)

### Configuration as Defaults
Weights and thresholds are documented as Phase 1 defaults, not universal constants.
They work well for typical Python repos but may need calibration for:
- Larger codebases
- Different domains (microservices, data pipelines, ML)
- Different languages (when TypeScript adapter is added)

Future versions will expose these through configuration without changing the architecture.

## Known Limitations

1. **Static analysis confidence:** Cannot resolve dynamic calls (getattr, eval, etc.)
2. **Churn unavailable:** If git metadata missing, defaults to 0.0 (neutral)
3. **Complexity heuristic:** AST depth is proxy; doesn't account for McCabe complexity
4. **Debt weights:** Tuned for general Python repos; may not fit all domains
5. **Thresholds:** Practical for typical projects; larger repos may need calibration
6. **Performance:** BFS on graphs >10k symbols may be slow (O(n + m))

All limitations are documented before implementation and do not block Phase 1 completion.

## Testing

```bash
# Run unit tests
pytest packages/impact-analysis/tests/ -v

# Run with coverage
pytest packages/impact-analysis/tests/ --cov=impact_analysis

# Run property-based tests (hypothesis)
pytest packages/impact-analysis/tests/ -k "property" -v
```

## Dependencies

- Python 3.10+
- No external dependencies for core components
- pytest, hypothesis for testing
- black, ruff, mypy for code quality

## Integration with Ortho

Used by:
- CLI: `ortho analyze --impact`, `--debt`, `--health`
- Pillar 4 (Orchestration): Context assembly for impact reports
- Pillar 5 (Token Optimizer): Architecture-aware ranking

Depends on:
- Pillar 1 (Repo Intelligence): call_graph, import_graph, symbols
- Pillar 3 (Architecture Intelligence): architecture_model (optional)
- Git metadata (via gitpython or external)

## References

- FRD: `ortho-v3-frd.md`, Section 8 (Pillar 3)
- Architecture: `.ases/tasks/task-009-impact-analysis/architecture-review.md`
- Task Plan: `.ases/tasks/task-009-impact-analysis/plan.md`
- Specification: `.ases/tasks/task-009-impact-analysis/spec.md`
