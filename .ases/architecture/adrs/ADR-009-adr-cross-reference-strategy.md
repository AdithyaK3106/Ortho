# ADR-009: ADR Cross-Reference Strategy — Markdown-Text Extraction, Not a Markdown AST

**Status:** PROPOSED
**Date:** 2026-07-02
**Author:** ARCHITECT
**Approved by:** [Pending human approval]

---

## Context

Task-010 implements ADR awareness (FRD Pillar 3 feature, line 854): cross-reference the ADRs in
`.ases/architecture/adrs/*.md` against the actual repo tree, so drift (an ADR referencing a file
that was later deleted or renamed) is detected instead of silently rotting.

ADRs in this repo are free-form markdown prose (see ADR-001 through ADR-005) — there is no
frontmatter schema, no structured "referenced files" field, and no enforcement that authors write
paths in any particular way. `ADRTracker` must extract code references from this prose reliably
enough that two independent implementations produce identical results (a requirement the PLANNER
made explicit during GATE 1 revision).

---

## Problem Statement

**How should Ortho parse code references out of unstructured ADR markdown?**

Options:
1. **Full markdown AST parser** (e.g. a CommonMark-compliant parser) — walk the document tree,
   classify code spans/links/sections structurally
2. **Regex/line-based text extraction** — pattern-match specific structural markers
   (`File:`/`Code:` lines, markdown link syntax, backtick spans) directly against raw text
3. **NLP/semantic extraction** — infer "this ADR is about this file" from prose meaning

---

## Alternatives Considered

### Option A: Full Markdown AST Parser

**Description:** Add a markdown parsing dependency (e.g. `markdown-it-py`, `mistune`), build a
proper document tree, walk it for code spans, link nodes, and heading-delimited sections.

**Pros:**
- Handles markdown edge cases correctly (nested formatting, escaped characters, code fences)
- More "correct" in a formal sense

**Cons:**
- ❌ New dependency for a task whose spec explicitly favors stdlib-first (ponytail mode, active
  on this project) and local-first, no-ML-dependency precedent (matches the ReuseDetector
  decision in ADR-010)
- ❌ Overkill for the actual extraction surface: ADRs reference paths via four narrow patterns
  (File:/Code: lines, markdown links, backtick spans) — a full AST doesn't make classifying those
  four patterns meaningfully more reliable
- ❌ Larger surface area to keep deterministic across parser library versions (a markdown library
  upgrade could silently change tokenization and shift extraction results — the opposite of the
  determinism goal)

**Verdict:** ❌ **Rejected** — solves a more general problem than the one task-010 has, at the
cost of a new dependency and version-drift risk to determinism.

---

### Option C: NLP/Semantic Extraction

**Description:** Infer code references from prose meaning (e.g. "the database module" → maps to
`shared/storage/`).

**Pros:**
- Would catch prose-only references that Option B explicitly cannot (documented as Known
  Limitation 1 in spec.md)

**Cons:**
- ❌ Non-deterministic by construction — directly violates the GATE 1 requirement that two
  independent implementations produce identical results
- ❌ Requires an NLP dependency or model, violating the local-first-no-ML precedent already
  established for `ReuseDetector` (ADR-010) and consistent with FRD's local-first principle
- ❌ Unverifiable evidence — a false STALE flag from a wrong semantic inference would be far
  worse than the accepted under-reporting bias documented in plan.md's risk table

**Verdict:** ❌ **Rejected** — not deterministic, not local-first, and worse failure mode than
the accepted alternative.

---

### Option B: Regex/Line-Based Text Extraction (Chosen)

**Description:** Pattern-match the four extraction rules already fully specified in
`.ases/tasks/task-010-adr-awareness-reporting/spec.md` ("ADR Path Extraction Contract") directly
against raw markdown text, without building an intermediate document tree.

**Pros:**
- ✅ Zero new dependencies (stdlib `re` only)
- ✅ Deterministic by construction — same regex, same input, same output, no library-version
  sensitivity
- ✅ Precedence-ordered rules (File:/Code: lines → markdown links → backtick spans) are already
  fully specified in spec.md, closing the ambiguity that would otherwise make two independent
  implementations diverge
- ✅ Consistent with `ReuseDetector`'s local-first, deterministic, evidence-backed pattern
  (ADR-010) and task-008/009's established "stateless, deterministic" precedent
- ✅ Explicitly biases toward under-reporting (missed prose-only references) over false positives
  (wrong STALE classification) — the correct trade-off per plan.md's risk table, since a
  human-readable evidence trail matters more than exhaustive recall here

**Cons:**
- ❌ Cannot detect prose-only references (documented as Known Limitation 1 in spec.md, accepted)
- ❌ Regex patterns must be maintained carefully to avoid false-positive path matches (mitigated
  by the "path-shaped" heuristic in the extraction contract: must contain `/` or a recognized
  file extension, with bare identifiers like `` `ArchitectureModel` `` explicitly excluded)

**Verdict:** ✅ **Selected** — matches the actual problem size, keeps determinism guaranteed
rather than merely likely, and adds no dependency.

---

## Decision

**`ADRTracker` extracts code references from ADR markdown using stdlib regex against raw text,
following the four-rule precedence order and normalization/deduplication contract fully specified
in `spec.md`'s "ADR Path Extraction Contract" section — not a markdown AST parser.**

### Core Components

1. **Module:** `packages/arch-intelligence/src/arch_intelligence/adr_tracker.py`
   - `ADRTracker.check_adrs(adr_dir: Path, repo_root: Path) -> list[ADRStatus]`
   - No markdown parsing dependency; `re` module only

2. **Extraction contract** (already specified, referenced not restated here): see
   `.ases/tasks/task-010-adr-awareness-reporting/spec.md`, "ADR Path Extraction Contract"

3. **Data type:** `ADRStatus` dataclass — `adr_id`, `title`, `status`, `referenced_paths`,
   `missing_paths`, `classification`, `evidence` (all primitive/list-of-str)

---

## Rationale

1. **Determinism over completeness:** The GATE 1 revision explicitly required that "two
   independent implementations produce identical ADR parsing results." A full markdown AST parser
   makes this harder to guarantee (parser library behavior can shift across versions); explicit
   regex rules make it easy to guarantee (the rules themselves are the specification).

2. **Local-first, no new dependency:** Matches the same reasoning already accepted for
   `ReuseDetector`'s similarity algorithm (ADR-010) — stdlib first, no ML/NLP, no markdown library
   for a narrow extraction task that doesn't need one.

3. **Correct failure mode:** Under-reporting (missing a prose-only reference) is an acceptable,
   documented limitation. Over-reporting (a wrong STALE flag from misclassified prose) would be
   actively harmful — regex-based extraction against explicit patterns keeps this failure mode
   rare and explainable via the `evidence` field.

4. **Scoped to the actual problem:** ADRs in this repo (and the pattern established by ADR-001
   through ADR-005) already tend to reference code via backtick-quoted paths in prose or explicit
   `File:` sections in code blocks — the four-rule contract was derived by reading the actual
   ADRs, not designed in the abstract.

---

## Consequences

### Positive

- No new dependency added to `packages/arch-intelligence/pyproject.toml`
- Extraction behavior is fully specified and testable without needing to mock a parser library
- Consistent, auditable code (a human reviewing `adr_tracker.py` can trace every classification
  back to one of four named rules)

### Negative

- Prose-only references are permanently undetectable without a future architecture change
  (accepted, documented in spec.md Known Limitations)
- If ADR authoring style changes significantly in the future (e.g. a move to structured
  frontmatter), the extraction rules would need revision — but this is a low-cost change (edit
  regex patterns, not re-architect a parser integration)

### Neutral

- Performance is not a concern at this scale (ADR count is in the tens, not thousands; regex
  matching against markdown text is effectively instantaneous)

---

## Future Considerations

### If ADR Volume or Authoring Style Changes Significantly

**Scenario:** The project adopts structured ADR frontmatter (e.g. YAML `references: [...]` field)
as part of a future ADR tooling improvement.

**Mitigation:** Add frontmatter parsing as a fifth, higher-precedence extraction rule (frontmatter
`references:` list takes priority over all four current rules). This is additive, not a
re-architecture — the underlying `ADRStatus` contract and classification logic (OK/STALE/UNLINKED/
UNKNOWN) don't change.

**Current decision:** Not needed for task-010; revisit only if ADR authoring practice changes.

---

## Related Tasks

- **task-010:** ADR Awareness + Reporting (this task, Week 13–14)
- **task-001 through task-009:** Source ADRs (ADR-001 through ADR-005 wrote the actual prose this
  extraction contract was derived by reading)

---

## Related ADRs

- **ADR-010:** Reuse Similarity Algorithm — same task, same local-first/stdlib-first/deterministic
  reasoning applied to a different problem (structural code similarity instead of markdown text
  extraction)
- **ADR-004:** Storage Strategy (SQLite, local-first) — `ADRTracker` follows the same local-first
  principle: no external service, no network call, pure filesystem + text analysis

---

*End of ADR-009*
