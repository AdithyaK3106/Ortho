# task-012: Intent Routing + Registries — Plan

**State:** DRAFT (awaiting GATE 1)
**Workflow:** .ases/workflows/feature.md
**Format:** Compact (FRD Part 17)
**Date:** 2026-07-07
**Author:** PLANNER

## Summary

Phase 3 starts: Ortho orchestrates ASES workflows using agents and skills. This task delivers
the first capability: intent routing (semantic-router + seed utterances) and runtime registries
(load agent/skill metadata from `.md` files). Per FRD Section 11, users can say `ortho run "write
an ADR"` and Ortho identifies the right agent/skill combo without an LLM lookup. Weeks 15–16
scopes to routing + registries only; full orchestrator executor is Weeks 17+.

## Atomic Tasks (each = one commit)

| # | Task | Est | Depends |
|---|------|-----|---------|
| 1 | `AgentRegistry` (`packages/orchestration/src/orchestration/selector/agent_registry.py`): parse YAML frontmatter + body from `.md` files under `.ases/agents/core/` + `.ases/agents/custom/`, cache in memory, expose `list_agents()`/`get_agent(name)` | 60m | — |
| 2 | `SkillRegistry` (mirror shape, `.ases/skills/core/` + `.ases/skills/custom/`) | 45m | — |
| 3 | Author 8 core agent `.md` files + 10 core skill `.md` files per FRD Section 11 tables, frontmatter only + minimal system-prompt bodies | 90m | 1,2 |
| 4 | `IntentRouter` (`.../intent/router.py`): `semantic_router.SemanticRouter` + `HuggingFaceEncoder("BAAI/bge-small-en-v1.5")`, routes built from agent/skill frontmatter + hand-authored utterance seed corpus; `classify_intent()` returns `IntentClassification(type, confidence, method)` | 90m | — |
| 5 | LLM-fallback stub (`.../intent/classifier.py`): `llm_classify_intent()` triggered when `similarity_score < 0.7`; stub returns structured "needs LLM" result (no live wiring yet — documented limitation) | 45m | 4 |
| 6 | ADR-013 (new dependency: `semantic-router`) — required before implementation per FRD Section 17 | 30m | — |
| 7 | Add `semantic-router`, `pydantic` to `packages/orchestration/pyproject.toml`; verify import + encoder load | 30m | 6 |

## Key Data-Model Facts (binding constraints)

- Agent/skill `.md` files: YAML frontmatter (`---`-delimited) + body = system prompt text, parsed
  with `python-frontmatter` (lazy-import if available, else stdlib `yaml.safe_load`).
- `IntentClassification.method` field must distinguish `"router"` (fast, no LLM, confidence >= 0.7)
  from `"llm_fallback"` (confidence < 0.7, per FRD two-stage design).
- `IntentClassification.confidence` is the raw semantic similarity score [0.0, 1.0] from
  semantic-router (not a calibrated probability). Exposed directly; threshold (0.7) is internal.
- Registries are **immutable after initialization** (no reload()). Cache loaded at `__init__()`,
  held in memory, garbage-collected with the object. New instance needed if custom agents/skills
  added at runtime.
- **Duplicate Name Policy:** If same agent/skill name exists in both `core/` and `custom/`,
  custom entry **wins** (explicit override). Load order: core/ first, then custom/.
- **Frontmatter Validation:** Strict. Malformed YAML or missing required fields cause file to be
  skipped with a warning logged (not an error). Registry returns only successfully parsed entries.
  Tests ensure all 8 core agents + 10 core skills parse without skipping.
- `.ases/agents/` naming collision: existing ASES-methodology files (planner.md, architect.md,
  builder.md, etc.) vs. FRD's product-facing Agent Registry (orchestrator.md, coder.md, etc.).
  ARCHITECT decides directory namespacing at GATE 2 (e.g. `.ases/agents/core/` + `.ases/agents/custom/`
  per FRD, leaving process files untouched at root level).
- Utterance seed corpus: hand-authored from FRD examples + workflow `.md` gate descriptions (real
  usage logs do not exist yet — documented known limitation, matches FRD's fallback via
  `llm_classify_intent()`).

## Risks

| Risk | Mitigation |
|------|-----------|
| `.ases/agents/` directory collision | ARCHITECT resolves at GATE 2; plan defers decision |
| No real usage utterance logs | Seed corpus from FRD + workflow descriptions; fallback to LLM for misses |
| `semantic-router` + HuggingFace model runtime dependency | Tests use small fixture route set; CI must cache encoder model once |
| New dependency without ADR | ADR-013 drafted as Task 6, gates Task 7 (implementation cannot start until ADR done) |
| Scope creep: selector engine in same section | Explicit Out-of-Scope list; selector is task-013 (FRD Weeks 17–18) |

## Acceptance Criteria (binary, repository-independent)

- AC1: `AgentRegistry.list_agents()` returns all 8 core agents with name/display_name/intent_triggers
  from frontmatter; `get_agent("coder")` returns its body.
- AC2: `SkillRegistry.list_skills()` returns all 10 core skills with frontmatter fields.
- AC3: `IntentRouter.classify_intent("write an ADR for this decision")` returns
  `IntentClassification(type="architect", confidence>=0.7, method="router")` (or matching trigger)
  against the seed route set — no fallback on a clear-cut utterance.
- AC4: `IntentRouter.classify_intent("<ambiguous/off-domain text>")` returns `method="llm_fallback"`
  (low confidence triggers fallback, not wrong-but-confident routing).
- AC5: Zero regressions — all existing suites pass unchanged (repo-intelligence, context-hub,
  arch-intelligence, impact-analysis, shared/storage, apps/cli, api-server, tsc --noEmit).

## Expected Test Metrics

- Unit: 15+ (frontmatter parsing, registry caching, missing-file handling, router threshold logic)
- Integration: 5+ (registry loads all real core .md files, router against seed corpus)
- Edge: 5+ (malformed frontmatter, empty directory, duplicate names, unicode in prompts)
- Coverage: ≥85% on new modules; pass rate 100%

## Out of Scope (do NOT touch)

- Selector engine (`score_agent`, `score_skill`, `build_execution_plan`) — task-013 (FRD Weeks 17–18)
- Workflow executor, approval gate, `ortho run`/`status`/`approve`/`reject` — later Phase 3 tasks
- Live LLM calls — stub only; wiring is a later task
- Custom agent/skill directories — empty scaffolding only; no custom content
- Existing `.ases/agents/*.md` process-role files — read-only, untouched

## Architecture Impact

NOT none — new package contents, new external dependency, new directory structure, naming
collision decision. Full ARCHITECT session required at GATE 2.
Expected ADR: **ADR-013** (semantic-router adoption + agent/skill registry directory layout).
