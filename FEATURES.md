# Ortho v3 — Complete Features List

**Version:** 3.0  
**Status:** vNext COMPLETE (Engineering Decision Engine — all four roadmap phases)  
**Last Updated:** 2026-07-16  

---

## Table of Contents

1. [Pillar 1: Repository Intelligence](#pillar-1-repository-intelligence)
2. [Pillar 2: ContextHub](#pillar-2-contexthub)
3. [Pillar 3: Architectural Intelligence](#pillar-3-architectural-intelligence)
4. [Pillar 4: Engineering Orchestration](#pillar-4-engineering-orchestration)
5. [Pillar 5: Token Optimizer](#pillar-5-token-optimizer)
6. [CLI Commands](#cli-commands)
7. [Storage & Data](#storage--data)

---

## Pillar 1: Repository Intelligence

**Status:** ✅ COMPLETE (Phase 2)

### Code Parsing & Analysis

- **Python AST Parsing** — tree-sitter based, supports Python 3.8–3.14
  - Symbol extraction (functions, classes, methods, variables, types)
  - Docstring and signature capture
  - Full position tracking (line/column numbers)
  
- **TypeScript Adapter** — Full support for JavaScript/TypeScript
  - AST parsing via tree-sitter
  - Symbol extraction equivalent to Python
  - Import analysis for type checking

### Graph Construction

- **Call Graph Builder** — Static function call analysis
  - Detects direct function calls, method calls, async/await
  - Confidence scoring (0.0–1.0) for uncertain calls
  - Supports nested calls and higher-order functions
  - Limitation: Cannot resolve dynamic calls (getattr, eval, exec)

- **Import Graph Builder** — Module-level dependency tracking
  - Tracks what each file imports and from where
  - Distinguishes internal vs external imports
  - Symbol-level import tracking (which names imported)
  - External dependency detection

- **Dependency Graph** — Project-level dependency analysis
  - Parses `requirements.txt`, `pyproject.toml`, `package.json`
  - Version tracking (when available)
  - Transitive dependency resolution

### Incremental Indexing

- **Git-based Change Detection** — Incremental re-indexing
  - Uses `git diff` to find changed files since last index
  - Fallback to file mtime if not a git repo
  - Efficient: Only reindexes changed files

- **Module Detection** — Logical module identification
  - Directory + naming pattern based clustering
  - Namespace package support (PEP 420)
  - Virtual module creation from patterns

### Output

- **Symbol Registry** — Persistent storage of all code symbols
  - Stable symbol IDs (hash-based, survives renames)
  - Full visibility tracking (public/private/protected/internal)
  - Complete signature and docstring capture

- **Indexed Repository** — Complete file manifest
  - Language detection per file
  - File size and modification tracking
  - Git metadata (last commit, branch info)

---

## Pillar 2: ContextHub

**Status:** ✅ COMPLETE (Phase 1)

### Artifact Storage

- **Artifact Types Supported:**
  - FRD (Functional Requirements Document)
  - ADR (Architecture Decision Record)
  - Architecture documentation
  - Specifications and designs
  - Decision records
  - Lesson learned documents
  - Developer notes
  - Benchmarks and test results
  - Conversation histories
  - Git metadata
  - Project memory (structured key/value)
  - Evidence artifacts (test output, lint results, approvals)
  - Workflow run records

- **Artifact Metadata:**
  - Relevance scoping (global/project/module/file)
  - Tagging system (free-form tags per artifact)
  - Related symbol references (Symbol ID links)
  - Token estimation (for budget management)
  - Content hashing (for staleness detection)
  - Creation and modification timestamps

### Search Capabilities

- **BM25 Full-Text Search** — SQLite FTS5 powered
  - Keyword-based search on artifact content
  - Scoring by term frequency and relevance
  - Fast indexed lookup

- **Semantic Search** — Vector similarity search
  - SQLite-vec integration for KNN search
  - 1536-dimensional embeddings (text-embedding-3-small compatible)
  - Cosine distance similarity
  - Completely local (no external services required)

- **Hybrid Search** — Reciprocal Rank Fusion (RRF)
  - Combines BM25 and semantic results
  - RRF constant k=60 (standard)
  - Returns ranked results by combined score
  - Type and scope filtering

### Git Metadata Store

- **Commit History Tracking**
  - Last commit SHA per file
  - Commit timestamps
  - Author information (when available)
  - Churn metrics (change frequency)

- **Branch Information**
  - Current branch tracking
  - Remote tracking branches
  - Git remote URL storage

### Project Memory

- **Structured Key/Value Store**
  - Examples: `primary_language`, `test_framework`, `api_style`, `auth_approach`
  - Source tracking (manual vs auto-detected)
  - Update timestamps
  - Per-project scoping

### Artifact Versioning (Phase 2 Feature)

- **Version Tracking** — Historical artifact changes
- **Staleness Detection** — Flag artifacts whose source changed

---

## Pillar 3: Architectural Intelligence

**Status:** ✅ COMPLETE (Phase 2)

### Architecture Detection

- **Supported Styles:**
  - Layered (presentation → domain → data)
  - Microservices (service-to-service)
  - Hexagonal (ports & adapters)
  - MVC (model-view-controller)
  - Flat (no discernible layers)

- **Detection Process:**
  - Import pattern analysis
  - Naming convention detection
  - Directory structure heuristics
  - Confidence scoring (0.0–1.0)
  - Alternative style suggestions

### Layer & Subsystem Detection

- **Layer Identification:**
  - Automatic layer boundary detection
  - Per-layer file lists
  - Dependency relationships between layers
  - Layer naming and classification

- **Subsystem Clustering:**
  - Logical grouping by functionality
  - Coupling score calculation (0.0–1.0)
  - Subsystem boundary identification
  - Cross-layer relationships

### Dependency Analysis

- **Circular Dependency Detection:**
  - Identifies cycles in import/call graphs
  - Reports affected symbols and files
  - Severity scoring

- **Import Rule Enforcement (ADR-015):**
  - One-way, acyclic dependency rules
  - Layer boundary violation detection
  - Cross-cutting concern identification

### Change Impact Analysis

- **Blast Radius Calculation:**
  - Direct dependents (files importing changed file)
  - Transitive dependents (reachable within N hops)
  - Risk scoring (0.0–1.0)
  - Affected file count

- **Dependency Graph Traversal:**
  - Configurable traversal depth (1–N hops)
  - Impact report by symbol and file

### Technical Debt Scoring

- **Multi-Factor Scoring:**
  - Coupling score (fan-in + fan-out ratio)
  - Churn score (modification frequency from git)
  - Complexity score (AST depth + function count)
  - Test coverage score (inverse of test presence heuristic)

- **Per-Module Scoring:**
  - Individual module scores (0.0–1.0)
  - Evidence listing per score component
  - Breakdown by debt factor

### ADR Awareness

- **ADR Cross-Reference:**
  - Links ADRs to affected code symbols
  - Detects ADR violations
  - Reuse discovery (similar ADRs across codebase)

---

## Pillar 4: Engineering Orchestration

**Status:** ✅ COMPLETE (Phase 3)

### Intent Routing

- **Semantic Intent Classification** — semantic-router integration
  - Sub-10ms classification (no LLM call)
  - HuggingFace encoder (BAAI/bge-small-en-v1.5) for local embeddings
  - Confidence scoring
  - Fallback to LLM classifier for ambiguous cases

- **Intent Classes:**
  - `feature_development` — New feature implementation
  - `bug_fix` — Bug diagnosis and fixes
  - `refactor` — Code refactoring
  - `analysis` — Repository analysis and reports

### Agent Registry

- **Built-in Agents (8 agents):**
  - Orchestrator — Master workflow coordinator
  - Architect — System design and ADR writing
  - Coder — Implementation and code generation
  - Reviewer — Code review and standards
  - Tester — Test strategy and generation
  - Analyst — Impact and debt analysis
  - Documenter — Documentation generation
  - Debugger — Root cause analysis and debugging

- **Agent Manifest Format:**
  - Frontmatter metadata (name, display_name, description, triggers, skills)
  - System prompt (LLM persona definition)
  - Priority weighting
  - Context requirements

### Skill Registry

- **Built-in Skills (10+ skills):**
  - repo-analysis — How to interpret repository data
  - adr-writer — ADR format and criteria
  - impact-analyzer — Change impact interpretation
  - test-generator — Test strategy patterns
  - code-reviewer — Review checklist
  - context-retriever — Additional context requests
  - git-analyst — Git metadata interpretation
  - debt-analyzer — Technical debt scoring
  - spec-writer — FRD/spec format
  - debug-tracer — Root cause analysis

- **Skill Injection:**
  - Per-agent skill assignment
  - Token count estimation
  - Skill content injection into LLM context

### Selector Engine

- **Pure Python Scoring:**
  - Agent scoring (intent match + semantic sim + priority + context availability)
  - Skill scoring (agent type match + intent trigger + preference)
  - Deterministic, no LLM calls

- **Execution Plan Generation:**
  - Ordered agent steps
  - Skill assignment per agent
  - Token budget estimation
  - Approval gate placement

### Workflow Execution

- **Step-by-Step Execution:**
  - Agent invocation with context
  - LLM call orchestration
  - Evidence collection per step
  - State persistence (resumable workflows)

- **Human Approval Gates:**
  - Mandatory approval before high-risk steps
  - Rejection with reason capability
  - Timeout handling

- **Error Handling:**
  - LLM timeout handling
  - API error recovery
  - Fallback routing

---

## Pillar 5: Token Optimizer

**Status:** ✅ COMPLETE (Phase 4)

### Component 1: Semantic Duplicate Detector

- **Deduplication Algorithm:**
  - Token-based Jaccard similarity (5 chars ≈ 1 token)
  - Greedy clustering (deterministic, fast)
  - Highest-relevance chunk per cluster
  - Order preservation

- **Configuration:**
  - Similarity threshold (0.0–1.0, default 0.85)
  - Deterministic output (same input → same output)

### Component 2: Intent-Aware Reranker

- **Intent-Based Boosting:**
  - Per-intent-class keyword boost factors (0.5–2.0x)
  - Feature development: boosts API, interface, examples
  - Bug fix: boosts error handling, tests, edge cases
  - Refactor: boosts dependencies, coupling, metrics
  - Analysis: boosts architecture, design, patterns

- **Reranking Logic:**
  - Keyword extraction from chunk content
  - Max boost when multiple keywords match
  - Stable sorting (by score desc, ID asc)
  - Config-driven (customizable per deployment)

### Component 3: Graph Expander

- **Call Graph Enrichment:**
  - Extracts symbol names from queries
  - BFS traversal of call graph (callers + callees)
  - Configurable depth (1–N hops)
  - Max additions cap (prevent explosion)

- **Interface:**
  - Abstract CallGraphInterface (decoupled from repo-intelligence)
  - Deterministic neighbor ordering
  - Case-insensitive symbol matching

### Component 4: Context Compressor

- **Summarization Strategy:**
  - Identifies low-priority chunks (included=False)
  - Heuristic truncation + ellipsis (production: LLM-based)
  - Preserves high-priority chunks
  - Token count recomputation

- **Input Validation:**
  - Compression target ∈ [0.0, 1.0]
  - Model name validation
  - Error handling with fallback

### Component 5: Architecture-Aware Retrieval

- **Centrality Weighting:**
  - Layer-based boosts (service 1.5x, domain 1.4x, etc.)
  - Subsystem boosts (low-coupling 1.3x)
  - Per-architecture-style configuration
  - Max boost selection (not cumulative)

- **Supported Architectures:**
  - Layered, microservices, hexagonal, MVC, flat
  - Graceful fallback (identity if arch model missing)

### Component 6: Model Context Adapter

- **Per-Model Format Adjustment:**
  - Claude Opus: identity (no change)
  - Claude Haiku: remove verbose, keep essentials (2 paragraphs max)
  - GPT-4 variants: add conciseness hint
  - GPT-4o: GPT-4 + JSON output hint
  - Local models: add budget warnings
  - Unknown: identity fallback

- **Deterministic Transformations:**
  - Pure text manipulation (no ML)
  - All rules commented with model reasoning

### Component 7: Context Quality Logger

- **CSV Logging:**
  - Daily log rotation (.ortho/logs/context-quality-YYYYMMDD.csv)
  - All assembly decisions tracked
  - Fields: timestamp, workflow_run_id, step_id, query, intent_class, chunks_retrieved, chunks_included, tokens, ratios, model, LLM metrics

- **Log Reading:**
  - Parse CSV back to structured dicts
  - Filter by date range
  - Type conversion (auto-convert numeric fields)

### Component 8: Metrics Collection

- **Token Reduction Measurement:**
  - Compare Phase 3 baseline vs Phase 4 current
  - Average token calculation
  - Percentile computation (P50, P95)
  - Per-intent-class breakdowns

- **Metrics Output:**
  - reduction_pct (goal: ≥15%)
  - avg_phase3, avg_phase4
  - p50, p95 percentiles
  - Sample counts

### Component 9: Ranking Weight Tuning

- **Auto-Tuning Algorithm:**
  - Pearson correlation: rerank_factor vs target metric
  - Positive correlation (>0.7): increase weights by 10%
  - Negative correlation (<-0.7): decrease weights by 10%
  - Weight bounds [0.5, 2.0] (prevent wild swings)

- **Tuning Output:**
  - Updated weight dictionary
  - Change deltas report
  - Per-intent-class tuning

---

## CLI Commands

**Status:** ✅ COMPLETE (Phase 3+)

### Repository Operations

```bash
ortho init                          # Initialize .ortho/ directory
ortho scan                          # Full repository scan and index
ortho scan --watch                  # Watch mode (re-index on changes)
ortho index --since HEAD~1          # Incremental re-index
```

### Context Operations

```bash
ortho context add <file>            # Add artifact to ContextHub
ortho context add --type adr <file> # Add with explicit type
ortho context search "<query>"      # Hybrid search (BM25 + semantic)
ortho context list                  # List all artifacts
ortho context stats                 # Storage statistics
```

### Analysis Operations

```bash
ortho analyze                       # Full architecture report
ortho analyze --impact <file>       # Change impact for file
ortho analyze --debt                # Technical debt report
ortho analyze --deps                # Dependency health report
```

### Engineering Decision Engine (vNext, 2026-07-16)

```bash
ortho review [path]                 # Unified: violations + decision + test intelligence, one scan
ortho guardrails [path]             # Architecture violations, each with checkable evidence
ortho decide <file|intent>          # Change impact + recommended tests + coverage gaps
ortho plan "<intent>"               # Implementation paths ranked by effort/risk
ortho refactor [path]               # Bloat/coupling/cycle findings with evidence
ortho ask "<question>"              # Structural Q&A from the real call/import graph
ortho orchestrate "<intent>"        # plan + decide + review chained; human approves, never auto-merges
ortho cross-repo <pathA> <pathB>    # Real AST-structural code reuse across 2-5 repos
ortho feedback accept|reject "<rule_id> <location>" [--reason]
                                    # Record decisions; future runs cite "rejected before: <why>"
ortho memory <query>                # Search accumulated engineering memory
```

Every finding carries evidence (`✓` lines: measured counts, real import
edges). Every command's run is captured to per-repo engineering memory.
All 10 capabilities are also exposed as MCP tools for Claude Code
(`MCP_SETUP.md`).

### Orchestration Operations

```bash
ortho run "<intent>"                # Main entry: run ASES workflow
ortho run --dry-run "<intent>"      # Show execution plan only
ortho status                        # Show active workflow state
ortho approve                       # Approve pending human gate
ortho reject "<reason>"             # Reject with reason
ortho history                       # Show past workflow runs
ortho history --id <run_id>         # Show specific run details
```

### Debugging

```bash
ortho debug run "<intent>"          # Show full context assembled
ortho debug context "<query>"       # Show context retrieval trace
```

### Configuration

```bash
ortho config show                   # Show current configuration
ortho config set <key> <value>      # Set config value
```

---

## Storage & Data

**Status:** ✅ COMPLETE

### Local Storage

- **SQLite Databases:**
  - `.ortho/ortho.db` — Main repository data
    - Repositories table (metadata)
    - Files table (file manifest)
    - Symbols table (code symbols)
    - Call edges, import edges (graphs)
    - Artifacts (ContextHub storage)
    - Project memory (key/value facts)
    - Architecture models (detected styles)
    - Workflow runs (orchestration history)
    - Agent/skill manifests (registry cache)

  - `.ortho/vectors.db` — Embedding storage
    - artifact_embeddings (semantic search)
    - symbol_embeddings (for future use)

### Configuration

- **`.ortho/config.toml`** — Project configuration
  - Project metadata (name, primary language)
  - Indexing settings (languages, exclude patterns, incremental)
  - ContextHub settings (embedding model, provider)
  - LLM settings (default model, fallback, max tokens)
  - Orchestration settings (human approval, timeout)
  - Token optimizer settings (default budget, compression)

### Logs

- **`.ortho/logs/`** — Quality and operation logs
  - `context-quality-YYYYMMDD.csv` — Assembly decisions (daily rotation)
  - Parseable CSV format (machine-readable)

### ASES Artifacts

- **`.ases/workflows/`** — ASES workflow definitions
  - Feature, bug-fix, refactor, analysis, documentation workflows
  - Each defines steps, roles, gates, evidence requirements

- **`.ases/agents/`** — Agent definitions
  - Core agents (built-in)
  - Custom agents (user-defined)
  - YAML frontmatter + system prompt

- **`.ases/skills/`** — Skill definitions
  - Core skills (built-in)
  - Custom skills (user-defined)
  - YAML frontmatter + skill content

---

## Performance Characteristics

### Indexing

- **Scan Performance:** <30 seconds for medium Python repo (1000 files)
- **Incremental Re-index:** <5 seconds (git diff based)
- **Symbol Extraction:** ~1ms per file (AST parsing)

### Search

- **BM25 Search:** <10ms (SQLite FTS5)
- **Semantic Search:** <50ms (sqlite-vec KNN)
- **Hybrid Search:** <100ms (RRF merge)

### Orchestration

- **Intent Classification:** <10ms (semantic-router, no LLM)
- **Selector Engine:** <20ms (scoring all agents/skills)
- **Context Assembly:** <500ms (retrieval + assembly)
- **Token Optimization:** <100ms (all phases)

### Compression & Adaptation

- **Deduplication:** <10ms
- **Reranking:** <5ms
- **Graph Expansion:** <50ms
- **Architecture Boosting:** <5ms
- **Model Adaptation:** <1ms
- **Quality Logging:** Async (negligible latency)

---

## Limitations & Known Issues

### Phase 2 Limitations

- **Call Graph:** Cannot resolve dynamic calls (getattr, eval, monkey-patching)
- **Namespace Packages:** Advanced PEP 420 patterns may not detect correctly
- **Windows Git:** Temp file issue (non-blocking, doesn't affect functionality)

### Phase 3 Limitations

- **Orchestration:** Requires manual ASES workflow definitions (can be automated in Phase 5)

### Phase 4 Limitations

- **Component 4 (Compressor):** Heuristic truncation, not real LLM (upgrade planned)
- **Component 8 (Metrics):** Baseline from 45/50 repos (5 repos pending)
- **Auto-Tuning:** Requires sufficient logs for correlation (>10 samples per class)

---

## Future Enhancements (Phase 5+)

- IDE extensions (VS Code, JetBrains)
- Real-time collaborative workflows
- Advanced ML-based architecture detection
- Component 4 LLM API integration (real summarization)
- Auto-healing (bug detection + fix suggestions)
- Cross-repo dependency analysis
- Artifact versioning and diff
- Advanced search filters (by type, scope, age)

---

## Summary

Ortho v3 is a complete, production-ready AI engineering platform with:

✅ **Deep repository understanding** (Pillar 1)  
✅ **Persistent knowledge store** (Pillar 2)  
✅ **Architectural reasoning** (Pillar 3)  
✅ **Workflow orchestration** (Pillar 4)  
✅ **Token optimization** (Pillar 5 — fully complete Phase 4)  
✅ **883 tests executed, 100% pass** (verified 2026-07-12 — see `TEST_VERIFICATION_REPORT.md`)  
✅ **Local-first storage** (no cloud dependencies)  
✅ **ASES workflow compliance** (all 5 gates passed)  

Ready for production use and Phase 5 optimization work.
