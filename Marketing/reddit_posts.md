# Reddit Posts — Ready to Post

Post one per day, not all at once. Space them 2-3 days apart across subreddits.
Best time to post: Tuesday–Thursday, 10am–1pm EST.

---

## POST 1 — r/Python

**Title:**
```
I built a tool that catches architecture violations in AI-generated Python code – it scans your repo locally and remembers what you reject
```

**Body:**
```
Been using Claude Code and Copilot a lot lately. They write code fast, but they have no idea what my architecture is — they'll add a DB call inside a router, import a service from a utility module, introduce a circular dependency. All looks fine until something downstream breaks.

So I built Ortho. It scans a Python repo, builds a real architecture model (call graph, import graph, layer detection), and finds violations with evidence you can actually verify:

```
$ ortho guardrails

Scanning ~/flask... (3,218 files, 4.1s)
Architecture: layered  ·  confidence 0.92

VIOLATIONS  3 found

  ✗  Layer boundary: src/flask/cli.py → src/flask/app.py
     api layer imports from app layer (one-way rule violated)
     Evidence: src/flask/cli.py:47  from flask.app import Flask

  ✗  Circular dependency: flask.ctx ↔ flask.globals
     3-hop cycle: ctx → globals → app → ctx
     Evidence: src/flask/ctx.py:12  from .globals import _request_ctx_stack
```

The part I find most useful: when you reject a finding, it stores why. Next scan:

```
  ⊘  Layer boundary: src/flask/cli.py → src/flask/app.py
     Rejected 2026-07-15: intentional, Flask's own structure, not touching it
```

The AI stops suggesting changes to things you've already decided.

It's local-first — nothing leaves your machine. Works as a CLI and as an MCP server so Claude can call it directly during a coding session.

GitHub: https://github.com/AdithyaK3106/Ortho

Happy to answer questions about how the layer detection works or the architecture model.
```

**Flair:** Project / Showcase

---

## POST 2 — r/ExperiencedDevs

**Title:**
```
What do you actually do when AI-generated code violates your architecture? Curious how teams are handling this
```

**Body:**
```
We've been shipping a lot of AI-assisted code (Claude Code + Copilot). The code quality per-file is often fine. The problem we keep hitting is architecture: the AI has no model of our layer boundaries, so it'll happily import from a layer it shouldn't touch, introduce a new cycle, or dump logic into a module that already has coupling problems.

Curious how other experienced teams are handling this. A few approaches I've seen:

1. **Rely on PR review** — catch it when a human reviews. Works but slow and depends on the reviewer catching it.
2. **Linting rules** — tools like pylint can catch some of this but they're file-level, not cross-file architecture-level.
3. **Architecture tests** — packages like `import-linter` or `pytest-archon` that enforce layer rules in CI. Probably the most systematic.
4. **Nothing yet** — just accepting that AI code occasionally violates the architecture and fixing it later.

We ended up building our own tool (Ortho) that does cross-file architecture scanning with a feedback loop — when you reject a finding as a false positive, it stores the reason and cites it on future scans. Happy to share more if useful.

But genuinely curious what others are doing. Is this even a real problem for your teams or do you find the AI mostly stays within bounds?
```

**Note:** Don't lead with the tool. Let the discussion start, then mention Ortho naturally in comments when people ask.

---

## POST 3 — r/devops

**Title:**
```
Local-first architecture review for AI-generated code — no source sent to cloud (SOC2/HIPAA friendly)
```

**Body:**
```
Most AI code review tools (CodeRabbit, Greptile, Qodo) send your source to their cloud. For teams under SOC2, HIPAA, or any kind of IP restriction, that's a non-starter before you even compare features.

I built Ortho for exactly this. It runs entirely locally:
- Scans your Python repo (CLI + MCP server for Claude Code)
- Finds architecture violations with real evidence — layer boundary crossings, circular deps, coupling hotspots
- Stores decisions: when you reject a finding, next scan says "Rejected 2026-07-15: [your reason]" instead of repeating the alert
- Zero telemetry, zero network calls during scan, one SQLite file in your repo root

Output looks like this:

```
$ ortho guardrails

Architecture: layered  ·  confidence 0.92

VIOLATIONS  3 found

  ✗  Layer boundary: api/router.py → db/session.py
     Evidence: api/router.py:14  from db.session import get_session

  ✗  Circular dependency: services/auth ↔ services/user
     3-hop cycle: auth → user → models/user → auth
```

Install (Windows):
```
irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex
```

macOS/Linux:
```
git clone https://github.com/AdithyaK3106/Ortho.git && cd Ortho && ./install.sh
```

Currently Python primary, TypeScript secondary. Open to questions about the architecture detection approach.

GitHub: https://github.com/AdithyaK3106/Ortho
```

**Flair:** Tools / Projects

---

## COMMENT STRATEGY

When your post gets comments:

- Answer every technical question directly and honestly (including limitations)
- If someone mentions a competitor, acknowledge it fairly — "CodeRabbit is great if cloud is fine for you, Ortho is for when it's not"
- If someone asks "why not just use [X linter]", explain the cross-file/architecture-model distinction
- If someone finds a bug or limitation, acknowledge it and say you'll fix it — this builds credibility
- Don't argue with downvotes. If a comment is negative, either address it substantively or leave it

**Don't do:**
- Post the same content across subreddits on the same day (Reddit detects this)
- Use overly promotional language ("game-changer", "revolutionary")
- Delete posts that get negative feedback — it looks worse than leaving them
