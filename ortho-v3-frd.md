# ORTHO v3 — Functional Requirements Document
### The Engineering Bible

**Version:** 1.0  
**Status:** Living Document — All Ortho development derives from this FRD  
**Owner:** Solo Engineer  
**Stack:** Python (packages) + TypeScript (CLI)  
**Storage:** Local-first — SQLite + sqlite-vec  
**Interface:** CLI → future IDE extension  
**Methodology:** ASES (AI Software Engineering System)

---

> This document is the single source of truth for Ortho v3.
> Every feature, every package, every architectural decision, every external library,
> every ASES workflow, and every line of code must trace back to something written here.
> If it is not in this document, it does not get built.

---

## Table of Contents

1. Mission and Philosophy
2. System Architecture
3. ASES — The Engineering Operating System
4. Monorepo Structure
5. Shared Foundation
6. Pillar 1 — Repository Intelligence
7. Pillar 2 — ContextHub
8. Pillar 3 — Architectural Intelligence
9. Pillar 4 — Engineering Orchestration
10. Pillar 5 — Token Optimizer
11. Agent and Skill Selector System
12. CLI Design
13. External Libraries and GitHub Repositories
14. Storage Schema
15. Data Flow
16. Development Roadmap
17. Engineering Standards
18. Glossary

---

## 1. Mission and Philosophy

### Mission

Ortho is an AI Engineering Platform.

Its purpose is not to replace Claude or any LLM.

Ortho provides engineering intelligence around LLMs by:
- Understanding repositories deeply
- Managing project knowledge persistently
- Orchestrating engineering workflows intelligently
- Delivering the highest relevance context with the fewest tokens

The LLM is the execution engine. Ortho is the engineering brain.

### Core Philosophy — The 10 Principles

Every decision made during Ortho's development must be evaluated against these principles. If a proposed feature, library, or architectural choice conflicts with more than one principle, it does not belong in Ortho.

| # | Principle | What It Means in Practice |
|---|-----------|--------------------------|
| 1 | Repository understanding before generation | Never prompt an LLM without first scanning the repo |
| 2 | Architecture before implementation | Design interfaces before writing code |
| 3 | Context before prompting | Assemble context through Ortho before any LLM call |
| 4 | Evidence before confidence | Never accept LLM output without verification artifacts |
| 5 | Small composable modules | Each package has one job. No bloat. |
| 6 | Local-first whenever practical | SQLite, no cloud, no account required |
| 7 | Model-agnostic architecture | Claude today, anything tomorrow |
| 8 | Every capability independently usable | No forced coupling between pillars |
| 9 | Simplicity over cleverness | Boring code that works beats clever code that breaks |
| 10 | Build only what serves the mission | The question before every PR: which pillar does this serve? |

---

## 2. System Architecture

### High-Level Flow

```
User Request (CLI)
        ↓
  Intent Router (semantic-router — fast, no LLM)
        ↓
  Orchestrator Agent (LLM — only if ambiguous)
        ↓
  Selector Engine (pure Python — agent + skill selection)
        ↓
  ┌─────────────────────────────────────────┐
  │         Pillar 1           Pillar 2     │
  │   Repository Intelligence  ContextHub   │
  │         Pillar 3                        │
  │   Architectural Intelligence            │
  └─────────────────────────────────────────┘
        ↓
  Context Assembly
        ↓
  Pillar 5 — Token Optimizer
        ↓
  LLM (Claude / GPT / Gemini / Local)
        ↓
  Evidence Collection (ASES)
        ↓
  Human Approval Gate
        ↓
  Engineering Result
```

### Architecture Rules

- The flow is a graph, not a pipeline. The orchestrator can loop — call LLM, retrieve more context, call again.
- The LLM is always the last step. Nothing after it is automated without human approval.
- Each pillar exposes a clean interface. No pillar imports from another pillar directly — they communicate through shared types and the orchestration layer.
- ASES governs the process. Ortho provides the intelligence. These never swap responsibilities.

---

## 3. ASES — The Engineering Operating System

### What ASES Is

ASES (AI Software Engineering System) is the engineering methodology used to build Ortho. It is not part of Ortho's runtime. It is not exposed to users.

ASES is the development process. It answers: "How should software be built?"

Ortho answers: "How can AI better understand and reason about software?"

### The Problem ASES Solves

Without ASES, AI-assisted development collapses into this loop:

```
Feature Request → Claude implements → Claude validates → Next feature → Integration fails
```

The problem is not poor code. The problem is self-validation without external evidence.

ASES breaks this loop by requiring:
- Planning before implementation
- External verification artifacts for every task
- Human approval at defined checkpoints
- Traceable decisions logged as ADRs

### ASES Core Principles

- Evidence is more trustworthy than confidence
- Planning is more valuable than rushing into implementation
- Architecture should guide implementation
- Repository understanding should precede code generation
- Context should be assembled before prompting an LLM
- Human approval remains the final authority
- Every engineering decision must leave a traceable artifact
- Workflows must be repeatable and deterministic

### ASES Workflow Library

ASES workflows live in `ases/workflows/`. They are markdown files. They are the input to Pillar 4's automation engine.

**Core workflows (must exist before Phase 3 begins):**

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `feature-development.md` | New feature request | Plan → Architect → Implement → Test → Review → Evidence → Approve |
| `bug-fix.md` | Bug report | Reproduce → Locate → Fix → Verify → Evidence → Approve |
| `refactor.md` | Refactoring request | Analyze → Plan → Refactor → Verify → Evidence → Approve |
| `architecture-review.md` | Arch question/change | Scan → Model → Analyze → ADR → Approve |
| `analysis.md` | Codebase question | Scan → Retrieve → Synthesize → Report |
| `documentation.md` | Doc generation | Scan → Retrieve → Draft → Review → Approve |
| `code-review.md` | Review request | Retrieve → Analyze → Comment → Evidence |
| `debugging.md` | Unknown bug | Trace → Hypothesize → Verify → Fix → Evidence |

### How to Use ASES Properly

**Rule 1 — Always start with a workflow.**
Before writing a single line of code, identify which ASES workflow applies. Run the workflow steps manually in Phase 1 and 2. Phase 3 automates them.

**Rule 2 — Every task produces evidence.**
Evidence artifacts include: test output, lint results, coverage reports, review notes, approval records. These are stored in ContextHub under artifact type `evidence`.

**Rule 3 — Every architectural decision gets an ADR.**
Any decision about package boundaries, storage design, interface contracts, or library selection must be written as an ADR in `docs/adr/`. ADRs are stored in ContextHub and cross-referenced against code by Pillar 3.

**ADR template:**
```markdown
# ADR-{number}: {Title}

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
What situation prompted this decision?

## Decision
What was decided?

## Consequences
What are the positive and negative consequences?

## Evidence
What justified this decision?
```

**Rule 4 — ASES usage in Phases 1 and 2 is research for Phase 3.**
Every time a workflow step is run manually, log what happened, what decisions were made, and where human intervention was required. This data becomes the training signal for the orchestration engine.

**Rule 5 — The graduation rule.**
An ASES workflow step is ready for automation when:
- It has been run manually at least 5 times
- The steps are deterministic (same input reliably produces same output)
- Evidence artifacts are well-defined
- The human approval points are clearly identified

**Rule 6 — Never automate a bad process.**
If a workflow step consistently requires significant human correction, fix the workflow first. Automating a broken process creates automated failure.

### The Long-Term Vision

```
Today:   Developer + Claude + ASES (as docs/prompts/discipline)
Future:  Developer + Ortho (which internally executes ASES workflows)
```

ASES is simultaneously the methodology used to build Ortho and the blueprint for what Ortho will eventually automate. The product eats its own process.

---

## 4. Monorepo Structure

```
ortho/
├── packages/
│   ├── repo-intelligence/          # Python — AST, symbols, graphs
│   │   ├── src/
│   │   │   ├── adapters/           # Language adapters (python/, typescript/, go/)
│   │   │   ├── scanner.py
│   │   │   ├── symbol_registry.py
│   │   │   ├── call_graph.py
│   │   │   ├── import_graph.py
│   │   │   ├── dependency_graph.py
│   │   │   ├── module_detector.py
│   │   │   └── incremental_indexer.py
│   │   ├── tests/
│   │   ├── benchmarks/
│   │   └── pyproject.toml
│   │
│   ├── context-hub/                # Python — artifact store + retrieval
│   │   ├── src/
│   │   │   ├── store.py
│   │   │   ├── ingestion.py
│   │   │   ├── retrieval.py
│   │   │   ├── search/
│   │   │   │   ├── bm25.py         # SQLite FTS5
│   │   │   │   ├── semantic.py     # sqlite-vec
│   │   │   │   └── hybrid.py       # RRF fusion
│   │   │   ├── git_metadata.py
│   │   │   └── conversation_store.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── arch-intelligence/          # Python — architecture analysis
│   │   ├── src/
│   │   │   ├── arch_detector.py
│   │   │   ├── layer_detector.py
│   │   │   ├── subsystem_detector.py
│   │   │   ├── circular_deps.py
│   │   │   ├── impact_analyzer.py
│   │   │   ├── debt_scorer.py
│   │   │   └── adr_crossref.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   ├── orchestration/              # Python — workflow + agent engine
│   │   ├── src/
│   │   │   ├── intent/
│   │   │   │   ├── router.py       # semantic-router integration
│   │   │   │   └── classifier.py   # LLM fallback classifier
│   │   │   ├── selector/
│   │   │   │   ├── agent_registry.py
│   │   │   │   ├── skill_registry.py
│   │   │   │   └── selector_engine.py
│   │   │   ├── workflow/
│   │   │   │   ├── executor.py
│   │   │   │   ├── planner.py
│   │   │   │   └── state_store.py
│   │   │   ├── agents/
│   │   │   │   └── orchestrator.py
│   │   │   └── evidence.py
│   │   ├── tests/
│   │   └── pyproject.toml
│   │
│   └── token-optimizer/            # Python — context ranking + assembly
│       ├── src/
│       │   ├── ranker.py
│       │   ├── deduplicator.py
│       │   ├── compressor.py
│       │   ├── budget_manager.py
│       │   ├── graph_expander.py
│       │   ├── prompt_assembler.py
│       │   └── quality_logger.py
│       ├── tests/
│       └── pyproject.toml
│
├── shared/
│   ├── types/                      # TypeScript — canonical data models
│   │   ├── src/
│   │   │   ├── repository.ts
│   │   │   ├── symbol.ts
│   │   │   ├── artifact.ts
│   │   │   ├── architecture.ts
│   │   │   ├── workflow.ts
│   │   │   ├── context.ts
│   │   │   └── llm.ts
│   │   └── package.json
│   │
│   ├── interfaces/                 # TypeScript — cross-package contracts
│   │   └── src/
│   │       ├── ISymbolProvider.ts
│   │       ├── IArtifactStore.ts
│   │       ├── IArchitectureModel.ts
│   │       ├── IContextAssembler.ts
│   │       ├── IWorkflowExecutor.ts
│   │       └── ILanguageAdapter.ts
│   │
│   ├── storage/                    # Python — SQLite abstractions
│   │   └── src/
│   │       ├── database.py
│   │       ├── vector_store.py
│   │       ├── migrations/
│   │       └── config.py
│   │
│   └── utils/                     # Python + TS utilities
│       ├── logging.py
│       ├── errors.py
│       └── token_counter.py
│
├── apps/
│   ├── cli/                        # TypeScript — user-facing CLI
│   │   ├── src/
│   │   │   ├── commands/
│   │   │   │   ├── init.ts
│   │   │   │   ├── scan.ts
│   │   │   │   ├── index.ts
│   │   │   │   ├── context.ts
│   │   │   │   ├── analyze.ts
│   │   │   │   ├── run.ts
│   │   │   │   ├── status.ts
│   │   │   │   └── history.ts
│   │   │   └── index.ts
│   │   └── package.json
│   │
│   └── api-server/                 # Python — FastAPI (local server)
│       ├── src/
│       │   ├── main.py
│       │   └── routers/
│       └── pyproject.toml
│
├── ases/
│   ├── workflows/                  # ASES workflow .md files
│   ├── agents/                     # Agent persona .md files
│   │   ├── core/                   # Built-in agents
│   │   └── custom/                 # User-defined agents
│   ├── skills/                     # Skill .md files
│   │   ├── core/                   # Built-in skills
│   │   └── custom/                 # User-defined skills
│   └── templates/                  # Task templates
│
├── docs/
│   ├── adr/                        # Architecture Decision Records
│   └── architecture/               # Architecture docs
│
├── tests/
│   └── fixtures/                   # Fixture repo for integration tests
│       └── sample-python-project/
│
└── pyproject.toml                  # Root workspace config
```

### Dependency Rules

Dependencies flow in one direction only:

```
cli → api-server → orchestration → [repo-intelligence, context-hub, arch-intelligence] → shared
token-optimizer → shared
```

No package imports from a package above it in this chain. No circular dependencies between packages. Shared packages (`shared/types`, `shared/storage`, `shared/utils`) may be imported by any package. They import nothing from the pillar packages.

---

## 5. Shared Foundation

### Shared Types (TypeScript)

These are the canonical data models. Every pillar uses these. When a type is unclear, define it here first, then implement it.

```typescript
// repository.ts
interface Repository {
  id: string;           // hash(root_path)
  root_path: string;
  name: string;
  languages: Language[];
  indexed_at: Date;
  git_remote?: string;
}

interface File {
  id: string;           // hash(repo_id + rel_path)
  repo_id: string;
  rel_path: string;
  language: Language;
  size_bytes: number;
  last_modified: Date;
  git_last_commit?: string;
}

// symbol.ts
interface Symbol {
  id: string;           // hash(repo_id + file_id + name + kind)
  repo_id: string;
  file_id: string;
  name: string;
  qualified_name: string;   // module.class.method
  kind: SymbolKind;         // function | class | method | variable | constant | type
  visibility: Visibility;   // public | private | protected | internal
  start_line: number;
  end_line: number;
  docstring?: string;
  signature?: string;
}

interface CallEdge {
  caller_id: string;    // Symbol.id
  callee_id: string;    // Symbol.id
  call_site_line: number;
  confidence: number;   // 0.0 - 1.0 (static analysis is probabilistic)
}

interface ImportEdge {
  importer_file_id: string;
  imported_file_id?: string;
  imported_module: string;
  is_external: boolean;
  symbols_imported: string[];
}

// artifact.ts
type ArtifactType =
  | 'frd' | 'adr' | 'architecture' | 'spec' | 'decision'
  | 'lesson_learned' | 'dev_note' | 'benchmark' | 'conversation'
  | 'git_metadata' | 'project_memory' | 'evidence' | 'workflow_run';

interface Artifact {
  id: string;
  repo_id: string;
  type: ArtifactType;
  title: string;
  content: string;
  source: string;           // file path, git commit, 'manual', 'generated'
  created_at: Date;
  last_modified: Date;
  relevance_scope: 'global' | 'project' | 'module' | 'file';
  tags: string[];
  related_symbols?: string[];   // Symbol.id references
  embedding?: number[];         // stored in sqlite-vec
  estimated_tokens: number;     // pre-computed for budget management
}

// architecture.ts
interface ArchitectureModel {
  repo_id: string;
  style: ArchStyle;           // layered | hexagonal | mvc | microservices | flat | unknown
  style_confidence: number;
  layers: Layer[];
  subsystems: Subsystem[];
  service_boundaries: ServiceBoundary[];
  detected_at: Date;
}

interface Layer {
  id: string;
  name: string;
  file_ids: string[];
  depends_on: string[];       // Layer.id references
  confidence: number;
  evidence: string[];
}

interface Subsystem {
  id: string;
  name: string;
  file_ids: string[];
  layer_id?: string;
  coupling_score: number;     // 0.0 (loose) - 1.0 (tight)
}

// workflow.ts
interface WorkflowRun {
  id: string;
  repo_id: string;
  intent: string;
  intent_class: string;
  execution_plan: ExecutionPlan;
  status: 'pending' | 'running' | 'awaiting_approval' | 'approved' | 'rejected' | 'complete' | 'failed';
  started_at: Date;
  completed_at?: Date;
  evidence: Evidence[];
}

interface ExecutionPlan {
  intent_class: string;
  steps: ExecutionStep[];
  total_estimated_tokens: number;
  human_approval_required: boolean;
  approval_reason?: string;
}

interface ExecutionStep {
  step_id: string;
  agent_name: string;
  skill_names: string[];
  context_package_id: string;
  receives_from?: string;       // prior step_id
  produces: string;             // output key
  approval_gate: boolean;
  status: 'pending' | 'running' | 'complete' | 'failed';
}

interface Evidence {
  type: 'test_output' | 'lint_result' | 'coverage' | 'review_note' | 'approval';
  content: string;
  produced_at: Date;
  step_id: string;
}

// context.ts
interface ContextChunk {
  id: string;
  source_type: 'symbol' | 'artifact' | 'git' | 'architecture';
  source_id: string;
  content: string;
  relevance_score: number;
  token_count: number;
  included: boolean;
}

interface TokenBudget {
  total: number;
  used: number;
  remaining: number;
  model: string;
}

interface ContextPackage {
  id: string;
  workflow_run_id: string;
  step_id: string;
  chunks: ContextChunk[];
  budget: TokenBudget;
  assembled_at: Date;
}

// llm.ts
interface LLMRequest {
  model: string;
  system_prompt: string;
  context_package_id: string;
  user_message: string;
  max_tokens: number;
  temperature: number;
}

interface LLMResponse {
  model: string;
  content: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  stop_reason: string;
}
```

### Shared Storage (Python)

```python
# database.py
class OrthoDatabase:
    """Single SQLite connection manager for the .ortho/ directory."""
    
    def __init__(self, project_root: Path):
        self.db_path = project_root / '.ortho' / 'ortho.db'
        self.vec_path = project_root / '.ortho' / 'vectors.db'
    
    def migrate(self) -> None:
        """Run all pending migrations in order."""
        ...
    
    def connection(self) -> sqlite3.Connection:
        """Returns a connection with WAL mode and foreign keys enabled."""
        ...

# vector_store.py  
class VectorStore:
    """sqlite-vec wrapper for embedding storage and KNN search."""
    
    def upsert(self, id: str, embedding: list[float], metadata: dict) -> None: ...
    def search(self, query_embedding: list[float], k: int, filter: dict) -> list[SearchResult]: ...
    def delete(self, id: str) -> None: ...
```

### OrthoConfig

Every project has a `.ortho/config.toml`:

```toml
[project]
name = "my-project"
root = "."
primary_language = "python"

[indexing]
languages = ["python", "typescript"]
exclude_patterns = ["**/node_modules/**", "**/__pycache__/**", "**/dist/**"]
incremental = true

[context_hub]
embedding_model = "text-embedding-3-small"
embedding_provider = "openai"  # openai | local | ollama

[llm]
default_model = "claude-sonnet-4-6"
fallback_model = "claude-haiku-4-5-20251001"
max_tokens = 8192

[orchestration]
human_approval = true
approval_timeout_seconds = 300

[token_optimizer]
default_budget = 16000
compression_threshold = 0.6
```

---

## 6. Pillar 1 — Repository Intelligence

### Purpose

Understand a software repository. Answer the question: "What exists inside this repository?"

### Features

| Feature | Description | Phase |
|---------|-------------|-------|
| `repo scan` | Walk file tree, detect languages, build file manifest | 1 |
| `ast extract` | Parse source files into AST using tree-sitter | 1 |
| `symbol extract` | Pull functions, classes, methods, variables, exports | 1 |
| `symbol registry` | Persist symbols with location, type, visibility, docstring | 1 |
| `import graph` | Track what each module imports and from where | 1 |
| `dependency graph` | Project-level external deps (requirements.txt, package.json) | 1 |
| `call graph` | Build directed graph of function calls across files | 1 |
| `module detector` | Identify logical modules from directory + naming patterns | 1 |
| `incremental indexer` | Diff-based re-indexing on file changes | 1 |
| `language adapter interface` | Plugin contract for new language support | 1 |
| TypeScript adapter | Full support for TypeScript repos | 2 |

### Language Adapter Interface

Every language is a plugin. The core engine is language-agnostic.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

class LanguageAdapter(ABC):
    """Plugin contract for language support in Repository Intelligence."""
    
    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier: 'python', 'typescript', 'go'"""
        ...
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """File extensions this adapter handles: ['.py', '.pyi']"""
        ...
    
    @abstractmethod
    def extract_symbols(self, file_path: Path, source: str) -> list[Symbol]:
        """Extract all symbols from source code."""
        ...
    
    @abstractmethod
    def extract_imports(self, file_path: Path, source: str) -> list[ImportEdge]:
        """Extract all import statements."""
        ...
    
    @abstractmethod
    def extract_calls(self, file_path: Path, source: str, symbols: list[Symbol]) -> list[CallEdge]:
        """Extract function call relationships."""
        ...
    
    @abstractmethod
    def chunk(self, file_path: Path, source: str, max_chunk_size: int) -> list[ContextChunk]:
        """Split source into AST-aware chunks for context retrieval."""
        ...
```

### Symbol ID Stability Rule

Every symbol gets a stable `symbol_id`:

```python
def make_symbol_id(repo_id: str, file_rel_path: str, name: str, kind: str) -> str:
    return hashlib.sha256(f"{repo_id}:{file_rel_path}:{name}:{kind}".encode()).hexdigest()[:16]
```

This ID is the foreign key used everywhere — ContextHub, Arch Intelligence, Token Optimizer all reference symbols by this ID. Never by raw string names. This survives file renames if you track the mapping.

### Incremental Indexing Strategy

```python
class IncrementalIndexer:
    def get_changed_files(self, since_commit: str) -> list[ChangedFile]:
        """Use git diff to find changed files since last index."""
        # git diff --name-status {since_commit} HEAD
        ...
    
    def reindex_files(self, changed: list[ChangedFile]) -> IndexResult:
        """Only reindex what changed. Update symbol registry and graphs."""
        # ADDED: full extraction
        # MODIFIED: delete old symbols, re-extract
        # DELETED: remove symbols from registry
        ...
```

Phase 1 uses git diff. If not a git repo, falls back to file mtime comparison.

---

## 7. Pillar 2 — ContextHub

### Purpose

Persist and organize all engineering knowledge. Answer the question: "What do we already know?"

### Features

| Feature | Description | Phase |
|---------|-------------|-------|
| Artifact store | Ingest and persist typed engineering artifacts | 1 |
| Ingestion contract | Validate artifact metadata before storage | 1 |
| BM25 full-text search | SQLite FTS5 keyword search | 1 |
| Semantic search | sqlite-vec embedding similarity search | 1 |
| Hybrid search | RRF fusion of BM25 + semantic | 1 |
| Git metadata store | Commit history, file churn, branch info | 1 |
| Project memory | Structured key/value project facts | 1 |
| Conversation store | Persist past AI sessions with context snapshots | 1 |
| Artifact versioning | Track changes to artifacts over time | 2 |
| Staleness detector | Flag artifacts whose source has changed | 2 |

### Ingestion Contract

Every artifact that enters ContextHub must pass this validation:

```python
@dataclass
class ArtifactIngestionRequest:
    type: ArtifactType          # Required — must be a known type
    title: str                  # Required — non-empty
    content: str                # Required — non-empty
    source: str                 # Required — file path, 'manual', 'generated', git SHA
    relevance_scope: str        # Required — 'global' | 'project' | 'module' | 'file'
    tags: list[str]             # Required — can be empty list
    related_symbols: list[str]  # Optional — Symbol.id references
    
def validate_ingestion(req: ArtifactIngestionRequest) -> ValidationResult:
    """Reject artifacts that don't meet the contract. No silent failures."""
    ...
```

ContextHub never interprets artifacts. It stores and retrieves. Interpretation belongs to Arch Intelligence and the Orchestrator.

### Hybrid Search — RRF Fusion

```python
def hybrid_search(
    query: str,
    query_embedding: list[float],
    limit: int = 10,
    type_filter: list[ArtifactType] | None = None,
    scope_filter: str | None = None,
) -> list[ArtifactSearchResult]:
    
    # BM25 results from SQLite FTS5
    bm25_results = bm25_search(query, limit=limit * 2, filters=...)
    
    # Semantic results from sqlite-vec
    semantic_results = semantic_search(query_embedding, k=limit * 2, filters=...)
    
    # Reciprocal Rank Fusion
    # score(d) = sum(1 / (k + rank(d))) for each result list
    # k=60 is standard RRF constant
    return rrf_merge(bm25_results, semantic_results, k=60, limit=limit)
```

### Project Memory

```python
class ProjectMemory:
    """Structured key/value store for project-level facts."""
    
    def set(self, key: str, value: str, source: str = 'manual') -> None:
        """Store a project fact. Examples:
        - set('primary_language', 'python')
        - set('test_framework', 'pytest')
        - set('api_style', 'REST')
        - set('auth_approach', 'JWT')
        """
        ...
    
    def get(self, key: str) -> str | None: ...
    def list_all(self) -> dict[str, str]: ...
```

---

## 8. Pillar 3 — Architectural Intelligence

### Purpose

Understand how the repository works. Answer: "How does everything fit together?"

### Features

| Feature | Description | Phase |
|---------|-------------|-------|
| Architecture detector | Infer style (layered/hexagonal/mvc/flat) with confidence | 2 |
| Layer detector | Identify logical layers from import patterns + naming | 2 |
| Subsystem detector | Cluster related modules into named subsystems | 2 |
| Service boundary detector | Find seams between subsystems | 2 |
| Circular dependency detector | Identify cycles in call/import graph | 2 |
| Change impact analyzer | Blast radius for a file/symbol change | 2 |
| Dependency health analyzer | Flag tightly coupled or high-fan-in deps | 2 |
| Technical debt scorer | Heuristic score per module | 2 |
| Reuse discovery | Find similar code patterns across files | 2 |
| ADR awareness | Cross-reference ADRs against actual code | 2 |

### Confidence Scores — Mandatory

Every detection result carries a confidence score and evidence list. There are no binary architecture assertions.

```python
@dataclass
class ArchitectureDetectionResult:
    style: ArchStyle
    confidence: float           # 0.0 - 1.0
    evidence: list[str]         # Human-readable justifications
    alternative: ArchStyle | None
    alternative_confidence: float | None
```

### Change Impact Analysis

```python
class ImpactAnalyzer:
    def analyze(
        self,
        changed_file_id: str,
        depth: int = 3,         # How many hops in the call graph to follow
    ) -> ImpactReport:
        """
        Given a file, traverse the call graph outward to find
        all files/symbols that depend on it.
        
        Returns:
        - direct_dependents: files that directly import changed_file
        - transitive_dependents: files reachable within `depth` hops
        - risk_score: 0.0-1.0 based on centrality of changed file
        - blast_radius: total count of affected files
        """
        ...
```

### Technical Debt Scorer

```python
@dataclass
class DebtScore:
    module_id: str
    total_score: float          # 0.0 (clean) - 1.0 (critical)
    coupling_score: float       # Fan-in + fan-out ratio
    churn_score: float          # How often this file changes (git)
    complexity_score: float     # AST depth / function count
    test_coverage_score: float  # Inverse of test presence heuristic
    evidence: list[str]
```

---

## 9. Pillar 4 — Engineering Orchestration

### Purpose

Coordinate engineering work. This is the decision engine of Ortho. Answer: "What should be done and how?"

### The Orchestrator Never Generates Code

The orchestration engine coordinates. It assembles context, selects agents, issues prompts, and validates output. Code generation is entirely the LLM's job. This line must never be crossed.

### Features

| Feature | Description | Phase |
|---------|-------------|-------|
| Intent router (semantic) | Fast no-LLM intent classification via semantic-router | 3 |
| Intent classifier (LLM fallback) | LLM classification for ambiguous intents | 3 |
| Workflow registry | Load and register ASES workflows from `ases/workflows/` | 3 |
| Agent registry | Discover and register agent `.md` files | 3 |
| Skill registry | Discover and register skill `.md` files | 3 |
| Selector engine | Score and select agents + skills per intent | 3 |
| Workflow executor | Run workflows step by step with state | 3 |
| Task planner | Break complex intents into sub-tasks | 3 |
| Context request builder | Specify what Pillars 1-3 data a task needs | 3 |
| Model router | Select LLM based on task type and cost | 3 |
| Human approval gate | Pause and request human sign-off | 3 |
| Evidence collector | Gather verification artifacts after each step | 3 |
| Workflow state store | Persist state for interrupted workflow resumption | 3 |

---

## 10. Pillar 5 — Token Optimizer

### Purpose

Deliver the highest quality context using the fewest possible tokens. Maximize Engineering Value per Token.

### Features

| Feature | Description | Phase |
|---------|-------------|-------|
| Intent-aware reranker | Rescore context chunks by task intent | 4 |
| Duplicate remover | Detect and remove semantically overlapping chunks | 4 |
| Graph expander | Pull symbol call-graph neighbors to configurable depth | 4 |
| Token budget manager | Enforce hard ceiling with priority ranking | 4 |
| Context compressor | Summarize low-priority chunks when over budget | 4 |
| Architecture-aware retrieval | Weight architecturally central modules higher | 4 |
| Model context adapter | Per-model prompt assembly strategy | 4 |
| Prompt assembler | Combine system + context + task into final prompt | 4 |
| Context quality logger | Log what was sent + what returned for tuning | 4 |

### Token Budget Interface — Define in Phase 1

Even though the full optimizer isn't built until Phase 4, define this interface during Phase 1. Every pillar's output carries estimated token counts from day one.

```python
@dataclass
class TokenBudget:
    total: int
    used: int
    model: str
    
    @property
    def remaining(self) -> int:
        return self.total - self.used
    
    def can_fit(self, tokens: int) -> bool:
        return tokens <= self.remaining
    
    def consume(self, tokens: int) -> None:
        if not self.can_fit(tokens):
            raise BudgetExceededError(f"Cannot fit {tokens} tokens — {self.remaining} remaining")
        self.used += tokens
```

---

## 11. Agent and Skill Selector System

### Overview

When `ortho run "add rate limiting to the auth service"` is called, four questions must be answered automatically:

1. What is the intent? (feature development, bug fix, refactor, analysis...)
2. Which agents should handle it?
3. Which skills does each agent need?
4. In what order do they execute?

This is answered by a two-stage system: a fast semantic router (no LLM cost) followed by the Selector Engine.

### Stage 1 — Intent Router (semantic-router)

Fast first-pass classification. No LLM call. Sub-10ms.

```python
from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder

# Routes are loaded from ASES workflow .md frontmatter
# The utterances come from real examples logged during ASES Phase 1 + 2 usage
feature_dev = Route(
    name="feature_development",
    utterances=[
        "add rate limiting to the auth service",
        "implement a new endpoint for user preferences",
        "build a caching layer for the API",
        "create a new module for email notifications",
    ]
)

bug_fix = Route(
    name="bug_fix",
    utterances=[
        "fix the null pointer in the payment service",
        "users are getting 500 errors on checkout",
        "the login is broken after the last deploy",
    ]
)

refactor = Route(
    name="refactor",
    utterances=[
        "the auth module is too tightly coupled",
        "extract the database logic into a repository pattern",
        "reduce the complexity in the order service",
    ]
)

analysis = Route(
    name="analysis",
    utterances=[
        "what is the blast radius if I change the user model",
        "show me the architecture of the payment system",
        "which modules have the highest technical debt",
    ]
)

# HuggingFaceEncoder = fully local, no API key needed
router = SemanticRouter(
    encoder=HuggingFaceEncoder(name="BAAI/bge-small-en-v1.5"),
    routes=[feature_dev, bug_fix, refactor, analysis, ...],
    auto_sync="local"
)

def classify_intent(user_input: str) -> IntentClassification:
    route = router(user_input)
    
    if route.name is None or route.similarity_score < 0.7:
        # Ambiguous — fall back to LLM classifier
        return llm_classify_intent(user_input)
    
    return IntentClassification(
        type=route.name,
        confidence=route.similarity_score,
        method="semantic_router"
    )
```

**Utterance sourcing:** During Phases 1 and 2, log every user command to `ases/router_training/`. These become the utterances for production routes. Real usage, not invented examples.

### Stage 2 — Agent Registry

Agents live in `ases/agents/`. Built-in agents in `core/`. User-defined in `custom/`.

**Agent .md frontmatter schema:**

```yaml
---
name: architect
display_name: Architect Agent
description: Designs system architecture, evaluates trade-offs, writes ADRs, detects service boundaries
intent_triggers:
  - feature_development
  - refactor
  - new_service
  - architecture_review
skills_preferred:
  - repo-analysis
  - adr-writer
  - impact-analyzer
priority: high
requires_context:
  - architecture_model
  - dependency_graph
  - adr_store
---
```

Everything below the frontmatter is the LLM system prompt for this agent.

**Core agents:**

| Agent file | Role | Intent triggers |
|-----------|------|-----------------|
| `orchestrator.md` | Plans execution, selects agents/skills | All intents |
| `architect.md` | System design, ADRs, boundaries | feature_development, refactor, architecture_review |
| `coder.md` | Implementation, code generation | feature_development, bug_fix |
| `reviewer.md` | Code review, standards compliance | After any code generation |
| `tester.md` | Test strategy, test generation | feature_development, bug_fix |
| `analyst.md` | Repo analysis, impact, debt | analysis, before large changes |
| `documenter.md` | Docs, ADRs, specs, changelogs | documentation |
| `debugger.md` | Root cause analysis, tracing | bug_fix, debugging |

### Stage 3 — Skill Registry

Skills live in `ases/skills/`. Same two-tier model.

**Skill .md frontmatter schema:**

```yaml
---
name: adr-writer
display_name: ADR Writer
description: Enables the agent to produce well-structured Architecture Decision Records following the project ADR template
agent_types:
  - architect
  - documenter
intent_triggers:
  - architecture_review
  - new_service
  - refactor
provides:
  - adr_format
  - decision_framework
  - trade_off_analysis
estimated_tokens: 800
---
```

Everything below the frontmatter is the skill content injected into the agent's context alongside its system prompt.

**Core skills:**

| Skill file | What it provides | Primary agents |
|-----------|-----------------|----------------|
| `repo-analysis.md` | How to read Ortho's repo intelligence output | All |
| `adr-writer.md` | ADR format and decision criteria | architect, documenter |
| `impact-analyzer.md` | How to use Ortho's change impact data | architect, analyst |
| `test-generator.md` | Test strategy patterns and coverage requirements | tester |
| `code-reviewer.md` | Review checklist and common failure patterns | reviewer |
| `context-retriever.md` | How to request additional context mid-task | All |
| `git-analyst.md` | How to interpret git metadata and churn data | analyst |
| `debt-analyzer.md` | Technical debt scoring interpretation | analyst |
| `spec-writer.md` | FRD/spec format and completeness criteria | architect, documenter |
| `debug-tracer.md` | Root cause analysis methodology | debugger |

### Stage 4 — Selector Engine

Pure Python. No LLM. Scores agents and skills, builds the execution plan.

```python
def score_agent(
    agent: AgentManifest,
    intent: IntentClassification,
    available_context: list[str],
) -> float:
    score = 0.0
    
    # Direct intent trigger match
    if intent.type in agent.intent_triggers:
        score += 1.0
    
    # Semantic similarity (intent keywords vs agent description)
    score += semantic_similarity(intent.raw_text, agent.description) * 0.5
    
    # Priority weight
    score += {"high": 0.3, "medium": 0.15, "low": 0.0}[agent.priority]
    
    # Penalize if required context is unavailable
    for ctx in agent.requires_context:
        if ctx not in available_context:
            score -= 0.2
    
    return max(0.0, score)


def score_skill(
    skill: SkillManifest,
    agent: AgentManifest,
    intent: IntentClassification,
    remaining_token_budget: int,
) -> float:
    # Hard exclude if over token budget
    if skill.estimated_tokens > remaining_token_budget:
        return 0.0
    
    score = 0.0
    
    if agent.name in skill.agent_types:
        score += 0.8
    
    if intent.type in skill.intent_triggers:
        score += 0.6
    
    if skill.name in agent.skills_preferred:
        score += 0.4
    
    return score


def build_execution_plan(
    intent: IntentClassification,
    agent_scores: dict[str, float],
    skill_scores: dict[str, dict[str, float]],
    token_budget: TokenBudget,
) -> ExecutionPlan:
    # Select top agents above threshold
    selected_agents = [
        a for a, score in sorted(agent_scores.items(), key=lambda x: -x[1])
        if score >= 0.5
    ]
    
    # Build ordered steps (Architect first, Coder second, Tester/Reviewer last)
    steps = order_agents_by_workflow(selected_agents, intent.type)
    
    # Assign skills per agent
    for step in steps:
        agent = get_agent(step.agent_name)
        step.skill_names = [
            skill for skill, score in sorted(
                skill_scores[agent.name].items(), key=lambda x: -x[1]
            )
            if score > 0.3
        ]
    
    return ExecutionPlan(
        intent_class=intent.type,
        steps=steps,
        total_estimated_tokens=sum_token_estimates(steps),
        human_approval_required=requires_approval(intent.type),
    )
```

### Full Execution Flow

```
ortho run "add rate limiting to the auth service"

Step 1: semantic-router classifies intent
        → "feature_development" (confidence: 0.91)

Step 2: Selector Engine scores all agents
        → architect: 1.8, coder: 1.5, tester: 1.2, reviewer: 1.1, analyst: 0.9

Step 3: Selector Engine scores skills per agent
        → architect gets: [repo-analysis, impact-analyzer, adr-writer]
        → coder gets: [repo-analysis, context-retriever]
        → tester gets: [test-generator]
        → reviewer gets: [code-reviewer]

Step 4: Execution plan built
        → Step 1: architect (design + ADR) → human approval gate
        → Step 2: coder (implement) → human approval gate  
        → Step 3: tester (write tests) → evidence collected
        → Step 4: reviewer (review) → evidence collected → human approval gate

Step 5: Token Optimizer assembles context for Step 1
        → Retrieves: auth module symbols, architecture model, existing middleware ADRs
        → Ranks, deduplicates, compresses to fit budget

Step 6: architect agent called with:
        system_prompt = orchestrator.md content
        + architect.md system prompt
        + [repo-analysis.md, impact-analyzer.md, adr-writer.md] injected as skills
        + assembled context package
        + user task

Step 7: LLM returns architectural plan + ADR draft

Step 8: Evidence collected, human approval requested

Step 9: On approval, proceed to Step 2 (coder)...
```

---

## 12. CLI Design

### Commands

```bash
# Initialization
ortho init                          # Set up .ortho/ in current directory

# Repository Intelligence
ortho scan                          # Scan and index the repository
ortho scan --watch                  # Watch mode — re-index on changes
ortho index --since HEAD~1          # Re-index only what changed since commit

# ContextHub
ortho context add <file>            # Ingest a markdown artifact
ortho context add --type adr <file> # Ingest with explicit type
ortho context search "<query>"      # Hybrid search across all artifacts
ortho context list                  # List all artifacts
ortho context stats                 # Storage statistics

# Architectural Intelligence
ortho analyze                       # Full architecture report
ortho analyze --impact <file>       # Change impact for a specific file
ortho analyze --debt                # Technical debt report
ortho analyze --deps                # Dependency health report

# Orchestration
ortho run "<intent>"                # Main entry point — runs full ASES workflow
ortho run --dry-run "<intent>"      # Show execution plan without running
ortho status                        # Show active workflow state
ortho approve                       # Approve the pending human gate
ortho reject "<reason>"             # Reject with reason
ortho history                       # Show past workflow runs
ortho history --id <run_id>         # Show details for a specific run

# Debugging
ortho debug run "<intent>"          # Show full context assembled for any command
ortho debug context "<query>"       # Show what context would be retrieved

# Configuration
ortho config show                   # Show current config
ortho config set <key> <value>      # Set a config value
```

### CLI Architecture

The CLI is thin TypeScript (commander.js). All logic lives in the Python packages via the local API server.

```typescript
// Every CLI command calls the local FastAPI server
// This means the IDE extension later just calls the same endpoints
async function runCommand(intent: string, options: RunOptions) {
  const response = await fetch('http://localhost:17234/api/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ intent, options })
  });
  return response.json();
}
```

The API server runs as a background process started by `ortho init` and managed as a local daemon.

---

## 13. External Libraries and GitHub Repositories

This section is authoritative. These are the only external libraries approved for use in Ortho. Any new library must be added here via an ADR.

---

### Repo 1 — AST Code Chunking

**Library:** `astchunk`  
**GitHub:** https://github.com/yilinjz/astchunk  
**License:** MIT  
**Install:** `pip install astchunk`  
**Use in:** `packages/repo-intelligence/` — symbol chunking for context retrieval  

**What it does:** AST-based code chunking that preserves syntactic structure and semantic boundaries. Recursively breaks large AST nodes into smaller chunks while merging siblings. Prevents the common failure where fixed-size chunking breaks function definitions mid-way, causing LLMs to generate incorrect code.

**What to copy:**
```python
from astchunk import ASTChunkBuilder

def chunk_file(file_path: Path, source: str, language: str) -> list[ContextChunk]:
    builder = ASTChunkBuilder({
        "max_chunk_size": 1500,      # characters — tune per model
        "language": language,         # "python" | "typescript" | "java"
        "metadata_template": "default",
        "repo_level_metadata": {
            "filepath": str(file_path)
        },
        "chunk_expansion": True       # adds scope ancestry header to each chunk
    })
    
    raw_chunks = builder.chunkify(source)
    
    return [
        ContextChunk(
            id=make_chunk_id(file_path, i),
            source_type="symbol",
            source_id=extract_symbol_id(chunk['metadata']),
            content=chunk['content'],
            relevance_score=0.0,       # scored later by Token Optimizer
            token_count=count_tokens(chunk['content']),
            included=False
        )
        for i, chunk in enumerate(raw_chunks)
    ]
```

**Integration point:** Called by `LanguageAdapter.chunk()` for each source file during indexing. Chunks are stored in ContextHub and retrieved by the Token Optimizer.

---

### Repo 2 — Call Graph Generation

**Library:** `pyan3`  
**GitHub:** https://github.com/Technologicat/pyan  
**License:** LGPL-2.1  
**Install:** `pip install pyan3`  
**Use in:** `packages/repo-intelligence/` — Python call graph builder  

**What it does:** Static call graph generator for Python. Reads source code and constructs a directed graph showing which functions call which other functions. Supports modern Python (3.10–3.14) including walrus operators, match statements, async/await. Exposes a Python API for programmatic use.

**What to copy:**
```python
import pyan

def build_python_call_graph(repo_root: Path, file_paths: list[Path]) -> list[CallEdge]:
    # Generate module dependency graph as structured data
    call_graph_data = pyan.create_callgraph(
        filenames=[str(f) for f in file_paths],
        root=str(repo_root),
        no_defines=True,    # only show call edges, not definition edges
        draw_uses=True,
        grouped=True,
    )
    
    edges = []
    for caller, callee in call_graph_data.edges():
        edges.append(CallEdge(
            caller_id=resolve_symbol_id(caller, repo_root),
            callee_id=resolve_symbol_id(callee, repo_root),
            call_site_line=-1,          # pyan doesn't give line numbers
            confidence=0.8              # static analysis confidence
        ))
    
    return edges
```

**Limitation:** pyan uses static analysis — it cannot resolve dynamic calls, monkey-patching, or runtime-determined callees. All CallEdge confidence values should be < 1.0. Ortho's UI must communicate this uncertainty.

**TypeScript alternative:** Use `code2flow` (https://github.com/scottrogowski/code2flow) for JavaScript/TypeScript call graphs.

---

### Repo 3 — Vector Search (ContextHub)

**Library:** `sqlite-vec`  
**GitHub:** https://github.com/asg017/sqlite-vec  
**License:** Apache-2.0  
**Install:** `pip install sqlite-vec`  
**Use in:** `packages/context-hub/` + `shared/storage/`  

**What it does:** A vector search SQLite extension that runs everywhere. Stores embeddings as SQLite virtual tables and performs KNN-style similarity search. Stays inside the `.ortho/` SQLite file — zero external dependencies.

**What to copy:**
```python
import sqlite3
import sqlite_vec
import struct

def init_vector_store(db: sqlite3.Connection) -> None:
    """Load sqlite-vec extension and create vector tables."""
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS artifact_embeddings USING vec0(
            artifact_id TEXT PRIMARY KEY,
            embedding FLOAT[1536]
        )
    """)

def upsert_embedding(
    db: sqlite3.Connection,
    artifact_id: str,
    embedding: list[float]
) -> None:
    # sqlite-vec accepts JSON or compact binary
    embedding_bytes = struct.pack(f'{len(embedding)}f', *embedding)
    db.execute(
        "INSERT OR REPLACE INTO artifact_embeddings(artifact_id, embedding) VALUES (?, ?)",
        (artifact_id, embedding_bytes)
    )

def semantic_search(
    db: sqlite3.Connection,
    query_embedding: list[float],
    k: int = 10,
) -> list[tuple[str, float]]:
    """Returns list of (artifact_id, distance) sorted by similarity."""
    query_bytes = struct.pack(f'{len(query_embedding)}f', *query_embedding)
    results = db.execute("""
        SELECT artifact_id, distance
        FROM artifact_embeddings
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
    """, (query_bytes, k)).fetchall()
    return results
```

**Embedding generation:** Use the Anthropic embeddings API (model: `voyage-code-3` for code, `voyage-3-lite` for docs). Store in sqlite-vec. For fully local mode, use `sqlite-lembed` with a local `.gguf` embedding model.

---

### Repo 4 — Intent Routing

**Library:** `semantic-router`  
**GitHub:** https://github.com/aurelio-labs/semantic-router  
**License:** MIT  
**Install:** `pip install semantic-router`  
**Use in:** `packages/orchestration/src/intent/router.py`  

**What it does:** Superfast intent classification using semantic vector space. Cuts routing time from seconds (LLM call) to milliseconds (embedding lookup). Routes user intent to predefined categories without an LLM call.

**What to copy:**
```python
from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder
import yaml
from pathlib import Path

def load_routes_from_workflows(workflow_dir: Path) -> list[Route]:
    """
    Load Route objects from ASES workflow .md frontmatter.
    Each workflow defines its own semantic trigger examples.
    """
    routes = []
    for md_file in workflow_dir.glob("*.md"):
        with open(md_file) as f:
            content = f.read()
        
        # Parse frontmatter
        if content.startswith("---"):
            frontmatter = yaml.safe_load(content.split("---")[1])
            if "router_utterances" in frontmatter:
                routes.append(Route(
                    name=frontmatter["name"],
                    utterances=frontmatter["router_utterances"]
                ))
    return routes

def build_intent_router(workflow_dir: Path) -> SemanticRouter:
    routes = load_routes_from_workflows(workflow_dir)
    return SemanticRouter(
        encoder=HuggingFaceEncoder(name="BAAI/bge-small-en-v1.5"),  # local, fast
        routes=routes,
        auto_sync="local"       # persists route vectors to disk
    )
```

**ASES workflow frontmatter addition:**
Add `router_utterances` to each ASES workflow `.md` file:

```yaml
---
name: feature_development
display_name: Feature Development
# ... existing frontmatter ...
router_utterances:
  - "add rate limiting to the auth service"
  - "implement a new endpoint for user preferences"
  - "build a caching layer for the API"
  # Add real examples from Phase 1+2 usage logs
---
```

---

### Repo 5 — Code2Flow (TypeScript call graph)

**Library:** `code2flow`  
**GitHub:** https://github.com/scottrogowski/code2flow  
**License:** MIT  
**Install:** `pip install code2flow`  
**Use in:** `packages/repo-intelligence/src/adapters/typescript/`  

**What it does:** Generates call graphs for Python, JavaScript, Ruby, and PHP by parsing ASTs. Supports JavaScript/TypeScript call graph generation as a complement to pyan3.

**What to copy:**
```python
import code2flow

def build_js_call_graph(file_paths: list[str], output_path: str) -> dict:
    code2flow.code2flow(
        file_paths,
        output_path,
        language="js",
        no_trimming=True
    )
    # Parse the output JSON for CallEdge construction
```

---

### Complete Dependency Map

| Package | Python deps | TypeScript deps |
|---------|-------------|-----------------|
| `repo-intelligence` | `tree-sitter`, `tree-sitter-python`, `astchunk`, `pyan3`, `gitpython` | — |
| `context-hub` | `sqlite-vec`, `semantic-router[local]`, `gitpython` | — |
| `arch-intelligence` | `networkx` (graph analysis) | — |
| `orchestration` | `semantic-router`, `anthropic`, `pydantic`, `fastapi` | — |
| `token-optimizer` | `anthropic`, `tiktoken` | — |
| `shared/storage` | `sqlite-vec` | — |
| `apps/cli` | — | `commander`, `typescript`, `zod` |
| `apps/api-server` | `fastapi`, `uvicorn`, `pydantic` | — |

---

## 14. Storage Schema

### SQLite Schema (`.ortho/ortho.db`)

```sql
-- Core repository
CREATE TABLE repositories (
    id TEXT PRIMARY KEY,
    root_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    primary_language TEXT,
    indexed_at TEXT,
    git_remote TEXT,
    config_json TEXT
);

-- File manifest
CREATE TABLE files (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    rel_path TEXT NOT NULL,
    language TEXT NOT NULL,
    size_bytes INTEGER,
    last_modified TEXT,
    git_last_commit TEXT,
    UNIQUE(repo_id, rel_path)
);

-- Symbol registry
CREATE TABLE symbols (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    file_id TEXT NOT NULL REFERENCES files(id),
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK(kind IN ('function','class','method','variable','constant','type')),
    visibility TEXT NOT NULL CHECK(visibility IN ('public','private','protected','internal')),
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    docstring TEXT,
    signature TEXT
);
CREATE INDEX idx_symbols_file ON symbols(file_id);
CREATE INDEX idx_symbols_qualified ON symbols(qualified_name);

-- Call graph
CREATE TABLE call_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_id TEXT NOT NULL REFERENCES symbols(id),
    callee_id TEXT NOT NULL REFERENCES symbols(id),
    call_site_line INTEGER,
    confidence REAL NOT NULL DEFAULT 0.8
);
CREATE INDEX idx_call_edges_caller ON call_edges(caller_id);
CREATE INDEX idx_call_edges_callee ON call_edges(callee_id);

-- Import graph
CREATE TABLE import_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    importer_file_id TEXT NOT NULL REFERENCES files(id),
    imported_file_id TEXT REFERENCES files(id),  -- NULL if external
    imported_module TEXT NOT NULL,
    is_external INTEGER NOT NULL DEFAULT 0,
    symbols_imported TEXT  -- JSON array
);

-- ContextHub artifacts
CREATE TABLE artifacts (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_modified TEXT NOT NULL,
    relevance_scope TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',  -- JSON array
    related_symbols TEXT DEFAULT '[]',  -- JSON array of symbol IDs
    estimated_tokens INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL  -- for staleness detection
);

-- FTS5 full-text search on artifacts
CREATE VIRTUAL TABLE artifacts_fts USING fts5(
    title,
    content,
    content='artifacts',
    content_rowid='rowid'
);

-- Project memory
CREATE TABLE project_memory (
    key TEXT NOT NULL,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    value TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (key, repo_id)
);

-- Architecture model
CREATE TABLE architecture_models (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    style TEXT NOT NULL,
    style_confidence REAL NOT NULL,
    evidence TEXT NOT NULL,  -- JSON array
    model_json TEXT NOT NULL,  -- Full ArchitectureModel as JSON
    detected_at TEXT NOT NULL
);

-- Workflow runs
CREATE TABLE workflow_runs (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL REFERENCES repositories(id),
    intent TEXT NOT NULL,
    intent_class TEXT NOT NULL,
    execution_plan_json TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    evidence_json TEXT NOT NULL DEFAULT '[]'
);

-- Agent/skill registry cache
CREATE TABLE agent_manifests (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);

CREATE TABLE skill_manifests (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    content TEXT NOT NULL,
    estimated_tokens INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);
```

### Vector Store (`.ortho/vectors.db`)

```sql
-- Loaded via sqlite-vec extension
CREATE VIRTUAL TABLE artifact_embeddings USING vec0(
    artifact_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]   -- dimension matches embedding model output
);

CREATE VIRTUAL TABLE symbol_embeddings USING vec0(
    symbol_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]
);
```

---

## 15. Data Flow

### Phase 1 Data Flow (scan + index)

```
ortho scan
    ↓
Scanner walks file tree → builds files table
    ↓
LanguageAdapter.extract_symbols() per file → builds symbols table
LanguageAdapter.extract_imports() per file → builds import_edges table
LanguageAdapter.extract_calls() per file → builds call_edges table
LanguageAdapter.chunk() per file → produces ContextChunks
    ↓
Chunks embedded (embedding model) → stored in artifact_embeddings
    ↓
IncrementalIndexer stores last indexed commit hash
```

### Phase 3 Data Flow (ortho run)

```
ortho run "add rate limiting"
    ↓
IntentRouter.classify() → IntentClassification{type: "feature_development"}
    ↓
AgentRegistry.load_all() + SkillRegistry.load_all()
    ↓
SelectorEngine.score_agents() + SelectorEngine.score_skills()
    ↓
SelectorEngine.build_execution_plan() → ExecutionPlan
    ↓
For each ExecutionStep:
    ContextRequestBuilder.build() → ContextRequest
        ↓
    Pillar1.query(symbols_needed) + Pillar2.retrieve(artifacts_needed) + Pillar3.query(arch_data)
        ↓
    TokenOptimizer.assemble(chunks, budget) → ContextPackage
        ↓
    PromptAssembler.build(agent, skills, context_package, task) → LLMRequest
        ↓
    LLM(LLMRequest) → LLMResponse
        ↓
    EvidenceCollector.collect(response) → Evidence[]
        ↓
    if step.approval_gate: HumanApprovalGate.wait()
        ↓
    WorkflowStateStore.update(step, status)
    ↓
WorkflowRun marked complete
```

---

## 16. Development Roadmap

### Phase 1 — Foundation (Weeks 1–8)

**Goal:** CLI that scans a Python repo and makes its contents searchable. No AI yet.

**Week 1–2: Shared foundation**
- [ ] Set up monorepo (Poetry workspaces)
- [ ] Define all shared types (TypeScript + Python dataclasses)
- [ ] Implement SQLite storage layer with migrations
- [ ] Implement `OrthoConfig` and `.ortho/` directory structure
- [ ] Logging, error handling, config utilities
- [ ] CLI skeleton with `ortho init`
- [ ] ADR: Storage strategy (SQLite + sqlite-vec)
- [ ] ADR: Language adapter plugin model

**Week 3–4: Repo Intelligence — Python**
- [ ] `LanguageAdapter` interface
- [ ] Python adapter: tree-sitter AST + `astchunk` integration
- [ ] Symbol extraction and registry
- [ ] Import graph builder
- [ ] `ortho scan` command — scans and reports

**Week 5–6: Repo Intelligence — call graph + incremental**
- [ ] Call graph builder using `pyan3`
- [ ] Dependency graph (requirements.txt, pyproject.toml)
- [ ] Module detector
- [ ] Incremental indexer (git diff based)
- [ ] `ortho index` with `--watch` mode

**Week 7–8: ContextHub**
- [ ] Artifact store with all types + ingestion contract
- [ ] BM25 search (SQLite FTS5)
- [ ] Semantic search (sqlite-vec + embedding API)
- [ ] Hybrid RRF search
- [ ] Git metadata store (gitpython)
- [ ] Project memory store
- [ ] `ortho context add` / `ortho context search`
- [ ] Staleness detector

**Phase 1 exit criteria:**
- `ortho init` sets up a project
- `ortho scan` indexes a medium Python repo in < 30 seconds
- `ortho context search "authentication flow"` returns relevant results
- All data lives in `.ortho/` — zero cloud, zero account
- Token budget interface defined (even though optimizer isn't built)

---

### Phase 2 — Reasoning (Weeks 9–14)

**Goal:** Ortho can reason about repo structure, dependencies, and architecture.

**Week 9–10: Architecture detection**
- [ ] Architecture style detector with confidence scores
- [ ] Layer detector from import patterns
- [ ] Subsystem detector
- [ ] Architecture model data structure
- [ ] TypeScript language adapter

**Week 11–12: Dependency + risk analysis**
- [ ] Circular dependency detector (networkx)
- [ ] Change impact analyzer with blast radius
- [ ] Dependency health analyzer
- [ ] Technical debt scorer

**Week 13–14: ADR awareness + reporting**
- [ ] ADR cross-reference against code
- [ ] Reuse discovery (AST-level similarity)
- [ ] `ortho analyze` command
- [ ] `ortho analyze --impact <file>`

**Phase 2 exit criteria:**
- `ortho analyze` correctly identifies architectural style with confidence score
- `ortho analyze --impact src/auth/service.py` lists all affected files
- Circular dependencies detected and reported
- ASES workflow usage logged throughout — building router training data

---

### Phase 3 — Execution (Weeks 15–22)

**Goal:** Ortho orchestrates full ASES workflows using agents and skills.

**Prerequisite:** ASES workflows are stable, documented, and have been run manually ≥ 5 times each. Router training utterances collected from Phase 1+2 logs.

**Week 15–16: Intent routing + registries**
- [ ] `semantic-router` integration with workflow utterances
- [ ] Agent registry (load + cache from `ases/agents/`)
- [ ] Skill registry (load + cache from `ases/skills/`)
- [ ] Core agent `.md` files written
- [ ] Core skill `.md` files written

**Week 17–18: Selector engine + execution**
- [ ] Selector engine (score_agent, score_skill, build_execution_plan)
- [ ] Workflow executor (step runner with state)
- [ ] Human approval gate (CLI prompt)
- [ ] Context request builder
- [ ] Model router

**Week 19–20: Evidence + verification**
- [ ] Evidence collector
- [ ] Verification router
- [ ] Workflow state store (resumable)
- [ ] `ortho run` command (main entry point)
- [ ] `ortho status` / `ortho approve` / `ortho reject`

**Week 21–22: Integration**
- [ ] End-to-end test: `ortho run "implement feature X"` completes full workflow
- [ ] Task planner for complex multi-step intents
- [ ] `ortho history` command
- [ ] FastAPI server stabilised

**Phase 3 exit criteria:**
- `ortho run "add X to Y"` executes a complete ASES Feature Development workflow
- Human approval gates function correctly
- Evidence artifacts stored per run
- Interrupted workflows resume correctly

---

### Phase 4 — Optimization (Weeks 23–28)

**Goal:** Maximize engineering value per token.

**Week 23–24: Ranking + deduplication**
- [ ] Intent-aware reranker
- [ ] Semantic duplicate detector
- [ ] Graph expander (neighbor retrieval)
- [ ] Token budget manager (replace placeholder from Phase 1)

**Week 25–26: Compression + architecture-aware retrieval**
- [ ] Context compressor (summarize low-priority chunks)
- [ ] Architecture-aware retrieval (weight central modules higher)
- [ ] Model context adapter (per-model strategy)
- [ ] Replace basic prompt assembler with full optimizer

**Week 27–28: Measurement**
- [ ] Context quality logger
- [ ] Basic quality metrics
- [ ] `ortho debug context` command
- [ ] Tune ranking weights from logs

**Phase 4 exit criteria:**
- Token usage reduced ≥ 20% for equivalent tasks vs Phase 3 baseline
- Context quality logs available and useful
- No measurable degradation in LLM output quality

---

## 17. Engineering Standards

### Every package must include

- `README.md` with purpose, responsibilities, and public API
- `tests/` with unit tests (pytest)
- `benchmarks/` where performance matters (Pillar 1, Pillar 5)
- Architecture documentation
- Clear interface definitions

### Before every PR

Ask: "Which pillar does this serve?" If the answer is none or ambiguous, the feature doesn't belong.

### ADR requirement

Any decision about: package boundaries, storage backends, library selection, interface contracts, performance trade-offs — must produce an ADR in `docs/adr/` before implementation begins.

### ASES compliance checklist (run before every task)

```
[ ] Which ASES workflow applies to this task?
[ ] Has repository context been assembled (ortho scan run recently)?
[ ] Is the plan documented before implementation starts?
[ ] Are interfaces defined before implementation?
[ ] Is there a verification plan (what tests will prove this works)?
[ ] What evidence artifacts will this task produce?
[ ] Is human approval required for this change?
```

### Code style

- Python: `ruff` for linting, `black` for formatting, `mypy` for type checking
- TypeScript: `eslint`, `prettier`, strict mode
- All Python functions have type annotations
- No `any` types in TypeScript
- All errors are explicit types — no bare `except Exception`

### Testing strategy

- Unit tests per module (pure function testing, no I/O)
- Integration tests against `tests/fixtures/sample-python-project/`
- The fixture project must be realistic — a small Flask/FastAPI app with real structure
- Benchmark suite for: indexing speed (Pillar 1), retrieval quality (Pillar 2/5)

---

## 18. Glossary

| Term | Definition |
|------|-----------|
| **ASES** | AI Software Engineering System — the engineering methodology used to build Ortho. Not a runtime component. |
| **Pillar** | One of the five permanent capability groups: Repo Intelligence, ContextHub, Arch Intelligence, Orchestration, Token Optimizer |
| **Symbol** | A named code entity: function, class, method, variable, or type |
| **Symbol ID** | A stable hash identifier for a symbol — used as the foreign key across all pillars |
| **ContextHub** | The long-term knowledge store — all engineering artifacts, not just code |
| **Context Package** | A ranked, deduplicated, budget-constrained bundle of context chunks assembled for a specific LLM call |
| **Token Budget** | The hard ceiling on tokens for a given LLM call |
| **Artifact** | Any piece of engineering knowledge stored in ContextHub: FRD, ADR, doc, conversation, evidence |
| **Agent** | A specialized LLM persona defined by a `.md` file with a focused system prompt |
| **Skill** | A capability document (`.md` file) injected into an agent's context to give it specific knowledge |
| **Orchestrator** | The master agent that reads intent and produces an execution plan |
| **Execution Plan** | The ordered list of agents + skills + context needs for a given workflow run |
| **Selector Engine** | Pure Python scoring logic that selects agents and skills — no LLM involved |
| **Intent Router** | The `semantic-router` layer that classifies user intent without an LLM call |
| **ADR** | Architecture Decision Record — a documented engineering decision with context, choice, and consequences |
| **Evidence** | A verification artifact produced after an execution step: test output, lint result, approval record |
| **Blast Radius** | The number of files/symbols affected by changing a given file — computed by impact analysis |
| **RRF** | Reciprocal Rank Fusion — the algorithm used to merge BM25 and semantic search results |
| **MEVT** | Maximum Engineering Value per Token — the objective of Pillar 5 |
| **Language Adapter** | A plugin that implements the `LanguageAdapter` interface for a specific programming language |
| **Incremental Indexer** | The component that re-indexes only what changed since the last index run |
| **Confidence Score** | A 0.0–1.0 probability attached to every detection result from Pillar 3 |
| **Staleness** | An artifact whose source has changed since it was ingested into ContextHub |
| **Graduation Rule** | The criteria determining when an ASES workflow step is ready to be automated |

---

*This document is the BIBLE for Ortho v3.*  
*All features are derived from it.*  
*All code traces back to it.*  
*All decisions are recorded as ADRs that reference it.*  
*When in doubt, return to Section 1.*
