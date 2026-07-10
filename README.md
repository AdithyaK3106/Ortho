# Ortho

### Engineering Intelligence for AI-assisted Software Development

Transform repository understanding into engineering decisions before any AI writes code.

**Repository Intelligence** → **Architecture Intelligence** → **Context Assembly** → **AI Execution**

---

## Why Ortho?

Modern AI coding assistants can write code. They struggle with:

- **Repository architecture** — "Where does this fit?"
- **Engineering constraints** — "What dependencies will I break?"
- **Implementation strategy** — "What's the right approach?"
- **Change impact** — "Who else does this affect?"
- **Architectural safety** — "Will this violate patterns?"

Ortho solves this by building an **Engineering Intelligence layer** before AI execution.

---

## Architecture

```
Foundation
├── Repository Intelligence (✓ Done)
├── ContextHub (✓ Done)
└── Architecture Intelligence (✓ Done)

Engineering Intelligence (🚧 Planned)
├── Change Planner
├── Feature Planner
├── Refactoring Advisor
├── Architecture Guardrails
├── Engineering Insights
└── Decision Engine

AI Execution
├── Claude
├── Gemini
├── GPT
└── Local Models
```

---

## Today

What Ortho can do now:

✓ **Repository Intelligence** — AST parsing, symbols, imports, call graphs  
✓ **Architecture Detection** — Layered, MVC, Microservices, Flat, Hexagonal  
✓ **Layer & Subsystem Analysis** — Boundary detection, coupling metrics  
✓ **Dependency Graphs** — Visual exploration of internal relationships  
✓ **Blast Radius Analysis** — Impact assessment for changes  
✓ **Technical Debt Scoring** — Multi-factor assessment (churn, coupling, complexity)  
✓ **Context Assembly** — Relevant code bundled with token budgets  
✓ **Interactive Dashboard** — Explore architecture, impact, and metrics  
✓ **Ground Truth Benchmarks** — 135+ verified test cases  

---

## Next

What's planned:

🚧 **Change Planner** — Predict impact before code generation  
🚧 **Feature Planner** — Suggest implementation paths  
🚧 **Refactoring Advisor** — Recommend improvements  
🚧 **Architecture Guardrails** — Enforce patterns and constraints  
🚧 **Engineering Insights** — Actionable recommendations  
🚧 **Decision Engine** — Structured decision support  

---

## Why This Matters

| Traditional AI Coding | Ortho |
|----------------------|-------|
| Starts from prompt | Starts from repository |
| Reads arbitrary files | Understands architecture |
| Limited change awareness | Computes exact blast radius |
| Generic engineering context | Builds structured context |
| Generates code immediately | Plans before execution |

---

## Philosophy

### Engineering before Generation

LLMs should not begin implementation until they understand:

- Repository architecture and layering
- Subsystem ownership and boundaries
- Implementation constraints and patterns
- Engineering risks and technical debt
- Change impact and blast radius

Ortho provides this understanding.

---

## The Dashboard

**Today:** The dashboard answers "What does this repository look like?"

- Repository overview (files, architecture, dependencies)
- Architecture verdict (detected style, confidence, evidence)
- Engineering risks (debt hotspots, circular dependencies)
- Change impact (blast radius, affected files)
- Trust metrics (benchmark results, verification)

**Tomorrow:** The dashboard will answer "What should I do next?"

- Recommended refactorings
- Safe change paths
- Architectural improvements
- Technical debt paydown strategies

---

## Quick Start

```bash
# Install
pip install -e packages/repo-intelligence
pip install -e packages/context-hub
pip install -e packages/arch-intelligence
pip install -e packages/orchestration
pip install -e packages/token-optimizer

# Scan a repository
ortho scan /path/to/repo

# Analyze architecture
ortho analyze --architecture

# Compute blast radius
ortho analyze --impact src/core.py
```

### Try the Demo

```bash
cd ortho-demo/dashboard
python -m http.server 8000
# Open http://localhost:8000/index.html?repo=flask
```

**Pre-analyzed repositories:** Flask, Click, LangChain, Django, FastAPI, and others.

---

## Demo Flow

1. **Scan** → Parse Python repository, extract symbols, imports, calls
2. **Understand** → Detect architecture style and layers
3. **Assess Risks** → Score technical debt, find hotspots
4. **Compute Impact** → Calculate blast radius for changes
5. **Generate Context** → Assemble relevant code with token budgets
6. **Ready for AI** → AI now has complete engineering understanding

---

## Future Vision

### Engineering Intelligence

**Repository Intelligence** answers: "What exists?"

**Engineering Intelligence** will answer: "What should the engineer do?"

Examples of planned capabilities:

- **Change Planning** — Before touching a file, know what breaks
- **Refactoring Planning** — Suggested improvements with impact estimates
- **Migration Planning** — Safe paths for architectural changes
- **Architecture Review** — Automated analysis of proposed changes
- **Feature Planning** — Implementation strategy based on codebase structure

All clearly **planned**, not yet implemented.

---

## Stack

- **Python** — analysis packages (Poetry workspaces)
- **TypeScript** — CLI + shared types
- **SQLite + sqlite-vec** — local-first storage and vector search
- **semantic-router** — fast intent routing (no LLM required)
- **tree-sitter** — AST parsing for Python

---

## Evaluation

Run the test suite:

```bash
pytest packages/ -v
```

Run benchmarks against real repositories:

```bash
python benchmarks/run_benchmark.py --all
```

**Test Coverage:**
- 135+ ground-truth test cases
- Repository Intelligence (symbol, import, call extraction)
- Architecture Detection (style, layer, subsystem analysis)
- Impact Analysis (blast radius, risk scoring)
- Search & Retrieval (BM25, semantic, hybrid)
- Token Optimization (context assembly, budget management)

**Determinism Verification:** All metrics are bit-perfect reproducible across runs.

---

## Methodology

Ortho is built using **ASES v1.2** — a methodology that enforces planning before implementation, external verification for every task, and human approval gates.

See [`ortho-v3-frd.md`](ortho-v3-frd.md) for the complete Functional Requirements Document.

---

## License

MIT — see [LICENSE](LICENSE).
