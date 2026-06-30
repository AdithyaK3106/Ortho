# Architecture Decision Record Index

**Last Updated:** 2026-06-27 00:20 UTC  
**Maintainer:** ARCHITECT  
**Total ADRs:** 3

---

## Purpose

This index tracks all Architecture Decision Records (ADRs) for ASES. ADRs are permanent records of significant decisions that are hard to change later. Once ACCEPTED, they are locked (content never edited, only status changed if superseded).

---

## ADR Directory

| ID | Title | Status | Date | Summary |
|---|---|---|---|---|
| ADR-001 | ASES as Multi-Agent Engineering System | ACCEPTED | 2026-06-27 | Multi-agent orchestration with role separation, artifact-driven handoffs, evidence-gated completion to prevent isolated implementation, fabricated confidence, and honest uncertainty gaps |
| ADR-002 | Bootstrap Protocol for ASES Construction | ACCEPTED | 2026-06-27 | Phase 0 uses 5-rule minimal protocol (read CLAUDE.md, update CLAUDE.md, no false claims, verify and capture, commit) since full ASES cannot govern its own construction |
| ADR-003 | Evidence Capture Strategy — Terminal Output Only | ACCEPTED | 2026-06-27 | Evidence must come from tool output (compiler, linter, test runner), never from Claude assessment; Claude interprets logs but never generates them |

---

## Status Legend

- **DRAFT** — ARCHITECT is writing it
- **PROPOSED** — Written, awaiting human approval
- **ACCEPTED** — Human approved, locked (content never edited after this)
- **SUPERSEDED BY ADR-NNN** — Newer ADR overrides this one

---

## Accessing Full ADRs

Click a link to read the full ADR:

- [ADR-001: ASES as Multi-Agent Engineering System](./ADR-001-ases-multi-agent-orchestration.md)
- [ADR-002: Bootstrap Protocol for ASES Construction](./ADR-002-bootstrap-protocol.md)
- [ADR-003: Evidence Capture Strategy — Terminal Output Only](./ADR-003-evidence-capture-terminal-only.md)

---

## Guidelines for Adding ADRs

### When to Create an ADR

Create an ADR when:
- ✓ A new module, service, or layer is introduced
- ✓ A dependency is added to the project
- ✓ An API contract is defined or changed
- ✓ A database schema design is decided
- ✓ A security approach is chosen
- ✓ A decision reverses or overrides a previous decision
- ✓ A decision will be hard or expensive to change later

### When NOT to Create an ADR

ADR is optional for:
- ✗ Bug fixes that don't change design
- ✗ Refactoring within existing module boundaries
- ✗ Adding a feature that fits cleanly into existing patterns

### Naming Convention

`ADR-[NNN]-[kebab-case-title].md`

Example: `ADR-004-repository-pattern-for-expenses.md`

Numbers are sequential and never reused, even if superseded.

---

## Recent ADR Changes

### 2026-06-27 (Initial Bootstrap)
- ADR-001 ACCEPTED: Multi-agent orchestration system
- ADR-002 ACCEPTED: Bootstrap protocol
- ADR-003 ACCEPTED: Evidence capture terminal-only

---

*End of ADR INDEX*
