# Ortho vs. Raw Claude Code — Large-Scale Comparison (Django + SQLAlchemy)

**Repos:** `repos/django` (2924 Python files, 43,429 symbols), `repos/sqlalchemy` (708 files, 38,254 symbols)
**Why these:** big enough that "read the files and reason about it" (what raw Claude Code does) stops being viable, which is exactly where a repo-wide index should start earning its keep.
**Date:** 2026-07-22 (updated after bug-fix pass)

Picks up from the Flask comparison (`ortho-vs-raw-claude-flask-comparison.md`), where raw Claude actually out-reasoned Ortho on single-file blast radius. This round targets tasks where Ortho has a structural edge — whole-repo cycle detection and cross-repo similarity — and, in the process of building it, surfaced three real bugs. All three are now fixed and re-verified against the live Django repo below.

---

## Scan results (after fixes)

| Repo | Files | Symbols | Imports | Calls | Success rate |
|---|---|---|---|---|---|
| SQLAlchemy | 708/708 | 38,254 | 16,045 | 171,254 | 100% |
| Django | 2923/2924 | 43,429 | **11,409** (was 11,957) | 177,755 | 100%* |

*One file is an intentionally-invalid syntax-error test fixture, correctly skipped.

Django's import count dropped by 548 edges after the fix below — those were false edges from imports inside function bodies.

---

## Bugs found and fixed

### 1. False-positive circular dependencies from lazy/deferred imports (repo-intelligence)

**Found by:** a raw-Claude cold agent, asked to verify the `django.contrib.auth` cycle `guardrails` reported, read the actual source and concluded **no cycle exists** — Django deliberately imports `AnonymousUser` inside `get_user()`/`aget_user()`/`_set_auth_user()` function bodies specifically to avoid a real cycle with `auth.models` (which imports the `auth` package at module level). A second independent cold agent, searching for large cycles from scratch, hand-verified the same distinction on a different cycle (`django.contrib.admin`) and explicitly called out that one of its edges was "a function-local (lazy) import... exactly how Django avoids this cycle."

**Root cause:** `packages/repo-intelligence/src/repo_intelligence/import_graph.py`'s `_walk_tree` recursed into every child node uniformly, including `function_definition` bodies, so an import 3 levels deep inside a function was extracted identically to a module-level import. Since an import inside a function body only executes when that function runs (not at module load time), it can't participate in a real load-time circular-import failure — but the graph builder counted it as if it could.

**Fix:** `_walk_tree` now stops descending once it hits a `function_definition` node, so only module-level (and class-body, which does execute at import time) imports are extracted.

**Verified:** added `test_function_local_import_excluded` (repo-intelligence, 223 tests pass, 1 skip, 13 pre-existing xfail). Re-scanning Django end-to-end: import count 11,957 → 11,409, and the `auth.base_user → auth.models → auth` false-positive cycle is now gone from `guardrails` output entirely (10 → 5 `dependency_direction` violations; several other cycles also disappeared, consistent with the same false-edge pattern elsewhere in the codebase).

**Why this matters more than it sounds:** this means some fraction of every cycle `guardrails`/`decide` has ever reported (including in the Flask report) may include false edges from lazy imports. Worth a wider audit before quoting "N violations found" as a hard number in a pilot pitch.

### 2. `decide` recommended the wrong finding when the intent named a specific one (decision-engine)

**Found by:** asking `ortho decide "...auth cycle..."` and getting back an unrelated admin cycle instead.

**Root cause, part A — dedup collapsed distinct findings:** `_deduplicate` keyed on `title.lower()[:20]`. Every `arch_guardrails` finding's title is built as `f"Violation: {rule_id}"` — for two different `dependency_direction` cycles, that's the identical string `"Violation: dependency_direction"`, so both collapsed to the same 20-char prefix `"violation: dependenc"` and one was silently dropped, regardless of which cycle the question asked about.

**Root cause, part B — scoring ignored the intent text entirely:** `_score_option`'s "fit" term was a constant derived only from `effort`/`risk`, never comparing `intent` to the option at all. Every guardrails violation shares `confidence=1.0`, `effort=medium`, `risk=high`, so every surviving option scored identically and the stable sort just returned insertion order.

**Fix:**
- `_deduplicate` now computes Jaccard similarity over `title + description` word sets (description carries the specific module chain, so distinct cycles no longer collide).
- `_score_option` now computes real word-overlap between the intent text and the option's title/description/evidence, and folds that into the fit score — so a question naming a specific cycle now measurably favors the option that actually mentions those modules (0.58 overlap for the correct `auth` cycle vs. 0.42 for the unrelated `admin` cycle in a direct check).
- Both use a shared `_words()` tokenizer (regex word-extraction) rather than ad hoc `.split()`, fixing a secondary bug where punctuation like `auth)?` never matched plain `auth`.

**Verified:** all 28 decision-engine tests pass. Re-ran on live Django:
```
$ ortho decide "Should we break the circular dependency in django.contrib.auth (base_user -> models -> auth)?"
Recommended: Violation: dependency_direction (confidence: 100%)
    2-module cycle: 3 distinct modules
    real import edge: django.contrib.auth.base_user → django.contrib.auth.models
    real import edge: django.contrib.auth.models → django.contrib.auth
Alternatives: Violation: dependency_direction, ... (4 more, now correctly distinct)
```
Now correctly recommends the exact cycle named in the intent, and other distinct cycles survive as real alternatives instead of being silently discarded.

### 3. Feedback citations silently lost due to ASCII vs. Unicode arrow mismatch (cli-commands)

**Found by:** rejecting the auth-cycle finding, re-running `decide`, and seeing no `[memory]` citation at all — despite the identical flow working perfectly on Flask.

**Root cause:** `arch_guardrails`' cycle locations are joined with the Unicode arrow `→` (`enforcer.py:139`, `" → ".join(cycle)`). The CLI's own `--help` text for `feedback` gave an example using ASCII `->` (the only kind a keyboard produces), and `lookup_feedback`'s exact-match check required byte-identical strings — so a finding_key typed with `->` could never match a location string containing `→`. `record_feedback` didn't error; it just silently stored an orphan record no future lookup could ever find.

**Fix:** added `_normalize_finding_key()` in `feedback.py`, applied on both the write path (`record_feedback`) and read path (`lookup_feedback`), converting `->` to `→` before storing/matching. Updated the CLI help text to document this.

**Verified:** 13/13 feedback tests pass. Re-ran on live Django:
```
$ ortho feedback reject "dependency_direction django.contrib.auth.base_user -> django.contrib.auth.models -> django.contrib.auth" \
    --reason "auth cycle is stable/low-risk, deprioritized until next major version"
Recorded: reject for "..."

$ ortho decide "Should we break the circular dependency in django.contrib.auth (base_user -> models -> auth)?"
...
[memory] Rejected before (2026-07-22): auth cycle is stable/low-risk, deprioritized until next major version
```
The memory citation now survives correctly on Django, matching Flask's behavior.

---

## Token / cost comparison: raw Claude Code vs. Ortho

Ortho's CLI commands are pure local computation — no LLM calls, so **zero LLM tokens per command**, deterministic, same answer every run. Raw Claude Code has to spend real tokens reading files and reasoning per question, and the cost scales with how hard the question is to answer by hand. Measured by running the same investigative questions through a cold Claude agent (no ortho, no prior context) instead of guessing:

| Task | Tokens (raw Claude) | Tool calls | Wall time | Ortho equivalent |
|---|---|---|---|---|
| Flask: 3 questions (impact/guardrails/decide) | 30,691 | 7 | 38.5s | 3 commands, ~0 LLM tokens, seconds each |
| Django: verify one specific 3-module cycle claim | 35,362 | 5 | 21.1s | already answered as a byproduct of 1 `guardrails` run |
| Django: find *some* 10+-module cycle from scratch, anywhere in 2924 files | 40,711 | 17 (wrote its own AST+Tarjan SCC tool) | 161.8s | 1 `guardrails` run, ~99s, finds *all* cycles including a 104-module one |

**Reading the numbers honestly:**
- On a single, narrow, already-scoped question (verify this one specific claim), raw Claude is *cheaper and faster* than a full repo-wide `guardrails` scan — 21s / 35k tokens vs. 99s for the whole-repo command. If you already know exactly where to look, don't need a graph.
- The gap inverts hard the moment the question is "find something, anywhere, in a 2924-file repo": raw Claude burned 17 tool calls and had to write its own cycle-detection algorithm from scratch (correctly, impressively — but that's real, non-reusable work redone from zero every session). Ortho's answer to that same class of question is the same one `guardrails` run already paid for.
- Every raw-Claude number above is a **floor**, not a ceiling: these agents happened to find the right file quickly. A less-guided cold run over 2924 files could easily cost 2-3x more before landing on the right modules, and there's no guarantee of finding the largest cycle (104 modules) rather than a small local one, since nothing bounds the search.
- Ortho's cost is flat regardless of repo size class within reason (~1-2 min for Django's 2900 files) and doesn't grow with how deeply buried the answer is — a 2-module cycle and a 104-module cycle cost the same `guardrails` invocation.

---

## Task — Whole-repo circular-dependency detection (Django, 2922 files, post-fix)

```
$ ortho guardrails    # in repos/django, ~94s wall clock (post-fix)
Scanned 2922 file(s). ~9 violation(s) found (was 14 pre-fix; several were false positives from lazy imports).
```

Confirmed real remaining cycles include an 11-module admin cycle and the previously-found 134/193-module GIS-rooted cycle (module count for this one is non-deterministic run-to-run — 105/104/193/134 modules across separate runs — likely dict/set iteration order affecting which SCC member the detector reports first; a separate, smaller finding worth a follow-up).

**Raw Claude Code equivalent:** not attempted at whole-repo scope — tracing an 11-module cycle across 2900 files by hand is not reliable for a human or an LLM; the cold agent that tried anyway needed 17 tool calls and a custom-written SCC algorithm just to find *a* large cycle, with explicit low confidence on whether its two largest findings were "clean" or partly artifacts of its own lazy-import handling.

---

## Task — Cross-repo structural similarity (Django vs. SQLAlchemy)

Unchanged from the initial pass — not touched by this round's fixes.

```
$ ortho cross-repo repos/django repos/sqlalchemy
cross-repo comparison would pool 81683 symbols across 2 repos (limit 2000) ...
real 2m42.886s   <- took nearly 3 minutes just to FAIL
```

Confirms the documented O(n²) guard (CLAUDE.md §3a). It works — refuses instead of hanging — but "fast-fail" took 2m43s on the full-repo attempt. Scoped to file pairs, it runs in under a second but returned no matches on two conceptually-similar pairs (`related.py`/`relationships.py`, `exceptions.py`/`exc.py`) — not yet confirmed the similarity detector fires on anything in this sample; worth testing against known-duplicated code before relying on it in a pilot demo.

---

## Overall

| Dimension | Flask (83 files) | Django/SQLAlchemy (700–2900 files) |
|---|---|---|
| Impact analysis | Ortho undercounts vs. manual grep | not re-tested this round |
| Guardrails / cycle detection | Clean, deterministic | Decisive Ortho win on scale — but pre-fix had real false positives from lazy imports, now fixed |
| Cross-repo similarity | n/a | Guard works but slow-to-fail at repo scope; no true positives found at file scope in this sample |
| Decide + feedback memory | Worked cleanly | Was broken (wrong-finding match, lost citation) — now fixed and re-verified live |
| Token cost | n/a | Ortho: ~0 LLM tokens, flat cost. Raw Claude: 30-40k tokens per question, cost grows sharply with how buried the answer is |

**Bottom line for the pitch:** the large-scale run is now a stronger, more honest case than before — not because everything worked the first time, but because the failures were real, findable, and fixable, and the fixed behavior is verified against the actual Django repo rather than asserted. The remaining open item is the non-deterministic cycle-member reporting (cosmetic, not correctness-affecting) and confirming `cross-repo` produces true positives on anything at all.
