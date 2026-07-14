# ADR-016: Engineering Copilot Layer (change-planner, arch-guardrails, decision-engine)

Status: ACCEPTED
Date: 2026-07-14
Author: ARCHITECT
Approved by: urbra on 2026-07-14

## Context

ADR-015 (2026-07-12) defined 3 layers — Core (orchestration), Intelligence
(repo-intelligence, arch-intelligence, impact-analysis), Storage — plus
Apps and Shared. Phase 6 (completed after ADR-015) added four new packages
— `change-planner`, `feature-planner`, `refactoring-advisor`,
`arch-guardrails`, `decision-engine`, `cli-commands` — none of which are
classified in ADR-015's layer table. task-017 requires wiring
`cli-commands` to `arch-guardrails`/`change-planner`/`decision-engine`,
which in turn consume `repo-intelligence`/`arch-intelligence` output, and
without an explicit layer assignment there is no rule to check the wiring
against.

## Problem Statement

Where do the Phase 6 packages sit in the one-way acyclic dependency graph,
and what are they allowed to import?

## Alternatives Considered

- **Option A:** Classify them as part of the existing Intelligence layer —
  rejected because Intelligence packages are defined as parallel/independent
  analysis producers that don't consume each other's output; change-planner
  and arch-guardrails explicitly aggregate multiple intelligence sources by
  design (see `decision_engine.engine.DecisionEngine.decide()`, which takes
  a `sources: dict[str, list[Any]]` spanning change_planner, feature_planner,
  refactoring_advisor, arch_guardrails).
- **Option B:** Classify them as part of Core (orchestration) — rejected
  because Core is defined as intent-routing/selection/execution
  infrastructure with no knowledge of specific intelligence implementations,
  whereas these packages are themselves intelligence *consumers* with
  business logic (confidence scoring, recommendation ranking).
- **Option C (chosen):** New layer, "Engineering Copilot," sitting between
  Apps and Intelligence. Consumes Intelligence layer output exclusively
  through protocol-typed adapters (never raw Intelligence internals passed
  across a second Intelligence package's boundary), and is itself consumed
  by Apps (`cli-commands`, `apps/cli`, `apps/api-server`).

## Decision

Add a fourth layer, **Engineering Copilot**, positioned between Apps and
Intelligence:

```
apps/*
    ↓
core/* (orchestration)
    ↓
engineering-copilot/*   (change-planner, feature-planner, refactoring-advisor, arch-guardrails, decision-engine)  ← NEW
    ↓
intelligence/*          (arch-intelligence, impact-analysis, repo-intelligence)
    ↓
storage/*
    ↓
shared/*
```

**Can import from:** Intelligence (via `__all__` only), Storage, Shared
**Cannot import from:** Apps, Core, each other's internals (only via each
package's own `__all__` — e.g. `arch-guardrails` may import
`decision_engine.Recommendation` type via `__all__`, not
`decision_engine.engine._score_option`)

`cli-commands` remains classified as **Apps** (it is the CLI-facing
orchestration surface, matches ADR-015's existing Apps definition: "Can
import from: Core, Intelligence, Storage, Shared").

Cross-Intelligence-package data bridging (e.g. combining
`repo_intelligence.ImportEdge` with `arch_intelligence.ArchitectureModel`)
must happen in the Apps layer (`cli-commands`) or within a single
Engineering Copilot package that accepts pre-built primitives (plain
dicts/lists) from the Apps layer — never inside one Intelligence package
importing another Intelligence package's types directly.

## Rationale

This preserves ADR-015's core invariant (Intelligence packages stay
parallel and independent, never cross-import each other) while giving the
Phase 6 aggregation packages a legitimate, named place to live. Apps-layer
bridging keeps the "who resolves file-path-to-module-identity" question
answered in exactly one place per pipeline run, rather than duplicated
across Intelligence packages that would otherwise each need their own
resolution logic to talk to each other.

## Consequences

Positive:
- Phase 6 packages get an explicit, enforceable position instead of
  silently violating or silently exempting ADR-015.
- task-017's corrected design (adapters bridging repo-intelligence data
  into arch-intelligence/arch-guardrails via cli-commands) is a template
  future Engineering Copilot wiring tasks can follow.

Negative:
- `cli-commands` (Apps layer) carries more responsibility than a typical
  thin CLI wrapper — it becomes the place where cross-Intelligence bridging
  logic lives. If this grows large, a future ADR may want to extract a
  dedicated "bridge" package between Apps and Engineering Copilot.

Neutral:
- No existing code needs to move for this ADR alone; task-017 is the first
  task built under it.

## Future Considerations

If cross-Intelligence bridging logic in `cli-commands` grows beyond ~2-3
adapter classes, consider extracting a dedicated
`packages/repo-graph-bridge` package sitting between Apps and Engineering
Copilot, so `cli-commands` stays a thin orchestration surface again.

## Related Tasks

- task-017-repo-graph-queries: first task built under this ADR.

## Related ADRs

- ADR-015: Layer Boundaries & Import Rules — extended by this ADR, not
  superseded. ADR-015's Apps/Intelligence/Storage/Shared rules remain in
  effect unchanged; this ADR only adds the missing Engineering Copilot row.
