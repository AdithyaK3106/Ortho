# Task: Architecture Intelligence Recovery (Phase 5)

**Task ID:** ortho-phase5-arch-intelligence  
**Methodology:** ASES v1.2  
**Priority:** HIGH (core product accuracy)  
**Scope:** Recover architecture detection from 0% accuracy to generalizable intelligence  
**Date Created:** 2026-07-13

## Problem Statement

**Current State:**
- Architecture detector executes without errors
- Produces predictions on all 8 repositories
- **Accuracy on ground truth: 0%** (Click and Flask both classified as "unknown")
- Confidence scores: 0.40 across the board (low, honest)

**Mission:**
Diagnose root causes and rebuild architecture intelligence to correctly classify repositories while maintaining honest confidence scoring. Focus on **correctness and generalization**, not test count.

## Success Criteria

1. **Root-cause audit complete** with evidence for each hypothesis
2. **Ground truth expanded** to 8 repositories (manually validated, no synthetic labels)
3. **Architecture benchmark operational** measuring style, layer, subsystem accuracy
4. **Confidence calibration verified** (error < 0.15)
5. **Remaining tech debt documented** (mock tests, xfails, cleanup roadmap)
6. **Style accuracy ≥ 50%** on 8-repository corpus by Phase 5 end
7. **All 883 passing tests preserved** throughout

## Investigation Hypotheses

**Hypothesis A:** Evidence threshold (0.45) is too high → all repos hit "unknown"  
**Hypothesis B:** Directory-only vocabulary misses layer signals → Flask/Click lack explicit naming  
**Hypothesis C:** Missing graph features → fan-in/fan-out, coupling, entry points ignored  
**Hypothesis D:** Broken confidence calibration → 0.40 on everything is suspicious  
**Hypothesis E:** Framework detection missing → Flask/Click patterns not recognized  

## Deliverables

### 1. Architecture Audit Report
- Forensic trace of detector on Click & Flask
- Root cause evidence for each hypothesis
- Component-level diagnosis (scorer logic, vocabulary, graph analysis)
- Proposed redesign strategy

### 2. Ground Truth Expansion  
- Manual classification of 6 additional repositories
- Architecture style + layers + subsystems for each
- Visible signals documented (naming, imports, structure, coupling)

### 3. Architecture Benchmark
- Accuracy metrics (style, layer precision/recall, subsystem)
- Confusion matrices per repository
- Confidence calibration analysis
- Failure mode breakdown

### 4. Test Debt Report
- 50 remaining mock/inert tests classified (keep/rewrite/delete)
- 46 xfail markers audited (fixed/documented/removed)
- Cleanup priority order

### 5. Generalization Report
- 8-repository performance comparison
- Per-repository failure patterns
- Signals present but not detected
- Evidence of overfitting (if any)

### 6. Implementation Plan
- Ordered improvements (ROI-driven)
- Atomic commit structure
- Validation checkpoints

## Constraints

- ❌ Do NOT add features
- ❌ Do NOT rewrite working code  
- ❌ Do NOT hardcode repository names or answers
- ❌ Do NOT use synthetic ground truth
- ✅ Preserve all 883 passing tests
- ✅ Every change must generalize
- ✅ Honest confidence > optimistic wrong answer

## ASES Workflow

This task will be executed using strict ASES:

1. **PLANNER:** Architecture audit, hypothesis validation, root-cause documentation
2. **ARCHITECT:** Ground truth expansion, detector redesign, evidence integration strategy
3. **BUILDER:** Implement improvements incrementally, preserve passing tests
4. **TEST-DESIGNER:** Architecture benchmark suite, validation metrics
5. **VERIFIER:** Run 8-repo generalization, measure accuracy, calibration, confidence
6. **REVIEWER:** Ensure no hardcoding, validate ground truth, gate each commit
