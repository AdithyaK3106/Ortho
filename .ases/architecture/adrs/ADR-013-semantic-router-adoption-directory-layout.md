# ADR-013: Semantic-Router Adoption + Directory Layout (`.ases/agents/` Collision)

**Date:** 2026-07-07  
**Status:** ACCEPTED  
**Decision:** Adopt semantic-router for intent classification; resolve `.ases/agents/` collision via FRD-mandated `core/` + `custom/` subdirectories; implement immutable registry pattern.

---

## Context

Task-012 (Intent Routing + Registries, Phase 3 Weeks 15–16) requires:
1. A classifier that routes user intents ("write an ADR", "implement this") to the right agent (architect, coder, etc.) without calling an LLM (fast path).
2. Two registries that load agent and skill metadata from `.md` files in `.ases/agents/` and `.ases/skills/`.
3. A directory structure that avoids collision: existing ASES process-role files (planner.md, architect.md, etc. — development methodology) occupy `.ases/agents/`, but new product Agent Registry files (orchestrator.md, architect.md, coder.md, etc. — Ortho runtime) also need to live there.

## Decision

### 1. Semantic-Router Adoption

**Chosen:** `semantic-router` + `HuggingFaceEncoder("BAAI/bge-small-en-v1.5")`

**Rationale:**
- **Fast, deterministic inference:** Semantic similarity (no LLM calls) means response time ~100ms (vs. 5–10s for LLM fallback).
- **Local, offline inference:** HuggingFace encoder runs on CPU; no API keys, no network dependency (after model is cached).
- **Small model footprint:** BAAI/bge-small-en-v1.5 is ~130MB; acceptable for dev environments and CI caching.
- **Deterministic output:** Same utterance → same embedding → same routing decision every time (key for reproducible ASES workflows).
- **Matches FRD design:** FRD Section 11 explicitly mandates semantic-router with HF encoder.

**Alternatives Considered:**

| Alternative | Why Not |
|-------------|---------|
| Custom embeddings (hand-crafted rules, keyword matching) | Too simplistic; scales poorly as intent set grows. No semantic understanding. |
| Ollama (local LLM) | Overkill for this task; adds runtime dependency and latency; contradicts "fast path" design. |
| HuggingFace Inference API | Requires API key and network; breaks local-first principle (FRD Principle 6). |
| OpenAI embeddings | Requires API key; contradicts local-first. |

**Chosen approach balances simplicity, speed, and FRD alignment.**

### 2. Directory Layout: Resolve `.ases/agents/` Collision

**Problem:** Two semantically different things want to live in `.ases/agents/`:
- **ASES process-role files** (planner.md, architect.md, builder.md, reviewer.md, test-designer.md, verifier.md, api-contract-gate.md, architecture-arbitrator.md) — these drive *how we develop* Ortho (fed to Claude sessions at gates).
- **Product Agent Registry files** (orchestrator.md, architect.md, coder.md, reviewer.md, tester.md, analyst.md, documenter.md, debugger.md) — these drive *how Ortho serves users* (runtime personas loaded by AgentRegistry).

**Chosen:** FRD Section 11 Explicit Structure

```
.ases/agents/
├── (root level) ASES process-role files [UNCHANGED, READ-ONLY]
│   ├── planner.md
│   ├── architect.md
│   ├── builder.md
│   ├── reviewer.md
│   ├── test-designer.md
│   ├── verifier.md
│   ├── api-contract-gate.md
│   └── architecture-arbitrator.md
├── core/ [NEW, product Agent Registry]
│   ├── orchestrator.md
│   ├── architect.md (PRODUCT, different from ASES process-role)
│   ├── coder.md
│   ├── reviewer.md (PRODUCT)
│   ├── tester.md
│   ├── analyst.md
│   ├── documenter.md
│   └── debugger.md
└── custom/ [NEW, empty scaffold for user-defined agents]
    └── .gitkeep

.ases/skills/
├── core/ [NEW, product Skill Registry]
│   ├── repo-analysis.md
│   ├── adr-writer.md
│   ├── impact-analyzer.md
│   ├── test-generator.md
│   ├── code-reviewer.md
│   ├── context-retriever.md
│   ├── git-analyst.md
│   ├── debt-analyzer.md
│   ├── spec-writer.md
│   └── debug-tracer.md
└── custom/ [NEW, empty scaffold for user-defined skills]
    └── .gitkeep
```

**Why This Works:**
- Existing ASES process-role files (root level) are untouched, read-only. No breaking changes.
- Product Agent Registry lives in `core/` subdirectory (new). Clear separation by directory.
- `AgentRegistry` loads from `core/` + `custom/` only (ignores root level); ASES system ignores `core/` subdirectory. Each system sees its own files.
- FRD Section 11 is explicit: agents/skills live in `ases/{agents,skills}/{core,custom}/`. This is the FRD design, not a deviation.

**Justification:** This is not an ad-hoc collision fix; it's the FRD-mandated architecture. Implementing it as specified avoids future collision with user custom agents.

### 3. Immutable Registry Pattern

**Chosen:** Registries load all metadata at `__init__()`, cache in memory, no `reload()` method.

**Rationale:**
- **Simplicity:** No file watching, no concurrent modification logic, no cache invalidation strategy.
- **Determinism:** Cache is fixed for the lifetime of the object; no surprise changes during a run.
- **Matches Phase 3 scope:** Intent routing happens once at startup; agents don't change mid-run. Full dynamic loading is a Phase 4+ feature.

**Lifecycle:**
1. `AgentRegistry(agents_root="/root/.ases/agents")` — Scans `core/` and `custom/` at init time.
2. Parse all `.md` files (frontmatter + body).
3. Cache in memory as `self._agents: dict[str, Agent]`.
4. Queries (`list_agents()`, `get_agent(name)`) return from cache (zero I/O).
5. Object garbage-collected → cache discarded.

**If custom agents are added at runtime:**
- Create a new `AgentRegistry` instance to reload.
- Old instance's cache is unaffected (immutable).
- Acceptable trade-off: custom agent loading is not a Weeks 15–16 use case.

**Alternative Considered:**
- Hot-reload with `reload()` method: Adds complexity (file watcher, cache invalidation, concurrent access logic). Not justified for MVP. Deferred to Phase 4+ if needed.

---

## Trade-Offs

| Trade-Off | Impact | Accepted? |
|-----------|--------|-----------|
| Semantic-router adds external dependency | Adds 1 external package; acceptable for local-first design | ✅ |
| HuggingFace encoder ~130MB download | CI must cache once; acceptable | ✅ |
| Directory structure adds `core/` subdirectory | Mirrors FRD design; no downside | ✅ |
| Immutable registries = no hot-reload | Acceptable for Phase 3 MVP; dynamic loading is Phase 4+ | ✅ |
| Custom agents require new registry instance | Acceptable; custom loading is rare in MVP | ✅ |

---

## Implementation Notes

1. **Task-012 (Weeks 15–16):**
   - Create `.ases/agents/core/` and `.ases/skills/core/` directories with 8 + 10 `.md` files.
   - Implement `AgentRegistry` and `SkillRegistry` to load from these directories.
   - Implement `IntentRouter` with semantic-router.
   - Add `semantic-router`, `pydantic` to `packages/orchestration/pyproject.toml`.

2. **Task-013 (Weeks 17–18):**
   - Selector engine (`score_agent`, `score_skill`) consumes these registries.
   - Workflow executor uses intent classification + selector output.

3. **Validation:**
   - All 8 core agents must parse successfully (frontmatter valid, no skipped entries).
   - All 10 core skills must parse successfully.
   - Malformed `.md` files logged with warning; not loaded into cache.

---

## Consequences

**Positive:**
- ✅ Fast intent routing (no LLM latency).
- ✅ Deterministic, reproducible behavior.
- ✅ Local-first, offline-capable.
- ✅ Clean directory separation (no collision).
- ✅ Simple, immutable cache (no concurrent logic).

**Negative:**
- ⚠️ HuggingFace model dependency (one-time 130MB download).
- ⚠️ Utterance corpus hand-authored initially (real usage logs don't exist yet).
- ⚠️ No hot-reload for custom agents (must create new registry instance).

**Mitigations:**
- Model cached once in CI; offline inference thereafter.
- Utterance corpus refined over time (task-013+ adds dynamic learning).
- Hot-reload is a Phase 4+ enhancement.

---

## Related Decisions

- **ADR-001:** Storage Strategy (SQLite, local-first)
- **ADR-004:** Storage Strategy (SQLite + sqlite-vec)
- **ADR-009:** ADR Cross-Reference Strategy
- **ADR-010:** Reuse Similarity Algorithm
- **ADR-011:** Index Persistence Strategy
- **ADR-012:** Canonical Artifacts Schema

---

*Approved: 2026-07-07*  
*Revision: Ready for BUILDER task-012 implementation.*
