---
name: task-009-spec
type: specification
phase: Phase 2, Week 11–12
task_id: task-009-impact-analysis
---

# Task-009 Specification: Impact Analysis + Debt Scoring

## Overview

Implement Pillar 3 (Architectural Intelligence) components for:
1. **Change impact analysis** — given a file change, compute blast radius (affected downstream files)
2. **Technical debt scoring** — per-module score on coupling, churn, complexity, test coverage
3. **Dependency health** — flag tightly coupled, high fan-in/fan-out, circular dependency patterns

## Component 1: ImpactAnalyzer

### Purpose
Answer: "If I change file X, what other files could break?"

### Class: `ImpactAnalyzer`

```python
class ImpactAnalyzer:
    def __init__(self, call_graph: dict, import_graph: dict):
        """
        call_graph: dict[symbol_id] -> list[symbol_id]  (caller -> list of callees)
        import_graph: dict[file_id] -> list[file_id]    (importer -> list of imported files)
        """
        self.call_graph = call_graph
        self.import_graph = import_graph
    
    def analyze(
        self,
        changed_file_id: str,
        depth: int = 3
    ) -> ImpactReport:
        """
        Traverse call and import graphs starting from changed_file_id.
        
        Algorithm:
        1. Find all symbols in changed_file_id
        2. BFS on call_graph: who calls these symbols? (direct dependents)
        3. BFS on import_graph: who imports this file? (recursive up to depth)
        4. Map symbols back to files
        5. Compute risk_score based on centrality (fan-in + fan-out)
        
        Args:
            changed_file_id: File being modified
            depth: How many hops to traverse (default 3)
        
        Returns:
            ImpactReport with direct_dependents, transitive_dependents, risk_score, blast_radius
        
        Edge cases:
        - File not in graphs → return empty report with risk_score=0.0
        - Cycles in graph → use visited set to prevent infinite loop
        - Symbol not found → skip (confidence < 1.0)
        """
        ...
    
    def analyze_symbol(
        self,
        symbol_id: str,
        depth: int = 3
    ) -> ImpactReport:
        """Variant: analyze by symbol instead of file."""
        ...
```

### Data Type: `ImpactReport`

```python
@dataclass
class ImpactReport:
    changed_file_id: str
    direct_dependents: list[str]          # File IDs that directly depend
    transitive_dependents: list[str]      # All reachable within depth
    risk_score: float                     # 0.0–1.0
    blast_radius: int                     # len(transitive_dependents)
    evidence: list[str]                   # Human-readable justifications
    
    def __post_init__(self):
        # Validate scores
        assert 0.0 <= self.risk_score <= 1.0, "risk_score must be 0.0–1.0"
        assert self.blast_radius >= 0, "blast_radius must be non-negative"
```

### Risk Score Computation

**Formula:**
```
risk_score = (fan_in + fan_out) / (2 * num_symbols) 
           = centrality of changed file
           
fan_in = number of files importing this file
fan_out = number of files this file imports
num_symbols = number of symbols in changed file (default 1 if unknown)
```

**Intuition:** A file that is imported by many files (high fan_in) is central and risky to change.

### Tests (13+ total)

**Unit tests (6+):**
- `test_impact_simple_import_chain` — A → B → C, change A, blast radius = 2
- `test_impact_cycle_handling` — A → B → A, no infinite loop
- `test_impact_depth_limit` — Depth 1 vs depth 3, different results
- `test_impact_symbol_level` — Change one symbol, not entire file
- `test_impact_no_dependents` — Leaf file, blast_radius = 0
- `test_impact_high_fan_in` — Central file, risk_score close to 1.0

**Integration tests (4+):**
- `test_impact_real_repo` — Run on fastapi, verify symbols map to files
- `test_impact_missing_file` — Handle file_id not in graphs gracefully
- `test_impact_large_graph` — 1000+ symbols, no timeout

**Edge cases (3+):**
- `test_impact_empty_graphs` — No graphs, empty report
- `test_impact_self_loop` — File imports itself, no double-counting
- `test_impact_disconnected_component` — Isolated modules

---

## Component 2: DebtScorer

### Purpose
Answer: "Which modules are highest tech debt?"

### Class: `DebtScorer`

```python
class DebtScorer:
    def __init__(
        self,
        call_graph: dict,
        import_graph: dict,
        symbols: list[Symbol],
        git_metadata: dict[str, GitFileMetadata]
    ):
        """
        git_metadata: dict[file_path] -> GitFileMetadata
            - commits_30d: int
            - last_modified: datetime
            - size_bytes: int
        """
        ...
    
    def score_module(self, file_id: str) -> DebtScore:
        """Compute debt score for a single file."""
        ...
    
    def score_all_modules(self) -> list[DebtScore]:
        """Compute scores for all files, sorted by total_score desc."""
        ...
```

### Data Type: `DebtScore`

```python
@dataclass
class DebtScore:
    module_id: str
    total_score: float          # 0.0–1.0 (weighted average)
    coupling_score: float       # 0.0–1.0
    churn_score: float          # 0.0–1.0
    complexity_score: float     # 0.0–1.0
    test_coverage_score: float  # 0.0–1.0
    evidence: list[str]         # One line per dimension
    
    def __post_init__(self):
        for score in [self.total_score, self.coupling_score, self.churn_score,
                      self.complexity_score, self.test_coverage_score]:
            assert 0.0 <= score <= 1.0, f"All scores must be 0.0–1.0, got {score}"
```

### Scoring Formulas

**1. Coupling Score**
```
coupling = (fan_in + fan_out) / (2 * num_files_in_module)
clamped to [0.0, 1.0]

Interpretation:
- 0.0: Isolated module, no dependencies
- 0.5: Moderate coupling
- 1.0: Hub module (many dependents and dependencies)
```

**2. Churn Score**
```
churn = min(1.0, commits_30_days / 20)

Interpretation:
- 0.0: No changes (stable)
- 0.5: 10 commits in 30 days (moderate)
- 1.0: 20+ commits in 30 days (very active)

Rationale: Frequently changed files are risky.
```

**3. Complexity Score**
```
complexity = min(1.0, avg_ast_depth / 8)

where:
  avg_ast_depth = average nesting depth of functions in file
  
Interpretation:
- 0.0: Simple functions (depth ≤ 2)
- 0.5: Moderately nested (depth ~ 4)
- 1.0: Deep nesting (depth ≥ 8)
```

**4. Test Coverage Score**
```
if test_*.py exists in same package:
  test_coverage = 0.0 (has tests, good)
elif test_*.py exists elsewhere:
  test_coverage = 0.5 (tests exist, but not co-located)
else:
  test_coverage = 1.0 (no tests found, bad)

Interpretation:
- 0.0: Tests present
- 1.0: No tests
```

**5. Total Score (Weighted Average)**
```
total = 0.3 * coupling 
      + 0.2 * churn 
      + 0.2 * complexity 
      + 0.2 * test_coverage 
      + 0.1 * (other factors: size, age, etc.)
```

### Tests (21+ total)

**Unit tests (8+):**
- `test_coupling_score_isolated` — One file, no deps → 0.0
- `test_coupling_score_hub` — High fan-in and fan-out → 1.0
- `test_churn_score_stable` — 0 commits → 0.0
- `test_churn_score_active` — 30 commits → 1.0
- `test_complexity_score_simple` — Depth 1 → 0.0
- `test_complexity_score_deep` — Depth 10 → 1.0
- `test_test_coverage_score_present` — test_*.py exists → 0.0
- `test_test_coverage_score_absent` — No tests → 1.0

**Property-based tests (10+ cases via hypothesis):**
- `test_debt_score_bounds` — All scores in [0.0, 1.0]
- `test_debt_score_deterministic` — Same input → same output
- `test_debt_score_independent` — Each module scored independently
- (+ 7 more generating random graphs, varying git metadata, etc.)

**Integration tests (3+):**
- `test_score_real_repo` — Run on fastapi, verify scores reasonable
- `test_score_all_modules` — Sort by risk, verify ordering

---

## Component 3: DependencyHealthAnalyzer

### Purpose
Answer: "Which dependencies are problematic?"

### Class: `DependencyHealthAnalyzer`

```python
class DependencyHealthAnalyzer:
    def __init__(
        self,
        call_graph: dict,
        import_graph: dict,
        architecture_model: ArchitectureModel | None = None
    ):
        ...
    
    def analyze_module(self, file_id: str) -> DependencyHealthReport:
        """Analyze health of a single module."""
        ...
    
    def analyze_all_modules(self) -> list[DependencyHealthReport]:
        """Full repository health report."""
        ...
    
    def find_cycles(self) -> list[list[str]]:
        """Detect all circular dependency chains."""
        ...
```

### Data Type: `DependencyHealthReport`

```python
@dataclass
class DependencyHealthReport:
    module_id: str
    fan_in: int                     # Count of incoming dependencies
    fan_out: int                    # Count of outgoing dependencies
    high_fan_in: bool               # fan_in > 10
    high_fan_out: bool              # fan_out > 15
    is_hub: bool                    # fan_in > 8 AND fan_out > 8
    cycles_involved: list[list[str]]  # [[A, B, C, A], ...]
    recommendations: list[str]      # ["Extract interface", ...]
    evidence: list[str]             # Justifications
```

### Thresholds & Patterns

| Pattern | Trigger | Recommendation |
|---------|---------|-----------------|
| High fan-in | fan_in > 10 | This is a core module; test thoroughly |
| High fan-out | fan_out > 15 | This module has too many dependencies; consider layering |
| Hub | fan_in > 8 AND fan_out > 8 | Extract into separate layer or break into smaller modules |
| Circular dep | A → B → A | Break cycle with interface/abstraction |

### Tests (10+ total)

**Unit tests (6+):**
- `test_fan_in_count_simple` — Direct imports only
- `test_fan_out_count_simple` — Direct exports only
- `test_cycle_detection_simple` — A → B → A
- `test_cycle_detection_complex` — 3-node cycle
- `test_hub_detection` — High fan_in AND high fan_out
- `test_recommendations_generated` — Each pattern triggers recommendation

**Integration tests (4+):**
- `test_health_real_repo` — Run on fastapi, verify no false positives
- `test_health_no_cycles` — Clean repo has no cycles
- `test_health_with_architecture_model` — Use layers from task-008

---

## Component 4: CLI Integration

### New Commands

```bash
ortho analyze --impact <file>
  → ImpactAnalyzer.analyze(file_id, depth=3)
  → Print blast radius, risk_score, dependents

ortho analyze --impact-symbol <symbol>
  → ImpactAnalyzer.analyze_symbol(symbol_id, depth=3)
  → Similar output, but for a symbol

ortho analyze --debt [--module <path>]
  → DebtScorer.score_all_modules()
  → Print table: module | total_score | coupling | churn | complexity | coverage

ortho analyze --health [--module <path>]
  → DependencyHealthAnalyzer.analyze_all_modules()
  → Print: module | fan_in | fan_out | hub | cycles | recommendations
```

### Output Formats

**Text (default):**
```
$ ortho analyze --impact src/auth.py

Impact Report for src/auth.py
Risk Score: 0.72 (HIGH)
Blast Radius: 5 files affected

Direct Dependents (1):
  - src/api/routes.py

Transitive Dependents (5):
  - src/api/routes.py
  - src/middleware/auth.py
  - src/handlers/user.py
  - src/handlers/token.py
  - src/handlers/verify.py

Evidence:
  - auth.py imported by 1 file, called from 5 functions
  - get_user() called from routes.py (high centrality)
  - Cycle detected: auth.py → cache.py → auth.py (ignored in traversal)
```

**JSON:**
```json
{
  "changed_file_id": "src/auth.py",
  "risk_score": 0.72,
  "blast_radius": 5,
  "direct_dependents": ["src/api/routes.py"],
  "transitive_dependents": [...],
  "evidence": [...]
}
```

### Tests (8+ total)

- `test_cli_impact_command` — Runs `ortho analyze --impact`
- `test_cli_debt_command` — Runs `ortho analyze --debt`
- `test_cli_health_command` — Runs `ortho analyze --health`
- `test_cli_json_format` — --format json produces valid JSON
- `test_cli_text_format` — --format text produces readable output
- `test_cli_module_scope` — --module narrows scope
- `test_cli_depth_option` — --depth N controls traversal
- `test_cli_missing_file` — Handles non-existent file gracefully

---

## Expected Test Metrics Summary

| Category | Count | Note |
|----------|-------|------|
| Unit tests | 20+ | Isolate each component |
| Integration tests | 16+ | Real graphs + architecture |
| Property-based (hypothesis) | 10+ | Determinism, bounds, edge cases |
| CLI tests | 8+ | End-to-end command validation |
| Edge cases | 6+ | Cycles, missing data, large graphs |
| **Total** | **60+** | Exceeds 55+ minimum |
| **Coverage target** | **≥85%** | Per component, aggregated |
| **Pass rate** | **100%** | No known xfail (known limitations documented before GATE 4) |

---

## Known Limitations (To Mark as xfail if Testing Confirms)

1. **Static analysis confidence:** ImpactAnalyzer cannot resolve dynamic calls (e.g., `getattr(obj, method_name)()`). Confidence < 1.0.
2. **Churn unavailable:** If git metadata missing, churn_score defaults to 0.0 (neutral).
3. **Complexity heuristic:** AST depth is a proxy; doesn't account for McCabe complexity or actual logic.
4. **Debt weights:** Tuned for general Python repos; may not fit all domains (microservices, data pipelines, etc.).
5. **Performance:** BFS on graphs > 10k symbols may be slow; document O(n) complexity.

---

## Rollback (If Implementation Fails)

1. **Branch-level:** `git reset --hard HEAD~[N]`
2. **Published (main):** `git revert [commit]` + document in ADR
3. **Clean up:** `rm -rf .ases/tasks/task-009-* .ases/evidence/task-009/`
4. **Restart:** Replan with updated requirements

---

*Specification created by PLANNER, 2026-07-02*
*Awaiting GATE 1 approval*
