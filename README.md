# Ortho v3 — AI Engineering Platform

> **The LLM is the execution engine. Ortho is the engineering brain.**

Ortho provides engineering intelligence *around* LLMs by understanding repositories deeply,
managing project knowledge persistently, orchestrating engineering workflows intelligently,
and delivering the highest-relevance context with the fewest tokens.

---

## What It Does

| Pillar | Package | Purpose |
|--------|---------|---------|
| **1 — Repository Intelligence** | `packages/repo-intelligence` | AST parsing, symbol extraction, import/call graphs, incremental indexing |
| **2 — ContextHub** | `packages/context-hub` | Artifact store, BM25 + semantic + hybrid search, git metadata, project memory |
| **3 — Architectural Intelligence** | `packages/arch-intelligence` | Architecture style detection, layer/subsystem clustering, ADR tracking, reuse detection |
| **4 — Engineering Orchestration** | `packages/orchestration` | Intent routing, agent/skill registry, workflow executor with approval gates |
| **5 — Token Optimizer** | `packages/token-optimizer` | Context ranking, deduplication, prompt assembly, token budget management |

The TypeScript CLI (`apps/cli`) is the user-facing interface.  
The FastAPI server (`apps/api-server`) exposes all pillars over HTTP.

---

## Quick Start

```bash
# Install Python dependencies
pip install -e packages/repo-intelligence
pip install -e packages/context-hub
pip install -e packages/arch-intelligence
pip install -e packages/orchestration
pip install -e packages/token-optimizer

# Install CLI dependencies
cd apps/cli && npm install && npm run build && cd ../..

# Initialise a project
ortho init

# Scan a repository
ortho scan /path/to/repo

# Analyse architecture
ortho analyze --architecture

# Run an engineering workflow
ortho run "add logging to the API layer"
```

> **Note:** `PythonAdapter` (AST parsing) requires `tree-sitter` and `tree-sitter-languages`.  
> All other package features work without them.

---

## Development

```bash
# Run full test suite (496 tests)
pytest

# Run benchmarks against a real repo
python benchmarks/run_benchmark.py --only flask

# Type-check TypeScript CLI
cd apps/cli && npx tsc --noEmit
```

### Methodology

Ortho is built using **ASES v1.2** — an AI Software Engineering methodology that enforces
planning before implementation, external verification for every task, and human approval gates.
See `ASES_FRD_v1.2.md` and `.ases/` for the full methodology and all task evidence.

The full Functional Requirements Document is at [`ortho-v3-frd.md`](ortho-v3-frd.md).

---

## Stack

- **Python** — all analysis packages (Poetry workspaces)
- **TypeScript** — CLI + shared type definitions
- **SQLite + sqlite-vec** — local-first storage and vector search
- **semantic-router + BAAI/bge-small-en-v1.5** — fast intent routing (no LLM required)
- **tree-sitter** — AST parsing for Python (TypeScript adapter planned)

---

## License

MIT — see [LICENSE](LICENSE).
