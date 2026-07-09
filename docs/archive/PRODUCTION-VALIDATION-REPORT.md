# Ortho Production Validation Report

**Date:** 2026-07-07
**Scope:** CLI integration hardening + end-to-end validation on real repositories (FastAPI, LangChain)
**Verdict:** All CLI commands work from arbitrary directories on the current platform; both real-repo pipelines complete every stage. Analysis-quality and LLM-execution limitations remain (documented below).

---

## 1. Bug Fix Report

### Critical — features that could never work

| # | Bug | Root Cause | Resolution |
|---|-----|-----------|------------|
| 1 | `ortho run/status/approve/reject/history` always failed | All five TS commands called `http://localhost:17234/api/*` — **no server implements those endpoints anywhere** (api-server is a stub on port 8000 with `/health` + 2 dummy routes) | New `apps/cli/src/commands/workflow_cli.py` drives the real orchestration stack (SelectorEngine → WorkflowExecutor → WorkflowStateStore → SQLite) directly; the five TS commands are now thin spawn wrappers via `pybridge.ts` |
| 2 | `ortho context` did not exist in the CLI | `context.py` bridge was written but no `context.ts` was ever created or registered in `index.ts` | Added `context.ts` (add/search subcommands), registered it |
| 3 | SelectorEngine could not talk to the real registries | Engine calls `all_agents()`/`all_skills()`; real registries (task-012) expose `list_agents()`/`list_skills()`. The engine was only ever tested against mocks that defined the phantom names | Registries now expose both names for the same method |
| 4 | Every execution plan was empty (silent no-op) | Engine tested `intent.type in agent.intent_triggers` (exact membership) but agent manifests carry natural-language trigger phrases ("write an ADR") — the test never fired, no agent ever reached the 0.5 selection threshold | Trigger match now uses the same substring semantics as `AgentRegistry.get_agents_by_intent`, plus workflow-stage membership (an agent named in the intent's stage list is triggered by definition) |
| 5 | `step_runner` crashed on real skills | Accessed `skill.content`; the real `Skill` dataclass has `system_prompt` | Accepts either (`content` for legacy doubles, `system_prompt` for real manifests) |

### High — correctness bugs found during validation

| # | Bug | Root Cause | Resolution |
|---|-----|-----------|------------|
| 6 | Token budget overrun (found by property test) | `build_plan` hard-excluded each skill against the remaining budget *individually*, so two skills could each fit while overshooting together (1400 tokens selected against an 800 budget) | Greedy selection in deterministic order (score desc, name asc) with accumulated token cost |
| 7 | FTS5 query injection — `ortho context search "tool-calling"` crashed with `no such column: calling` (found on LangChain E2E) | Raw user input passed to FTS5 `MATCH`; hyphens parse as column-filter syntax | Each term is now quoted (`"tool-calling"`), neutralizing all FTS5 operators |
| 8 | `_transition_state` validated but never applied transitions | Status assignment was duplicated at every call site; tests (GATE 4 artifact) expected the method to mutate | Method now assigns `workflow_run.status` after validation (None-guarded) |
| 9 | Non-interactive approval gate crashed with `EOF when reading a line` | Windows reports NUL/redirected stdin as a tty, so the `isatty()` guard can't catch it | `EOFError` on the prompt now rejects the gate safely with an actionable message |

### Medium — usability / portability

| # | Bug | Resolution |
|---|-----|------------|
| 10 | Impact report printed opaque hash IDs (`3af506ee6a404b1a`) and a "Blast Radius: 2" that contradicted 18 listed dependents | File IDs are mapped to repo-relative paths (in dependents *and* evidence lines); blast radius now reports total affected files (direct + transitive) |
| 11 | `spawn("python", ...)` fails on macOS/Linux systems that ship only `python3` | `pybridge.ts` falls back to `python3` on `ENOENT` |
| 12 | `analyze --adr-check` / `--reuse` printed nothing on empty results | Explicit "No ADRs found…" / "No reuse clusters…" messages |
| 13 | `analyze` (unindexed repo) hid the "run `ortho scan` first" hint | Evidence lines printed when style is `unknown` |
| 14 | Dead `node-fetch` dependency (only used by the phantom HTTP calls) | Removed from package.json |
| 15 | Path resolution duplicated (and previously buggy) across scan/analyze/index commands | Consolidated in `pybridge.ts` — ortho root resolved from `require.main.filename`, independent of cwd |

### Test-suite defects (previously never executed)

| # | Defect | Resolution |
|---|--------|------------|
| 16 | `test_selector_engine.py` failed at **collection**: imported `packages.orchestration.src.intent.router` and `packages.shared.types` — modules that never existed | Local test-double dataclasses; file is now self-contained |
| 17 | `test_workflow_executor.py` failed at collection: used `@settings` without importing it | Import fixed |
| 18 | Float-comparison bug: `assert (1.3 - 1.1) >= 0.2` is false in IEEE arithmetic | `pytest.approx` |
| 19 | Hypothesis health-check failures (function-scoped fixtures under `@given`) | Suppressed with justification (fixtures are read-only mocks) |
| 20 | Two impact tests asserted the old raw-ID output contract | Updated to the path-mapped contract (the improvement in #10 was intentional) |

**Regression status after all fixes:**
repo-intelligence 142 ✅ · context-hub 54 ✅ · arch-intelligence 76 ✅ · impact-analysis 42 ✅ · orchestration 93 ✅ (was 86 collectable) · apps/cli pytest 30 ✅ · apps/cli jest 6 ✅ — **443 passing, 0 failing**

---

## 2. End-to-End Test Report

Both repos ran the full pipeline from a **fresh `.ortho/`**, invoked from the target repo's own directory (not Ortho's).

Pipeline: init → scan → DB validation → architecture detection → layer detection → subsystem detection → impact analysis → context add/search → workflow execution (plan → gates → evidence) → status/history.

### FastAPI (`Repos/fastapi`)

| Stage | Result | Metrics |
|-------|--------|---------|
| init | ✅ | config.toml, ortho.db, vectors.db created |
| scan | ✅ | **14.3 s**, 1121/1121 files, 0 errors |
| DB validation | ✅ | 5438 symbols, 3440 import edges, 1507 call edges persisted (13,267 dropped unresolved by design), 0 orphan edges, **1.93 MB** |
| analyze | ✅ 1.6 s | style=microservices 0.90 (see Remaining Issues #1), 2 layers, 978 subsystems |
| impact | ✅ 0.4 s | `fastapi/applications.py`: risk 1.00, 46 affected files, real importer paths |
| context add/search | ✅ | BM25 hit at 0.999 relevance |
| workflow run | ✅ 8.3 s wall | intent→analysis, 1 step (analyst + 4 skills), status=complete, evidence persisted |
| status/history | ✅ | read from SQLite, correct run states |

### LangChain (`Repos/langchain`)

| Stage | Result | Metrics |
|-------|--------|---------|
| init | ✅ | fresh `.ortho/` |
| scan | ✅ | **55.2 s**, 2529/2530 files — the 1 "error" is `non-utf8-encoding.py`, LangChain's own deliberately non-UTF8 negative fixture; correctly counted, not crashed on |
| DB validation | ✅ | 16,449 symbols, 11,555 import edges, 18,402 call edges persisted (43,719 dropped unresolved), 0 orphan edges, **9.0 MB** |
| analyze | ✅ 10.7 s | style=microservices 0.90 (same caveat), 1 layer, 1733 subsystems |
| impact | ✅ 0.5 s | `langchain_classic/agents/agent.py`: risk 0.21, 5 affected files, all genuine importers |
| context add/search | ✅ | hyphenated query works after FTS5 fix |
| workflow run | ✅ 8.4 s wall | status=complete, evidence persisted |
| status/history | ✅ | correct |

### Additional verification

- **Arbitrary-directory check:** every command also exercised from an empty non-repo directory — clean, actionable messages ("run `ortho scan` first", "No workflow runs…"), no stack traces, exit 0.
- **Approval gates:** interactive path, `--yes` auto-approve, cross-process `approve`/`reject` on a genuinely awaiting run, and EOF/non-interactive rejection all verified against the formal state machine (complete/rejected terminal states + evidence records).
- **Reuse detection sanity check:** empty results on both real repos are legitimate — a synthetic pair of structurally identical functions is detected at similarity 1.00.
- **Workflow evidence:** inspected raw `evidence_json` in SQLite — real timestamps, token counts, step IDs; agent output clearly marked `[stub-llm]`.

---

## 3. Remaining Issues (genuine, not speculation)

1. **Architecture style heuristics are placeholder-grade.** `_score_microservices` returns 0.9 for *any* repo with ≥15 unique caller symbols (`min(callers//3, 5)` saturates), so FastAPI and LangChain both classify as "microservices". Layer/subsystem extraction runs correctly; the *style label* is not trustworthy on real repos. Fixing this is detector algorithm redesign (out of scope for an integration pass; the 76 arch tests are calibrated to the current heuristics).
2. **Subsystem detection degenerates on sparse call graphs** (978 and 1733 subsystems ≈ mostly singleton Louvain communities). Driver: ~90% of dynamic calls are dropped as unresolved per ADR-011's "never guess" rule, leaving most files disconnected.
3. **LLM client is a stub** (documented task-012/013 limitation; real client lands with the token optimizer, task-014). Workflow orchestration, state machine, gates, and evidence are fully real; agent output is a deterministic `[stub-llm]` acknowledgement.
4. **Semantic IntentRouter not wired into the CLI** — it requires an utterance corpus and a HuggingFace model download that don't ship with the repo. A deterministic keyword classifier bridges intent → workflow class; swap-in point is marked in `workflow_cli.py`.
5. **Installation story is repo-checkout only.** The CLI resolves the Ortho root from the compiled entry point, which works for a git checkout (`node apps/cli/dist/index.js` or `npm link`) but there is no npm/pip packaging that would bundle the Python packages. Packaging is unstarted product work, not a path bug.
6. **`approval_gates` table is never written** — gate decisions live in `workflow_runs.evidence_json` (append-only). Schema exists but is unused by the executor.
7. **macOS/Linux not physically tested** in this pass (Windows only). Portability hazards were removed (no `shell:true`, no `__dirname` math, UTF-8 stream reconfigure, `python3` fallback, `pathlib`/`path.join` everywhere), but a real Linux/macOS run should be the next validation step.

---

## 4. Production Readiness Assessment

| Area | Status |
|------|--------|
| CLI works from arbitrary directories | ✅ Verified (target repos, neutral dirs, Ortho root) |
| No hardcoded paths / cwd assumptions | ✅ All spawns route through entry-point-based resolution |
| Python integration | ✅ Bare-script bootstrap idiom, no install-state dependence, namespace-package imports |
| Cross-platform hardening | ✅ Windows verified end-to-end; Unix hazards removed; physical Unix run pending (issue #7) |
| FastAPI full pipeline | ✅ Every stage passes |
| LangChain full pipeline | ✅ Every stage passes |
| Test suites | ✅ 443 passing, 0 failing, no skipped-because-broken |
| Performance | ✅ 1121 files/14 s and 2530 files/55 s scan; sub-second impact queries on 16K symbols |
| Analysis quality | ⚠️ Style detection placeholder-grade (issue #1); impact/layers/context/search are sound |
| Workflow execution | ⚠️ Real state machine + evidence; LLM output stubbed until task-014 |

**Bottom line:** Ortho is production-usable as an installed-from-checkout CLI for repository intelligence (scan, impact, context, search) on real-world-scale repos. The orchestration layer is structurally complete and persistent but awaits a live LLM client, and architecture *style* labeling needs a real detector before its output should be trusted.
