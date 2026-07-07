# task-012: Intent Routing + Registries — Specification

**State:** DRAFT (awaiting GATE 1)
**Workflow:** .ases/workflows/feature.md
**Format:** Compact (FRD Part 17)
**Date:** 2026-07-07

## Overview

**Objective:** Implement intent routing (semantic-router + hand-authored utterances) and two
runtime registries (agents, skills) that load metadata from `.md` frontmatter files. By end of
task, `classify_intent("write an ADR")` correctly identifies agent=architect + intent_type=architect,
and all 8 core agents + 10 core skills are loadable from `.ases/agents/core/` and `.ases/skills/core/`.

## Files to CREATE

| File | Purpose |
|------|---------|
| `packages/orchestration/src/orchestration/__init__.py` | Package export stub |
| `packages/orchestration/src/orchestration/intent/__init__.py` | Intent subpackage |
| `packages/orchestration/src/orchestration/intent/router.py` | `IntentRouter` class: semantic routing via `semantic_router.SemanticRouter` |
| `packages/orchestration/src/orchestration/intent/classifier.py` | `llm_classify_intent()` stub (falls back when router confidence < 0.7) |
| `packages/orchestration/src/orchestration/intent/types.py` | `IntentClassification` dataclass |
| `packages/orchestration/src/orchestration/selector/__init__.py` | Selector subpackage |
| `packages/orchestration/src/orchestration/selector/agent_registry.py` | `AgentRegistry` class: loads `.md` files, caches agents |
| `packages/orchestration/src/orchestration/selector/skill_registry.py` | `SkillRegistry` class: loads `.md` files, caches skills |
| `packages/orchestration/src/orchestration/selector/types.py` | `Agent`, `Skill` dataclasses (frontmatter parsed to these) |
| `.ases/agents/core/orchestrator.md` | Core agent 1: entry point, workflow selection (frontmatter + stub prompt) |
| `.ases/agents/core/architect.md` | Core agent 2: design, ADR writing |
| `.ases/agents/core/coder.md` | Core agent 3: implementation |
| `.ases/agents/core/reviewer.md` | Core agent 4: code review, quality gates |
| `.ases/agents/core/tester.md` | Core agent 5: test design, coverage |
| `.ases/agents/core/analyst.md` | Core agent 6: impact analysis, debt scoring |
| `.ases/agents/core/documenter.md` | Core agent 7: documentation, ADR |
| `.ases/agents/core/debugger.md` | Core agent 8: debugging, trace analysis |
| `.ases/agents/custom/.gitkeep` | Empty custom agents directory |
| `.ases/skills/core/repo-analysis.md` | Core skill 1 |
| `.ases/skills/core/adr-writer.md` | Core skill 2 |
| `.ases/skills/core/impact-analyzer.md` | Core skill 3 |
| `.ases/skills/core/test-generator.md` | Core skill 4 |
| `.ases/skills/core/code-reviewer.md` | Core skill 5 |
| `.ases/skills/core/context-retriever.md` | Core skill 6 |
| `.ases/skills/core/git-analyst.md` | Core skill 7 |
| `.ases/skills/core/debt-analyzer.md` | Core skill 8 |
| `.ases/skills/core/spec-writer.md` | Core skill 9 |
| `.ases/skills/core/debug-tracer.md` | Core skill 10 |
| `.ases/skills/custom/.gitkeep` | Empty custom skills directory |
| `packages/orchestration/tests/__init__.py` | Test package stub |
| `packages/orchestration/tests/test_agent_registry.py` | Unit + integration tests for registry loading, caching, missing-file handling |
| `packages/orchestration/tests/test_skill_registry.py` | Unit + integration tests for skill registry |
| `packages/orchestration/tests/test_intent_router.py` | Unit + integration tests for routing, threshold logic, fallback |
| `packages/orchestration/tests/fixtures/utterances.json` | Hand-authored seed utterance corpus for router training |

## Files to MODIFY

| File | Change |
|------|--------|
| `packages/orchestration/pyproject.toml` | Add `semantic-router`, `pydantic`, `frontmatter` (or use stdlib `yaml.safe_load` if frontmatter unavailable) to dependencies |
| `.ases/architecture/adrs/INDEX.md` | Add ADR-013 entry (semantic-router adoption) |

## Files NOT to touch

- `.ases/agents/` existing process-role files (planner.md, architect.md, builder.md, reviewer.md, test-designer.md, verifier.md, api-contract-gate.md, architecture-arbitrator.md) — read-only
- Selector engine scoring functions (task-013)
- Workflow executor, approval gate, CLI commands (later Phase 3 tasks)
- Existing orchestration package stubs beyond adding `__init__.py` files

## Specification Details

### 1. Registry Cache Behavior

**Cache Model:** Immutable after initialization. Registries load all `.md` files from disk during
`__init__()` and hold the cache in memory for the lifetime of the object. No runtime reload.

**Lifecycle:**
- `__init__()`: Scan `agents_root/{core,custom}/` for all `*.md` files. Parse frontmatter + body.
  Load into memory. Raise `FileNotFoundError` if `core/` subdir does not exist.
- During runtime: `list_agents()`, `get_agent()`, `get_agents_by_intent()` all return from in-memory
  cache. Zero disk I/O.
- End of object lifetime: Cache is garbage-collected with the registry instance.

**Rationale:** Registries are configured once at startup and do not need hot-reload. If custom
agents/skills are added to `.ases/agents/custom/` or `.ases/skills/custom/` at runtime, a new
registry instance must be created to pick them up. This keeps the implementation simple and
deterministic (no concurrent modification risk, no need for file watchers).

### 2. Duplicate Name Policy

**Policy:** If the same agent/skill name appears in both `core/` and `custom/`, **the custom entry
wins** (explicit override). Load order: `core/` first, then `custom/`; custom entries with the
same `name` field replace core entries in the cache.

**Deterministic Behavior:**
```python
# Pseudocode for AgentRegistry:
agents = {}
for md_file in sorted(agents_root / "core" / "*.md"):
    agent = parse_md(md_file)
    agents[agent.name] = agent
for md_file in sorted(agents_root / "custom" / "*.md"):
    agent = parse_md(md_file)
    agents[agent.name] = agent  # Overwrites core if same name
return list(agents.values())
```

**Rationale:** Custom agents are intended to extend or override core agents (FRD Section 11).
Deterministic override (custom > core) is simpler than error-on-duplicate, and reflects the
intent that custom definitions take precedence.

### 3. Router Confidence

**Confidence Semantics:** The `confidence` field in `IntentClassification` is the raw semantic
similarity score from `semantic_router.SemanticRouter.classify()` (a normalized value [0.0, 1.0]).
It represents how semantically similar the user input is to the closest route, not a
probability-calibrated confidence.

**Threshold Behavior:** The default threshold is **0.7** (per FRD Section 11). Inputs with
`similarity_score >= 0.7` route normally (method="router"); below 0.7, fallback to
`llm_classify_intent()` (method="llm_fallback").

**Confidence Exposure:** The threshold (0.7) is a constant in `IntentRouter.__init__()` but can be
made configurable (pass as a parameter) in future refinements without changing the semantics of
the `confidence` field itself. For task-012, the threshold is hardcoded to 0.7.

**Example:**
```python
router = IntentRouter(utterances_corpus)
result = router.classify_intent("write an ADR")
# result.confidence is the semantic similarity score (e.g., 0.82)
# result.method is "router" because 0.82 >= 0.7
```

### 4. Frontmatter Validation

**Validation Policy:** Strict. Malformed YAML or missing required fields cause the file to be
**skipped with a warning** (logged, but does not halt initialization).

**Required Fields (Agent):**
```yaml
name, display_name, description, intent_triggers, skills_preferred, priority, requires_context
```

**Required Fields (Skill):**
```yaml
name, display_name, description, agent_types, intent_triggers, provides, estimated_tokens
```

**Behavior on Error:**
- **Malformed YAML:** Log warning (e.g., "Failed to parse frontmatter in orchestrator.md: YAML
  error"). Skip the entry. Continue loading remaining files.
- **Missing required field:** Log warning (e.g., "Agent architect.md missing required field:
  'priority'"). Skip the entry. Continue loading.
- **Invalid data type** (e.g., `estimated_tokens: "2000"` instead of integer): Log warning. Skip.
  Continue.
- **Empty file or body:** Log warning. Skip.

**Result:** `list_agents()` or `list_skills()` returns only successfully parsed entries. Skipped
entries are not in the cache. Tests should cover this via edge-case tests (see test-plan.md).

**Rationale:** Strict validation prevents silent failure (malformed config goes unnoticed).
Skipping rather than halting allows partial loads (useful for testing a subset of agents/skills).
Logging ensures developers see why an expected agent/skill is missing.

---

### `IntentClassification` (dataclass, `intent/types.py`)

```python
from dataclasses import dataclass

@dataclass
class IntentClassification:
    """
    Result of classifying a user intent.
    
    type: The agent type selected (e.g., "architect", "coder", "reviewer", "orchestrator").
    confidence: Raw semantic similarity score [0.0, 1.0] from semantic-router (not a calibrated probability).
               Exposed directly; threshold (0.7) is internal to IntentRouter.classify_intent().
    method: "router" (semantic-router fast path, confidence >= 0.7) or "llm_fallback" (confidence < 0.7, needs LLM).
    """
    type: str  # agent type (e.g., "architect", "coder", "llm_fallback")
    confidence: float  # [0.0, 1.0], raw semantic similarity score
    method: str  # "router" or "llm_fallback"
```

### `Agent` (dataclass, `selector/types.py`)

```python
@dataclass
class Agent:
    """Parsed agent metadata from .md frontmatter."""
    name: str
    display_name: str
    description: str
    intent_triggers: list[str]  # utterance examples/keywords that trigger this agent
    skills_preferred: list[str]  # skill names this agent prefers
    priority: str  # "high", "medium", "low"
    requires_context: list[str]  # context types needed (e.g., ["repo", "git_history"])
    system_prompt: str  # body of .md file (after frontmatter)
```

### `Skill` (dataclass, `selector/types.py`)

```python
@dataclass
class Skill:
    """Parsed skill metadata from .md frontmatter."""
    name: str
    display_name: str
    description: str
    agent_types: list[str]  # agents that can use this skill
    intent_triggers: list[str]  # utterances that trigger this skill
    provides: list[str]  # outputs this skill produces (e.g., ["adr", "test_code"])
    estimated_tokens: int  # rough token budget
    system_prompt: str  # body of .md file
```

### `AgentRegistry` (class, `selector/agent_registry.py`)

```python
class AgentRegistry:
    """
    Loads and caches agents from .ases/agents/core/ and .ases/agents/custom/.
    Cache is immutable after initialization. No reload() method; create a new instance to refresh.
    If duplicate agent names exist in both core/ and custom/, custom/ entry wins.
    """
    
    def __init__(self, agents_root: Path = Path(".ases/agents")):
        """
        Load all agents from agents_root/core/*.md and agents_root/custom/*.md.
        Files are loaded in order: core/ first, then custom/ (custom overrides core on name collision).
        Malformed YAML or missing required fields cause the file to be skipped with a warning logged.
        
        Raises: FileNotFoundError if agents_root/core/ does not exist.
        Cache lifetime: until object is garbage-collected.
        """
        
    def list_agents(self) -> list[Agent]:
        """
        Return all successfully loaded agents sorted by name.
        Skipped entries (due to validation errors) are not included.
        """
        
    def get_agent(self, name: str) -> Agent | None:
        """Get agent by name from cache, or None if not found or skipped due to validation error."""
        
    def get_agents_by_intent(self, intent_type: str) -> list[Agent]:
        """Get all agents whose intent_triggers contain intent_type. Sorted by name."""
```

### `SkillRegistry` (class, `selector/skill_registry.py`)

```python
class SkillRegistry:
    """
    Loads and caches skills from .ases/skills/core/ and .ases/skills/custom/.
    Cache is immutable after initialization. No reload() method; create a new instance to refresh.
    If duplicate skill names exist in both core/ and custom/, custom/ entry wins.
    """
    
    def __init__(self, skills_root: Path = Path(".ases/skills")):
        """
        Load all skills from skills_root/core/*.md and skills_root/custom/*.md.
        Files are loaded in order: core/ first, then custom/ (custom overrides core on name collision).
        Malformed YAML or missing required fields cause the file to be skipped with a warning logged.
        
        Raises: FileNotFoundError if skills_root/core/ does not exist.
        Cache lifetime: until object is garbage-collected.
        """
        
    def list_skills(self) -> list[Skill]:
        """
        Return all successfully loaded skills sorted by name.
        Skipped entries (due to validation errors) are not included.
        """
        
    def get_skill(self, name: str) -> Skill | None:
        """Get skill by name from cache, or None if not found or skipped due to validation error."""
        
    def get_skills_for_agent(self, agent_name: str) -> list[Skill]:
        """Get skills whose agent_types list contains agent_name. Sorted by name."""
```

### `IntentRouter` (class, `intent/router.py`)

```python
class IntentRouter:
    """
    Routes user utterances to agents using semantic-router (HuggingFace encoder, BAAI/bge-small-en-v1.5).
    Immutable after initialization. Threshold is hardcoded to 0.7 for this task.
    
    Confidence field is the raw semantic similarity score [0.0, 1.0] from semantic-router.
    It is NOT a calibrated probability, only a similarity metric.
    """
    
    def __init__(self, utterances_corpus: dict[str, list[str]]):
        """
        Build routes from utterance corpus.
        utterances_corpus: {agent_type: [utterance1, utterance2, ...], ...}
        Internally creates semantic_router.SemanticRouter with HuggingFaceEncoder("BAAI/bge-small-en-v1.5").
        
        Raises: RuntimeError if HuggingFace encoder fails to load.
        """
        
    def classify_intent(self, user_input: str) -> IntentClassification:
        """
        Classify user input against routes using semantic similarity.
        
        Returns IntentClassification with:
        - type: The agent type (route.name) or "orchestrator" (fallback)
        - confidence: Raw similarity score [0.0, 1.0] from semantic-router
        - method: "router" if confidence >= 0.7, else "llm_fallback"
        
        Routing logic:
        - If best route has similarity_score >= 0.7 and route.name is not None:
          return IntentClassification(type=route.name, confidence=score, method="router")
        - Otherwise:
          return IntentClassification(..., method="llm_fallback") and call llm_classify_intent()
        
        Note: llm_classify_intent() is a stub; no live LLM yet (documented limitation).
        """
```

### `llm_classify_intent()` (function, `intent/classifier.py`)

```python
def llm_classify_intent(user_input: str, fallback_context: str = "") -> IntentClassification:
    """
    Fallback classifier for when router confidence < 0.7.
    STUB: Returns IntentClassification(type="orchestrator", confidence=0.5, method="llm_fallback").
    Documented limitation: no live LLM call wired yet (task done when integrated in task-013 or later).
    """
```

### Agent `.md` file format

```markdown
---
name: architect
display_name: Architect
description: Designs systems, writes ADRs, makes architectural decisions
intent_triggers:
  - write an ADR
  - design the system
  - architectural decision
  - database schema
skills_preferred:
  - adr-writer
  - spec-writer
priority: high
requires_context:
  - repo
  - existing_architecture
---

You are an expert software architect. Your role is to design systems, evaluate trade-offs,
and document decisions via ADRs. Work with the coder and reviewer to ensure designs are
implementable and sound.

[Minimal 1-2 paragraph prompt stub; detailed prompts deferred to later refinement.]
```

### Skill `.md` file format (similar structure, same frontmatter keys)

```markdown
---
name: adr-writer
display_name: ADR Writer
description: Writes architectural decision records following ASES format
agent_types:
  - architect
  - documenter
intent_triggers:
  - write ADR
  - document decision
provides:
  - adr
estimated_tokens: 2000
---

You specialize in writing clear, concise architectural decision records (ADRs)...
```

## Acceptance Criteria (restated from plan.md)

- AC1: All 8 core agents (orchestrator, architect, coder, reviewer, tester, analyst, documenter, debugger) are successfully parsed from `.ases/agents/core/*.md`. `AgentRegistry.list_agents()` returns exactly 8 entries (all valid frontmatter, no skipped due to validation errors). `get_agent("coder")` returns the Agent with populated name/display_name/intent_triggers/system_prompt fields.
- AC2: All 10 core skills (repo-analysis, adr-writer, impact-analyzer, test-generator, code-reviewer, context-retriever, git-analyst, debt-analyzer, spec-writer, debug-tracer) are successfully parsed from `.ases/skills/core/*.md`. `SkillRegistry.list_skills()` returns exactly 10 entries with all required frontmatter fields.
- AC3: `IntentRouter.classify_intent("write an ADR for this decision")` correctly identifies the architect agent: returns `IntentClassification(type="architect", confidence>=0.7, method="router")` (exact type may vary based on seed utterances, but confidence must meet threshold and method must be "router").
- AC4: `IntentRouter.classify_intent("<deliberately ambiguous or off-domain text>")` returns `method="llm_fallback"` (confidence < 0.7, triggering fallback correctly).
- AC5: Zero regressions — all existing suites pass unchanged (repo-intelligence, context-hub, arch-intelligence, impact-analysis, shared/storage, apps/cli, api-server, tsc --noEmit).

## Expected Test Metrics

- Unit: 15+ tests (frontmatter parsing, cache behavior, duplicate-name override, lookup by intent/agent, etc.)
- Integration: 5+ tests (registry loads all real core .md files, router against seed corpus, immutability)
- Edge: 5+ tests (malformed YAML, missing required fields, empty directories, duplicate names in core+custom, unicode in prompts, confidence threshold boundary at 0.7)
- Coverage: ≥85% on new modules; pass rate 100%

**Validation coverage:** Tests must verify that malformed .md files are skipped (not loaded into cache) with warnings logged, and that all 8 core agents + 10 core skills load successfully without skipping.

## Known Limitations (declared BEFORE verification)

- No live LLM fallback: `llm_classify_intent()` returns a stub result (confidence=0.5, type="orchestrator"). Real LLM wiring is task-013 or later.
- Utterance seed corpus is hand-authored, not from real Phase 1+2 usage logs. Real-usage refinement deferred (matches FRD's two-stage design with fallback).
- Directory naming collision (`.ases/agents/` holds both process-role files and product agent metadata) resolved by ARCHITECT at GATE 2 (likely via `.ases/agents/core/` subdirectory).
- Registries are immutable after initialization; no hot-reload. If custom agents/skills are added at runtime, a new registry instance must be created. This is acceptable for Phase 3 (a single startup, no dynamic agent loading during a run).
- Frontmatter validation skips (does not error on) malformed YAML or missing required fields, with warnings logged. This is by design (partial loads during development), but acceptance tests will ensure all 8 core agents + 10 core skills parse successfully (no skipped entries).
