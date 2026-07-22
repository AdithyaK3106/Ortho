# Ortho vs. Raw Claude Code — Head-to-Head on Flask

**Repo:** `repos/flask` (real open-source repo, 83 Python files, 1620 symbols)
**Method:** Same 3 questions asked two ways — (A) raw Claude Code with no tooling but file reads/grep, cold, no prior context; (B) `ortho` CLI after `ortho init` + `ortho scan` on the same repo.
**Date:** 2026-07-22

---

## Setup notes (real findings, not staged)

- `ortho init`/`scan` here means **this project's own CLI** (`apps/cli/dist/index.js`), not the global `ortho` on PATH — that resolves to an unrelated third-party npm package (`@gitlawb/ortho`) that happens to share the name and hangs indefinitely on `init`. Worth fixing before any external demo: either `npm link` this repo's CLI or rename the binary to avoid collision.
- `ortho analyze --impact` initially crashed (`ModuleNotFoundError: impact_analysis`). Root cause: pip had every Ortho Python package installed editable from a **stale temp path** (`...\Temp\sh_install_test\Ortho\packages\...`) left over from a prior `install.sh` test run, instead of the real repo path. Fixed with `pip install -e packages/<pkg>` against the actual project directory. This means a fresh clone + `pip install -e .` flow may have this exact failure mode for a new pilot user — worth a smoke test.
- Scan stats: 83/83 files, 1620 symbols, 601 imports, 3829 calls, 100% parse success, 392 calls persisted (3437 dropped as unresolved — expected for dynamic dispatch/stdlib calls).

---

## Task 1 — Blast radius of changing `ctx.py`

| | Raw Claude Code | Ortho |
|---|---|---|
| **Answer** | Traced `AppContext`/`_cv_app` usage via grep across `app.py`, `templating.py`, `__init__.py`, `globals.py`, `helpers.py`, `cli.py`, `debughelpers.py` | `Blast Radius: 2 file(s)` — `app.py`, `ctx.py` itself; confidence 67.9% |
| **Effort** | ~7 tool calls, 2 full file reads, manual reasoning about ContextVar semantics | 1 command |
| **Grounding** | Verified via real grep of import statements — genuinely correct, arguably *more thorough* than Ortho here (caught `globals.py`'s `_cv_app` sharing, which Ortho's direct-dependents view doesn't surface) | Real call/import graph traversal, but shallower — doesn't walk through `globals.py`'s proxy re-exports, so undercounts true blast radius |

**Verdict:** Interesting result — raw Claude's manual grep actually found broader (correct) blast radius than Ortho's current impact analyzer, which only reports direct file-level import/call edges and misses indirection through shared module-level state (`ContextVar`). This is a genuine gap in `impact-analysis`, not a talking point in Ortho's favor as-is. Worth flagging as a real limitation: **transitive/indirect coupling through shared globals isn't captured.**

---

## Task 2 — Architecture violations / oversized modules

| | Raw Claude Code | Ortho |
|---|---|---|
| **Answer** | No pre-set threshold, so self-invented ">500 lines" cutoff by eyeballing size distribution. Flagged `app.py` (1625), `cli.py` (1127), `sansio/app.py` (1013, self-selected as "also large") | `guardrails`: 4 violations, all `module_sizing`, threshold **500 lines** (a real configured rule): `app.py` (1625, +1125 over), `cli.py` (1127, +627), `ctx.py` (540, +40), `sansio/scaffold.py` (792, +292) |
| **Effort** | 3 tool calls, `wc -l`-style estimate, explicitly "not exhaustive" for layer violations | 1 command |
| **Grounding** | Threshold invented on the spot — different Claude session could pick 400 or 800 and get a different list. No layer-violation check performed (self-admitted partial) | Deterministic, same threshold every run, includes `ctx.py` and `scaffold.py` which raw Claude's ad hoc skim missed entirely |

**Verdict:** Clear Ortho win. Same repo, two different sessions of raw Claude would produce two different oversized-module lists depending on what cutoff it invents that day. Ortho's answer is reproducible and caught 2 real violations (`ctx.py`, `scaffold.py`) that raw Claude's manual skim missed.

---

## Task 3 — Should `app.py` be split? (with memory/feedback loop)

**Raw Claude:** "Possible incremental win, higher risk than reward" — reasonable, hedged, but has **no memory**. Every fresh session re-derives this from scratch and could contradict a decision the team already made last week.

**Ortho**, run twice:

```
$ ortho decide "Should we split flask/app.py into smaller modules?"
Recommended: Violation: module_sizing (confidence: 100%)
[memory] Seen before: guardrails: ...flask (2026-07-22)

$ ortho feedback reject "module_sizing src.flask.app" \
    --reason "app.py splitting deferred; too risky before v3.2 release, revisit after"
Recorded: reject for "module_sizing src.flask.app"

$ ortho decide "Should we split flask/app.py into smaller modules?"   # re-run
Recommended: Violation: module_sizing (confidence: 100%)
[memory] Rejected before (2026-07-22): app.py splitting deferred; too risky before v3.2 release, revisit after
[memory] Seen before: guardrails: ...flask (2026-07-22)
```

**Verdict:** This is the one thing raw Claude Code structurally cannot do — no session-to-session memory. Ortho surfaces the team's actual prior rejection and *why*, not just "seen before." This is the real differentiator, more than any single-shot analysis quality difference.

---

## Overall

| Dimension | Winner | Why |
|---|---|---|
| Single-shot repo Q&A depth | **Tie / raw Claude edge** | Raw Claude's grep-and-reason can be more thorough per-question; Ortho's impact analyzer currently misses indirect coupling through shared globals |
| Reproducibility / consistency | **Ortho** | Same command, same threshold, same answer every time — no invented cutoffs |
| Evidence format | **Ortho** | File:line, exact counts, not prose estimates |
| Cross-session memory & feedback | **Ortho, decisively** | Raw Claude cannot cite a past team decision; this is a structural capability gap, not a quality-of-reasoning gap |
| Speed | **Ortho** | 1 command vs. multiple tool calls/reads per question |

**Honest framing for the demo:** don't pitch Ortho as "smarter reasoning than Claude" — the impact-analysis result shows it currently isn't, on this repo. Pitch it as "deterministic, evidence-backed, and it remembers what your team already decided" — which is true and is the part raw Claude cannot replicate no matter how good the reasoning is.

## Bugs found while building this (worth fixing before a pilot)
1. `ortho analyze --impact` — impact analyzer misses transitive coupling via shared module-level state (e.g. `ContextVar`s, module globals) — undercounts blast radius vs. manual grep.
2. Global `ortho` binary name collides with an unrelated published npm package (`@gitlawb/ortho`) — a new user who ran `npm install -g` for something else could silently get the wrong tool.
3. Fresh-install packaging risk: editable installs can end up pointing at a stale/relocated path (as found here), breaking `impact_analysis` import silently until reinstalled from the correct location — worth a clean-clone smoke test.
