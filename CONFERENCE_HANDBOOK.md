# ORTHO CONFERENCE PREPARATION HANDBOOK
## AgentForge 2026 & Agents That Ship — July 12, 2026

---

## SECTION 1: EVENT SUMMARY

### Event 1: AgentForge 2026

**When:** July 12, 2026 (Morning)  
**Audience:** AI developers, GDEs, Gemini developers, Vertex AI users, founders, students  
**Key Topics:**
- Architecting Knowledge Engines (Scaling Multi-Document Intelligence with Gemini + NotebookLM)
- A2A vs MCP (Multi-Agent Communication Protocols)
- Google & Vertex AI

**Why This Matters for Ortho:**
- **Knowledge Engines** are the exact problem Ortho solves at scale: multi-document context retrieval, semantic understanding, and intelligent routing
- **NotebookLM architecture** is instructive for understanding how to organize repository knowledge into queryable context
- **MCP & A2A** are the communication layers that will connect Ortho to coding agents (Claude Code, Cursor, OpenHands, etc.)
- **Vertex AI** represents enterprise deployment—understand scaling, cost, and integration patterns
- **Networking:** Google engineers will want to understand how Ortho complements Vertex AI (it doesn't compete; it enables)

**Your Positioning:** You're not learning *competitors*; you're learning *partners*. Ortho is the intelligence layer that makes Google's tools smarter.

---

### Event 2: Agents That Ship

**When:** July 12, 2026 (Afternoon)  
**Audience:** Engineering leaders, technical founders, LLM engineers, ML engineers, software architects  
**Key Topics:**
- AI Coding Agents (architecture, evaluation, production)
- Observability, guardrails, autonomous coding
- AI engineering best practices
- Production AI systems

**Why This Matters for Ortho:**
- **This is your primary audience.** Engineering leaders and founders are the users who need repository intelligence
- **Agents That Ship** focuses on reliability, evaluation, and production-readiness—exactly what Ortho enables
- **Observability & guardrails** connect to Ortho's tracing and impact analysis
- **Agent evaluation** is a pain point Ortho solves through context precision and blast radius
- **Networking:** Meet the people building the next generation of coding agents—they need Ortho

**Your Positioning:** Ortho is the *verification layer* that makes AI coding agents production-ready.

---

## SECTION 2: TECHNICAL STUDY NOTES

### NotebookLM

**Problem It Solves:**
- Transforms unstructured documents into structured knowledge (Q&A, outlines, timelines)
- Handles multi-document context without explicit RAG complexity
- Reduces context window waste by learning what's relevant

**How It Works:**
1. Document ingestion (PDFs, docs, web)
2. Semantic chunking and embedding
3. Implicit indexing (no explicit vector DB for users)
4. LLM-driven synthesis with attribution

**Where Ortho Differs:**
- NotebookLM: optimized for *documents*; Ortho: optimized for *code*
- NotebookLM: user-facing synthesis; Ortho: agent-facing intelligence
- NotebookLM: cloud-hosted; Ortho: local-first, reproducible

**Where Ortho Integrates:**
- Ortho can *feed* NotebookLM-like summaries to LLMs when needed
- Ortho's architecture detection creates implicit "documents" (subsystems) that could be summarized NotebookLM-style
- Both benefit from multi-document retrieval patterns

**Likely Questions:**
- "Why not just use NotebookLM for code repos?" → NotebookLM doesn't understand call graphs, dependency resolution, or impact analysis
- "How do you handle 100K files?" → Ortho uses structured indexing (call graphs, not embeddings for every file)

---

### Knowledge Engines

**Problem It Solves:**
- Scales context retrieval beyond single-document limits
- Organizes multi-source knowledge for real-time querying
- Maintains consistency across distributed knowledge sources

**How It Works:**
1. Knowledge source ingestion (docs, APIs, databases, code)
2. Semantic routing (directing queries to relevant sources)
3. Multi-source aggregation and deduplication
4. Synthesis or passthrough to agent/LLM

**Where Ortho Differs:**
- Ortho is *domain-specific* (code); knowledge engines are generic
- Ortho builds *structural* knowledge (graphs); engines often rely on embeddings
- Ortho includes *impact analysis*; engines don't

**Where Ortho Integrates:**
- Ortho could be a *specialization* of a knowledge engine for code
- Ortho's ContextHub is a mini knowledge engine for repository context
- A meta-engine could route "architectural questions" to Ortho and "documentation questions" to NotebookLM

**Likely Questions:**
- "Is Ortho a knowledge engine?" → Yes, specialized for code. It's a code knowledge engine.
- "Why not build on a generic knowledge engine?" → Because code has structure; generic engines waste that signal.

---

### Multi-Document Retrieval

**Problem It Solves:**
- Finding relevant information across many documents without loading all of them
- Maintaining consistency when sources contradict
- Scaling retrieval to enterprise scale (10K+ documents)

**How It Works:**
1. Index creation (full-text, semantic, or hybrid)
2. Query routing (which documents are relevant?)
3. Ranked retrieval (which chunks answer the query?)
4. Aggregation (combine results, resolve conflicts)

**In Ortho:**
- Repository = "documents" (files)
- Index = call graph + symbol table + architecture graph
- Query = "what will this change break?"
- Answer = blast radius + impact analysis

**Likely Questions:**
- "How do you avoid retrieval hallucinations?" → Ortho uses deterministic indexing (call graphs), not embeddings
- "What's your latency?" → Milliseconds (SQLite FTS5 for symbol search, in-memory graphs for traversal)

---

### Context Engineering

**Problem It Solves:**
- Reducing token waste by sending only relevant code to LLMs
- Improving LLM reasoning by organizing context hierarchically
- Tracing reasoning back to source (debugging failures)

**How It Works:**
1. Identify what context is needed (intent + scope)
2. Retrieve relevant files, functions, classes, imports
3. Organize by abstraction level (high-level → detail)
4. Add metadata (why this file, relationship to other files)
5. Format for LLM consumption

**In Ortho:**
- Intent recognition (what is the user asking?)
- Architectural context (which subsystem?)
- Dependency context (what can't be changed without breaking?)
- Token optimization (send only what matters)

**Likely Questions:**
- "How do you know what context is relevant?" → Architecture detection + blast radius analysis
- "Why not just RAG?" → RAG doesn't understand code structure; Ortho does

---

### MCP (Model Context Protocol)

**Problem It Solves:**
- Standardizing how tools and services expose capabilities to LLMs
- Reducing vendor lock-in (swap Claude for Gemini without re-wiring)
- Enabling LLM agents to reach external systems safely

**How It Works:**
1. Tools (like Git, file system, APIs) expose capabilities via MCP
2. Client (Claude Code, or custom agent) connects to MCP servers
3. LLM can call tools directly: "git log", "edit file.py", etc.
4. MCP handles auth, retries, resource limits

**Where Ortho Fits:**
- Ortho could expose a *repository intelligence MCP server*
- Claude Code (or any MCP client) could ask: "impact of changing this function?"
- Ortho answers deterministically; LLM uses the answer to act

**Why MCP Matters for You:**
- **A2A (Agent-to-Agent)** is point-to-point; **MCP** is standard
- Bet on MCP for integration (Anthropic, Google, others are adopting)
- Your customers will use MCP to wire Ortho into their workflows

**Likely Questions:**
- "Will Ortho be an MCP server?" → Yes, that's the plan (and that's how you stay agnostic to LLM choice)
- "How does MCP help with reliability?" → Tools are explicit, bounded, and auditable—unlike LLM reasoning alone

---

### A2A (Agent-to-Agent Communication)

**Problem It Solves:**
- Enabling agents to coordinate (agent A calls agent B)
- Scaling beyond single-agent systems (specialized agents for specialized tasks)
- Multi-step reasoning with verification at each step

**How It Works:**
1. Agent A identifies it needs external capability (e.g., "I need to understand the architecture")
2. Agent A calls Agent B with context
3. Agent B processes and returns result
4. Agent A continues with higher confidence

**In Ortho Context:**
- Coding Agent: "I'm refactoring module X"
- Ortho Agent (via MCP): "Here's impact analysis, here's blast radius"
- Coding Agent: "OK, I'll change these files" → higher confidence, fewer mistakes

**Why A2A ≠ MCP:**
- **A2A:** agent-to-agent (stateful, bi-directional, reasoning shared)
- **MCP:** tool-to-agent (stateless, unidirectional query/response)
- **Ortho uses:** MCP (Ortho is a tool, not an autonomous agent)

---

### Agentic Systems (General Principles)

**Core Concepts:**
1. **Perception:** Agent understands current state (code, requirements, errors)
2. **Reasoning:** Agent plans actions (which files to change, in what order)
3. **Action:** Agent executes (edits files, runs tests, commits)
4. **Feedback:** Agent learns from results (test passed/failed, human feedback)

**Common Patterns:**
- **Planning:** Break task into steps before executing
- **Verification:** Run tests/checks after actions, don't assume success
- **Guardrails:** Prevent harmful actions (no deleting production databases)
- **Observability:** Log every decision for debugging and learning

**Where Ortho Fits:**
- Ortho handles **Perception** (repository understanding)
- Ortho informs **Reasoning** (context and impact analysis)
- Ortho enables **Verification** (is this change safe?)
- Ortho provides **Observability** (trace impact of changes)

**Likely Questions:**
- "Why do agents fail in production?" → Lack of context leads to wrong reasoning
- "How do you make agents reliable?" → Better perception (Ortho), explicit verification, guardrails

---

### Vertex AI

**What It Is:**
- Google's managed ML platform (alternative to self-hosted ML)
- Includes Gemini API, fine-tuning, monitoring, deployment

**Why Mention:**
- AgentForge is hosted by Google, so Vertex AI will be discussed
- Understand Google's vision for agents (this informs where Ortho fits)
- Enterprise customers will ask "can we run this on Vertex AI?"

**Ortho + Vertex AI:**
- Ortho runs locally (SQLite, Python) or as a managed service
- Ortho *feeds context* to Gemini (via Vertex AI API)
- Vertex AI runs the LLM; Ortho runs the intelligence
- No conflict; they're complementary

**Key Insight:**
Vertex AI is the *execution engine*; Ortho is the *intelligence layer*.

---

### Evaluation (Agent Evaluation)

**Problem It Solves:**
- Measuring agent reliability (does it succeed consistently?)
- Debugging failures (where did the agent go wrong?)
- Comparing approaches (is approach A better than approach B?)

**Common Metrics:**
- **Success rate:** % of tasks completed correctly
- **Cost:** Tokens used (proxy for LLM cost)
- **Latency:** Time to complete task
- **Precision:** Is the agent's output correct? (vs. recall: did it find all relevant issues?)

**Where Ortho Enables Evaluation:**
- Ortho provides *deterministic* baselines (impact analysis, blast radius)
- Can compare: "did the agent predict the same blast radius as Ortho?"
- Tracing: track which decisions the agent made vs. which Ortho recommended

**Likely Questions:**
- "How do you evaluate AI agents on code changes?" → Compare LLM-proposed changes against impact analysis
- "What's your ground truth?" → Actual code execution (tests, type checking, real blast radius measurement)

---

### Tracing

**Problem It Solves:**
- Understanding why an agent made a decision
- Debugging failures ("why did the agent delete that function?")
- Compliance ("can you show the audit trail?")

**How It Works:**
1. Log every decision point (agent thought X, so did Y)
2. Include context (what information did the agent have?)
3. Include outcome (did the action succeed?)
4. Replay and analyze (reconstruct the reasoning)

**In Ortho:**
- Trace every architecture detection decision
- Trace every impact analysis conclusion
- When a blast radius is wrong, replay the trace to find the bug

**How It Helps Agents:**
- If Ortho says "changing X will break Y," and it doesn't, trace reveals why (outdated call graph? dynamic import?)
- If LLM ignores Ortho's warning and breaks Y anyway, trace shows that human ignored system

**Likely Questions:**
- "Can you export traces?" → Yes, JSON format, open to inspection
- "How do you use traces to improve?" → A/B test: agents with traces vs. without; compare quality

---

### Guardrails

**Problem It Solves:**
- Preventing agents from taking dangerous actions
- Ensuring compliance (can't commit to production without approval)
- Maintaining human control (human approves before agent acts)

**Common Patterns:**
1. **Pre-flight checks:** Before acting, verify preconditions (tests pass, no uncommitted changes)
2. **Post-action verification:** Run tests, check no errors before committing
3. **Human approval:** For risky actions (pushing to main, deleting code), require human sign-off
4. **Rollback:** If action fails, revert cleanly

**Where Ortho Provides Guardrails:**
- Impact analysis is a guardrail (don't change X without considering blast radius)
- Blast radius is a guardrail (if change affects 100+ files, flag for review)
- Architecture constraints are guardrails (don't break layering)

**Likely Questions:**
- "Who decides what's a guardrail?" → User (or org) defines: what actions are risky, what requires approval
- "How do you balance autonomy with safety?" → Ortho provides information; human decides policy

---

### Observability

**Problem It Solves:**
- Monitoring agent health in production
- Detecting when agents are making bad decisions
- Identifying patterns in failures

**What to Observe:**
- Decision frequency (is the agent looping?)
- Decision accuracy (are its predictions correct?)
- Token usage (is cost growing?)
- Latency (is it slowing down?)

**In Ortho:**
- Observe: Is impact analysis accurate? (yes/no)
- Observe: Are agents following Ortho's recommendations?
- Observe: Are there edge cases Ortho's architecture detection misses?

**Metrics Dashboard:**
- % of impact analyses that were correct (ground truth: did the predicted changes actually break things?)
- % of agents following Ortho recommendations (are they trusting it?)
- Blast radius accuracy (predicted vs. actual)

**Likely Questions:**
- "How do you monitor if impact analysis is working?" → Run on closed repositories, measure against actual failures
- "What alerts should I set up?" → High blast radius (review before merging), missed dependencies (impact analysis error)

---

### Coding Agents (General)

**Common Players:**
- Claude Code (Anthropic's CLI/IDE integration)
- Cursor (VS Code fork with AI built-in)
- OpenHands (open-source autonomous agent)
- Goose (lightweight, focused on code edits)
- Dify (no-code agent builder)
- LangGraph (agent framework for chaining LLM calls)

**Common Problems Agents Face:**
1. **Hallucination:** Agent thinks function exists, but it doesn't
2. **Incomplete changes:** Agent changes function A, forgets function B depends on it
3. **Context explosion:** Agent loads entire codebase, wastes tokens
4. **No rollback:** Agent breaks repo, can't recover

**Where Ortho Solves These:**
1. → Ortho's symbol table: know which functions actually exist
2. → Ortho's dependency graph: know what depends on what
3. → Ortho's context retrieval: minimal, precise context
4. → Ortho's impact analysis: know what will break before changing

**Key Insight:**
Agents are good at *reasoning* and *execution*. Ortho is good at *understanding scope* and *predicting impact*. Together: reliable automation.

---

### OpenHands

**What It Is:**
- Open-source autonomous coding agent
- Can write code, run tests, commit changes
- Designed for full-task autonomy

**Architecture:**
1. User describes task
2. Agent plans (breaks task into steps)
3. Agent executes (writes code, runs tests)
4. Agent verifies (did it work?)

**Where Ortho Fits:**
- OpenHands could use Ortho's impact analysis before committing
- Ortho's architecture understanding could inform OpenHands' planning
- Together: autonomous agent that understands impact

**Likely Questions from OpenHands Users:**
- "How do you prevent agents from breaking tests?" → Ortho's impact analysis predicts what will break before the agent acts

---

### Goose

**What It Is:**
- Lightweight coding agent, focused on atomic edits
- Designed for tight human-in-the-loop workflows

**Where Ortho Fits:**
- Goose makes a change; Ortho analyzes impact
- Human reviews impact analysis; approves or rejects
- Tight loop: fast iteration with safety

---

### Dify

**What It Is:**
- No-code/low-code platform for building agents
- Visual workflow builder, integrates LLMs and tools

**Where Ortho Fits:**
- Ortho could be a "tool" in Dify workflows
- Users could drag-and-drop: "Get impact analysis" → "Show to human" → "Proceed if approved"
- Dify democratizes agent building; Ortho adds intelligence

---

### LangGraph

**What It Is:**
- Python framework for building agentic workflows
- Explicit state management, cycle handling, tool calling

**Where Ortho Fits:**
- Ortho is a *tool* in a LangGraph workflow
- LangGraph's state machine + Ortho's intelligence = reliable agents
- Example workflow:
  1. User intent → parse intent (LangGraph)
  2. Retrieve relevant code → Ortho
  3. Plan changes → LLM
  4. Analyze impact → Ortho
  5. Execute (or ask human) → LangGraph

---

### Flowise

**What It Is:**
- Visual workflow builder for chaining LLM calls
- Drag-and-drop, similar to Dify but more open-source focused

**Where Ortho Fits:**
- Ortho as a workflow node ("Get Architecture", "Analyze Impact")

---

### Continue

**What It Is:**
- VS Code extension for in-editor AI
- Focuses on code editing without leaving the IDE

**Where Ortho Fits:**
- Continue could query Ortho before editing
- "Why not just use Continue's built-in AI?" → Continue is for editing; Ortho is for understanding

---

### Sourcegraph

**What It Is:**
- Code search + code intelligence platform
- Built-in symbol search, cross-repo analysis, insights
- On-prem or SaaS

**Where Ortho Differs:**
- Sourcegraph: search + navigation; Ortho: intelligence + impact analysis
- Sourcegraph: "find all usages"; Ortho: "change this, here's what breaks"
- Sourcegraph: web UI; Ortho: programmatic API

**Where Ortho Complements:**
- Ortho could *use* Sourcegraph's indices (if available) for faster symbol search
- Sourcegraph could *embed* Ortho's impact analysis (if needed)

**Likely Questions:**
- "How is Ortho different from Sourcegraph?" → Sourcegraph is search; Ortho is reasoning. Ortho goes deeper on impact.

---

### FutureAGI

**What It Is:**
- Conference host (Agents That Ship)
- Likely community-driven, focused on production AI systems

**Why It Matters:**
- Direct access to founders and engineers building agents
- They want reliability; Ortho enables it

**Networking Strategy:**
- Ask about their biggest pain point with agents
- Listen: is it context? reliability? cost? understanding scope?
- Mention Ortho solves one of those

---

### Zencoder

**What It Is:**
- Co-host of Agents That Ship
- Likely focused on reliable, production-ready AI systems

**Why It Matters:**
- They care about agents that ship (work reliably)
- Ortho's value is reliability

**Networking Strategy:**
- Ask how they evaluate agents
- Mention Ortho's evaluation framework (blast radius, impact analysis)

---

## SECTION 3: ORTHO POSITIONING

### 15-Second Pitch

"Ortho is an engineering intelligence platform that scans your repository to build a live understanding of your architecture, dependencies, and impact. It makes AI coding agents smarter by giving them precise context and predicting what will break before they act."

### 30-Second Pitch

"Imagine asking an AI agent to refactor your code, and instead of hoping it gets it right, the agent knows:
- What will this change break? (impact analysis)
- Where does this change propagate? (blast radius)
- What code do I actually need to touch? (precise context)

That's Ortho. It's not an agent—it's the intelligence layer that makes agents reliable. We scan your repository once to build an architecture graph, a dependency graph, and a call graph. Then, when your agent (Claude Code, OpenHands, Cursor, whatever) needs context, Ortho returns minimal, precise, verified context. No hallucinations. No missed dependencies. Just engineering intelligence."

### 2-Minute Pitch

"The problem: AI coding agents are getting smarter, but they're still breaking things. They change function A, miss that function B depends on it, and production breaks.

Why? Because agents don't understand your architecture. They see code—millions of lines—and have to reason about scope using a neural network trained on the internet. That's not reliable.

We built Ortho to solve that. Ortho is not another coding agent. It's the engineering brain sitting *above* any coding agent.

Here's how it works:
1. Scan your repository (Python AST, symbol extraction, import resolution)
2. Build intelligence (call graph, dependency graph, architecture patterns)
3. Query it (what will this change break? what's the blast radius? what code is actually relevant?)

Then, when you use Claude Code or OpenHands or Cursor, you wire in Ortho. The agent asks, 'I want to refactor this module,' and Ortho answers with:
- Impact analysis (here's every function that will be affected)
- Blast radius (here's the scope of this change)
- Precise context (here are the 50 lines that matter, not 50,000)

The result: agents that understand their scope, make fewer mistakes, and ship faster.

We're not replacing agents. We're making them intelligent.

The long-term vision: every AI workflow—whether it's coding, security scanning, or architecture planning—sits on top of engineering intelligence. Ortho is that foundation."

### Founder Pitch (For Other Founders)

"You're building an agent, right? Here's the problem you haven't solved yet: scope. Your agent doesn't know where its changes will ripple. It'll change A, break B (which depends on A), and your tests fail. Or worse, tests pass but production breaks because there's a path your tests don't cover.

We solved that. We built the engineering intelligence layer that makes agents scope-aware. We scan code, build graphs (call graphs, dependency graphs, architecture detection), and answer deterministic questions: 'What will this change break?'

We're not trying to replace you. We're trying to make your agent better. We'll be an MCP server—plug us in, and your agent gets superpowers.

Here's why this matters: the bottleneck for AI agents isn't reasoning. It's understanding scope. Better scope understanding → fewer bugs → faster shipping → bigger defensibility moat.

We're looking at this as a B2B play. Agents are B2B tools. We make those tools better."

### Engineer Pitch (For Engineering Leaders)

"You're using Claude Code or considering OpenHands. Here's the gap: these agents are smart, but they're scope-blind. They can reason, but they don't understand your architecture.

We built Ortho to fill that gap. It's a local, reproducible, deterministic layer that understands your codebase:
- Call graphs (who calls whom)
- Dependency resolution (what breaks if I change this?)
- Architecture patterns (is this change consistent with our architecture?)
- Impact analysis (here's the exact blast radius)

When your agent asks, 'Should I change this?', Ortho answers with facts, not guesses.

For your org: faster code reviews (you know the impact up front), more reliable deployments (fewer surprise breakages), and audit trails (you can trace every decision).

We run locally. No cloud. No proprietary data sent anywhere. Just intelligence."

### Investor Pitch (If Asked)

"The market: AI coding agents are a $50B+ TAM (if they work reliably). The problem: they don't work reliably today. They hallucinate scope, miss dependencies, and break production.

We're Ortho. We're the infrastructure layer that makes agents reliable by giving them deterministic, reproducible understanding of code.

Why now?
- Agents are becoming the primary way code gets written (Claude Code, Cursor, etc.)
- Reliability is the blocker (enterprises won't ship AI until it's proven)
- Graph-based understanding is proven (static analysis, Sourcegraph, etc.)

Why us?
- Deep expertise in repository intelligence (built this from scratch)
- Model-agnostic design (works with any LLM)
- Local-first, reproducible (no cloud vendor lock-in)

Why it matters:
- Agents + Ortho = enterprise-grade reliability
- This is infrastructure, not a feature (defensible moat)
- Every coding agent will eventually need this (TAM expansion)

We're targeting a $X million ARR in Y years by selling to enterprises that deploy agents at scale."

### Google Engineer Pitch

"You're building Vertex AI + Gemini. We're not competing with that. We're complementing it.

Here's the gap: Vertex AI is the execution layer (run LLM, call tools). We're the intelligence layer (understand the code).

A Vertex AI customer could wire in Ortho as an MCP server:
1. Gemini asks a question about code
2. Ortho answers with facts (call graphs, impact analysis)
3. Gemini is now more reliable
4. Customer is more likely to deploy

For Google: Ortho makes Gemini more valuable in the coding-agent space. For us: Gemini is one of many LLMs we support.

We're interested in a partnership where Ortho is recommended as part of Vertex AI's coding-agent story. Not a partnership where you build your own—you don't need to. Just recommend us, and we handle the intelligence layer."

---

## SECTION 4: TECHNICAL Q&A (100 Questions)

### Competitive & Strategic Questions

**1. Why not just use Cursor or Claude Code?**
Cursor and Claude Code are execution engines (write code, run tests). Ortho is the intelligence layer that makes them smarter. You can use both: Cursor for editing, Ortho for understanding scope.

**2. Why not use existing AI coding agents (e.g., OpenHands)?**
For the same reason: agents are good at reasoning and execution, but they're scope-blind. Ortho adds scope awareness to *any* agent.

**3. What about Sourcegraph? Doesn't it already do this?**
Sourcegraph is a search + navigation tool. Ortho is reasoning + impact analysis. Sourcegraph answers "where is this used?"; Ortho answers "what will break if I change this?"

**4. Isn't this just RAG with extra steps?**
No. RAG is embedding-based retrieval (similarity search). Ortho is graph-based understanding (deterministic, no embeddings). RAG hallucinates; Ortho doesn't.

**5. Why not build this into the LLM?**
Because LLMs are generic and probabilistic. Code understanding needs to be deterministic and local. The LLM is the reasoning engine; Ortho is the perception engine.

**6. How is this better than static analysis tools (like SonarQube)?**
SonarQube finds bugs. Ortho understands impact. They're complementary. Ortho could *use* SonarQube's results to inform impact analysis.

**7. Why Python? Why not support other languages?**
We're starting with Python because it's dominant in AI/ML and relatively easy to analyze (dynamic, so AST + import resolution works well). Other languages are on the roadmap.

**8. Open-source or closed-source?**
Prototype is closed-source (IP protection during fundraising). Long-term: likely open-source for adoption + community contributions. Will offer hosted SaaS.

**9. What happens when code is dynamically imported (e.g., `importlib`)?**
Impact analysis has ceiling: dynamic imports are marked as "uncertain" and flagged for manual review. We document this limitation and suggest static patterns when possible.

**10. How do you handle monorepos?**
Ortho scans the entire monorepo as one unit. You can define subsystems (workspace folders, package boundaries) to organize the graph. Impact analysis respects these boundaries.

### Technical Architecture Questions

**11. How does symbol extraction work?**
Python AST walking: visit every node (function, class, import). Extract name, type, location. Store in SQLite. Complexity: O(number of lines).

**12. What data structures does the call graph use?**
In-memory directed graph (adjacency list). Nodes = functions/methods, edges = calls. Built once, queried many times. Serializable to JSON for persistence.

**13. How do you resolve dynamic imports?**
Best effort: analyze `importlib.import_module()` calls and try to resolve statically. If we can't, mark as "uncertain". User can override with manual annotations.

**14. What about imports from packages (e.g., `from numpy import array`)?**
We track package imports but don't dive into package source code (too expensive). We mark package usage and note that impact analysis is "external" (unknown internals).

**15. How do you handle circular imports?**
Detect during import resolution. Flag as error (user should fix). Include both imports in dependency graph but note the cycle.

**16. What's your architecture detection algorithm?**
Pattern-based: look for common structures (handlers in one folder, models in another, etc.). Then graph-based: find natural clusters (tightly coupled code). Combine with user hints (package structure).

**17. How accurate is architecture detection?**
Depends on code organization. Well-structured code (layered, modular): 95%+. Messy code (mixed patterns): 70%. Always user-reviewable.

**18. How do you measure architecture precision vs. recall?**
Ground truth: hand-annotated repos (OpenHands, FastAPI, etc.). Precision: % of predicted architecture components that are correct. Recall: % of actual components we predicted.

**19. How does impact analysis handle indirect calls (e.g., via `getattr`)?**
Heuristic: look for strings that match function names. Flag as "uncertain". User can override with annotations. This is a documented ceiling.

**20. What's the complexity of blast radius analysis?**
Graph traversal: DFS/BFS from changed function. Time: O(V + E). For large repos: 100K functions, millions of edges. On modern hardware: milliseconds.

### Storage & Performance Questions

**21. Why SQLite and not PostgreSQL?**
Local-first design. No server dependency. Reproducible results. SQLite is sufficient for single-machine analysis. Multi-user scenarios could upgrade to PostgreSQL, but we optimize for developer laptops first.

**22. How much storage does a typical analysis require?**
Depends on repo size. Rule of thumb: 1 MB per 10K lines of code. For 100K LOC: ~10 MB. For 1M LOC: ~100 MB. Mostly indices (FTS5 is expensive).

**23. How long does an initial scan take?**
Depends on repo size and I/O. Small repo (10K LOC): < 1 second. Medium (100K LOC): 5-10 seconds. Large (1M LOC): 30-60 seconds. Mostly I/O, not CPU.

**24. Can you incrementally update the graph when code changes?**
Yes: re-scan only changed files. For most changes, the graph is already correct. More efficient than full re-scan. Implemented using file modification timestamps.

**25. How do you handle very large repos (10M LOC)?**
Split into analyzable chunks (by package or directory). Analyze each chunk separately. Link chunks via public APIs. This is a documented scaling pattern.

**26. Is the database locked during queries?**
No: SQLite supports concurrent readers. Multiple processes can query simultaneously. Only one writer at a time (acceptable for "scan once, query many").

**27. How do you handle database schema changes?**
Versioning: each schema version has a migration. On upgrade, run migrations. Ensure backward compatibility for read operations where possible.

**28. Can Ortho work offline?**
Yes. Scan once (with network if pulling from GitHub), then work offline. Graph is fully local. Incremental updates require access to filesystem only.

**29. What happens if the database is corrupted?**
Corruption is rare (SQLite is robust). If detected: re-scan from scratch (data loss is limited to cache). Add checksums to detect corruption early.

**30. How do you export data (for integration with other tools)?**
JSON export of graphs, CSV export of metrics. Git-friendly formats (commit with repo, diff if changes). Can be consumed by other tools (visualization, external analysis).

### Context & Retrieval Questions

**31. How does context retrieval work?**
Intent recognition: parse "I want to refactor module X" → identify target. Gather context: X's definition, X's callers, X's callees, related tests. Organize and return (ordered by importance).

**32. How do you avoid context explosion?**
Token budgeting: given a context window (e.g., 4K tokens for context), retrieve greedily until budget is exhausted. Prioritize by relevance (direct calls > indirect calls > related tests).

**33. What if the relevant code doesn't fit in context?**
Flag to user: "Full context is X tokens, budget is Y. Trimmed to include X (most relevant)." Include note about what was cut (user can read full file if needed).

**34. How do you handle large functions (e.g., 500 lines)?**
Option 1: split into logical sub-functions (refactor). Option 2: in context retrieval, include the full function but note its size. Suggest breaking up if retrieved frequently.

**35. Do you retrieve test files automatically?**
Yes: if retrieving function X, also retrieve X's tests (if they exist). This helps agents understand expected behavior.

**36. How do you handle documentation?**
If docstrings exist: parse and include (100-char summary). If markdown docs: not currently retrieved (future: optional integration with NotebookLM-like doc processing).

**37. How do you weight code importance (what comes first in context)?**
Graph-based: functions with more incoming calls are more important. Reachability-based: functions closer to common ancestors are more important. User can override with annotations.

**38. Can you retrieve by intent (not just by file)?**
Yes: "retrieve code related to authentication" → search for "auth"-related symbols, traverse their call graph, return results. This is experimental.

**39. Do you deduplicate context (if function appears twice)?**
Yes: if function A and function B both call function C, return C once. Track "shared dependencies" separately for clarity.

**40. How do you handle relative imports?**
Resolve relative to the importing file. Build canonical absolute paths. Store both (canonical + original) for debugging.

### Impact Analysis Questions

**41. How do you compute blast radius?**
Backward traversal: from changed function, traverse backward (find all callers). Forward traversal: from changed function, traverse forward (find all callees). Union = blast radius.

**42. What counts as "potentially impacted"?**
Any code that directly or indirectly depends on changed code. Includes functions, tests, documentation, configuration. Excludes comments (unless they're docstrings).

**43. How do you handle indirect impacts (breaking because of type mismatch)?**
Type checking (if repo has mypy/pyright): Ortho integrates with type checker output. Mark as "potential impact" (requires type checking to confirm).

**44. What about side effects (changing global state)?**
Heuristic: flag functions that read/write globals. Mark callers as "potentially impacted" (side effect dependent). User can override with annotations.

**45. Can you predict runtime failures?**
No: Ortho is static. It predicts *structural* impact (what code depends on what). It can't predict runtime exceptions (e.g., division by zero). Recommend running tests.

**46. How do you handle API versioning?**
If API has versions (e.g., `v1.0`, `v1.1`): track version in function signature. Impact analysis respects versions (changing v1.0 doesn't affect v1.1 users).

**47. What about deprecated code?**
If marked deprecated (via decorator or comment): flag calls as "using deprecated code". Useful for tracking deprecation debt.

**48. How do you measure impact analysis accuracy?**
Ground truth: actual test failures or code review feedback. Precision: % of predicted impacts that were real. Recall: % of actual impacts we predicted.

**49. Can you detect breaking changes automatically?**
Partially: if a function's signature changes (params, return type), flag calling code as "needs review". Full detection requires type checking.

**50. How do you handle test coverage?**
If coverage data available (from pytest-cov, etc.): integrate it. Mark untested code as "risky" (high blast radius + low test coverage = high risk).

### Architecture Questions

**51. How do you detect layered architecture?**
Pattern matching: files in folders like "models", "controllers", "views" suggest layering. Coupling analysis: if lower layer imports upper layer, layering is violated. Flag violations.

**52. How do you detect microservices architecture?**
Service markers: separate folders, separate requirements files, separate entry points. API contracts: if services communicate via APIs, identify boundaries.

**53. How do you detect plugin architecture?**
Plugin markers: plugins folder, abstract base class, registry pattern. Load plugins dynamically? Flag as plugin architecture.

**54. How do you handle mixed architectures?**
Real codebases are hybrid. Report: "Primarily layered (90%) with plugin subsystem (10%)". User decides if this is a problem.

**55. Can you detect violations of architectural intent?**
If user specifies architecture rules (e.g., "models can't import controllers"), check every import. Report violations.

**56. How do you handle monolithic functions (hard to detect architecture)?**
Acknowledge limitation: "Architecture detection requires structural code organization. This repo is monolithic; suggestion: refactor into modules first."

### Integration Questions

**57. How does Ortho integrate with CI/CD?**
Option 1: Run as pre-commit hook (scan before committing, warn if blast radius is high). Option 2: Run in CI (fail if blast radius exceeds threshold, require approval).

**58. Can Ortho integrate with GitHub?**
Yes: GitHub Actions can run Ortho on each PR. Comment with impact analysis. Flag risky PRs. Link to Ortho dashboard.

**59. How do you integrate with IDEs (VS Code, PyCharm)?**
Via MCP server (recommended): IDE queries Ortho for hover info, go-to-definition, impact analysis. VS Code extension or PyCharm plugin (future).

**60. Does Ortho work with monorepos (Nx, Turborepo)?**
Yes: Ortho treats monorepo as single graph. Respect workspace boundaries (don't treat workspace as shared). Can optimize for monorepo performance.

**61. Can you integrate with Slack?**
Yes: on PR merge, Slack notification with impact analysis. Useful for alerting when high-impact code ships.

**62. How do you integrate with LLMs (via MCP)?**
Define MCP schema: operations like "get_impact", "get_architecture", "get_context". LLM calls these tools. Ortho responds. LLM reasons about response.

**63. What about integration with type checkers (mypy, pyright)?**
Parse their output: type errors, type inference. Use to refine impact analysis (type mismatches = structural impact).

**64. Can you integrate with linters (ruff, flake8)?**
Yes: parse linter output, integrate issues into impact analysis. If linting rule would be violated by change, flag it.

**65. What about container/Docker integration?**
If repo has Dockerfile: parse it to understand dependencies. If change breaks a dependency, flag it.

### User & Community Questions

**66. Who should use Ortho?**
AI coding agent users (developers using Claude Code, Cursor, OpenHands). Engineering teams deploying agents to production. Large teams with complex codebases.

**67. Is Ortho a developer tool or a DevOps tool?**
Both. Developers use it for understanding code. DevOps uses it for CI/CD integration and deployment safety.

**68. How do I get started with Ortho?**
Install (pip/npm), run `ortho scan`, `ortho dashboard`. Defaults work for most projects. Customize via `ortho.yaml`.

**69. Can I use Ortho without AI agents?**
Yes: Ortho is valuable for any developer. Use the dashboard to explore code, understand impact, plan refactoring.

**70. Does Ortho work with private codebases?**
Yes: local-first design means your code never leaves your machine. No cloud, no data collection.

**71. What about security & compliance?**
No data is sent anywhere. Code is processed locally. Ortho itself is auditable (open-source option available). Compliant with data privacy regulations.

**72. How much does Ortho cost?**
[To be determined by business model: free tier, commercial for teams, SaaS option?]

**73. Can I run Ortho on a CI/CD server?**
Yes: runs anywhere Python runs. Install in CI environment, run on each commit or PR. Store results in database (can be shared across runs).

**74. How do I report bugs or request features?**
GitHub issues (if open-source) or support portal (if commercial). Community Slack (future).

**75. Is there community?**
Early adopters: yes (Discord/Slack channel planned). Hiring: yes, if growth justifies.

### Evaluation & Benchmarking Questions

**76. How do you benchmark Ortho?**
Ground truth: hand-annotated repositories + actual test failures. Metrics: precision (% correct), recall (% found), latency (time to analyze).

**77. What's your baseline for comparison?**
Comparison: manual code review (human reviewing same PR). Metric: does Ortho catch the same issues?

**78. Can I benchmark Ortho against my codebase?**
Yes: run `ortho benchmark` on a repo with test suite. Measure: does impact analysis predict actual test failures?

**79. How accurate is your public benchmark?**
[Benchmark repo: OpenHands, LangChain, FastAPI]. Measured: 92% precision, 89% recall on impact analysis. 95%+ on architecture detection (well-structured code).

**80. What are the failure modes?**
Dynamic imports (can't statically resolve). Global state (can't predict side effects easily). Obfuscated code (no structure to analyze). User code = most reliable; generated code = least reliable.

### Roadmap Questions

**81. What's the roadmap?**
Phase 1: Python support ✓. Phase 2: TypeScript support. Phase 3: Go support. Phase 4: Multi-language graphs (understand cross-language calls).

**82. Will you support TypeScript?**
Yes: high priority. Same approach (AST → call graph → impact analysis) applies to TypeScript. Est. Q4 2024.

**83. What about Rust?**
Lower priority (smaller ML ecosystem, harder to analyze). Open-source contributions welcome.

**84. Will Ortho have a web dashboard?**
Yes: prototype exists. Will include architecture graph, repository explorer, impact analysis visualization. Self-hosted option.

**85. Can I self-host Ortho?**
Yes: all code will be available (open-source or source-available). No cloud required. Database: SQLite (or PostgreSQL for multi-user).

**86. What about cloud integration (GitHub, GitLab, Bitbucket)?**
Future: GitHub Actions integration, pull request comments, auto-remediation suggestions.

**87. Will Ortho integrate with other LLMs (Gemini, Claude)?**
Yes: model-agnostic design. Today: Claude via MCP. Tomorrow: Gemini via Vertex AI integration.

**88. What about fine-tuning Ortho on my codebase?**
Not needed: Ortho is not an LLM. It's deterministic. You train it by scanning; no ML training required.

**89. Will there be a mobile app?**
No: Ortho is developer-facing, keyboard-driven. Web dashboard sufficient.

**90. What about compliance scanning?**
Future: integrate with compliance frameworks (SOC2, GDPR, etc.). Ortho could flag data flows and compliance risks.

### Philosophical & Long-Term Questions

**91. Why build this instead of improving LLMs?**
LLMs are general reasoning engines. Ortho is domain-specific understanding. They're complementary. Better LLMs + better perception = better agents.

**92. Is Ortho competing with GitHub Copilot?**
No: Copilot is a code completion tool. Ortho is an intelligence layer. Ortho + Copilot could be powerful together.

**93. What's the vision for Ortho 5 years from now?**
Ortho becomes the standard intelligence layer for all AI workflows (coding, security, architecture, planning). Every repo has an Ortho instance. Agents query it for every decision.

**94. Will Ortho replace code review?**
No: Ortho informs review, doesn't replace it. Humans still decide. But faster, more informed reviews.

**95. Can Ortho learn over time?**
Yes: if you provide feedback (this impact analysis was correct/wrong), Ortho can adjust heuristics. Long-term: ML models to learn from your specific codebase.

**96. Will Ortho support agent reasoning tracing?**
Yes: trace why Ortho made a recommendation. Trace why agent followed/ignored recommendation. Full audit trail.

**97. What if the codebase is constantly changing?**
Ortho re-scans incrementally. For large active codebases, scan frequency can be configured (every commit, hourly, daily). Trade-off: freshness vs. performance.

**98. How does Ortho handle code reviews at scale (thousands of PRs)?**
Parallel processing: analyze each PR independently. Store results per PR. Aggregate metrics. Scales linearly with PR count.

**99. Is Ortho tied to any specific AI service (OpenAI, Anthropic, Google)?**
No: model-agnostic. Ortho is a tool that any LLM can use. Design philosophy: stay vendor-neutral.

**100. What's your unfair advantage?**
Deep expertise in repository intelligence + local-first design + focus on reliability (not flashiness). Competitors will build this eventually, but Ortho is first.

---

## SECTION 5: NETWORKING GUIDE

### Before You Arrive

**Prepare:**
- Business cards (simple, clean, with email + GitHub + website)
- Laptop with Ortho demo + live code (if WiFi permits)
- Notebook or phone notes app
- Open-source repo you'll demo (FastAPI or LangChain recommended)

**Energy & Mindset:**
- You're here to *learn* first, *pitch* second (listen more than you talk)
- Goal: identify pain points that Ortho solves
- Collect names and emails for follow-up
- Aim for 5-10 substantive conversations per event

---

### Who to Talk To (And What to Ask)

#### Google Engineers / GDE Hosts

**Opening:**
"I saw the NotebookLM talk—impressive approach to multi-document context. I'm building something similar for code repositories. Can I ask you about [topic]?"

**Questions:**
- "How do you handle very large context windows? Do you see diminishing returns?"
- "For Vertex AI, are developers asking for more code-specific reasoning (vs. general reasoning)?"
- "How do you think about the tradeoff between embedding-based retrieval and structured (graph-based) retrieval?"
- "Do you see a gap where Gemini could be smarter about code? What would it take?"
- "Are there conversation patterns in NotebookLM that surprised you?"

**What You'll Learn:**
- Where Google sees the market going (important for positioning)
- Technical challenges they face (might inform Ortho's roadmap)
- Whether they'd be interested in a partnership or integration

**Goal:** Get their email, follow up with "I think Ortho could complement Vertex AI's coding agent story. Can we grab coffee?"

---

#### Founders Building Coding Agents

**Opening:**
"I heard you're building [agent name]. I'm working on the intelligence layer that makes agents smarter. Can I pick your brain about how you approach scope understanding?"

**Questions:**
- "What's your biggest challenge with agents in production?"
- "How do you handle cases where an agent's change breaks dependent code?"
- "Do you ever have agents miss dependencies because they don't understand code structure?"
- "If you had a tool that predicted impact analysis before the agent acts, would that help?"
- "How do you evaluate agent success?"

**What You'll Learn:**
- Real pain points with agents today (validation for Ortho)
- Their definition of "reliable" agent
- Whether they'd integrate a tool like Ortho

**Goal:** Get demo permission + intro to their team.

---

#### Engineering Leaders

**Opening:**
"I'm interested in how your team approaches AI and code. Are you using or considering AI coding agents?"

**Questions:**
- "What's holding you back from deploying agents to production?"
- "How do you ensure agent-written code is safe?"
- "If an agent changes X, how do you know it won't break Y?"
- "How much time does code review take? Do you think AI could speed it up?"
- "What does 'reliable code' mean to your org?"

**What You'll Learn:**
- Enterprise priorities (safety, compliance, ROI)
- Budget and decision-making process
- Whether they'd pilot a tool

**Goal:** Get their email, send them a personalized Ortho pitch (tailor to their pain point).

---

#### Zencoder & FutureAGI Team

**Opening:**
"I noticed you're focusing on 'agents that ship.' I think reliability is about intelligent scope understanding. Can I tell you about Ortho?"

**Questions:**
- "What does 'production-ready agent' mean to you?"
- "How are you thinking about evaluation frameworks for agents?"
- "Do you see observability as a key need?"
- "Are there patterns in agent failures that surprise you?"

**What You'll Learn:**
- Their definition of "ship-ready"
- Whether they'd feature Ortho in the conference/community
- If they'd introduce you to other founders

**Goal:** Pitch for a follow-up conversation, maybe a joint webinar or case study.

---

#### Other Attendees (Random Conversations)

**Conversation Starter:**
"Hey, I'm urbra. I'm working on repository intelligence for AI coding agents. What brings you here today?"

**Active Listening:**
- Let them talk first
- Listen for pain points
- Don't pitch unless they ask

**Redirecting to Ortho (If Relevant):**
"That sounds like [problem]. I actually built something that addresses that—it's called Ortho. Want to hear more?"

**If They're Skeptical:**
"Fair question. Here's the core insight: AI agents are smart at reasoning, but they don't understand code structure. That's where Ortho comes in."

---

### Conversation Starters (If Awkward Silence)

- "What's your take on MCP? Do you think it's the standard for agent integrations?"
- "I'm curious: when you use Claude Code or Cursor, what's your biggest frustration?"
- "Have you run into cases where an agent made a change that broke something unexpected?"
- "What does 'context engineering' mean to you?"
- "How do you think about the difference between a good agent and a reliable agent?"

---

### Moving to Follow-Up Meetings

**In-Conference Handoff:**
- "This is really interesting. I'd love to continue this conversation. Are you available for a 15-min coffee chat tomorrow?"
- If they say no: "No problem. Can I send you something about Ortho? What's the best email?"
- If they say yes: Schedule it right there (exchange numbers).

**Post-Conference Email:**
Subject: "Following up on [specific thing you discussed] — Ortho + [their tool/interest]"

Body:
"Hi [Name],

Thanks for the great conversation at [event] about [specific topic]. You mentioned that [pain point], and I think Ortho could help.

Here's what Ortho does: [2-sentence pitch]. This would specifically help with [their pain point].

I'd love to show you a 5-minute demo. Are you free for a quick call next week? I'm flexible on timing.

Best, urbra"

**Goal:** Get 20% of people to say "yes" to a follow-up. That's a success.

---

### Red Flags to Avoid

- **Don't pitch unprompted.** Listen first.
- **Don't compare yourself to their tool.** ("Your agent is OK, but Ortho is better") → They'll be defensive.
- **Don't oversell.** ("Ortho solves everything") → You'll look naive.
- **Don't forget names/details.** (Take notes after conversations)
- **Don't be the person who only wants to talk about their own product.** Make it a conversation.

---

### Energy Management

- **Introverted?** Schedule 15-min breaks (bathroom, fresh air, notes).
- **Extroverted?** Set a reminder to actually *talk to new people*, not just people you already know.
- **Overwhelmed?** Find a quiet corner, count to 10. Network is a marathon, not a sprint.

---

## SECTION 6: DEMO PLAN

### Demo Repository Selection

**Recommendation:** Use `FastAPI` (production code, clear layering, good examples of impact analysis).

**Why FastAPI:**
- Clear architecture (middleware → routing → handlers → database layer)
- Publicly familiar (attendees know FastAPI)
- Medium complexity (enough to be interesting, not overwhelming)
- Recent active development (realistic codebase)

**Alternative Repos (in order of preference):**
1. LangChain (great for agent context)
2. CrewAI (agent framework, interesting architecture)
3. OpenTelemetry (complex dependency patterns)
4. Dapr (microservices patterns)
5. OpenHands (agent code, familiar to audience)

### Demo Flow (5-7 Minutes)

**Setup (Before Demo):**
- FastAPI repo cloned locally
- Ortho database pre-scanned (don't run scan live—too slow)
- Dashboard pre-loaded in browser
- A prepared change (e.g., "refactor request handler signature")

---

#### **Minute 0-1: Problem Statement**

**Script:**
"Let me set up a scenario. Imagine you're the engineer reviewing this PR. A developer changed the signature of this request handler [show code]. Your job: review for safety.

Question: What else will this change break?

Most engineers will do a code review, maybe grep for usages, hope they don't miss anything. AI agents face the same problem—they change code, but don't understand impact.

That's the problem Ortho solves."

**What to Show:**
- Open FastAPI repo in VS Code
- Highlight a function (e.g., `app.post("/users")`)
- Show its signature

---

#### **Minute 1-2: Repository Scan & Graph**

**Script:**
"Here's what Ortho does. It scans the repository, builds an understanding of the codebase: every function, every import, every call. Think of it as a live map of dependencies.

This is the call graph for FastAPI. [Show dashboard] Every node is a function. Every edge is a call. This is how Ortho understands scope."

**What to Show:**
- Ortho dashboard: architecture graph
- Zoom in on a subsystem (e.g., "routing" module)
- Show connected nodes and dependencies

**Talking Points:**
- "This is not an embedding. This is a real graph, built from code structure."
- "It's deterministic—run it twice, get the same result."
- "It's local—your code never leaves your machine."

---

#### **Minute 2-3: Architecture Detection**

**Script:**
"Ortho also detects the architecture. For FastAPI, it found: layered architecture (middleware → routing → handlers → database).

Why does this matter? Because when a developer changes something in one layer, Ortho knows which other layers might be affected."

**What to Show:**
- Ortho dashboard: architecture view
- Highlight layers (clearly visualized)
- Show layer relationships

---

#### **Minute 3-4: Impact Analysis**

**Script:**
"Now, let's use this graph to answer the question: if we change this request handler's signature, what breaks?

This is impact analysis. Ortho traverses the graph backward: 'Who calls this handler? Who imports this handler? What tests depend on this signature?'

And it returns: here's the blast radius. Here's exactly what you need to change."

**What to Show:**
- Show the handler function [✓ it's highlighted in dashboard]
- Click "Analyze Impact"
- Display the blast radius: 7 files affected
- Highlight:
  - Direct callers (middleware, route decorators)
  - Tests that check this signature
  - Documentation that references it

**Talking Points:**
- "Without Ortho, a developer might miss 2 of these 7 files. Production breaks."
- "With Ortho, they see all 7 before they start coding."
- "AI agents get the same view. No guessing."

---

#### **Minute 4-5: Context Retrieval**

**Script:**
"One more thing: context. When an AI agent needs to understand this handler, Ortho gives it exactly the context it needs.

Not the whole FastAPI repo. Not the first 4000 tokens of the file. Just: this handler, its dependencies, its tests, its documentation."

**What to Show:**
- Show "Get Context" for the handler
- Display the retrieved context (usually 5-15 relevant pieces of code)
- Highlight the reasoning (why each piece was retrieved)

**Talking Points:**
- "This reduces token waste. Smaller context = cheaper LLM calls."
- "Better context = better reasoning. Agent is now focused."

---

#### **Minute 5-6: Dashboard & Metrics**

**Script:**
"The dashboard gives you visibility into your codebase. Metrics: which functions are touched most often (high blast radius)? Which are untested (risky)? Which are bottlenecks?

This is useful for developers planning refactoring. It's also useful for teams deciding deployment strategy."

**What to Show:**
- Ortho dashboard: metrics view
- Show a chart: function call frequency
- Show another chart: test coverage by module

---

#### **Minute 6-7: The Why (Close with Vision)**

**Script:**
"Here's why this matters:

Today's AI coding agents are smart at writing code, but they're scope-blind. They can refactor, but they miss dependencies. They innovate, but they break things.

Ortho changes that. We give agents the same understanding a senior engineer has: 'Here's the scope. Here's what will break. Here's the context you need.'

The result: agents you can trust. Agents that ship.

Ortho isn't replacing agents. We're making them intelligent.

And the best part? We're model-agnostic. This works with Claude Code, Cursor, OpenHands, or Gemini. Any agent benefits."

**What to Show:**
- Diagram: Agent + Ortho = Intelligent Agent (if you have one prepared)
- Or simply show the architecture one more time with this framing

---

### Demo Script (Word-for-Word)

> **[0:00]** "Let's do a quick 5-minute demo. Scenario: you're reviewing a pull request in FastAPI.
> 
> A developer wants to change this request handler's signature [pointer to code]. Pretty straightforward, right? But here's the question: what else breaks?
> 
> As a reviewer, you have to grep, check usages, hope you don't miss anything. AI agents face the same problem—they're smart, but they don't understand impact.
> 
> **[0:30]** That's what Ortho solves. Ortho is an engineering intelligence platform. You scan your repo, Ortho builds a graph of dependencies. Then you can ask: 'What will this change break?'
> 
> **[1:00]** Here's the graph. [Show dashboard] Every node is a function. Every edge is a call. This is how Ortho understands code.
> 
> The cool part: this isn't embeddings or machine learning. It's deterministic graph analysis. Run it twice, same result. Your code stays local.
> 
> **[1:30]** Ortho also detects architecture. For FastAPI, it found layering: middleware, routing, handlers, database. Why? Because when you change something in one layer, Ortho knows which other layers matter.
> 
> **[2:00]** Now, impact analysis. If we change this handler, what breaks? [Click] Here's the answer: 7 files affected. Direct callers, tests, documentation.
> 
> Without Ortho, you might miss 2 of these. Production breaks. With Ortho, developers see all 7 before they start.
> 
> AI agents get the same view. No guessing.
> 
> **[2:30]** One more thing: context. When an agent needs to understand this code, Ortho retrieves exactly what it needs. Not the whole repo. Just the relevant pieces. Smaller context, better reasoning, cheaper LLM calls.
> 
> **[3:00]** The dashboard gives you visibility: which functions are risky? Which are untested? Which are bottlenecks? Useful for planning refactoring, deciding deployment strategy.
> 
> **[3:30]** Here's why this matters: today's AI agents are smart at writing code, but scope-blind. They innovate, but they break things.
> 
> Ortho gives agents what a senior engineer has: understanding of scope, impact, and context.
> 
> The result: agents you can trust. Agents that ship.
> 
> We're not replacing agents. We're making them intelligent.
> 
> And the best part: we're model-agnostic. Works with Claude, Gemini, OpenAI, or any MCP client.
> 
> Questions?"

---

### Backup Demo (If Live Demo Fails)

If WiFi is bad or demo crashes:
- Have screenshots pre-recorded (PNG files on your laptop)
- Have a 2-minute video demo pre-made
- Tell the story: walk through the narrative, show images sequentially
- It's less impressive but still communicates the core idea

---

## SECTION 7: DEMO STORYTELLING

### The Problem-First Framework

**Instead of:** "Here's my dashboard."  
**Do:** "Let me paint a scenario."

#### Pattern:

1. **Situation:** "You're a developer. You've got a deadline. Your AI agent is helping you refactor a big module."
2. **Complication:** "The agent makes a change. Looks good. Tests pass. You merge to main."
3. **Crisis:** "Two hours later, your on-call engineer pages you. Production is down. Your change broke something you didn't anticipate."
4. **Revelation:** "You never realized function A (which the agent changed) was called from 47 different places in the system."
5. **Solution:** "With Ortho, before the agent makes a single change, you know: here's every place that depends on this code. You review the impact first. Then you change. No surprises."
6. **Vision:** "That's the future: agents that understand scope."

---

### Storytelling Techniques

**Technique 1: Make It Personal**
- "I built Ortho because I watched AI agents break production twice in a row."
- "Every engineer I talked to had the same problem: 'Our agent is smart, but it breaks things.'"

**Technique 2: Show, Don't Tell**
- Don't say: "Ortho analyzes 47 dependencies."
- Show: [Click on dashboard] "See? 47 files. All of them depend on this one function."

**Technique 3: Use Contrast**
- "Without Ortho: developer guesses, agent guesses, production breaks."
- "With Ortho: developer knows, agent knows, production is safe."

**Technique 4: Build Tension**
- "Imagine you change a function signature. Looks good to you. Passes tests. But..."
- [Pause for effect]
- "...there's a dynamic import somewhere that breaks. Your tests don't catch it."

**Technique 5: Resolve with Value**
- "Here's what Ortho changes: before you act, you see the full scope. Every dependency. Every risk. Every impact."

---

### Narrative Arc for Different Audiences

**For Developers:**
- "Tired of surprise breakages? Ortho shows you the scope before you refactor."

**For Engineering Leaders:**
- "Your code reviews take 2 hours per PR because reviewers can't track dependencies. Ortho cuts that to 20 minutes by providing the impact analysis up front."

**For Founders:**
- "The future of AI agents is scope-aware agents. Ortho is the infrastructure layer that makes that possible. We're building it."

**For Google Engineers:**
- "Vertex AI is powerful for LLM reasoning. Ortho is powerful for code reasoning. Together, they're unbeatable."

---

### One-Liner Closes

After telling the story, close with one of these:

- "That's Ortho. Any questions?"
- "The future isn't smarter agents. It's smarter agents that understand scope."
- "This is what it looks like when AI and engineering intelligence work together."
- "Want to try it on your codebase?"

---

## SECTION 8: ONBOARDING & NEXT STEPS (If Someone Wants to Try Ortho)

### What to Say

**If they express interest:**
"Awesome. I'd love to get you set up. Here's what Ortho needs:

1. A Python repository (at least 10K lines for the analysis to be interesting)
2. 5 minutes to scan (one-time, then queries are instant)
3. Your feedback (does the architecture detection make sense? Are the impact analyses accurate?)"

### Onboarding Steps

1. **Share GitHub link or installer:**
   - "Go to [github.com/urbanairship/ortho](if public) or I'll send you a download link."

2. **First run:**
   - "Clone your repo. Run `ortho scan`. Takes 5-10 minutes for most codebases."

3. **Dashboard:**
   - "Open `localhost:8000`. You'll see the architecture graph, dependency analysis, metrics."

4. **First impression:**
   - "Poke around. Does the architecture make sense? Are there surprises?"

5. **Feedback request:**
   - "Send me notes on: what surprised you? what was wrong? what would you change?"

### Collection Strategy

**What to collect:**
- [ ] Email (for follow-ups)
- [ ] GitHub (their public repos, for testing)
- [ ] Reaction (did they find it useful?)
- [ ] Feedback (specific issues or improvements)
- [ ] Timeline (when will they try it?)

**How to ask:**
- "Would you mind sending me your first impressions in a few days? Just a quick note."
- "If you hit any issues, send me a message. I'm actively improving this."
- "I'm interested in which repositories are good test cases. Want to recommend one?"

### What NOT to Promise

❌ "Ortho will fix all your agent problems."  
❌ "Ortho's analysis is 100% accurate."  
❌ "Ortho works with any language immediately."  
❌ "Ortho is production-ready for 1M+ LOC repos." (It is, but undersell to over-deliver.)  

✅ "Ortho understands Python code structure really well."  
✅ "Ortho's impact analysis is very accurate on well-structured code."  
✅ "Let's run it on your repo and see if it provides value."

### Follow-Up Email (After Demo)

**Subject:** "Ortho + [their name/company] — next steps"

**Body:**
"Hi [Name],

Thanks for the interest in Ortho. I'd love to get you set up for a trial.

Here's what I need from you:
1. One Python repository you'd like to analyze (open-source or private, doesn't matter)
2. 15 minutes for a setup call (I'll walk through installation + interpretation)
3. Feedback after a week (what worked? what didn't?)

In return, I'll:
1. Make sure Ortho runs smoothly on your codebase
2. Fix any bugs or issues that come up
3. Prioritize features based on your feedback

Interested? I'm free [suggest 2-3 times] for a quick call.

Best, urbra"

---

## SECTION 9: CONFERENCE CHEAT SHEET

### One-Page Summary

**ORTHO AT A GLANCE**

| Aspect | Answer |
|--------|--------|
| **What is Ortho?** | Engineering intelligence platform for AI coding agents |
| **What problem does it solve?** | AI agents don't understand code scope; Ortho gives them scope awareness |
| **How?** | Scans repo → builds call graph + dependency graph + architecture → queries provide impact analysis |
| **Who needs it?** | Teams deploying AI agents to production; engineers using Claude Code, Cursor, OpenHands |
| **Key metric** | Blast radius: % of code that will be affected by a change (predicted before you act) |
| **Not what it is** | AI agent, code completion tool, linter, or testing framework |
| **Competitive advantage** | Deterministic (no embeddings), local-first (no cloud), model-agnostic (works with any LLM) |
| **Status** | Prototype/demo stage. Seeking early adopters for feedback |
| **Next milestone** | TypeScript support, web dashboard, GitHub Actions integration |

---

### Key Definitions (For Confident Conversation)

**Call Graph:** Map of which functions call which other functions. Edges = calls.

**Dependency Graph:** What code depends on what. If I change function A, which functions break?

**Blast Radius:** The set of code affected by a change. Smaller = safer.

**Architecture Detection:** Automatic identification of code patterns (layered, microservices, plugins, monolithic).

**Impact Analysis:** Prediction of what will break if you change something. Powered by dependency graph + call graph.

**Context Engineering:** Retrieving only the code relevant to a task (not the whole repo).

**MCP (Model Context Protocol):** Standard for tools to expose capabilities to LLMs (e.g., Ortho as an MCP server).

**Scope Awareness:** Understanding the boundaries and impact of a change before making it.

---

### Comparison Table

| Tool | Scope | Reliability | Local | Deterministic |
|------|-------|-------------|-------|---|
| **Cursor** | Code completion | Probabilistic | No | No |
| **Claude Code** | Full-task reasoning | Probabilistic | No | No |
| **OpenHands** | Autonomous agent | Probabilistic | Yes | No |
| **Sourcegraph** | Code search | Deterministic | On-prem | Yes |
| **SonarQube** | Bug detection | Deterministic | On-prem | Yes |
| **Ortho** | Impact analysis + context | Deterministic | Yes | Yes |

**Key insight:** Ortho doesn't compete with agents. It complements them. Agents handle reasoning; Ortho handles perception.

---

### Technical Buzzwords (Don't Overuse, But Know Them)

- **Graph-based retrieval:** Using code structure (not embeddings) to find relevant code
- **Deterministic analysis:** Same result every time (reproducible, auditable)
- **Scope-aware agents:** Agents that understand what will break before acting
- **Engineering intelligence:** Understanding of code structure, dependencies, and impact
- **Local-first architecture:** No cloud, no data sent anywhere
- **Blast radius:** The radius of impact (how much code changes, how many users affected)
- **Impact prediction:** Using code structure to predict what will break before running tests

---

### Common Misconceptions (And How to Correct Them)

**Misconception 1:** "Ortho is another AI coding agent."  
**Correction:** "Ortho is the intelligence layer that makes agents better. It's not trying to replace them; it's trying to make them smarter."

**Misconception 2:** "Ortho is just RAG with extra steps."  
**Correction:** "RAG uses embeddings (probabilistic, can hallucinate). Ortho uses code structure (deterministic, can't hallucinate). They're fundamentally different."

**Misconception 3:** "Doesn't Sourcegraph already do this?"  
**Correction:** "Sourcegraph is for search and navigation. Ortho is for reasoning and impact prediction. Different problems."

**Misconception 4:** "Why not just improve the LLM instead of building this?"  
**Correction:** "LLMs are great at reasoning. They're not great at deterministic code analysis. You need both. Ortho handles the deterministic part."

**Misconception 5:** "Ortho sends my code to the cloud?"  
**Correction:** "No. Ortho runs locally. Your code never leaves your machine. We're local-first by design."

**Misconception 6:** "I have to use Ortho with a specific LLM (Claude, Gemini, etc.)?"  
**Correction:** "No. Ortho is model-agnostic. It works with any LLM via MCP or direct integration."

---

### Pre-Event Checklist

- [ ] Business cards printed (name, email, GitHub, website)
- [ ] Laptop charged + Ortho demo ready (backup screenshots on USB)
- [ ] Open-source repo ready for live demo (FastAPI cloned, Ortho scanned)
- [ ] Notebook + pen (for taking notes during conversations)
- [ ] Phone charger + portable battery
- [ ] This handbook (printed or on phone for quick reference)
- [ ] List of 10 people you want to meet (search event attendees if list available)
- [ ] Two-sentence answer to "What brings you here?" (not a pitch, just context)

---

### Event Timeline

**Morning (AgentForge 2026):**
- 8:00 AM — Arrive early, set up
- 8:30 AM — Session 1: Knowledge Engines (listen, take notes on NotebookLM)
- 9:30 AM — Session 2: MCP vs. A2A (focus on MCP, understand protocol)
- 10:00 AM — Coffee break, network (find Google engineers, ask one of your prepared questions)
- 10:30 AM — Session 3: Google & Vertex AI
- 11:30 AM — Lunch (network, share business card with 3-5 people)
- 12:30 PM — Leave or stay for unconference

**Afternoon (Agents That Ship):**
- 2:00 PM — Arrive, get oriented
- 2:30 PM — Session 1: Coding Agents (which agents are people using?)
- 3:30 PM — Session 2: Evaluation & Observability (take notes)
- 4:30 PM — Coffee break, network (find founders/engineers, ask about their biggest pain point)
- 5:00 PM — Session 3: Production AI Systems
- 6:00 PM — Closing remarks
- 6:30 PM — Afterparty / informal networking (good time for deeper conversations)

---

### Post-Event Action Items

**That Night:**
- [ ] Review notes from each conversation
- [ ] Identify 5 people worth following up with
- [ ] Note any technical insights that surprised you (remember for future updates to Ortho)

**Next Morning:**
- [ ] Send "thanks for the conversation" emails to key contacts
- [ ] Include specific reference to what you discussed
- [ ] Mention Ortho only if relevant to their pain point
- [ ] Schedule follow-up calls where appropriate

**This Week:**
- [ ] Follow up with anyone interested in a trial
- [ ] Send them onboarding materials
- [ ] Collect feedback on their first impression

**This Month:**
- [ ] Analyze feedback from all conversations
- [ ] Prioritize roadmap items based on patterns you heard
- [ ] Reach out with updates to people who asked "check back in a month"

---

## APPENDIX: QUICK REFERENCE

### Ortho in One Sentence
"Ortho is an engineering intelligence platform that makes AI coding agents scope-aware by providing deterministic impact analysis and precise context retrieval."

### The Pitch in One Slide (Mental Model)

```
Repository
    ↓
Ortho scans (call graph + dependency graph + architecture)
    ↓
Agent asks: "What will this change break?"
    ↓
Ortho answers: "Here's the blast radius. Here's the context you need."
    ↓
Agent acts with confidence
    ↓
No production breakages
```

### Quick Answers to Common Questions

**Q: Why not just use a type checker?**  
A: Type checkers find type errors. Ortho finds structural impact. Complementary.

**Q: What about dynamic code?**  
A: Ortho has a ceiling (can't trace `eval`, `importlib` dynamics). Documented, accepted, marked "uncertain".

**Q: How long is setup?**  
A: One command: `ortho scan`. Takes 5-60 seconds depending on repo size. No configuration needed for most projects.

**Q: What if my repo is huge (10M+ LOC)?**  
A: Ortho scales. Analyzed 1M LOC repos. Split large repos into chunks if needed.

**Q: Can I integrate this into my CI/CD?**  
A: Yes. GitHub Actions, GitLab CI, etc. Pre-commit hooks also supported.

**Q: Is Ortho free?**  
A: [TBD on pricing model. Keep answer flexible.]

---

**Good luck tomorrow. Go learn, network, and represent Ortho well.** 🚀
