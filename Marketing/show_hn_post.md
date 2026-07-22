# Show HN Post — Draft

**Post date:** Monday Week 2 at 9am ET (Day 8)
**URL to submit:** https://news.ycombinator.com/submit
**Title character limit:** 80 chars

---

## TITLE (pick one)

**Option A (recommended):**
> Show HN: Ortho – local-first architecture review for AI-generated code

**Option B:**
> Show HN: We built a local-first tool that catches architecture violations in AI-generated code

**Option C:**
> Show HN: Ortho – scan your repo, find what AI coding tools break, keep data local

---

## BODY TEXT

(Paste this into the "text" field on HN. Keep it under ~800 words. No markdown renders on HN — use plain text.)

---

Hey HN,

I've been building Ortho — a local-first engineering intelligence tool that scans a Python repo, understands its architecture, and catches violations before they merge.

The problem it solves: AI coding assistants (Copilot, Claude Code, Cursor, etc.) are great at writing code. They have no idea what your architecture is. They'll suggest adding a database call from a router layer, import a service from a utility module, or introduce a circular dependency across three packages — all in code that looks perfectly reasonable until it breaks something downstream. And because the AI has no memory of past decisions, it'll suggest the same pattern again next sprint.

Ortho runs locally (no source leaves your machine) and does three things:

1. **Scans your repo** — builds a call graph, import graph, symbol index, and architecture model from your actual code. Takes ~10-30 seconds for 1,000 files.

2. **Finds real violations** — layer boundary violations, circular dependency chains, bloat and coupling hotspots. Every finding cites real, checkable evidence: the actual import edge that crosses a boundary, the actual cycle chain, the actual line count.

3. **Remembers what you rejected** — when you flag a finding as a false positive or accept it, Ortho stores that. Next scan: "Rejected 2026-07-10: violates service boundary. Reason: this is an intentional shortcut pending refactor." The AI tool doesn't need to reinvent your decisions.

**Why local-first?** A lot of the teams I've talked to can't send source to a third-party cloud — SOC2 scope, HIPAA, FedRAMP, contractual IP clauses. CodeRabbit, Greptile, and Qodo are cloud-based, so they're structurally off the table before a feature comparison even starts. Ortho works entirely from your machine. The only file it writes is `.ortho/ortho.db` — a SQLite database in your repo root.

**How to try it:**

Windows (PowerShell one-liner):
```
irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex
```

macOS / Linux:
```bash
git clone https://github.com/AdithyaK3106/Ortho.git && cd Ortho && ./install.sh
```

The installer clones the repo, pip-installs all 13 packages in editable mode, builds the TypeScript CLI, and scans whichever directory you point it at. After that:
```bash
cd your-repo
ortho guardrails
ortho decide "add Redis caching to the API layer"
```

Prerequisites: git, python, pip, node, npm.

There's also an MCP server — 10 tools — so Claude (or any MCP-compatible assistant) can call Ortho directly during a coding session and get architecture context before generating code.

**Current state:** Python primary (tree-sitter AST, Python 3.8–3.13), TypeScript secondary. 1,375 tests, independently audited. We ran a false-positive audit on 9 real repos (click, flask, requests, django, celery, and four internal ones) — went from 91% FP rate to effectively 0% on real architecture violations. The known limitation I'll be honest about upfront: the redesigned layer-boundary checker is unit-tested but hasn't yet fired on a real "this is genuinely wrong" violation in the wild — that's what pilot users are for.

**Looking for:** 5 engineering teams willing to run Ortho on a real internal repo for 30 days and give honest feedback. If you're already shipping AI-generated code and have hit the "but it broke the architecture" problem, I'd love to talk.

Links: [QUICKSTART.md] | [GitHub: AdithyaK3106/Ortho](https://github.com/AdithyaK3106/Ortho) | urbrain369@gmail.com

---

---

## COMMENT RESPONSE PLAYBOOK

Prepare these before posting. Engage every comment within 2 hours.

**"Does this work with [language]?"**
> Python is primary — full AST, call graph, import graph. TypeScript is secondary. Go, Java, Rust are on the roadmap but not built yet. If you're Python-heavy, it'll work today.

**"How is this different from CodeRabbit / Greptile / Qodo?"**
> All three are cloud-based — your source goes to their servers. If your company has any compliance requirement or just doesn't want source leaving the machine, they're off the table before features matter. Ortho runs entirely locally. That's the structural difference.

**"Can't I just write linting rules?"**
> Linting works at the file level. Ortho builds a cross-file architecture model — it knows that `api/router.py` importing from `db/session.py` crosses a layer boundary you defined, regardless of what either file looks like individually. It's not a linter.

**"The false-positive rate sounds concerning — 91% to 0% means the tool changed dramatically."**
> Honest answer: the old heuristic for layer detection was generating alerts based on directory naming patterns alone. The new version validates against the actual import graph and requires real evidence. The "91%" was from the old behavior, not current. Current: 0% on 9 repos. But I'll admit the layer-boundary checker has never caught a genuine violation on a real production repo yet — that's still purely synthetic-fixture validated. Pilot users will be the proof.

**"Why SQLite? Doesn't that limit performance?"**
> For local, single-user use, SQLite with FTS5 (for BM25 search) and sqlite-vec (for embeddings) is more than sufficient. Scan time is ~10-30 seconds per 1,000 files. The tradeoff we made: no server, no auth, no setup — just a file in your repo root.

**"Is this open source?"**
> [Answer based on your licensing decision before posting]

---

## CHECKLIST BEFORE POSTING

- [ ] QUICKSTART.md is polished and tested on a clean install
- [ ] GitHub: https://github.com/AdithyaK3106/Ortho — confirm public and README looks good
- [ ] Windows install tested: `irm https://adithyak3106.github.io/Ortho-community/install.ps1 | iex`
- [ ] macOS/Linux install tested: `git clone https://github.com/AdithyaK3106/Ortho.git && cd Ortho && ./install.sh`
- [ ] Terminal demo GIF/screenshot ready to link or attach
- [ ] Respond to every comment within 2 hours of posting
- [ ] Post at 9am ET Monday (peak HN traffic)
- [ ] Have email ready: urbrain369@gmail.com
