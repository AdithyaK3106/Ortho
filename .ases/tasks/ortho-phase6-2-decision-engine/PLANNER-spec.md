# Phase 6.2: Decision Engine & CLI Integration — PLANNER Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6.2 (Decision Engine & CLI)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 with parallel BUILDER + TEST-DESIGNER  
**Duration:** 1 week (Phase 6.2 MVP)  
**Builds On:** Phase 6.1 (all 4 components: change-planner, feature-planner, refactoring-advisor, arch-guardrails)

---

## Executive Summary

Phase 6.2 delivers:

1. **Decision Engine** — Structured decision support combining multiple recommendation sources
2. **CLI Commands** — User-facing commands: `ortho plan`, `ortho refactor`, `ortho guardrails`, `ortho decide`
3. **Orchestrator Integration** — Wire all components into main workflow
4. **Report Generator** — Pretty-print recommendations with evidence

**Success Criteria (Hard Metrics):**
- ✅ Decision engine combines 3+ sources (change, feature, refactoring, guardrails)
- ✅ CLI commands execute end-to-end (intent → analysis → recommendations)
- ✅ Reports include evidence, confidence scores, actionable fixes
- ✅ Integration tests verify full workflows
- ✅ 90%+ test pass rate (hard scenarios)
- ✅ Zero overfitting (adversarial user inputs)

---

## Current State (End of Phase 6.1)

**What Phase 6.1 Built:**
- ✅ Change Planner (22/22 tests, 92% coverage)
- ✅ Feature Planner (18/18 tests, 96% coverage)
- ✅ Refactoring Advisor (22/22 tests, 95% coverage)
- ✅ Arch Guardrails (18/18 tests, 98% coverage)
- ✅ Total: 78/78 tests passing (100%)

**Missing (Phase 6.2 Inputs):**
- Decision engine (orchestrates recommendations)
- CLI commands (user-facing interface)
- Report formatting (human-readable output)
- Integration with orchestrator
- End-to-end workflows

---

## Phase 6.2 Architecture

### Package Structure

```
packages/
├── decision-engine/          [NEW]
│   ├── src/decision_engine/
│   │   ├── engine.py         # Main decision orchestrator
│   │   ├── types.py          # Decision, Recommendation
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_engine.py    # 20 hard tests
│   │   └── fixtures/
│   └── README.md
│
├── cli-commands/             [NEW]
│   ├── src/cli_commands/
│   │   ├── commands.py       # plan, refactor, guardrails, decide
│   │   ├── formatter.py      # Pretty-print reports
│   │   ├── types.py          # CliReport
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_commands.py  # 20 integration tests
│   │   └── fixtures/
│   └── README.md
│
└── orchestration/            [EXTEND]
    └── integration tests (5 end-to-end flows)
```

### Data Models

**Decision:**
```python
@dataclass
class Decision:
    intent: str                      # User's request
    options: list[Recommendation]    # ≥3 distinct options
    recommended_option: str          # Best fit
    reasoning: str                   # Why this option
    confidence: float                # 0.0-1.0
```

**Recommendation:**
```python
@dataclass
class Recommendation:
    title: str
    description: str
    source: str                      # change_planner | feature_planner | refactoring | guardrails
    effort: str                      # low | medium | high
    risk: str                        # low | medium | high
    evidence: list[str]
    confidence: float
    suggested_fix: str
```

---

## Acceptance Criteria

### AC1: Decision Engine MVP ✅

**Definition:**
- Aggregates recommendations from 4 sources
- Returns ≥3 distinct options
- Ranks by confidence + fit
- Provides reasoning

**Acceptance Criteria:**
- ✅ 20 hard test cases (multi-source decisions, edge cases)
- ✅ Combines 3+ sources (min 90% of scenarios)
- ✅ Returns ≥3 options (verified in variety tests)
- ✅ All options have confidence + reasoning
- ✅ Handles missing sources gracefully

**Test Cases (20 total):**

1. Single source: change-planner only
2. Single source: feature-planner only
3. Single source: refactoring-advisor only
4. Single source: guardrails only
5. Two sources: change + feature
6. Two sources: refactoring + guardrails
7. Three sources: change + feature + refactoring
8. Three sources: feature + refactoring + guardrails
9. All four sources combined
10. Conflicting recommendations (choose highest confidence)
11. Empty sources (handle gracefully)
12. All low confidence (report risk)
13. High confidence consensus (agree on top option)
14. Dispersed confidence (variety of scores)
15. Large option set (deduplicate similar recommendations)
16. Zero-risk option prioritized
17. Low-effort option when confidence equal
18. High-impact option when multiple viable
19. User preference override (recommend different option)
20. Adversarial: contradictory sources (handle conflicts)

---

### AC2: CLI Commands MVP ✅

**Definition:**
- `ortho plan <intent>` — Full feature planning
- `ortho refactor <path>` — Refactoring recommendations
- `ortho guardrails check` — Architectural violations
- `ortho decide <intent>` — Multi-source decision

**Acceptance Criteria:**
- ✅ 20 integration tests (end-to-end CLI flows)
- ✅ Commands parse args correctly
- ✅ Execute analysis end-to-end
- ✅ Reports readable + actionable
- ✅ Error handling for bad inputs

**Test Cases (20 total):**

1. `ortho plan "add user search endpoint"`
2. `ortho plan "add background job"`
3. `ortho plan "add caching layer"`
4. `ortho refactor src/service.py`
5. `ortho refactor --all` (full codebase)
6. `ortho guardrails check`
7. `ortho guardrails check --strict` (errors only)
8. `ortho guardrails check src/api/` (specific path)
9. `ortho decide "implement new feature"`
10. `ortho decide "improve code quality"`
11. `ortho decide "reduce technical debt"`
12. Plan with missing context (graceful degradation)
13. Refactor on empty codebase (no issues)
14. Guardrails on compliant architecture (no violations)
15. Decide with conflicting sources (choose best)
16. CLI with verbose output (`-v`, `--verbose`)
17. CLI with json output (`--json`)
18. CLI with quiet output (`-q`, `--quiet`)
19. CLI error: bad intent
20. CLI error: missing file/path

---

### AC3: Integration Tests MVP ✅

**Definition:**
- Full workflows (intent → decision → action)
- Orchestrator wiring verified
- End-to-end scenarios

**Acceptance Criteria:**
- ✅ 5 end-to-end workflows tested
- ✅ Real Phase 6.1 components used
- ✅ All happy path + error cases
- ✅ Performance acceptable (<5s per flow)

**Workflows (5 total):**

1. **Feature Development Workflow**
   - Intent: "add rate limiting to API"
   - Plan: Feature Planner suggests paths
   - Decision: Engine picks best path
   - Action: Recommend implementation

2. **Refactoring Workflow**
   - Intent: "improve code quality"
   - Analysis: Refactoring Advisor finds issues
   - Decision: Prioritize issues
   - Action: Provide fixes

3. **Architecture Enforcement Workflow**
   - Intent: "verify architecture compliance"
   - Check: Guardrails scan violations
   - Report: List violations + fixes
   - Action: Remediation steps

4. **Change Impact Workflow**
   - Intent: "assess impact of auth service change"
   - Predict: Change Planner forecasts affects
   - Report: Impact analysis
   - Action: Recommended verification steps

5. **Combined Workflow**
   - Intent: "implement new microservice"
   - Multiple sources: feature + change + guardrails
   - Decision: Best approach combining all input
   - Action: Full implementation roadmap

---

## Parallel Execution Plan (TEST-DESIGNER + BUILDER)

### BUILDER Tasks
1. Implement decision-engine package (20 hard tests)
2. Implement cli-commands package (20 integration tests)
3. Integration tests (5 workflows)
4. Wire into orchestrator

### TEST-DESIGNER Tasks (Parallel)
1. Decision engine tests (multi-source scenarios)
2. CLI command tests (end-to-end flows)
3. Integration tests (full workflows)
4. Report formatting tests (edge cases)

---

## Success Metrics (GATE 5)

| Metric | Target | Evidence |
|--------|--------|----------|
| **Decision Quality** | ≥3 options/intent | 20/20 tests verify |
| **CLI Functionality** | All commands work | 20/20 integration tests |
| **End-to-End Workflows** | 5/5 complete | Orchestrator tests |
| **Test Pass Rate** | 100% | 45+ tests passing |
| **Type Safety** | mypy --strict | Zero violations |
| **Code Coverage** | ≥85% | pytest-cov report |
| **Performance** | <5s per workflow | Timing verified |
| **No Overfitting** | Adversarial tests | CLI error handling |

---

## Rollback Plan

If any component fails GATE 5:
1. Revert to Phase 6.1 baseline (all 4 components still working)
2. Move failing tests to `tests/deferred/`
3. Create ADR explaining deferral
4. Phase 6.2 ships with 1-2/2 components
5. Phase 6.3 completes remaining work

---

## Definition of Done

✅ PLANNER: Spec complete (this document)  
⏳ ARCHITECT: Design complete (next phase)  
⏳ TEST-DESIGNER: Test specs (next phase)  
⏳ BUILDER: Implementation (next phase)  
⏳ GATE 5: Verification (all tests pass, metrics met)  
⏳ CODE REVIEW: Independent review  
⏳ MERGE: To main branch  

---

## Next Phase (6.3)

- Real LLM API integration for decision scoring
- Feedback loop (learn from user decisions)
- Advanced workflows (multi-intent planning)
- Team collaboration features

