# Phase 6.2: Decision Engine & CLI Integration — BUILDER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6.2 (Decision Engine & CLI)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 — Parallel implementation with TEST-DESIGNER  

---

## Build Order

### Phase 1: Setup
1. Create 2 package directories (decision-engine, cli-commands)
2. Define shared types (Decision, Recommendation, CliReport)
3. Set up test fixtures

### Phase 2: Parallel BUILDER + TEST-DESIGNER
- **BUILDER 1 + TEST-DESIGNER 1:** decision-engine (20 tests)
- **BUILDER 2 + TEST-DESIGNER 2:** cli-commands (20 tests)
- **BUILDER 3 + TEST-DESIGNER 3:** Integration tests (5 workflows)

### Phase 3: Final Testing
- All 55 tests pass
- Performance verified
- Metrics confirmed

---

## Component 1: Decision Engine

### Package Structure
```
packages/decision-engine/
├── src/decision_engine/
│   ├── __init__.py
│   ├── types.py                # Decision, Recommendation
│   ├── engine.py               # DecisionEngine class
│   └── ranker.py               # Ranking logic
├── tests/
│   ├── __init__.py
│   ├── test_engine.py          # 20 tests
│   ├── conftest.py
│   └── fixtures/
└── README.md
```

### Key Implementation

**Types (types.py):**
- `Decision` — intent, options (≥3), recommended_option, confidence, reasoning
- `Recommendation` — title, source, effort, risk, evidence, confidence

**Engine (engine.py):**
```python
class DecisionEngine:
    def decide(
        self,
        intent: str,
        change_predictions: list,
        feature_paths: list,
        refactoring_issues: list,
        guardrail_violations: list,
    ) -> Decision:
        """Aggregate all sources into ranked decision"""
        options = self._collect_options(...)
        deduped = self._deduplicate(options)
        ranked = self._rank_options(deduped, intent)
        return Decision(...)
```

**Ranker (ranker.py):**
```python
def rank_by_confidence_and_fit(
    options: list[Recommendation],
    intent: str,
) -> list[Recommendation]:
    """Score: confidence(0.7) × fit(0.3)"""
    pass
```

### Test Strategy
- 20 hard tests covering all scenarios
- Multi-source aggregation
- Deduplication verification
- Ranking correctness
- Edge case handling

---

## Component 2: CLI Commands

### Package Structure
```
packages/cli-commands/
├── src/cli_commands/
│   ├── __init__.py
│   ├── types.py                # CliReport
│   ├── commands.py             # CliCommands class
│   ├── formatter.py            # ReportFormatter
│   └── parser.py               # Argument parsing
├── tests/
│   ├── __init__.py
│   ├── test_commands.py        # 20 integration tests
│   ├── conftest.py
│   └── fixtures/
└── README.md
```

### Key Implementation

**Commands (commands.py):**
```python
class CliCommands:
    def plan(self, intent: str, **kwargs) -> str:
        """ortho plan "add endpoint" """
        paths = feature_planner.plan_feature(intent)
        return formatter.format_plan(paths, **kwargs)
    
    def refactor(self, path: str = None, **kwargs) -> str:
        """ortho refactor src/service.py"""
        issues = refactoring_advisor.find_issues(path)
        return formatter.format_refactor(issues, **kwargs)
    
    def guardrails(self, path: str = None, **kwargs) -> str:
        """ortho guardrails check"""
        violations = arch_guardrails.check_violations(path)
        return formatter.format_guardrails(violations, **kwargs)
    
    def decide(self, intent: str, **kwargs) -> str:
        """ortho decide "implement feature" """
        decision = decision_engine.decide(intent)
        return formatter.format_decision(decision, **kwargs)
```

**Formatter (formatter.py):**
```python
class ReportFormatter:
    def format_plan(self, paths: list) -> str:
        """Pretty-print feature paths"""
        pass
    
    def format_refactor(self, issues: list) -> str:
        """Pretty-print refactoring issues with evidence"""
        pass
    
    def format_guardrails(self, violations: list) -> str:
        """Pretty-print violations"""
        pass
    
    def format_decision(self, decision: Decision) -> str:
        """Pretty-print decision with options"""
        pass
```

### Test Strategy
- 20 integration tests (end-to-end commands)
- Output format verification (text, json, quiet, verbose)
- Error handling (bad input, missing context)
- Performance (<5s per command)

---

## Component 3: Integration Tests

### 5 Workflows
1. Feature Development: Feature planner → Decision → CLI output
2. Refactoring: Issues → Prioritization → Roadmap
3. Architecture: Violations → Fixes → Recommendations
4. Change Impact: Predictions → Analysis → Report
5. Combined: Multi-source → Decision → Action

### Test Strategy
- Real Phase 6.1 components (not mocks)
- Full workflows end-to-end
- Evidence traceability verified
- Performance acceptable (<5s per workflow)

---

## Success Checklist

- ✅ Decision-engine: 20 tests pass (100%)
- ✅ CLI-commands: 20 tests pass (100%)
- ✅ Integration: 5 workflows pass (100%)
- ✅ Type safety: mypy --strict
- ✅ Code coverage: ≥85%
- ✅ Performance: All commands <5s
- ✅ Adversarial tests: Edge cases handled
- ✅ No overfitting: Graceful on bad input

---

## Next Phase

1. **Component 4.1:** Real LLM API integration for decision scoring
2. **Component 5:** Feedback loop (learn from user decisions)
3. **Advanced workflows:** Multi-intent planning
4. **Team collaboration:** Multi-user decisions

