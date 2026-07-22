# Ortho — Demo Video Script
**Format:** Screen recording narration  
**Target length:** 3–4 minutes  
**Audience:** Everyone (developers, leads, pilot participants)

---

## SECTION 1 — The Problem (0:00–0:30)

**[Screen: a large Python repo open in a terminal. Dozens of folders visible.]**

> "You've just joined a new codebase. Or maybe you're returning to one you haven't touched in months.
> You need to understand it, fast — what the architecture is, what breaks if you change something,
> and what the right decision is. So you ask Claude."

**[Screen: Claude.ai chat open. User types: "What's the architecture of this repo?"]**

> "Claude gives you a reasonable answer — based on whatever you pasted in. But it can't see the repo.
> It doesn't know your call graph, your import boundaries, your past decisions, or what your team already tried and rejected.
> Every conversation starts from scratch."

**[Screen: Claude response — generic, no specifics. Pause for 2 seconds.]**

> "That's the gap. Ortho fills it."

---

## SECTION 2 — What Ortho Is (0:30–0:55)

**[Screen: terminal. Logo or title card: "Ortho — Engineering Decision Engine"]**

> "Ortho is an AI engineering platform that lives inside your repository.
> It scans your code, builds a live intelligence layer — call graphs, import graphs, architecture maps —
> and routes every question or decision through that context.
> It remembers what your team has already decided. And it enforces it."

**[Screen: quick montage — `ortho scan`, graph visualization, `ortho decide`, feedback log.]**

> "Let's walk through how to get started."

---

## SECTION 3 — Onboarding (0:55–1:45)

**[Screen: fresh terminal in a Python project root.]**

> "Step one: initialize Ortho."

```
ortho init
```

> "This sets up the local database — no cloud, no auth, everything stays on your machine."

**[Screen: `ortho scan` running, symbols appearing.]**

> "Step two: scan the repo."

```
ortho scan
```

> "Ortho parses every Python file with a tree-sitter AST adapter, extracts symbols, builds the call graph
> and import graph, and stores it all in a local SQLite database."

**[Screen: scan completes. Stats shown — e.g. 'Indexed 4,200 symbols across 38 modules'.]**

> "That's it. Ortho is now live on your codebase. From here, every command has full repo context."

---

## SECTION 4 — Core Features (1:45–3:00)

**[Screen: terminal]**

> "Ask anything about the codebase."

```
ortho ask "What does the ContextHub package own and what depends on it?"
```

> "Instead of you reading files, Ortho answers with BM25 search over the indexed symbols and architecture map."

---

**[Screen: terminal]**

> "Understand the blast radius before you change something."

```
ortho analyze --impact
```

> "This tells you exactly what breaks, what depends on what, and which subsystems are in the path of change —
> before you write a single line."

---

**[Screen: terminal]**

> "Catch architectural drift."

```
ortho guardrails --severity error
```

> "Ortho enforces one-way acyclic layer boundaries. Every violation comes with checkable evidence —
> the exact import, the file, the line. Not a heuristic. Not a guess."

---

**[Screen: terminal]**

> "Get a decision with citations."

```
ortho decide "Should we move the token optimizer into the orchestration layer?"
```

> "Multi-source synthesis. And here's the part that makes it different:"

**[Screen: output shows 'Previously rejected: ...' citation.]**

> "If your team already evaluated and rejected a similar approach, Ortho cites it. 
> The feedback loop is the moat — the tool gets smarter the longer you use it."

---

**[Screen: terminal]**

> "Plan a feature implementation."

```
ortho plan "add streaming support to the MCP server"
```

> "Ortho generates a concrete implementation path scoped to your actual codebase —
> not a generic tutorial."

---

**[Screen: terminal]**

> "Run a structured ASES workflow — with human approval at every stage."

```
ortho orchestrate
ortho status
ortho approve
```

> "PLANNER → ARCHITECT → BUILDER → TEST-DESIGNER → VERIFIER → REVIEWER.
> Ortho never auto-approves. Every stage requires your sign-off."

---

## SECTION 5 — Claude vs. Ortho (3:00–3:35)

**[Screen: side-by-side or split cut between Claude chat and Ortho terminal.]**

> "So what's the real difference?"

| | Claude (without Ortho) | Ortho |
|---|---|---|
| **Repo awareness** | Only what you paste | Full AST scan, live graph |
| **Architecture** | Inferred from snippets | Detected from actual structure |
| **Impact analysis** | Generic reasoning | Real call graph traversal |
| **Memory** | Resets every session | Persistent SQLite, searchable |
| **Decision history** | None | Cites past accept/reject |
| **Enforcement** | None | Layer boundary guardrails |
| **Workflow** | Ad hoc | Structured ASES stages |

> "Claude is brilliant at reasoning. Ortho gives it — and you — the ground truth to reason from."

---

## SECTION 6 — Close (3:35–3:50)

**[Screen: terminal. `ortho memory search "token optimizer"` running.]**

> "Every workflow you run, every decision you make, is stored and searchable.
> Your codebase builds up institutional memory over time."

**[Screen: fade to Ortho logo / project URL or GitHub link.]**

> "Ortho. Engineering decisions with evidence, memory, and enforcement.
> Get started with `ortho init` in your repo today."

---

## Production Notes

- **Total runtime:** ~3 min 45 sec at a natural narration pace (≈130 words/min)
- **Screen recording tips:**
  - Use a real Python repo with at least 20+ files so scan output looks meaningful
  - Pre-run `ortho init` and `ortho scan` if scan time is long; cut to results
  - For the Claude comparison, use a real chat screenshot showing a generic response
  - Zoom terminal font to 18pt+ for readability
- **Sections you can cut if running long:**
  - `ortho plan` demo (Section 4, bullet 5) — saves ~15 sec
  - The comparison table narration (read 3 rows instead of all 7) — saves ~10 sec
