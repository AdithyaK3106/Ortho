# task-012 Specification Refinements — Summary

**Date:** 2026-07-07  
**Refinement Type:** Specification Clarifications (no architecture or scope changes)

## Changes Made

Four specification refinement sections added to `spec.md` (new "Specification Details" section before "Contracts"):

### 1. Registry Cache Behavior

**Rule:** Registries are immutable after initialization. No `reload()` method.

- Load happens once in `__init__()`: scan `core/` and `custom/` directories, parse all `.md` files
- Cache held in memory for object lifetime
- To refresh (e.g., if custom agents added at runtime), create a new registry instance
- Rationale: Keeps implementation simple, deterministic, no concurrent modification risk

**Updated Contract Docstrings:**
- `AgentRegistry.__init__()`: "Cache lifetime: until object is garbage-collected"
- `SkillRegistry.__init__()`: Same
- Class docstrings: "No reload() method; create a new instance to refresh"

### 2. Duplicate Name Policy

**Rule:** If same agent/skill name exists in both `core/` and `custom/`, **custom wins**.

- Load order: `core/` first, then `custom/`
- Custom entries with same `name` field replace core entries in cache
- Deterministic behavior (no error, no silent failure, no ambiguity)
- Rationale: Custom agents are intended to extend/override core agents (per FRD Section 11)

**Updated Contract Docstrings:**
- Both registries: "If duplicate agent/skill names exist in both core/ and custom/, custom/ entry wins"
- `list_agents()` / `list_skills()`: "Return all successfully loaded [agents/skills] sorted by name"

### 3. Router Confidence

**Rule:** `confidence` is the raw semantic similarity score [0.0, 1.0], not a calibrated probability.

- Directly exposed to callers (no normalization or scaling)
- Threshold (0.7) is hardcoded to `IntentRouter.classify_intent()` for task-012
- Threshold can be made configurable in future tasks without changing confidence semantics
- Rationale: Raw scores provide better debugging/tuning signal; threshold is policy, not semantics

**Updated Documentation:**
- `IntentClassification` docstring: "Raw semantic similarity score [0.0, 1.0] from semantic-router (not a calibrated probability). Exposed directly; threshold (0.7) is internal."
- `IntentRouter` docstring: "Confidence field is the raw semantic similarity score [0.0, 1.0] from semantic-router. It is NOT a calibrated probability, only a similarity metric."
- `classify_intent()` docstring: "Returns IntentClassification with: ... confidence: Raw similarity score [0.0, 1.0] from semantic-router"

### 4. Frontmatter Validation

**Rule:** Strict validation with skip-on-error (not fail-on-error).

**Required Fields:**
- Agent: `name, display_name, description, intent_triggers, skills_preferred, priority, requires_context`
- Skill: `name, display_name, description, agent_types, intent_triggers, provides, estimated_tokens`

**Behavior on Error:**
- Malformed YAML → Log warning, skip entry, continue loading
- Missing required field → Log warning, skip entry, continue loading
- Invalid data type → Log warning, skip entry, continue loading
- Empty file → Log warning, skip entry, continue loading

**Result:** `list_agents()` / `list_skills()` returns only successfully parsed entries. Skipped entries are not in cache.

**Updated Contract Docstrings:**
- `AgentRegistry.__init__()`: "Malformed YAML or missing required fields cause the file to be skipped with a warning logged"
- `list_agents()`: "Skipped entries (due to validation errors) are not included"
- `get_agent()`: "Get agent by name from cache, or None if not found or skipped due to validation error"
- Same for `SkillRegistry`

**Added to Known Limitations:**
- "Registries are immutable after initialization; no hot-reload."
- "Frontmatter validation skips (does not error on) malformed YAML or missing required fields, with warnings logged. Tests ensure all 8 core agents + 10 core skills parse successfully (no skipped entries)."

---

## Consistency Verification

All four refinements are now consistently documented across:
- ✅ `spec.md` Specification Details section (new, detailed rules)
- ✅ `spec.md` Class/function contracts (docstrings updated)
- ✅ `spec.md` Acceptance Criteria (AC1–AC2 explicit about "no skipped entries")
- ✅ `spec.md` Expected Test Metrics (validation coverage explicitly called out)
- ✅ `spec.md` Known Limitations (immutability + validation behavior noted)
- ✅ `plan.md` Key Data-Model Facts (updated for consistency)

No architectural or scope changes. Approved scope and implementation approach remain unchanged.

---

## Impact on BUILDER (Task Implementation)

**When BUILDER begins implementation, these rules are binding:**

1. **Registry initialization:** Load both core/ and custom/ directories. Parse all .md files once. Raise FileNotFoundError if core/ missing. Log warnings for skipped entries; do not raise.
2. **Immutability:** Do not implement reload(). Cache held in memory until object garbage-collected.
3. **Custom override:** If same agent/skill name in both core/ and custom/, custom entry wins (last-loaded = final).
4. **Confidence semantics:** Do not normalize or scale confidence scores. Pass raw similarity from semantic-router directly to `IntentClassification.confidence`.
5. **Validation logic:** Strict parsing, skip-on-error behavior, warnings logged (examples: missing `priority` field → skip, malformed YAML → skip).

All edge-case tests (task-plan: "malformed YAML, missing fields, duplicates, etc.") must verify these behaviors, and all 8 core agents + 10 core skills must parse without skipping.

---

*Refinements approved and consistent. Ready for ARCHITECT GATE 2 review.*
