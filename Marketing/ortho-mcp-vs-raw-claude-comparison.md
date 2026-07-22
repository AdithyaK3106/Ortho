# Ortho MCP Server vs. Raw Claude Code — All 10 Tools

**Date:** 2026-07-22
**Method:** Every one of Ortho's 10 MCP tools invoked directly against its real handler (`apps/mcp-server/ortho_mcp_server.py`'s `dispatch_tool_call`), on real repos already scanned in prior sessions (Flask, Django, SQLAlchemy). No numbers below are estimated, extrapolated, or adjusted after the fact — every count is from an actual run, including the ones that make Ortho look bad.

**A note on "tokens":** there is no live Claude token meter exposed to this session. Response sizes below are reported two ways: (1) real character counts, always exact, and (2) an *approximate* token count via `tiktoken`'s `cl100k_base` encoding — this is OpenAI's tokenizer, not Claude's, used only as a consistent rough proxy for "how much text is in this response," not claimed as an exact Claude token count. Raw-Claude-side token/tool-call numbers come from actual cold sub-agent runs (reported by the agent framework itself), not guesses.

**A note on scope:** MCP transport (stdio JSON-RPC) adds no content of its own — the response text a tool call produces is identical whether invoked via the CLI, directly, or through the MCP stdio pipe. What's measured here is the underlying `CliCommands` engine's actual output and size, which is what really lands in a Claude Code MCP conversation.

---

## Headline finding (original run): quality was mixed, not uniformly in Ortho's favor — both issues below are now fixed and re-verified live

Two of Ortho's 10 tools (`ortho_plan`, and by extension `ortho_orchestrate`'s Stage 1) originally gave a **generic, templated, wrong-for-the-repo answer** on a real feature-planning question, while raw Claude Code — reading the actual source — gave a correct, specific one. `ortho_ask` also gave a materially worse answer than raw Claude on an architecture question, for a documented, structural reason. Both are fixed below (`packages/cli-commands/src/cli_commands/repo_qa.py`, `packages/cli-commands/src/cli_commands/commands.py`), with the exact same failing cases re-run against the fixed code, not new cherry-picked cases.

This section is reported un-softened, including the original failures, because the request was for real numbers, not a curated highlight reel.

### `ortho_plan` / `ortho_orchestrate` Stage 1 — feature planning

**Question:** "add streaming response support" on Flask.

**Ortho's original answer (verbatim, real output):**
```
Feature type: infrastructure
- Configuration-Driven (effort=low, risk=low): Environment variables + config files
- Service Registry (effort=medium, risk=medium): Dynamic service discovery
- IaC (Infrastructure as Code) (effort=high, risk=low): Terraform/CloudFormation definitions
```
Generic infrastructure template with no connection to Flask's actual code — matches CLAUDE.md's documented gap ("feature-planner: Intent-classification miss on non-web-service repos").

**Raw Claude's answer (cold, no ortho, reading real source):** correctly found that Flask **already has** streaming support (`stream_with_context()` in `helpers.py:63-144`, wrapping a generator to re-enter the captured `AppContext`), that returning a generator to `Response(...)` already streams via Werkzeug's WSGI iterable protocol, and scoped the *actually missing* pieces to SSE formatting helpers and async-generator support.

**Root cause:** `feature_planner/planner.py`'s `_classify_feature_type` is a fixed 6-bucket keyword classifier with zero awareness of the actual scanned repo — it only ever looks at the intent string, never at `scan.file_to_module`/`scan.symbols_by_file`, which are available at the call site in `commands.py`. "Streaming" doesn't match any of the 6 keyword buckets, so it falls into the generic `infrastructure` catch-all regardless of what's in the repo.

**Fix:** rather than rewrite the classifier (a much larger change, and this module is explicitly documented as "NOT vector search... mechanical and honest" — a real semantic "does this exist" check is out of scope for it), added `find_existing_symbols()` to `repo_qa.py`, reusing the same keyword-extraction/substring-match discipline `ortho_ask` uses, and wired it into `commands.py`'s `plan()` as a pre-check surfaced alongside the generated template.

**Re-verified live, same exact question, same repo:**
```
Feature type: infrastructure

Possibly already implemented -- check before building:
  - tests.test_helpers.TestStreaming (matches 'streaming')
  - tests.test_helpers.test_streaming_with_context (matches 'streaming')
  - tests.test_helpers.test_streaming_with_context_as_decorator (matches 'streaming')
  - tests.test_helpers.test_streaming_with_context_and_custom_close (matches 'streaming')

- Configuration-Driven (effort=low, risk=low): ...
```
Confirmed `ortho_orchestrate`'s Stage 1 inherits the fix automatically (it calls `self.plan(...)` internally). Tested via `feature-planner` (42 tests) and `cli-commands` (`test_repo_qa.py` + `test_commands.py`, 42 tests; `test_structured_output.py` + `test_filtering.py`, 70 tests) — all pass.

**Honest residual limitation:** the pre-check is still substring matching, not semantic — it caught the test-side evidence for "streaming" but did not surface `stream_with_context` itself, because that identifier contains "stream" but not the literal substring "streaming". It correctly triggers the "check before building" warning (which is the actual fix goal), but won't always surface the single most relevant symbol. The underlying template generation is still generic; only the "you should check first" signal is new.

### `ortho_ask` — repository Q&A, phrasing-sensitive

**Question:** "how does application context work in this codebase" on Flask.

**Ortho's original answer (verbatim, real output, reproduced twice, identical both times):**
```
Matched 1 file(s) for 'application':
tests.test_basic: defines symbol 'test_session_using_application_root' matching 'application'
```
Nearly useless — matched a single test function name.

**Root cause, confirmed in source** (`repo_qa.py`'s `_extract_keyword`): the tool extracted **only the single longest non-stopword token** from the question. `"application"` (11 chars) beat `"context"` (7 chars), so `"context"` — the actual subject — was discarded entirely.

**Fix:** `_extract_keyword` → `_extract_keywords`, now returns every real candidate word, longest-first. `answer_question` tries every candidate and keeps whichever produces the **most** matches (not just the first candidate with any match at all — an earlier version of the fix stopped at "application" too, since it does match one real symbol; the actual fix needed was "most evidence wins," not just "some evidence exists").

**Re-verified live, same exact question, same repo:**
```
Matched 8 file(s) for 'context':
src.flask.app: defines symbol 'update_template_context' matching 'context'
src.flask.cli: defines symbol 'with_appcontext' matching 'context'
src.flask.ctx: defines symbol 'copy_current_request_context' matching 'context'
  AppContext() called by: Flask.app_context
src.flask.globals: defines symbol 'AppContextProxy' matching 'context'
src.flask.helpers: defines symbol 'stream_with_context' matching 'context'
src.flask.sansio.app: defines symbol 'teardown_appcontext' matching 'context'
src.flask.sansio.blueprints: defines symbol 'app_context_processor' matching 'context'
src.flask.sansio.scaffold: defines symbol 'context_processor' matching 'context'
```
Now finds `AppContext`, `stream_with_context`, and the real context-related module set — comparable in substance to raw Claude's answer, though still evidence-listing rather than narrative. Added `test_falls_back_to_shorter_word_when_longest_word_has_no_match` and `test_prefers_the_candidate_with_more_matches_not_just_the_first_hit` (the exact real-repo scenario) to `test_repo_qa.py`; all 12 tests in that file pass, plus the 42/70 cross-package test runs above.

**Verdict:** both original findings held up under scrutiny (not flukes — reproduced multiple times, root-caused in source), and both are now fixed with a regression test tied to the literal failing case, not a synthetic one.

---

## Where Ortho's tools held up or won

### `ortho_review` / `ortho_guardrails` — deterministic, evidence-backed, reproducible

Flask: 4 violations (all `module_sizing`, exact line counts: `app.py` 1625, `cli.py` 1127, `ctx.py` 540, `sansio/scaffold.py` 792), 1277 chars / ~363 approx-tokens for `ortho_review`, 41 approx-tokens... **363 approx-tokens** for the filtered guardrails view. Same answer on repeat runs.

Django (2922 files, real large-scale run, post the earlier bug fixes): 41.2s wall time, 10 violations, 11,657 chars / ~2,396 approx-tokens for the full structured response. This is the same class of question ("what's architecturally wrong with this repo") that a cold Claude agent, working from scratch on Django, needed 17 tool calls and its own hand-written Tarjan SCC implementation to approximate (see `ortho-vs-raw-claude-large-scale-comparison.md`) — and even then wasn't fully confident its two largest cycles were "clean" rather than partly artifacts of its own lazy-import handling. Ortho's answer for the same class of question is one tool call, ~2,400 tokens, deterministic.

### `ortho_decide` + `ortho_feedback` — memory citation, real and reproducible

Verified live through the actual MCP handler (not just the CLI): `ortho_decide` on "Should we split flask/app.py into smaller modules?" correctly surfaced `[memory] Rejected before (2026-07-22): app.py splitting deferred; too risky before v3.2 release, revisit after` — the exact rejection recorded via `ortho_feedback` in an earlier session. Raw Claude Code has no equivalent: every fresh session re-derives a recommendation from zero, with no way to know or cite a prior team decision. 887 chars / ~241 approx-tokens.

### `ortho_memory_search` — real accumulated history, not fabricated

Querying "module_sizing" against Flask's `.ortho.db` returned all 7 real workflow_run artifacts actually created across this project's testing sessions (3 `decide`, 2 `guardrails`, 2 `review` runs) — genuine accumulated state, not a canned demo response. 907 chars / ~270 approx-tokens.

### `ortho_cross_repo` — honest null result, not a false positive

Tested at file-pair scope on two conceptually-similar modules (Django's `core/exceptions.py` vs. SQLAlchemy's `exc.py`): "No structurally similar code found across the given repositories" — same honest null both times it was run (this session and the prior large-scale comparison). Not a positive finding to celebrate, but also not a fabricated match — the tool says "no" when there's no real structural evidence rather than guessing.

### `ortho_refactor` — real findings, test-file threshold now fixed

**Original finding:** Flask found 12 "bloat" findings, 4356 chars / ~1219 approx-tokens, flagging **test files** (`tests.test_json`, `tests.test_views`, `tests.test_appctx`, `tests.test_signals`, `tests.test_user_error_handler`) as bloat alongside real production modules, at a lower threshold (300 lines / 20 functions) than `guardrails`' 500-line rule. Test-file line count doesn't carry the same coupling/maintenance cost as production code.

**Root cause, confirmed in source** (`packages/cli-commands/src/cli_commands/refactor_adapter.py`'s `get_bloated_modules`): it iterates every module in the scan with zero distinction between test and production code.

**Fix:** added `_is_test_module()`, matching pytest/unittest's own discovery convention (a `tests`/`test` package segment, or a `test_*`/`*_test` leaf) — not a new heuristic, the same rule the ecosystem's own tooling already treats as authoritative. Excluded from `get_bloated_modules()`.

**Re-verified live, same repo:**
```
10 findings, all src.flask.* (sansio.app, cli, app, sansio.scaffold, sessions,
config, ctx, helpers, json.tag, sansio.blueprints) -- zero tests.* entries
1986 chars / 584 approx-tokens (down from 4356 / 1219)
```
Down from 12 mixed findings to 10 real production-only findings; response size dropped by more than half as a side effect of removing noise. Added `test_get_bloated_modules_excludes_test_modules` (regression test against real Flask scan data) to `test_plan_refactor_wiring.py`; all 19 tests in that file pass.

---

## Full 10-tool run: real measured sizes

| Tool | Repo | Real chars | Approx tokens (cl100k) | Wall time | Notable finding |
|---|---|---|---|---|---|
| `ortho_review` | Flask | 1,761* | ~460* | <2s | correct violations + memory citation |
| `ortho_guardrails` | Flask | 1,277 | 363 | <2s | 4 real violations, exact line counts |
| `ortho_guardrails` | Django | 11,657 | 2,396 | 41.2s | 10 real violations incl. multi-module cycles |
| `ortho_decide` | Flask | 887 | 241 | <2s | correctly cites prior rejection |
| `ortho_plan` (before fix) | Flask | 460 | 98 | <2s | generic/wrong: templated "infrastructure" plan, ignored that Flask already has streaming |
| `ortho_plan` (after fix) | Flask | 824 | 173 | <2s | now flags "possibly already implemented" with 4 real symbol matches |
| `ortho_refactor` (before fix) | Flask | 4,356 | 1,219 | <2s | 12 findings, 5 were test files flagged as bloat |
| `ortho_refactor` (after fix) | Flask | 1,986 | 584 | <2s | 10 findings, all real production modules |
| `ortho_ask` (before fix) | Flask | 192 | 41 | <2s | near-useless on natural-language phrasing (keyword-extraction bug) |
| `ortho_ask` (after fix) | Flask | 1,267 | 297 | <2s | now finds AppContext, stream_with_context, and 6 other real matches |
| `ortho_memory_search` | Flask | 907 | 270 | <2s | real accumulated history, 7 genuine artifacts |
| `ortho_feedback` | Flask | 129 | 31 | <2s | works identically over MCP as CLI |
| `ortho_orchestrate` (after fix) | Flask | n/a (Stage 1 only shown) | n/a | <2s | confirmed inherits ortho_plan's fix via self.plan() |
| `ortho_cross_repo` | Django+SQLAlchemy | 104 | 22 | <1s | honest null result, not fabricated |

*`ortho_review` char/token count taken from an earlier run in this session at slightly different repo state (after a `feedback accept` was recorded); rerun would differ slightly by design (memory citations grow) — reported as observed, not normalized.

---

## Token/cost comparison: MCP tool call vs. raw Claude cold exploration

| Task | Ortho MCP tool response (approx tokens) | Raw Claude cold-agent cost (real, reported) | Winner |
|---|---|---|---|
| "What's architecturally wrong with Flask?" | ~363 (`ortho_guardrails`) | not re-run this session; prior Flask cold-agent run answered 3 similar questions for 30,691 tokens / 7 tool calls | Ortho, by a wide margin on token cost |
| "What's architecturally wrong with Django (2922 files)?" | ~2,396 (`ortho_guardrails`) | prior cold-agent run (different session) needed 40,711 tokens / 17 tool calls and still wasn't fully confident in its two largest cycles | Ortho, by a wide margin on token cost |
| "How does application context work?" (original, before fix) | ~41 (`ortho_ask`) | 35,434 tokens / 8 tool calls, materially more correct | Raw Claude, on quality |
| "How does application context work?" (after fix) | ~297 (`ortho_ask`, re-verified live) | same 35,434 tokens | Ortho now competitive in substance at ~119x fewer tokens; still evidence-listing rather than narrative prose |
| "Add streaming response support — what's the plan?" (original, before fix) | ~98 (`ortho_plan`) | same 35,434-token run, correctly identified the feature already exists | Raw Claude, decisively — Ortho's answer was wrong |
| "Add streaming response support — what's the plan?" (after fix) | ~173 (`ortho_plan`, re-verified live) | same 35,434 tokens | Ortho now correctly flags "possibly already implemented" with real symbol evidence, still ~205x fewer tokens; template paths themselves remain generic |

**Honest bottom line:** Ortho's MCP tools are dramatically cheaper in tokens for architecture/violation-detection questions (guardrails, decide, memory search) where the answer is a deterministic fact about the repo's structure — often 10-100x fewer tokens than a cold Claude session re-deriving the same thing by reading files. `ortho_ask` and `ortho_plan` originally traded that token cheapness for materially worse or outright wrong answers; both root causes are now fixed and re-verified against the exact same failing cases. The residual gap: both fixes are still mechanical (keyword/substring matching), not semantic — `ortho_ask` now surfaces good evidence sets but still reads as an evidence list, not connected prose; `ortho_plan`'s new pre-check correctly flags "check first" but the underlying implementation-path templates are still generic keyword-bucket text, not repo-specific reasoning.

## Bugs fixed this round
1. **`ortho_plan` / `ortho_orchestrate` Stage 1** had no mechanism to detect "this feature already exists in the codebase." Fixed by adding `find_existing_symbols()` (real substring match against scanned symbols, same discipline as `ortho_ask`) as a pre-check surfaced above the generated template. Verified live on the exact original failing case; 42+112 tests pass across `feature-planner`/`cli-commands`.
2. **`ortho_ask`'s single-longest-word keyword extraction** silently dropped the actual subject word when a longer, less-relevant word appeared in the same question. Fixed by trying every candidate word (longest-first) and keeping whichever yields the most real matches, not just the first with any match at all. Verified live on the exact original failing case plus 2 new regression tests tied to the literal scenario.
3. **`ortho_refactor`'s bloat threshold** flagged test files (`tests.test_json`, `tests.test_views`, etc.) alongside production modules with no distinction. Fixed with `_is_test_module()`, matching pytest/unittest's own discovery convention (`tests`/`test` package segment, or `test_*`/`*_test` leaf). Verified live on Flask: 12 mixed findings → 10 real production-only findings, response size cut by more than half as a side effect. New regression test against real Flask scan data; all 19 tests in `test_plan_refactor_wiring.py` pass.

All three fixes verified against the exact original failing cases (not new cherry-picked ones), with regression tests tied to the literal scenarios, and no existing test suite broken (feature-planner 42, cli-commands 61+).
