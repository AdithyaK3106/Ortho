# task-012: Intent Routing + Registries — Architecture Review

**ARCHITECT:** Review complete (GATE 2)
**Date:** 2026-07-07
**Verdict:** ✅ **APPROVED**

---

## Summary

The task-012 architecture is sound, fully compliant with FRD Section 11 requirements, and introduces no circular dependencies. The directory layout collision (`.ases/agents/` holding both ASES process roles and product Agent Registry) is **resolved by FRD itself** — the specification explicitly mandates `core/` + `custom/` subdirectories, which cleanly separates the two concerns.

---

## FRD Compliance

### Agent and Skill Registry Requirements (FRD Section 11)

**8 Core Agents — All Present:**
✅ orchestrator, architect, coder, reviewer, tester, analyst, documenter, debugger

**10 Core Skills — All Present:**
✅ repo-analysis, adr-writer, impact-analyzer, test-generator, code-reviewer, context-retriever, git-analyst, debt-analyzer, spec-writer, debug-tracer

**Data Models Match FRD Exactly:**
- Agent frontmatter: `name, display_name, description, intent_triggers, skills_preferred, priority, requires_context` ✅
- Skill frontmatter: `name, display_name, description, agent_types, intent_triggers, provides, estimated_tokens` ✅

**Scope Correctly Bounded:**
- Selector engine (`score_agent`, `score_skill`, `build_execution_plan`) correctly out-of-scoped to task-013 (FRD Weeks 17–18) ✅
- Intent router + registries only (FRD Weeks 15–16) ✅

---

## Directory Layout Resolution

### The Collision (FRD-Mandated Solution)

**Problem:** `.ases/agents/` currently holds ASES methodology role files (planner.md, architect.md, builder.md, etc.) — these drive *how this repo develops*. Task-012 needs to add product Agent Registry files (orchestrator.md, architect.md, coder.md, etc.) — these drive *how Ortho serves users*.

**FRD Section 11 Explicit Solution:**
> "Agents live in `ases/agents/` with `core/` (built-in) and `custom/` (user-defined) subdirectories."

**Architecture Decision:**

| Location | Content | Owner | Status |
|----------|---------|-------|--------|
| `.ases/agents/` (root) | ASES process-role files (planner.md, architect.md, builder.md, reviewer.md, test-designer.md, verifier.md, api-contract-gate.md, architecture-arbitrator.md) | Development process | **Untouched, read-only** |
| `.ases/agents/core/` | Product Agent Registry (orchestrator.md, architect.md, coder.md, reviewer.md, tester.md, analyst.md, documenter.md, debugger.md) | Ortho runtime | **Created by task-012** |
| `.ases/agents/custom/` | User-defined custom agents | End users | **Empty scaffold** |
| `.ases/skills/core/` | Product Skill Registry (10 core skills) | Ortho runtime | **Created by task-012** |
| `.ases/skills/custom/` | User-defined custom skills | End users | **Empty scaffold** |

**Rationale:** FRD is explicit about the subdirectory structure. This design cleanly separates development-process metadata (root level, untouched) from product runtime metadata (core/ subdirectories). No collision, no ambiguity.

---

## Module Architecture

### Package Structure

```
packages/orchestration/
├── src/orchestration/
│   ├── intent/
│   │   ├── router.py          — IntentRouter (semantic-router integration)
│   │   ├── classifier.py      — llm_classify_intent() stub
│   │   └── types.py           — IntentClassification dataclass
│   └── selector/
│       ├── agent_registry.py  — AgentRegistry (loads .ases/agents/core + custom)
│       ├── skill_registry.py  — SkillRegistry (loads .ases/skills/core + custom)
│       └── types.py           — Agent, Skill dataclasses
├── tests/
│   ├── test_agent_registry.py
│   ├── test_skill_registry.py
│   ├── test_intent_router.py
│   └── fixtures/utterances.json
└── pyproject.toml             — Add semantic-router, pydantic
```

### Module Responsibilities

| Module | Responsibility | Public API |
|--------|-----------------|-----------|
| `intent/router.py` | Semantic-router integration, utterance-based classification | `IntentRouter.__init__()`, `classify_intent(utterance)` → `IntentClassification` |
| `intent/classifier.py` | Fallback classifier for low-confidence inputs (stub) | `llm_classify_intent(utterance)` → `IntentClassification` |
| `intent/types.py` | Classification result type | `IntentClassification(type, confidence, method)` |
| `selector/agent_registry.py` | Load, cache, query agents from `.md` files | `AgentRegistry.__init__()`, `list_agents()`, `get_agent(name)`, `get_agents_by_intent(type)` |
| `selector/skill_registry.py` | Load, cache, query skills from `.md` files | `SkillRegistry.__init__()`, `list_skills()`, `get_skill(name)`, `get_skills_for_agent(agent_name)` |
| `selector/types.py` | Agent and Skill dataclasses | `Agent(name, display_name, ...)`, `Skill(name, display_name, ...)` |

---

## Dependency Analysis

### Import Graph (Acyclic)

```
orchestration/intent/
  ├─ imports: semantic_router (external), pydantic (external), stdlib
  ├─ imports: .types (local)
  └─ NO imports from: repo-intelligence, context-hub, arch-intelligence, impact-analysis, cli, api-server

orchestration/selector/
  ├─ imports: pathlib, yaml (stdlib), pydantic (external)
  ├─ imports: .types (local)
  └─ NO imports from: product packages or cli/api-server
```

**Verification:** orchestration/ is **self-contained** and depends only on:
- External packages: `semantic-router`, `pydantic`
- Stdlib: `pathlib`, `yaml`, `dataclasses`, `typing`
- Shared types: (optional, not required for task-012; deferred to task-013)

**No circular dependencies.** Safe to implement.

---

## Specification Compliance

### Cache Behavior

✅ **Immutable after initialization.** Registries load all `.md` files at `__init__()`, cache in memory, no `reload()`. Clear lifetime (object garbage-collected). Documented in spec.md §1.

### Duplicate Name Policy

✅ **Custom overrides core.** Load order: core/ first, custom/ second. Same name in both → custom entry wins. Deterministic, no error. Documented in spec.md §2.

### Router Confidence

✅ **Raw semantic similarity [0.0, 1.0].** Not normalized, not a probability. Exposed directly. Threshold (0.7) hardcoded, can be configurable later. Documented in spec.md §3.

### Frontmatter Validation

✅ **Strict with skip-on-error.** Malformed YAML or missing fields → skip entry, log warning. Registries return only successfully parsed entries. All 8 core agents + 10 core skills must parse without skipping (AC1–AC2). Documented in spec.md §4.

---

## Known Limitations (Documented)

- **No live LLM fallback:** `llm_classify_intent()` is a stub (returns confidence=0.5, type="orchestrator"). Real LLM wiring is task-013+.
- **Hand-authored utterance corpus:** Not from real Phase 1+2 logs (logs don't exist). Real-usage refinement deferred.
- **Immutable registries:** No hot-reload. New instance needed if custom agents/skills added at runtime. Acceptable for Phase 3 (single startup).
- **HuggingFace encoder dependency:** Requires model cache (~130MB) at runtime. RuntimeError if encoder fails to load.

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| HuggingFace encoder model download fails at runtime | Medium | RuntimeError surfaced to user; documented in spec. CI must cache model once. |
| Malformed core agent/skill `.md` files | Low | Validation skips with warnings; tests verify all 8+10 parse successfully (no skipped entries). |
| Directory collision (`.ases/agents/`) causes confusion | Low | FRD-mandated subdirectory structure (core/custom) cleanly separates concerns. Documentation explicit. |
| Utterance corpus too small for good routing | Low | Acceptable for Phase 3 MVP. Real-usage refinement in task-013+ (dynamic utterance learning). |
| Immutability prevents dynamic agent/skill loading | Low | By design, acceptable for initial release. Dynamic loading is a future enhancement. |

---

## Decisions Captured in ADR-013

Three architectural decisions require an ADR per FRD Section 17:

1. **Semantic-router adoption** — Why semantic-router (local, deterministic, no API) over alternatives (ollama, huggingface-inference, custom embeddings).
2. **Directory layout for `.ases/agents/`** — How FRD's explicit `core/` + `custom/` subdirectories resolve the collision.
3. **Immutable registry pattern** — Why no `reload()`, why new instances needed for dynamic updates.

ADR-013 drafted and ready for review.

---

## Verdict

### ✅ APPROVED

**Rationale:**
- ✅ FRD compliance complete (Section 11 requirements met exactly)
- ✅ Architecture sound (acyclic, self-contained)
- ✅ Directory layout resolves collision via FRD's explicit design
- ✅ Specification detailed and consistent (4 refinements thoroughly documented)
- ✅ All ACs binary and testable
- ✅ Known limitations declared upfront
- ✅ Ready for BUILDER implementation

**Conditions:**
- ADR-013 must be written and committed before BUILDER begins (Task 6 in plan.md)
- All 8 core agents + 10 core skills must parse without validation skips (AC1–AC2)
- Existing `.ases/agents/` process-role files remain untouched (read-only)

**Next Step:** BUILDER proceeds with Tasks 1–7. TEST-DESIGNER designs test plan in parallel.

---

*Architecture review completed by ARCHITECT role, GATE 2.*
*Ready for concurrent BUILDER + TEST-DESIGNER work.*
