# Phase 6.2: Decision Engine & CLI Integration — ARCHITECT Phase

**Project:** Ortho v3 — AI Engineering Platform  
**Phase:** Phase 6.2 (Decision Engine & CLI)  
**Date:** 2026-07-13  
**Methodology:** ASES v1.2 — Architecture & ADR Design  

---

## 1. Architecture Overview

Phase 6.2 orchestrates Phase 6.1's 4 components into a unified decision system with CLI interface.

```
User CLI Input (ortho plan/refactor/guardrails/decide)
    ↓
CLI Commands Parser
    ↓
┌─────────────────────────────────────────────────────┐
│        DECISION ENGINE (NEW)                        │
│  Orchestrates 4 recommendation sources              │
├─────────────────────────────────────────────────────┤
│ ├─ Change Planner (impact prediction)              │
│ ├─ Feature Planner (implementation paths)          │
│ ├─ Refactoring Advisor (issue detection)           │
│ └─ Arch Guardrails (violation enforcement)         │
└─────────────────────────────────────────────────────┘
    ↓
Report Formatter (pretty-print)
    ↓
User Output (CLI Report)
```

---

## 2. Component Design

### 2.1 Decision Engine

**Purpose:** Aggregate recommendations from multiple sources, rank by confidence + fit, return best options.

**Algorithm:**
```
1. Collect recommendations from all 4 sources
2. Normalize confidence scores (0.0-1.0)
3. Deduplicate similar recommendations (Jaccard > 0.8)
4. Rank by: confidence × fit_score
5. Return top 3+ options with reasoning
```

**Key Classes:**

```python
class DecisionEngine:
    def decide(
        self,
        intent: str,
        change_predictions: list[ImpactPrediction],
        feature_paths: list[ImplementationPath],
        refactoring_issues: list[RefactoringIssue],
        guardrail_violations: list[GuardrailViolation],
    ) -> Decision:
        """Make multi-source decision"""
        options = self._collect_options(
            change_predictions,
            feature_paths,
            refactoring_issues,
            guardrail_violations,
        )
        deduped = self._deduplicate(options)
        ranked = self._rank_options(deduped, intent)
        return Decision(
            intent=intent,
            options=ranked[:5],  # Top 5
            recommended_option=ranked[0],
            reasoning=self._generate_reasoning(ranked),
            confidence=ranked[0].confidence,
        )
```

**Deduplication:**
- Similarity metric: Jaccard on recommendation titles
- Merge if similarity > 0.8 (keep higher confidence)

**Ranking:**
```
score = (confidence * 0.7) + (fit_to_intent * 0.3)
  where fit_to_intent = semantic_similarity(intent, recommendation.description)
```

---

### 2.2 CLI Commands

**Purpose:** User-facing interface for all Phase 6.1 + 6.2 capabilities.

**Commands:**

```bash
# Feature planning
ortho plan "add user search endpoint"
ortho plan "implement microservice"

# Refactoring recommendations
ortho refactor src/service.py
ortho refactor --all

# Architecture compliance
ortho guardrails check
ortho guardrails check --strict

# Multi-source decision
ortho decide "improve code quality"
ortho decide "implement new feature"
```

**Options:**
- `-v, --verbose` — Detailed output with evidence
- `-q, --quiet` — Minimal output
- `--json` — JSON format (machine-readable)
- `--format` — Output format (text, json, csv)
- `--confidence` — Filter by min confidence (0.0-1.0)

**Implementation:**

```python
class CliCommands:
    def plan(self, intent: str, verbose: bool = False) -> str:
        """Execute feature planning workflow"""
        paths = feature_planner.plan_feature(intent)
        report = self._format_plan_report(paths, verbose)
        return report
    
    def refactor(self, path: str, all: bool = False) -> str:
        """Execute refactoring workflow"""
        issues = refactoring_advisor.find_issues(path if path else None)
        report = self._format_refactor_report(issues, all)
        return report
    
    def guardrails(self, path: str = None, strict: bool = False) -> str:
        """Execute guardrails check"""
        violations = arch_guardrails.check_violations(path)
        if strict:
            violations = [v for v in violations if v.severity == "error"]
        report = self._format_guardrails_report(violations)
        return report
    
    def decide(self, intent: str) -> str:
        """Execute multi-source decision"""
        decision = decision_engine.decide(intent)
        report = self._format_decision_report(decision)
        return report
```

---

### 2.3 Report Formatter

**Purpose:** Pretty-print recommendations for CLI output.

**Features:**
- Colored output (success=green, warning=yellow, error=red)
- Evidence indentation (hierarchy)
- Confidence badges (█████░░░░░ 50%)
- Effort/risk labels (L/M/H)
- Actionable summary

**Example Output:**

```
═══════════════════════════════════════════════════════════════
REFACTORING RECOMMENDATIONS (3 issues found)
═══════════════════════════════════════════════════════════════

[HIGH] Tight Coupling: auth.py ↔ payment.py
   Confidence: ███████░░░░ 85%
   → Extract shared interface to break bidirectional dependency
   Effort: 4-8 hours | Risk: Low
   Evidence:
     • auth.py imports payment.py (3 locations)
     • payment.py imports auth.py (2 locations)

[MEDIUM] Module Bloat: service.py (650 lines, 42 functions)
   Confidence: ██████████ 100%
   → Split into focused modules (auth, validation, business logic)
   Effort: 1-2 days | Risk: Medium
   Evidence:
     • Exceeds line threshold (500 limit)
     • High cohesion indicates split points

Summary: Prioritize tight coupling fix (highest impact/effort ratio)
```

---

## 3. ADRs

### ADR-021: Decision Engine Aggregation Strategy

**Status:** Proposed  
**Decision:** Combine recommendations from all 4 sources; deduplicate by semantic similarity.

**Rationale:**
- Each source has unique insights (change impact, patterns, debt, compliance)
- Combining provides comprehensive view
- Deduplication avoids redundant recommendations

**Consequences:**
- ✅ Holistic recommendations
- ✅ Avoids information overload
- ⚠️ Deduplication heuristic may merge different fixes

---

### ADR-022: CLI as Primary UX

**Status:** Proposed  
**Decision:** CLI commands are main user interface (not API, not web UI).

**Rationale:**
- Fits Ortho's local-first philosophy
- Integrates with standard DevOps workflows
- No web server/API complexity

**Consequences:**
- ✅ Simple deployment
- ✅ Works in CI/CD pipelines
- ⚠️ Batch operations only (no real-time feedback)

---

### ADR-023: Multi-Source Ranking

**Status:** Proposed  
**Decision:** Rank options by `confidence × fit_to_intent` (70%/30% weight).

**Rationale:**
- Confidence reflects data quality
- Fit ensures relevance to user intent
- 70/30 balance avoids both extremes

**Alternatives Considered:**
1. Confidence only (misses intent fit)
2. Fit only (ignores evidence quality)
3. Equal weight (treats all factors equally)

---

### ADR-024: Graceful Degradation

**Status:** Proposed  
**Decision:** If a source fails, continue with others (don't crash).

**Rationale:**
- Robust service (one source failure ≠ complete failure)
- Useful even with partial data

**Consequences:**
- ✅ Resilient
- ⚠️ May miss insights from failed source

---

### ADR-025: Evidence Traceability

**Status:** Proposed  
**Decision:** All recommendations link back to source component + evidence.

**Rationale:**
- Users can verify reasoning
- Builds trust

**Consequences:**
- ✅ Transparent
- ✅ Debuggable
- ⚠️ Verbose output if not summarized

---

## 4. Integration Points

### With Phase 6.1 Components

```python
# Decision Engine receives these inputs
engine.decide(
    intent="add user search",
    change_predictions=change_planner.predict_impact(file),
    feature_paths=feature_planner.plan_feature(intent),
    refactoring_issues=refactoring_advisor.find_issues(),
    guardrail_violations=arch_guardrails.check_violations(),
)
```

### With CLI

```bash
ortho plan "add user search"
  → Calls feature_planner.plan_feature()
  → Formats via ReportFormatter
  → Returns CliReport

ortho decide "implement feature"
  → Calls all 4 Phase 6.1 components
  → Passes to decision_engine.decide()
  → Formats via ReportFormatter
  → Returns CliReport
```

---

## 5. Performance Targets

| Operation | Target |
|-----------|--------|
| CLI parse + execute | <2s |
| Plan (single feature) | <1s |
| Refactor (full scan) | <5s |
| Guardrails check | <2s |
| Decide (all sources) | <5s |

---

## 6. No Overfitting Tests

### CLI Error Handling
- Bad intent (empty, malformed)
- Missing context (no codebase scanned)
- Invalid file paths
- Conflicting source recommendations

### Decision Engine Edge Cases
- All sources low confidence (<0.6)
- No recommendations from any source
- Identical recommendations from multiple sources
- Contradictory sources (one says "do A", another "don't do A")

---

## 7. Definition of Done (GATE 2)

✅ All 3 component designs complete (Decision Engine, CLI, Formatter)  
✅ Data models defined (Decision, Recommendation, CliReport)  
✅ 5 ADRs documented (aggregation, CLI UX, ranking, degradation, traceability)  
✅ Integration points specified  
✅ Performance targets set  
✅ No external dependencies (reuse Phase 6.1 + stdlib)  

---

## 8. Next Phase (BUILDER)

Implement all 3 components:
- BUILDER 1: decision-engine (20 hard tests)
- BUILDER 2: cli-commands (20 integration tests)
- BUILDER 3: Integration tests (5 workflows)

With parallel TEST-DESIGNER building comprehensive test suite.

