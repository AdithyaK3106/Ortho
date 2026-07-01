# Phase 1: Technical Evaluation Strategy

**Date:** 2026-07-01  
**Purpose:** Design evaluation plan to answer: "Should GitNexus integrate with Ortho, and if so, where?"  
**Constraint:** No assumptions. Every recommendation driven by measurable data.  
**Status:** Roadmap design (not execution)

---

## 1. Licensing Investigation

### Objective
Determine legal/commercial compatibility with no assumptions.

### Investigation Plan

**1.1 License Artifact Review**
- [ ] Clone GitNexus repository
- [ ] Read LICENSE file (verbatim, not summary)
- [ ] Read COPYING file (if exists)
- [ ] Read any LEGAL/ directory
- [ ] Search code comments for license notices

**1.2 Restriction Inventory**
For discovered license, document:
- [ ] License type (MIT, Apache, GPL, proprietary, etc.)
- [ ] Restrictions (no warranty, attribution required, copyleft, etc.)
- [ ] Commercial use prohibition (yes/no, under what conditions?)
- [ ] Redistribution conditions (can we bundle it?)
- [ ] SaaS implications (can we run it server-side for customers?)
- [ ] Modification allowed (can we fork/patch?)
- [ ] Patent clauses (are we liable?)

**1.3 Transitive License Audit**
- [ ] Extract GitNexus pyproject.toml or setup.py
- [ ] List all direct dependencies
- [ ] For each dependency, determine its license
- [ ] Check if any dependency has restrictive license (GPL, AGPL)
- [ ] Document license tree

**1.4 Commercial Scenario Testing**
Create hypothetical scenarios and determine viability:

| Scenario | Question | Answer | Risk |
|----------|----------|--------|------|
| **SaaS API** | Can Ortho ship GitNexus as part of Ortho Cloud (proprietary API)? | ? | GREEN/YELLOW/RED |
| **Embedded SDK** | Can we distribute GitNexus with Ortho SDK to customers? | ? | GREEN/YELLOW/RED |
| **Dual License** | Can Ortho offer proprietary + open-source versions? | ? | GREEN/YELLOW/RED |
| **Forking** | Can we fork/modify GitNexus internally? | ? | GREEN/YELLOW/RED |
| **Attribution** | What attribution is required? | ? | GREEN/YELLOW/RED |

**1.5 Maintainer Consultation**
Questions for GitNexus maintainers (if licensing unclear):
- [ ] Is this license enforced or aspirational?
- [ ] Are there commercial licensing options?
- [ ] Have other companies embedded GitNexus?
- [ ] What's the policy on forks?
- [ ] Any planned license changes?

### Deliverable: License Review Document

**Contents:**
- License type (verbatim from LICENSE file)
- Full text of restrictions (no paraphrasing)
- Transitive license tree (all dependencies + their licenses)
- Commercial scenario assessment (SaaS, SDK, fork, attribution)
- Risk level for each scenario (GREEN/YELLOW/RED)
- Unresolved questions for maintainers
- **Recommendation:** Can proceed / Legal review required / Cannot integrate

---

## 2. API & SDK Evaluation

### Objective
Determine how GitNexus is intended to be used and whether it's stable.

### Investigation Plan

**2.1 Usage Model Discovery**
Read documentation and code to answer:
- [ ] Is GitNexus primarily a CLI tool?
- [ ] Is it an MCP (Claude) server?
- [ ] Does it expose REST API?
- [ ] Does it provide Python SDK?
- [ ] Can it be embedded as a library?
- [ ] Which usage model is primary/recommended?

**2.2 Public API Surface**
- [ ] Read README carefully (what example code is shown?)
- [ ] Find main entry points (main.py, __init__.py, etc.)
- [ ] Identify exported classes/functions (what's in `__all__`?)
- [ ] Distinguish public vs internal interfaces (naming conventions, docs)
- [ ] Document API stability markers ("beta", "unstable", "experimental")

**2.3 Extension Points**
Can Ortho extend/customize GitNexus?
- [ ] Are there plugin/adapter interfaces?
- [ ] Can custom language providers be added?
- [ ] Can custom storage backends be configured?
- [ ] Can custom analyzers be plugged in?
- [ ] Is configuration data-driven or code-driven?

**2.4 Dependency Graph**
- [ ] Extract all dependencies from pyproject.toml
- [ ] For each, determine:
  - Version pinning strategy (>=X, ==X, <X)
  - License compatibility
  - System requirements (Python version, C extensions?)
  - Stability (mature/experimental)
  - Maintenance status (actively maintained?)

**2.5 Version Compatibility Assessment**
- [ ] What version are we evaluating?
- [ ] When was last release?
- [ ] What was the breaking change history (0.x → 1.0, etc)?
- [ ] Are there published compatibility guarantees?
- [ ] How long do versions get supported?

**2.6 Stability Signals**
| Signal | Finding | Assessment |
|--------|---------|------------|
| Latest version >= 1.0? | ? | Mature or pre-release? |
| Semantic versioning? | ? | Predictable upgrades? |
| Breaking changes documented? | ? | Can anticipate issues? |
| API deprecation path? | ? | Safe to depend on? |
| Test coverage visible? | ? | Confidence in stability? |
| Release frequency? | ? | Is it maintained? |

### Deliverable: SDK Evaluation Report

**Contents:**
- Primary usage model (CLI / SDK / MCP / library)
- Public API surface (main classes, functions)
- Extension capability (can Ortho hook in?)
- Dependency tree (versions, licenses)
- Version compatibility strategy
- Stability assessment (mature / pre-release / experimental)
- Integration risk (LOW / MEDIUM / HIGH)
- **Recommendation:** Safe to depend on / Caution required / Too unstable

---

## 3. Architecture Reverse-Engineering

### Objective
Understand GitNexus design (not features) to compare against Ortho's responsibilities.

### Investigation Plan

**3.1 Source Code Exploration**
Read (don't just skim) these files:
- [ ] README.md (architecture section)
- [ ] Main module structure (ls -la src/)
- [ ] Key classes (import hierarchy, responsibilities)
- [ ] Data models (what do symbols look like?)
- [ ] Storage layer (how is data persisted?)
- [ ] Indexing pipeline (parser → graph → storage)
- [ ] Search implementation (FTS5 / vector / custom?)
- [ ] Query interface (how does client interact?)

**3.2 Responsibility Identification**
For each major component, answer:
- **Parser:** What languages? Which parser backend (tree-sitter, native, custom)?
- **Symbol Table:** What metadata captured? How scoped?
- **Graph Generation:** Algorithms for call graph, import graph, dependency graph? Confidence scoring?
- **Indexing:** Incremental or batch? Invalidation strategy?
- **Storage:** Database schema? Graph serialization? Version tracking?
- **Search:** FTS5, vector embeddings, both? Ranking?
- **Retrieval:** How does client query? Caching?
- **Concurrency:** Thread-safe? Async APIs?

**3.3 Architectural Pattern Identification**
- [ ] Is it layered (parser → analysis → storage → search)?
- [ ] Is there a data model/schema layer?
- [ ] How are responsibilities separated?
- [ ] What are the boundaries between components?
- [ ] Are there well-defined interfaces or tightly coupled?

**3.4 Comparison Against Ortho's Architecture**

| Responsibility | Ortho Owns | GitNexus Owns | Conflict? |
|---|---|---|---|
| Language parsing | PythonAdapter | GitNexus language providers | ? |
| Symbol extraction | SymbolExtractor | GitNexus symbol model | ? |
| Qualified names | ImportGraphBuilder | GitNexus scope resolution | ? |
| Call graph generation | CallGraphBuilder | GitNexus call graph | ? |
| Dependency parsing | DependencyGraphBuilder | GitNexus manifest parsing | ? |
| Graph storage | SQLite schema | GitNexus storage abstraction | ? |
| Search (FTS) | BM25 via FTS5 | GitNexus FTS (if exists) | ? |
| Search (semantic) | sqlite-vec embeddings | GitNexus semantic (if exists) | ? |
| Incremental indexing | IncrementalIndexer (git diff) | GitNexus incremental (if exists) | ? |
| Architecture detection | ArchitectureDetector | (GitNexus N/A) | No |
| Artifact storage | ContextHub | (GitNexus N/A) | No |
| Project memory | ProjectMemory | (GitNexus N/A) | No |

For each "?" identify:
- Do both systems address the same responsibility?
- Is one strictly better? (evidence?)
- Can they coexist?
- Is replacement safe?

**3.5 Design Pattern Documentation**
Create ASCII diagrams showing:
- Data flow (input → parsing → storage → retrieval)
- Layer boundaries
- Component dependencies
- Extension points

### Deliverable: Architecture Deep Dive

**Contents:**
- Source code exploration notes (key files, patterns)
- Responsibility matrix (Ortho vs GitNexus)
- Data model (what do symbols/graphs look like?)
- Indexing strategy (how does data get updated?)
- Storage model (database schema, serialization?)
- Search implementation (algorithms, ranking?)
- Concurrency model (thread-safe? async?)
- Architectural diagrams (ASCII layers, data flow)
- **Comparison:** Which responsibilities overlap? Where can coexist?
- **Assessment:** Can they be integrated or are they at odds?

---

## 4. Component Mapping Matrix

### Objective
Classify every Ortho component as KEEP / REPLACE / WRAP / LEARN / IGNORE.

### Investigation Plan

**4.1 Complete Ortho Inventory**
For every component in Ortho's codebase, answer:
- What is its responsibility? (one sentence)
- Is there a GitNexus equivalent? (yes/no)
- If yes, what's it called?

**4.2 Classification Decision**
For each component, determine:

| Classification | Meaning | When to Choose |
|---|---|---|
| **KEEP** | No change, GitNexus not applicable | GitNexus has no equivalent, Ortho's version working well |
| **REPLACE** | Remove Ortho code, use GitNexus | GitNexus proven superior by benchmarks |
| **WRAP** | Keep Ortho interface, use GitNexus backend | GitNexus is better but Ortho interface must remain stable |
| **LEARN** | Keep Ortho code, adopt GitNexus patterns | GitNexus approach is better architecturally, reimplement in Ortho |
| **IGNORE** | Doesn't apply | Neither system addresses this |

**4.3 Evidence Requirements**
For every classification, document:

```
Component: [Name]
Responsibility: [What it does]
GitNexus Equivalent: [Name or "N/A"]
Classification: [KEEP / REPLACE / WRAP / LEARN / IGNORE]

Reasoning:
  [Why this choice? One paragraph.]

Evidence:
  [What proves this? Benchmark result? Architecture analysis? License check?]

Risk:
  [What could go wrong with this decision?]

Maintenance:
  [Who owns it after decision? Ortho? GitNexus?]
```

**4.4 Matrix Population**

| Component | Responsibility | GitNexus Equiv | Classification | Reasoning | Evidence Needed | Risk | Owner |
|---|---|---|---|---|---|---|---|
| PythonAdapter | Parse Python files, extract AST | GitNexus Python provider | TBD | ? | Benchmark: accuracy, speed | ? | ? |
| SymbolExtractor | Extract symbols with qualified names | GitNexus symbol model | TBD | ? | Benchmark: recall, precision | ? | ? |
| ImportGraphBuilder | Trace imports, detect cycles | GitNexus import resolution | TBD | ? | Benchmark: accuracy on edge cases | ? | ? |
| CallGraphBuilder | Generate call graph | GitNexus call graph | TBD | ? | Benchmark: accuracy, confidence scores | ? | ? |
| DependencyGraphBuilder | Parse requirements.txt, pyproject.toml | GitNexus dependency parsing | TBD | ? | Benchmark: format support, version accuracy | ? | ? |
| ModuleDetector | Detect packages, namespace packages | GitNexus module detection | TBD | ? | Benchmark: coverage, edge case handling | ? | ? |
| IncrementalIndexer | Git diff-based delta indexing | GitNexus incremental | TBD | ? | Benchmark: speed, correctness | ? | ? |
| ContextHub | Artifact storage, versioning | (GitNexus N/A) | KEEP | Not comparable | N/A | None | Ortho |
| ArchitectureDetector | Detect arch styles (layered, hex, etc) | (GitNexus N/A) | KEEP | Not comparable | N/A | None | Ortho |
| BM25 Search | Full-text search on artifacts | GitNexus FTS (if exists) | TBD | ? | Benchmark: relevance, speed | ? | ? |
| Semantic Search | Vector-based search | GitNexus semantic (if exists) | TBD | ? | Benchmark: relevance, speed | ? | ? |
| Hybrid Search (RRF) | Fuse BM25 + semantic | GitNexus hybrid (if exists) | TBD | ? | Benchmark: ranking quality | ? | ? |
| ProjectMemory | Key/value fact store | (GitNexus N/A) | KEEP | Not comparable | N/A | None | Ortho |
| ASES | Workflow governance | (GitNexus N/A) | KEEP | Not comparable | N/A | None | Ortho |

### Deliverable: Component Decision Matrix

**Contents:**
- Complete table (every Ortho component)
- Classification (KEEP / REPLACE / WRAP / LEARN / IGNORE) for each
- Reasoning (why this choice?)
- Evidence needed (what benchmark/analysis justifies it?)
- Risk (what could go wrong?)
- Ownership (who maintains it post-decision?)
- **Summary:** X components KEEP, Y components TBD (pending benchmarks), Z components REPLACE

---

## 5. Benchmark Specification

### Objective
Design tests (don't run yet) that prove whether GitNexus is better than Ortho.

### Test Repositories

**Baseline Set (production code, well-tested):**
- FastAPI (10k LOC, well-documented Python)
- LangChain (50k LOC, complex imports, multiple adapters)
- OpenClaude (100k+ LOC, large codebase)
- Dapr (multiple languages, Go + C#)

**Specialized Set:**
- Repo with complex imports (relative, circular, star imports)
- Repo with dynamic dependencies (setup.py with logic)
- Monorepo (multiple packages, cross-package calls)
- Repo with syntax errors (mixed Python 2/3, incomplete code)

### Benchmark A: AST Quality

**Hypothesis:** GitNexus parses code more accurately than Ortho.

**Procedure:**
1. Run Ortho on FastAPI repo, count parse errors
2. Run GitNexus on same repo, count parse errors
3. For failed parses, classify error (syntax, encoding, timeout)
4. Calculate success rate for each

**Metrics:**
- Parse success rate (% of files successfully parsed)
- Coverage (% of LOC analyzed)
- Error categories (what causes failures?)

**Success Criteria:**
- Both >99% success rate, OR
- GitNexus >99% and Ortho <99% (proves superiority), OR
- Both >95% (both acceptable)

**Decision Logic:**
- If GitNexus >99% and Ortho <99%: Consider REPLACE
- If both >99%: Consider KEEP (Ortho sufficient)
- If both <95%: Caution required for both

---

### Benchmark B: Symbol Extraction Accuracy

**Hypothesis:** GitNexus extracts more complete/accurate symbol lists.

**Procedure:**
1. Select 10 Python files of varying size (10, 100, 500, 1000, 2000 LOC)
2. **Manually audit** each file: count actual functions, classes, methods
3. Run Ortho, count extracted symbols
4. Run GitNexus, count extracted symbols
5. For each system, measure:
   - Recall: (symbols found) / (actual symbols)
   - Precision: (symbols found that are correct) / (total symbols found)
   - False negatives: missed symbols
   - False positives: incorrect symbols

**Metrics:**
- Recall % (did we find all symbols?)
- Precision % (how many were correct?)
- Symbols per LOC (baseline)

**Success Criteria:**
- >99% recall (missed <1 symbol per 100)
- >99% precision (false positives <1%)
- Both systems similar → KEEP Ortho
- GitNexus >>Ortho → Consider REPLACE

**Decision Logic:**
- If both >99% recall/precision: KEEP Ortho (sufficient)
- If GitNexus 99.5% and Ortho 98%: WRAP (better backend, same interface)
- If either <95%: Investigate why

---

### Benchmark C: Import Resolution Accuracy

**Hypothesis:** GitNexus handles import edge cases better.

**Procedure:**
1. Use LangChain repo (complex imports)
2. Manually verify 50 imports in each file:
   - Standard imports (`import X`)
   - From imports (`from X import Y`)
   - Relative imports (`from . import X`)
   - Star imports (`from X import *`)
   - Circular imports (detected?)
3. Run both systems
4. For each import, verify:
   - Source module identified correctly?
   - Target module identified correctly?
   - Circular detected correctly?

**Metrics:**
- Accuracy % (correct target for each import)
- Circular detection % (caught all cycles?)
- Edge case handling (relative imports, star imports)

**Success Criteria:**
- >95% accuracy on standard imports
- 100% circular detection
- Both systems similar → KEEP Ortho
- GitNexus >>Ortho → Consider REPLACE

---

### Benchmark D: Call Graph Accuracy

**Hypothesis:** GitNexus call graph is more accurate than Ortho.

**Procedure:**
1. Select file with 10-20 functions, moderate complexity
2. **Manually trace** all function calls in the file
3. Build expected call graph (X calls Y, etc.)
4. Run Ortho, extract call graph
5. Run GitNexus, extract call graph
6. For each system, measure:
   - Recall: (calls found) / (actual calls)
   - Precision: (calls found that are correct) / (total calls found)
   - False negatives: missed calls
   - False positives: spurious calls
   - Confidence calibration: are high-confidence edges correct?

**Metrics:**
- Recall % (did we find all calls?)
- Precision % (how many were correct?)
- Confidence score calibration

**Success Criteria:**
- >95% recall (missed <1 call per 20)
- >95% precision (false positives <5%)
- Confidence >0.8: should be >95% correct
- Both systems similar → KEEP Ortho
- GitNexus >>Ortho → Consider REPLACE

---

### Benchmark E: Dependency Parsing

**Hypothesis:** GitNexus handles more manifest formats and edge cases.

**Procedure:**
1. Use repos with multiple dependency formats:
   - requirements.txt (pip)
   - pyproject.toml (Poetry, setuptools)
   - setup.py (legacy)
2. Manually extract expected dependencies from each
3. Run Ortho, extract dependencies
4. Run GitNexus, extract dependencies
5. Measure:
   - Format support (which files recognized?)
   - Accuracy (correct versions extracted?)
   - Pre-release handling (e.g., 1.0rc1)
   - Editable installs (e.g., -e .)
   - Transitive dependencies (resolved?)

**Metrics:**
- Format support (X of Y formats)
- Version accuracy (% correct)
- Edge case handling

**Success Criteria:**
- Both handle all standard formats
- >95% version accuracy
- Both similar → KEEP Ortho
- GitNexus >>Ortho → Consider REPLACE

---

### Benchmark F: Incremental Indexing Speed

**Hypothesis:** GitNexus incremental update is faster than Ortho.

**Procedure:**
1. Index full FastAPI repo
2. Modify single file (add function, change import)
3. Run Ortho incremental update, measure time
4. Run GitNexus incremental update, measure time
5. Measure:
   - Time to update (ms)
   - Items updated (only changed symbols?)
   - Correctness (is stale data removed?)

**Metrics:**
- Update latency (ms)
- Staleness (is old data cleaned up?)
- Accuracy (are only changed items updated?)

**Success Criteria:**
- <100ms per file update (both)
- Zero stale data
- Both similar → KEEP Ortho
- GitNexus <50ms and Ortho >100ms → Consider WRAP

---

### Benchmark G: Large Repository Handling

**Hypothesis:** GitNexus scales better for large repos.

**Procedure:**
1. Index OpenClaude (100k+ files)
2. Measure:
   - Index time (how long to analyze everything?)
   - Memory usage (peak during indexing)
   - Memory at rest (after indexing complete)
   - Query latency (how fast to search for symbol X?)
   - Query correctness (results accurate?)

**Metrics:**
- Index time (minutes)
- Memory during (MB)
- Memory at rest (MB)
- Query latency (ms)
- Query accuracy (correct results?)

**Success Criteria:**
- Index <30 min
- Memory at rest <1GB
- Query <100ms
- Query >95% accurate
- Both similar → KEEP Ortho
- GitNexus scales better → Consider WRAP/REPLACE

---

### Benchmark H: Memory Footprint

**Hypothesis:** GitNexus memory usage is acceptable.

**Procedure:**
1. Index repos of increasing size:
   - 1k files
   - 10k files
   - 100k files
2. Measure peak memory at each step
3. Calculate memory per symbol/edge

**Metrics:**
- Memory per file (MB/file)
- Memory per symbol (KB/symbol)
- Linear or quadratic growth?

**Success Criteria:**
- <1 MB per 1k files
- <500MB for typical project
- Both similar → KEEP Ortho
- GitNexus <Ortho → Consider REPLACE

---

### Benchmark I: Confidence Score Calibration

**Hypothesis:** GitNexus confidence scores reliably indicate accuracy.

**Procedure:**
1. Extract call graph with confidence scores
2. Manually verify 50 edges marked >0.8 confidence
3. Manually verify 50 edges marked <0.5 confidence
4. Calculate:
   - % of high-confidence edges that are correct
   - % of low-confidence edges that are incorrect
   - Calibration error (do scores match reality?)

**Metrics:**
- High-confidence accuracy (%)
- Low-confidence error rate (%)
- Calibration (are scores accurate?)

**Success Criteria:**
- >95% of 0.8+ confidence edges are correct
- <20% of <0.5 confidence edges are correct
- Scores well-calibrated
- Both similar → KEEP Ortho
- GitNexus better calibrated → Consider WRAP

---

### Benchmark J: Repository Coverage

**Hypothesis:** GitNexus finds all code.

**Procedure:**
1. Count Python files in repo
2. Count files analyzed by Ortho
3. Count files analyzed by GitNexus
4. Identify missing files (why excluded?)

**Metrics:**
- Coverage % (files analyzed / total)
- Missing files (list)
- Exclusion reasons (hidden, too large, invalid?)

**Success Criteria:**
- >99% coverage
- Missing files documented
- Both similar → KEEP Ortho

---

### Deliverable: Benchmark Specification

**Contents:**
- 10 benchmarks (A through J)
- For each benchmark:
  - Hypothesis (what are we testing?)
  - Procedure (step by step, reproducible)
  - Metrics (what we measure)
  - Success criteria (what counts as success?)
  - Decision logic (how benchmark results drive decisions)
- Test repositories (which real repos to use)
- Measurement tools (how to measure latency, memory, etc?)
- Acceptance criteria (both pass / one better / one fails)
- **Phase 2 Plan:** How to execute benchmarks and make decisions

---

## Summary: Phase 1 Evaluation Strategy

| Document | Purpose | Input | Output | Decision Driver |
|---|---|---|---|---|
| **License Review** | Legal compatibility | LICENSE file, dependencies | Risk level, legal risks | Can we legally use GitNexus? |
| **SDK Evaluation** | API readiness | README, code, docs | Stability, usage model | Can we reliably depend on it? |
| **Architecture Deep Dive** | Design compatibility | Source code | Responsibility map | Can systems coexist? |
| **Component Matrix** | Replacement analysis | Ortho components vs GitNexus | KEEP/WRAP/REPLACE/LEARN/IGNORE | What should change? |
| **Benchmark Spec** | Objective evidence | Test procedures | Benchmark results (Phase 2) | Which is actually better? |

---

## Phase 1 Timeline

| Week | Task | Deliverable |
|---|---|---|
| 1 | License Review + SDK Evaluation | License Review, SDK Evaluation Report |
| 2 | Architecture Reverse-Engineering | Architecture Deep Dive |
| 2-3 | Component Mapping | Component Decision Matrix |
| 3 | Benchmark Specification | Benchmark Specification |

**Total effort:** ~60 hours (distributed across team)

---

## Gate: Phase 1 Completion

Before proceeding to Phase 2 (running benchmarks), verify:

- [ ] License Review complete, legal risk understood
- [ ] SDK Evaluation complete, API stability assessed
- [ ] Architecture Deep Dive complete, responsibilities mapped
- [ ] Component Matrix complete, all components classified
- [ ] Benchmark Spec complete, all 10 benchmarks designed
- [ ] Team alignment on evaluation methodology
- [ ] Test repos identified and accessible

---

## Principles Maintained

✅ No assumptions without evidence  
✅ Every recommendation driven by measurable data  
✅ Benchmark-driven, not opinion-driven  
✅ Compare architectures, not features  
✅ Preserve Ortho's ownership of Engineering Intelligence  
✅ Design for long-term evolution, not short-term convenience

