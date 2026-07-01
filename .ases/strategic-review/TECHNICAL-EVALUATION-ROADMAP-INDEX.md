# Technical Evaluation Roadmap: GitNexus Integration

**Date:** 2026-07-01  
**Purpose:** Evidence-based decision roadmap (not implementation)  
**Status:** Roadmap designed. Ready for Phase 1 execution.

---

## Overview

This roadmap reverses the previous overly-optimistic proposal. Instead of assuming GitNexus should replace Ortho's repository intelligence, we design a rigorous evaluation to prove (or disprove) any adoption.

**Key principle:** No component replacement without measurable evidence.

---

## Three Phases

### Phase 1: Technical Evaluation
**Purpose:** Gather objective evidence  
**Duration:** ~4 weeks  
**Deliverables:** 5 documents

1. **License Review** — Legal/commercial compatibility
2. **SDK Evaluation Report** — API stability & usage model
3. **Architecture Deep Dive** — Reverse-engineer GitNexus design
4. **Component Decision Matrix** — Classify every Ortho component
5. **Benchmark Specification** — Design 10 benchmarks (don't run yet)

**Gate:** Can we legally use GitNexus? Is it stable? Do we have measurable criteria for adoption?

---

### Phase 2: Selective Adoption
**Purpose:** Make per-component adoption decisions  
**Duration:** ~3 weeks (only if Phase 1 GO)  
**Deliverables:** 1 document + implementation planning

1. **Component Adoption Strategy** — REPLACE / WRAP / KEEP / LEARN for every component
2. Benchmark execution (from Phase 1 spec)
3. Adoption timelines & migration plans

**Gate:** Which components should actually change? Why?

---

### Phase 3: Production Integration
**Purpose:** Design safest possible integration  
**Duration:** Roadmap only (only if Phase 2 GO)  
**Deliverables:** 1 document

1. **Production Integration Architecture** — Adapter pattern, feature flags, rollback

**Gate:** How do we deploy without breaking anything?

---

## Phase 1 Roadmap: Technical Evaluation

### 1. Licensing Investigation

**Objective:** Determine legal/commercial compatibility (no assumptions)

**Method:**
- Read LICENSE file verbatim
- Check transitive dependencies
- Test 4 commercial scenarios (SaaS API, embedded SDK, forking, attribution)
- Consult GitNexus maintainers if unclear

**Deliverable:** License Review
- License type (verbatim)
- Restrictions identified
- Commercial scenario assessment (GREEN/YELLOW/RED)
- Risk level for each use case

**Success:** "Can we legally use GitNexus?" answered definitively.

---

### 2. API & SDK Evaluation

**Objective:** Prove how GitNexus is intended to be used

**Method:**
- Read README (what examples are shown?)
- Find main entry points
- Identify public vs internal APIs
- Check version compatibility strategy
- Assess stability signals

**Deliverable:** SDK Evaluation Report
- Primary usage model (CLI / SDK / MCP / library)
- API surface (public + internal)
- Extension capability
- Version compatibility
- Stability assessment (mature / pre-release)
- Integration risk (LOW / MEDIUM / HIGH)

**Success:** "Is GitNexus safe to depend on?" answered definitively.

---

### 3. Architecture Reverse-Engineering

**Objective:** Understand GitNexus design (not features)

**Method:**
- Read source code (not just docs)
- Identify responsibilities (parser, symbol table, graph, storage, search, retrieval)
- Map data models
- Document design patterns
- Compare against Ortho's architecture

**Deliverable:** Architecture Deep Dive
- Layer diagram
- Data flow (parser → storage → retrieval)
- Responsibility matrix (Ortho vs GitNexus)
- Design patterns
- Extension points
- Assessment: can they coexist?

**Success:** "How is GitNexus designed? Does it conflict with Ortho?" answered.

---

### 4. Component Mapping Matrix

**Objective:** Classify every Ortho component

**Method:**
- Inventory all Ortho components
- For each, determine: does GitNexus have an equivalent?
- Classify: KEEP / REPLACE / WRAP / LEARN / IGNORE
- Document reasoning for each classification

**Deliverable:** Component Decision Matrix
- Every Ortho component classified
- Classification rationale
- Evidence needed (which benchmark justifies this decision?)
- Risk assessment
- Ownership after decision

**Components:**
- PythonAdapter (TBD: depends on Benchmark A, B)
- SymbolExtractor (TBD: depends on Benchmark B)
- ImportGraphBuilder (TBD: depends on Benchmark C)
- CallGraphBuilder (TBD: depends on Benchmark D)
- DependencyGraphBuilder (TBD: depends on Benchmark E)
- ModuleDetector (TBD: depends on Benchmark C, J)
- IncrementalIndexer (TBD: depends on Benchmark F)
- ContextHub (KEEP: no GitNexus equivalent)
- ArchitectureDetector (KEEP: no GitNexus equivalent)
- Search: BM25, semantic, RRF (KEEP or LEARN: different purpose)
- ProjectMemory (KEEP: no GitNexus equivalent)
- ASES (KEEP: no GitNexus equivalent)

**Success:** "What should change and why?" definitively answered for every component.

---

### 5. Benchmark Specification

**Objective:** Design tests (don't run) that prove whether GitNexus is better

**Method:**
- Design 10 benchmarks (A-J)
- For each: hypothesis, procedure, metrics, success criteria
- Use real repositories (FastAPI, LangChain, OpenClaude, Dapr)
- Define what counts as "better" (e.g., >10% faster, >99% accurate)

**Deliverable:** Benchmark Specification
- 10 benchmarks fully designed
- Test procedures (step-by-step, reproducible)
- Success criteria for each
- Real test repositories identified
- Tools for measurement

**Benchmarks:**
- A: AST Quality (parse accuracy)
- B: Symbol Extraction (recall, precision)
- C: Import Resolution (accuracy on edge cases)
- D: Call Graph Accuracy (recall, precision, confidence)
- E: Dependency Parsing (format support, version accuracy)
- F: Incremental Indexing (speed, correctness)
- G: Large Repository Handling (scalability)
- H: Memory Footprint (growth rate)
- I: Confidence Score Calibration (reliability)
- J: Repository Coverage (% of files analyzed)

**Success:** "How will we objectively measure if GitNexus is better?" definitively answered.

---

### Phase 1 Timeline

| Week | Task | Output | Gate |
|------|------|--------|------|
| 1 | License + SDK | License Review, SDK Eval Report | Legal risk acceptable? |
| 2 | Architecture | Architecture Deep Dive | Conflict identified? |
| 2-3 | Mapping | Component Matrix | Every component classified? |
| 3 | Benchmarks | Benchmark Spec | Tests designed? |

---

### Phase 1 Success Criteria

**GO to Phase 2 if:**
- [ ] License compatible (GREEN or YELLOW, no RED)
- [ ] API stable (version >=1.0, well-documented)
- [ ] No architectural conflicts identified
- [ ] All components classified (KEEP or TBD pending benchmarks)
- [ ] All 10 benchmarks designed

**STOP if:**
- ❌ License incompatible (RED risk)
- ❌ API unstable (0.x, undocumented, frequently breaking)
- ❌ Fundamental architectural conflict

---

## Phase 2 Roadmap: Selective Adoption

**Only executes if Phase 1 SUCCESS.**

### Decision Framework

For each component with a GitNexus equivalent:

| Evidence | Decision |
|----------|----------|
| GitNexus >15% faster OR >5% more accurate | REPLACE |
| GitNexus 5-15% faster, more accurate | WRAP |
| Similar performance | KEEP |
| GitNexus architecture superior, not ready | LEARN |

**Standard:** 10+ test cases, 5+ real repositories, statistically significant (not margin-of-error)

### Adoption Strategy (Template)

For each decision:
```
Component: [Name]
Classification: REPLACE / WRAP / KEEP / LEARN

Reasoning: [What evidence supports this?]
Tradeoffs: [What do we gain/lose?]
Effort: [Hours to integrate?]
Risk: [What could go wrong?]
Rollback: [How to revert if issues?]
Owner: [Who maintains post-integration?]
Timeline: [When to cut over?]
```

### Phase 2 Timeline

| Week | Task | Output | Gate |
|------|------|--------|------|
| 1 | Benchmarks | Benchmark Results | Clear winner identified? |
| 2 | Decisions | Component Adoption Strategy | Team consensus? |
| 3 | Planning | Migration timelines | Ready to code? |

---

## Phase 3 Roadmap: Production Integration

**Only executes if Phase 2 GO.**

### Core Architecture

```
RepositoryAnalysisProvider (interface)
├── OrthoRepositoryAnalysisProvider
├── GitNexusRepositoryAnalysisProvider
└── HybridRepositoryAnalysisProvider

ContextHub → provider (interface, not implementation)
ArchitectureDetector → provider
IncrementalIndexer → provider
```

**Key principle:** Everything goes through interface. GitNexus never hardcoded.

### Key Components

1. **Adapter Architecture**
   - RepositoryAnalysisProvider interface
   - OrthoProvider (wraps existing code)
   - GitNexusProvider (wraps GitNexus)
   - Hybrid provider (both, with fallback)

2. **Configuration & Selection**
   - config.toml: `provider = "gitnexus"`
   - Environment variables
   - Feature flags (A/B testing)

3. **Fallback & Rollback**
   - Automatic failover to Ortho on error
   - Zero-downtime provider switch (config change)
   - Both providers read same data (no re-indexing needed)

4. **Versioning**
   - GitNexus pinned: `>=1.5,<2.0`
   - Adapter insulates major version changes
   - Deprecation window for old versions

5. **Telemetry & Observability**
   - Track provider in use
   - Monitor error rates, latency, memory
   - Alert on anomalies
   - Dashboard for both providers

6. **Testing**
   - Unit tests for each provider
   - Integration tests (ContextHub, ArchDetector)
   - A/B tests (both providers, compare results)
   - Regression tests (all Phase 1 tests pass)

---

## Document Map

```
.ases/strategic-review/

Phase 1 (Technical Evaluation):
├── PHASE-1-TECHNICAL-EVALUATION-STRATEGY.md (this roadmap)
│   ├── 1. Licensing Investigation
│   ├── 2. API & SDK Evaluation
│   ├── 3. Architecture Reverse-Engineering
│   ├── 4. Component Mapping Matrix
│   └── 5. Benchmark Specification

Phase 2 (Selective Adoption):
├── PHASE-2-SELECTIVE-ADOPTION-STRATEGY.md
│   ├── Decision Framework
│   ├── Per-Component Templates
│   ├── Possible Outcomes (A-E)
│   └── Decision Gate

Phase 3 (Production Integration):
├── PHASE-3-PRODUCTION-INTEGRATION-ARCHITECTURE.md
│   ├── Core Architecture (adapter pattern)
│   ├── Interface Definitions
│   ├── Configuration & Selection
│   ├── Fallback & Rollback
│   ├── Versioning
│   ├── Telemetry
│   ├── Testing
│   └── Migration Path

Index:
└── TECHNICAL-EVALUATION-ROADMAP-INDEX.md (this file)
```

---

## Execution Model

### Who

- **Phase 1:** Architecture team (4 people, ~60 hours)
  - Tech lead: licensing, architecture
  - Developers (2): reverse-engineering, benchmarks
  - QA: test specification

- **Phase 2:** Same team (4 people, ~40 hours)
  - Benchmark execution
  - Decision-making
  - Planning

- **Phase 3:** Dev team (6 people, variable hours depending on Phase 2 decisions)
  - Adapter implementation
  - Integration
  - Testing
  - Rollout

### When

- **Phase 1:** Weeks 1-4 (parallel work, some blocking)
- **Phase 2:** Weeks 5-7 (only if Phase 1 SUCCESS)
- **Phase 3:** Weeks 8+ (only if Phase 2 GO)

### How Much

- **Phase 1:** ~60 hours (no code written, pure analysis)
- **Phase 2:** ~40 hours (benchmarks, decisions, planning)
- **Phase 3:** 40-200 hours (depends on Phase 2 decisions)

---

## Possible Outcomes

### Outcome A: GitNexus Clearly Superior

**If benchmarks show GitNexus >20% faster, more accurate:**

- Multiple REPLACE decisions (PythonAdapter, CallGraphBuilder, DependencyGraphBuilder)
- Phase 3: Full integration, deprecate Ortho implementations (after 3 months)
- Impact: Multi-language support, 2x speed improvement, reduced maintenance

---

### Outcome B: GitNexus Marginal Improvement

**If benchmarks show 5-15% gains:**

- Multiple WRAP decisions (keep Ortho interface, use GitNexus backend)
- Phase 3: Dual implementations, gradual migration
- Impact: Incremental improvement, risk-managed integration

---

### Outcome C: Mixed Results

**If GitNexus better at X, Ortho better at Y:**

- Mix of WRAP, KEEP, LEARN decisions
- Phase 3: Selective integration, keep strong Ortho components
- Impact: Surgical improvements, minimal risk

---

### Outcome D: No Clear Winner

**If benchmarks show similar performance:**

- All KEEP or LEARN decisions
- Phase 3: Don't integrate, adopt architectural patterns only
- Impact: No implementation, design insights only

---

### Outcome E: GitNexus Has Issues

**If benchmarks reveal memory problems, accuracy issues, or scalability limits:**

- All KEEP decisions
- Phase 3: Do Not Integrate
- Use GitNexus as reference for architectural patterns only

---

## Decision Gates

### Gate 1: Phase 1 Completion → Phase 2 Go/No-Go

**GO to Phase 2 if:**
- License compatible
- API stable
- No architectural blockers
- All components classified

**STOP if:**
- License incompatible
- API unstable
- Fundamental conflicts

---

### Gate 2: Phase 2 Completion → Phase 3 Go/No-Go

**GO to Phase 3 if:**
- Benchmarks show GitNexus advantage (any outcome A-C)
- Integration complexity acceptable
- Team consensus on adoption

**STOP if:**
- Benchmarks show no advantage (Outcome D)
- GitNexus has issues (Outcome E)
- Risk too high relative to benefit

---

## Success Criteria

✅ **Phase 1:** All 5 documents completed, evidence gathered, GO/NO-GO decision made  
✅ **Phase 2:** Benchmarks run, adoption decisions made, timeline planned  
✅ **Phase 3:** Adapter architecture designed, migration path clear, rollback procedure documented

---

## Key Principles

1. **No assumptions without evidence**
   - Read license file, don't assume MIT
   - Run benchmarks, don't guess faster
   - Compare architectures, don't assume better

2. **Every recommendation driven by data**
   - Component decisions justified by benchmarks
   - Adoption timelines based on effort estimates
   - Risk mitigations based on identified threats

3. **Preserve Ortho's unique value**
   - ContextHub, ArchitectureDetector, ASES never replaced
   - Repository Intelligence becomes pluggable
   - Ortho remains Engineering Intelligence platform

4. **Design for long-term evolution**
   - Adapter pattern allows future provider swaps
   - Vendore independence maintained
   - Fallback strategy always available

5. **Risk-managed integration**
   - Both providers runnable in parallel
   - Feature flags for gradual rollout
   - Rollback in <2 minutes if needed

---

## Next Step

**Start Phase 1: Technical Evaluation**

Week 1 tasks:
1. [ ] License Review (read LICENSE file, assess risks)
2. [ ] SDK Evaluation (understand API, stability)
3. [ ] Schedule architecture deep-dive session

All evidence gathering. No implementation decisions yet.

---

*Roadmap designed by LEAD SYSTEM ARCHITECT*  
*Evidence-based, not assumption-based*  
*Ready for team review and Phase 1 execution*

