# Phase 2: Selective Adoption Strategy

**Date:** 2026-07-01  
**Purpose:** Design component-by-component adoption (only if benchmarks prove GitNexus is valuable)  
**Constraint:** Every decision driven by Phase 1 benchmark results  
**Status:** Roadmap design (decisions deferred until Phase 1 complete)

---

## Overview

Phase 2 only executes if Phase 1 benchmarks show GitNexus superiority in specific areas.

**Key principle:** No component replacement without benchmark evidence.

---

## Decision Framework

For each Ortho component that has a GitNexus equivalent, make decision:

| Decision | Criteria | Process |
|----------|----------|---------|
| **REPLACE** | GitNexus proves >15% faster OR >5% more accurate | Retire Ortho code, adopt GitNexus |
| **WRAP** | GitNexus proves marginally better (5-15% faster) | Keep Ortho interface, use GitNexus backend |
| **KEEP** | Ortho similar or better performance/accuracy | Maintain current implementation |
| **LEARN** | GitNexus architecture is superior but implementation not ready | Adopt GitNexus patterns, reimplement in Ortho |

**Evidence standard:** 10+ test cases, >5 repositories, statistical significance (not margin-of-error variance)

---

## Per-Component Adoption Templates

For each component with a potential GitNexus replacement:

### Template: [Component Name]

**Current Ortho Implementation:**
- [What it does]
- [Performance baseline from Phase 1]
- [Known limitations]
- [Customer impact if changed]

**GitNexus Alternative:**
- [What it offers]
- [Benchmark results: accuracy/speed/completeness]
- [Advantages vs Ortho]
- [Disadvantages vs Ortho]

**Decision:** REPLACE / WRAP / KEEP / LEARN

**If REPLACE:**
```
Why?
  [Benchmark evidence: e.g., "GitNexus 2x faster with 99.9% accuracy vs Ortho 95%"]

Tradeoffs?
  [What do we lose? e.g., "CustomPythonPatterns no longer supported"]
  [What do we gain? e.g., "Multi-language support, TypeScript/Go"]

Migration Complexity?
  [Effort to integrate: e.g., "8 hours, 100 tests affected"]
  [Code changes required: e.g., "Interface change in SymbolExtractor"]
  [Risks: e.g., "Data format incompatibility on edge cases"]

Rollback Strategy?
  [How to revert if issues discovered]
  [Feature flag to switch between implementations?]
  [Keep Ortho code in git history?]

Maintenance Cost?
  [Who owns GitNexus dependency? (Ortho team? external?)]
  [How to handle version upgrades?]
  [Break-glass procedures?]

Long-Term Ownership?
  [Ortho owns RepositoryAnalysisProvider interface]
  [GitNexus owns symbol extraction implementation]
  [Adapter layer owned by Ortho]

Timeline?
  [When to cut over? (immediately? phased?)]
  [Deprecation period for old code? (keep 3 months for rollback?)]
```

**If WRAP:**
```
Why?
  [GitNexus marginally better but interface stability critical]

Interface?
  [SymbolExtractorProvider (interface)]
  [OrthoSymbolExtractor (old impl)]
  [GitNexusSymbolExtractor (new impl)]
  [Factory method to select]

Feature Flags?
  [How to A/B test? (config, runtime, per-project?)]
  [Metrics to track: (accuracy, latency, memory?)]
  [Rollback trigger? (error rate >X%?)]

Testing?
  [Run both implementations on same inputs?]
  [Compare results (should be identical)]
  [Gradual rollout? (1% → 10% → 50% → 100%?)]
```

**If KEEP:**
```
Why?
  [Ortho performs similarly or better]

Any Learning?
  [Architecture patterns to adopt?]
  [Edge cases to handle?]
  [Performance optimizations?]

Maintenance?
  [Continue current approach]
```

**If LEARN:**
```
Why?
  [GitNexus architecture superior but not ready to replace]

What to Adopt?
  [Design pattern, algorithm, data structure?]

How to Implement?
  [Reimplement in Ortho using GitNexus inspiration?]
  [Timeline for improvement?]
```

---

## Component Adoption Decisions (Template-filled)

**Note:** All decisions deferred until Phase 1 benchmarks complete. Below are placeholders showing decision format.

---

### 1. PythonAdapter

**Current Ortho Implementation:**
- Parses Python files using tree-sitter
- Extracts functions, classes, methods
- Performance baseline: ~100ms per file
- Known limitation: Decorators handled via AST walk (edge cases possible)

**GitNexus Alternative:**
- Native Python parsing + tree-sitter fallback
- Higher decorator handling confidence
- Performance: unknown (pending Phase 1 Benchmark A & B)
- Advantages: multiple language support path
- Disadvantages: external dependency, version management

**Decision:** TBD (pending Benchmark A: AST Quality, Benchmark B: Symbol Extraction)

---

### 2. SymbolExtractor

**Current Ortho Implementation:**
- Extracts symbols from AST
- Returns: name, qualified_name, type, location, docstring
- Performance baseline: <5ms per 100 symbols
- Known limitation: Type inference not performed

**GitNexus Alternative:**
- Comprehensive symbol extraction
- Returns: name, qualified_name, type, location, docstring, decorators, annotations
- Performance: unknown
- Advantages: richer metadata
- Disadvantages: different data model

**Decision:** TBD (pending Benchmark B: Symbol Extraction Accuracy)

---

### 3. ImportGraphBuilder

**Current Ortho Implementation:**
- Traces imports (from/import statements)
- Detects circular imports
- Handles relative imports
- Performance: ~2ms per file
- Known limitation: Star imports not resolved to targets

**GitNexus Alternative:**
- Comprehensive import resolution
- Returns: source, target, type, location, edge confidence
- Handles star import expansion
- Performance: unknown
- Advantages: complete import graph
- Disadvantages: requires more processing

**Decision:** TBD (pending Benchmark C: Import Resolution Accuracy)

---

### 4. CallGraphBuilder

**Current Ortho Implementation:**
- Builds call graph via AST traversal
- Returns: caller, callee, location, confidence (0.8 for direct calls)
- Performance: ~5ms per file
- Known limitation: Confidence <0.9 for decorators, method dispatch

**GitNexus Alternative:**
- Native call graph generation
- Returns: caller, callee, location, confidence (0.9+)
- Better decorator/OOP handling
- Performance: unknown
- Advantages: higher accuracy
- Disadvantages: confidence model may differ

**Decision:** TBD (pending Benchmark D: Call Graph Accuracy)

---

### 5. DependencyGraphBuilder

**Current Ortho Implementation:**
- Parses requirements.txt, pyproject.toml
- Extracts: package, version_range, source
- Performance: <1ms per file
- Known limitation: Only Python manifest formats

**GitNexus Alternative:**
- Parses multiple manifest formats (requirements.txt, pyproject.toml, setup.py, package.json, go.mod, Cargo.toml, etc.)
- Returns: package, version, transitive info, security advisories
- Performance: unknown
- Advantages: multi-language support
- Disadvantages: more complex API

**Decision:** TBD (pending Benchmark E: Dependency Parsing)

---

### 6. ModuleDetector

**Current Ortho Implementation:**
- Detects Python packages (regular, namespace)
- Handles PEP 420 namespace packages
- Performance: <1ms per directory
- Known limitation: Regex-based heuristics

**GitNexus Alternative:**
- Language-native module detection
- More reliable than heuristics
- Performance: unknown
- Advantages: higher accuracy
- Disadvantages: harder to customize

**Decision:** TBD (pending Benchmark C: Import Resolution, Benchmark J: Repository Coverage)

---

### 7. IncrementalIndexer

**Current Ortho Implementation:**
- Uses git diff to identify changed files
- Re-analyzes only changed files
- Performance: ~100ms per file update
- Known limitation: Invalidates dependent items (conservative)

**GitNexus Alternative:**
- Git-aware incremental indexing
- Smarter invalidation (?) 
- Performance: unknown
- Advantages: potentially faster
- Disadvantages: different invalidation semantics

**Decision:** TBD (pending Benchmark F: Incremental Indexing Speed)

---

### 8. Search (BM25)

**Current Ortho Implementation:**
- FTS5-based full-text search
- Used for artifact search (not code search)
- Performance: <100ms per query
- Known limitation: Artifac-focused, not code-focused

**GitNexus Alternative:**
- Unknown if GitNexus implements search
- May be incomparable (different purpose)
- Advantages: unknown
- Disadvantages: unknown

**Decision:** TBD (Phase 1 architecture review determines if comparable)

---

### 9. ContextHub (Artifact Storage)

**Ortho Implementation:**
- Stores engineering artifacts (FRD, ADR, specs, docs, evidence)
- Versions artifacts, detects staleness
- Unique to Ortho

**GitNexus:**
- Not applicable (code-focused, not artifact-focused)

**Decision:** KEEP (no GitNexus equivalent)

---

### 10. ArchitectureDetector

**Ortho Implementation:**
- Detects architecture styles (layered, hexagonal, MVC, microservices, flat)
- Extracts layers, subsystems
- Generates confidence scores
- Unique to Ortho

**GitNexus:**
- Not applicable (no architecture detection)

**Decision:** KEEP (no GitNexus equivalent)

---

## Phase 2 Execution Plan

### Week 1: Benchmark Execution
- [ ] Run all Phase 1 benchmarks (A through J)
- [ ] Collect results in benchmark report
- [ ] Identify which components performed better

### Week 2: Decision-Making
For each component with benchmark results:
- [ ] Apply decision framework (REPLACE / WRAP / KEEP / LEARN)
- [ ] Document reasoning and evidence
- [ ] Identify risks, tradeoffs, migration costs
- [ ] Get team consensus

### Week 3-4: Adoption Planning
For each REPLACE or WRAP decision:
- [ ] Design migration (code changes, interface changes)
- [ ] Plan testing (how to verify old & new work identically)
- [ ] Plan rollback (feature flags, fallback paths)
- [ ] Estimate effort (hours, people, risk)

### Week 5: Final Decision Document
- [ ] Component Adoption Strategy (all decisions documented)
- [ ] Risk register (what could go wrong)
- [ ] Timeline (when to cut over)
- [ ] Team approval

---

## Possible Outcomes

### Outcome A: GitNexus Clearly Superior
**Benchmarks show GitNexus >20% faster on multiple components**

Decisions: Multiple REPLACE decisions
Example: PythonAdapter, CallGraphBuilder, DependencyGraphBuilder all REPLACE

Next step: Phase 3 (Production Integration)

---

### Outcome B: GitNexus Marginally Better
**Benchmarks show GitNexus 5-15% faster, slightly more accurate**

Decisions: Multiple WRAP decisions
Example: PythonAdapter = WRAP, CallGraphBuilder = WRAP, DependencyGraphBuilder = KEEP

Next step: Phase 3 (Production Integration with dual implementations)

---

### Outcome C: GitNexus Has Tradeoffs
**Benchmarks show GitNexus better at X, Ortho better at Y**

Decisions: Mix of WRAP, KEEP, LEARN
Example: CallGraphBuilder = WRAP (better accuracy), IncrementalIndexer = KEEP (both similar)

Next step: Phase 3 (Hybrid integration)

---

### Outcome D: No Clear Winner
**Benchmarks show both systems similar performance**

Decisions: All KEEP or LEARN
Example: All components KEEP except adoption of GitNexus architectural patterns

Next step: No integration, maintain Ortho independently

---

### Outcome E: GitNexus Has Issues
**Benchmarks reveal memory problems, accuracy issues, or scalability limits**

Decisions: All KEEP
Example: GitNexus performance degrades on 100k file repos

Next step: Do Not Integrate (use GitNexus as reference only)

---

## Decision Gate

Phase 2 → Phase 3 decision point:

**GO to Phase 3 if:**
- At least 1 component shows clear GitNexus advantage (>10% improvement)
- Integration complexity is acceptable (<40 hours per component)
- No legal/licensing blockers identified

**STOP if:**
- GitNexus benchmarks reveal fundamental incompatibilities
- Legal/licensing issues identified (RED risk)
- Integration too complex (>100 hours for marginal gains)

---

## Principles

✅ No adoption without benchmark evidence  
✅ Every decision justified by Phase 1 results  
✅ Preserve Ortho's unique features (ContextHub, architecture detection, ASES)  
✅ Make all replacements swappable (WRAP pattern preferable to REPLACE)  
✅ Plan fallback for every adoption (rollback strategy mandatory)

