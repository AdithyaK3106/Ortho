# Ortho — The Engineering Intelligence Layer for AI Coding

## Problem We Solve

Modern AI coding assistants (Claude, Copilot, Gemini, etc.) are powerful at **writing code**. They're terrible at **understanding context**:

- **No architecture awareness** — writes code that violates layer boundaries
- **No impact analysis** — changes break things the AI doesn't see coming
- **No engineering constraints** — ignores technical debt, coupling, cycles
- **No change strategy** — generates code without a plan

**Result:** AI-generated code looks good but breaks when integrated.

---

## Ortho as the Solution

Ortho is an **engineering intelligence layer** that sits *between* your developer and the AI coding tool. It answers:

✅ **What's the architecture?** — layer detection, subsystem detection, style inference  
✅ **What are the violations?** — layer boundaries, circular dependencies, module bloat  
✅ **What will break?** — blast radius analysis, affected modules, cascade risk  
✅ **What's the right approach?** — implementation paths, effort/risk scoring, strategy  
✅ **What have we learned?** — memory across all past runs, searchable knowledge base  

The AI tool then uses these answers to generate **architecturally aware, impact-safe code**.

---

## How It Works (3-Step Flow)

### 1. Developer Runs Ortho (Once Per Repo)

```bash
cd /path/to/repo
ortho scan          # Build the knowledge base
```

This parses the entire repository, extracts symbols/imports/calls, detects architecture, scores technical debt. Takes ~10-30 seconds depending on repo size. The results live in `.ortho/ortho.db` (local, encrypted, yours to keep).

### 2. Developer Asks the AI (With Ortho Context)

Instead of:
```
Claude: "Add caching to this API"
```

They can now ask:
```
Claude: "I want to add caching. Ortho says [paste guardrails/plan output]. 
What's the safest way given our architecture?"
```

Or better yet: **Claude calls Ortho directly via MCP tools** (see §5).

### 3. AI Generates Better Code

The AI now knows:
- The exact architecture (layered, microservices, flat, etc.)
- Which modules it can/can't touch
- What will break if it changes this file
- The recommended approach (3+ options, ranked by risk/effort)
- All past decisions made (memory search)

**Result:** Code that actually integrates.

---

## Integration Paths (Pick Your Tool)

### Path 1: Claude Code (MCP Server) ⭐ **Recommended**

Claude Code's native tool-calling system. Ortho exposes 5 MCP tools:

```
ortho_guardrails       # Check violations (layer, cycles, bloat)
ortho_decide           # Change impact + strategy
ortho_plan             # Feature planning
ortho_refactor         # Refactoring opportunities
ortho_memory_search    # Query what you've learned
```

**Developer experience:**
```
Claude: "Should I refactor this module?"
↓
Claude calls ortho_guardrails → gets violations
Claude calls ortho_refactor → gets bloat analysis
Claude synthesizes: "Yes, here's the plan..."
```

**Setup:**
```bash
pip install -e .
cd /path/to/repo
ortho scan
# Then use Claude Code with Ortho MCP server (configure in settings)
```

**Status:** MCP spec complete (see `docs/mcp-server-contract.md`), awaiting implementation.

---

### Path 2: VS Code Extension

Inline layer-boundary violations as you code. Shows:
- Which layer you're in (detected)
- What you can import from (allowed imports)
- What imports will break (forbidden imports)
- Quick-fix suggestions (move to different layer, use abstraction)

**Developer experience:**
```python
# user/models.py (Data layer)
from api/routes import create_user  # ⚠️ Red squiggle: forbidden import (Data ← API)
                                    # Suggestion: Create shared types in shared/types.py
```

**Status:** Planned for Phase 7.2+.

---

### Path 3: Git Hooks + CI/CD

Auto-run Ortho before commit/push:

```bash
# Pre-commit hook
ortho guardrails --severity error
if [ $? -ne 0 ]; then
  echo "Fix architecture violations before committing"
  exit 1
fi
```

**Developer experience:**
```bash
$ git commit -m "refactor: split core.py"
→ Ortho scan runs automatically
→ 3 new violations detected
→ Commit blocked
→ Developer fixes, commits again
```

**Setup:**
```bash
# Add to .git/hooks/pre-commit or use husky
ortho guardrails --severity error || exit 1
```

**Status:** Works today (no changes needed).

---

### Path 4: Terminal (Manual, Always Available)

Developers who like full control use Ortho standalone:

```bash
# Check violations before starting work
ortho guardrails

# Plan a feature
ortho plan "add user authentication"

# Decide before changing a file
ortho decide src/models/user.py

# Find refactoring opportunities
ortho refactor

# Review what you've learned
ortho memory search "layer_boundaries"
```

**Status:** Live and tested (200+ tests passing).

---

## Complete Package Checklist

### Core (Phase 7.1+) ✅
- [x] Repository intelligence (AST parsing, symbols, imports, calls)
- [x] Architecture detection (5 styles: layered, flat, microservices, MVC, hexagonal)
- [x] Architecture guardrails (layer boundaries, circular deps, module size)
- [x] Change impact analysis (blast radius, affected modules)
- [x] Feature planning (intent classification, implementation paths)
- [x] Refactoring advisor (bloat, coupling, cycles)
- [x] Engineering memory (every run persisted, searchable)
- [x] CLI tools (guardrails, decide, plan, refactor, memory)

### Integration (Phase 7.2+) 🚧
- [ ] MCP server for Claude Code
- [ ] VS Code extension
- [ ] GitHub Actions integration
- [ ] Pre-commit hook template
- [ ] JetBrains IDE plugin

### Admin/DevOps 🚧
- [ ] Installation wizard (detect Python version, package manager, OS)
- [ ] Telemetry opt-in (understand usage patterns, not tracking PII)
- [ ] Update checker (notify when new version available)
- [ ] License/support model (open source + commercial support)

---

## Why Ortho Matters

| Without Ortho | With Ortho |
|---------------|-----------|
| AI writes code, breaks things | AI writes code that integrates |
| Manual architecture review | Automated, instant feedback |
| Fragile context (ad-hoc notes) | Persistent knowledge base |
| Developers learn by failure | Developers learn by plan |
| Each project starts from scratch | Knowledge carries forward |

---

## Positioning (One Sentence)

> **Ortho gives AI coding tools the engineering intelligence they need to write code that actually works in production — without requiring developers to rearchitect their repos.**

---

## Go-to-Market Strategy

### Phase 1: Individual Developers (This Month)
- Target: Developers using Claude Code, Copilot, or local models
- Channel: GitHub, product forums, HN, Reddit
- Value prop: "Catch architecture problems before your AI writes code"
- Entry: `pip install -e .` → `ortho scan` → use with AI tool

### Phase 2: Teams (Q3 2026)
- Add: Team dashboards, shared memory, audit trails
- Channel: Company blogs, engineering conferences
- Value prop: "Enforce architecture as code, audit AI-generated code"
- Entry: Drop into existing CI/CD, get reports in Slack

### Phase 3: Enterprise (Q4 2026)
- Add: Custom architecture rules, policy enforcement, compliance
- Channel: Direct sales, integrations (GitHub Enterprise, etc.)
- Value prop: "Control what AI can and can't do in your codebase"
- Entry: Single-command deployment, managed SaaS option

---

## Competitive Advantage

1. **Real analysis, not LLM guessing** — uses AST parsing + graph algorithms, not another LLM
2. **Local-first** — all data stays on your machine; no cloud dependency
3. **Deterministic** — same repo = same results every time
4. **Production-ready** — 200+ tests, ASES methodology, battle-tested on real repos
5. **Extensible** — open architecture, custom rules, plugin ecosystem

---

## Success Metrics

### Developer Level
- Install-to-value time: <5 minutes (achieved: QUICKSTART.md)
- False-positive rate on violations: <5% (achieved: 92% reduction in task-018)
- Memory adoption (% of runs persisted): >80% (achieved: 100% on task-020)
- CLI adoption (% using CLI vs Python API): >50% (in progress with task-021+)

### Team Level
- Time to onboard new developers: -30% (via memory search)
- Architecture review cycle time: -70% (automated guardrails)
- Rework due to architecture issues: -80% (with impact analysis)

### Enterprise Level
- Policy violation rate: -95% (enforced via CI/CD)
- Audit trail completeness: 100% (every AI-assisted change logged)
- Time to resolve security/compliance issues: -60% (searchable memory)

---

## Roadmap

### Now (July 2026)
- ✅ Core Python engine complete
- ✅ CLI tools live
- ✅ Engineering memory
- 🚧 Documentation + QUICKSTART

### Next (August 2026)
- 🚧 MCP server implementation
- 🚧 VS Code extension
- 🚧 CI/CD templates (GitHub Actions, GitLab CI, Jenkins)

### Later (Q4 2026+)
- IDE plugins (JetBrains, Sublime)
- Team dashboards
- Custom rules engine
- SaaS hosting option

---

## For Your Friend (Building MCP Server)

See `docs/mcp-server-contract.md` for exact tool schemas. TL;DR:

1. **Expose 5 MCP tools:**
   - `ortho_guardrails(path)` → violations
   - `ortho_decide(intent, scan_path)` → change impact + strategy
   - `ortho_plan(intent, scan_path)` → implementation paths
   - `ortho_refactor(path)` → bloat/coupling/cycles
   - `ortho_memory_search(query)` → searchable knowledge base

2. **One constraint:** always pass explicit `scan_path` (no unbounded cwd scans)

3. **One required change:** structured JSON output (not text blobs)
   - Already designed in `docs/mcp-server-contract.md` §4
   - Small follow-up task, can be built now or alongside MCP

4. **Test against:** `repos/click/src/click` (known-good fixture, ~2 second scan)

---

## How to Present This

### To Developers
> "Ortho gives you a sanity check before asking AI to code. Catches layer violations, blast radius, and edge cases you'd miss. Takes 5 minutes to set up."

### To Teams/Leads
> "Ortho is an automated architecture review that runs on every change. Enforces your patterns, scales your team's knowledge, audits AI-assisted code."

### To Enterprises
> "Ortho is your control plane for AI-assisted development: enforce policies, audit all changes, scale engineering practices without adding headcount."

### To Investors (if relevant)
> "The AI coding market is $50B+ but 80% of failures are architectural, not algorithmic. Ortho fixes that blind spot. Today: open-source, tomorrow: enterprise + SaaS."

---

## Files to Reference

- `QUICKSTART.md` — new user onboarding
- `docs/mcp-server-contract.md` — MCP integration spec
- `.ases/tasks/` — full build evidence (ASES workflow)
- `status.md` — current state (200+ tests, Phase 7.1+ complete)
- `ortho-v3-frd.md` — complete functional requirements

---

## Next Actions

1. **[ ] Publish this doc** — put on `README.md` or prominent landing page
2. **[x] Build MCP server** — done; 10 tools live (`MCP_SETUP.md`), verified via real stdio protocol round-trip
3. **[ ] CLI marketing** — "Ortho: Engineering Intelligence for Your AI Assistant"
4. **[ ] Demo video** — 2-3 minute walkthrough (scan → guardrails → plan → AI integration)
5. **[ ] GH sponsorship** — make it easy for companies to fund development
6. **[ ] Run the five-pilot study** — the actual next blocker; see `PILOT_READINESS.md`. Everything above is secondary until real users have touched this.

---

**TL;DR:** Ortho is the missing intelligence layer between developers and AI coding tools. It's real, tested, and ready to integrate. The question isn't "how do we build this?" but "how do we get developers to use it?"

