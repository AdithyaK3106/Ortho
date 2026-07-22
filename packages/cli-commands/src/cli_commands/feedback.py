"""Accept/reject feedback loop.

The roadmap's stated moat: "this recommendation was rejected three months
ago because it introduced circular dependencies." A memory citation that
only ever says "seen before" doesn't deliver that -- it needs a developer
action recorded (accept/reject + why), then surfaced on future runs.

Stored as "decision" artifacts (an existing, already-valid ArtifactStore
type) keyed by the same "{rule_id} {location}" string cite_prior_findings
already uses to query workflow_run artifacts, so a feedback record and the
finding it responds to line up under one query without inventing a
parallel keying scheme.
"""

from __future__ import annotations

import logging
from pathlib import Path

_logger = logging.getLogger(__name__)

_VALID_DECISIONS = ("accept", "reject")


def _normalize_finding_key(finding_key: str) -> str:
    """"->" and " -> " are what a keyboard types; enforcer.py's cycle
    locations are joined with the Unicode arrow "→". Without this, a
    finding_key typed with ASCII arrows (as the CLI's own --help example
    shows) never matches the location string it's meant to reference, so
    record_feedback silently stores an orphan record and lookup_feedback
    never finds it -- no error, just a citation that quietly never appears.
    """
    return finding_key.replace("->", "→")


def record_feedback(
    repo_path: str,
    finding_key: str,
    decision: str,
    reason: str = "",
) -> bool:
    """Record an accept/reject decision for a specific finding.

    finding_key should match the "{rule_id} {location}" format
    workflow_capture.cite_prior_findings already queries by, so a later
    run's citation lookup finds this record naturally.

    Returns True on success, False on any failure (never raises -- matches
    capture_workflow_run's "log and swallow" discipline for this
    best-effort memory layer, since a feedback-recording failure must not
    block or crash the command the user actually ran).
    """
    if decision not in _VALID_DECISIONS:
        raise ValueError(f"decision must be one of {_VALID_DECISIONS}, got {decision!r}")
    if not finding_key or not finding_key.strip():
        raise ValueError("finding_key cannot be empty")

    finding_key = _normalize_finding_key(finding_key)

    try:
        resolved_root = Path(repo_path).resolve()
        if not resolved_root.is_dir():
            return False

        from repo_intelligence.index_store import mint_repo_id
        from storage import OrthoDatabase

        from context_hub.ingestion import ArtifactIngestionRequest
        from context_hub.store import ArtifactStore

        db = OrthoDatabase(resolved_root)
        db.migrate()
        repo_id = mint_repo_id(resolved_root)
        store = ArtifactStore(db, repo_id=repo_id)

        content = f"decision={decision}\nfinding={finding_key}\nreason={reason}"
        req = ArtifactIngestionRequest(
            type="decision",
            title=f"feedback: {finding_key}",
            content=content,
            source="cli",
            relevance_scope="project",
            tags=["feedback", decision],
        )
        store.ingest_artifact(req)
        return True
    except Exception as e:
        _logger.warning("Feedback recording failed for %r: %s", finding_key, e)
        return False


def lookup_feedback(repo_path: str, finding_key: str) -> str | None:
    """Return the most recent feedback line for this exact finding, or None
    if no feedback was ever recorded. Read-only, best-effort -- never
    raises, matching cite_prior_findings' discipline.

    Distinct from cite_prior_findings (which does fuzzy BM25 matching
    across workflow_run history): this is an exact lookup against a
    specific finding_key, used to answer "was THIS finding rejected
    before, and why" rather than "has something like this come up before."
    """
    if not finding_key or not finding_key.strip():
        return None

    finding_key = _normalize_finding_key(finding_key)

    try:
        resolved_root = Path(repo_path).resolve()
        if not resolved_root.is_dir():
            return None

        from storage import OrthoDatabase

        db_path = resolved_root / ".ortho" / "ortho.db"
        if not db_path.exists():
            return None

        from repo_intelligence.index_store import mint_repo_id
        from context_hub.store import ArtifactStore

        db = OrthoDatabase(resolved_root)
        store = ArtifactStore(db, repo_id=mint_repo_id(resolved_root))

        results = store.search(finding_key, artifact_type="decision", limit=10)
        # Exact match on the finding_key embedded in content, not just BM25
        # relevance -- a fuzzy match here would risk citing feedback for a
        # different finding as if it were about this one.
        exact_matches = [
            r for r in results
            if f"finding={finding_key}\n" in r.content or r.content.endswith(f"finding={finding_key}")
        ]
        if not exact_matches:
            return None

        top = max(exact_matches, key=lambda r: r.created_at)
        decision = ""
        reason = ""
        for line in top.content.splitlines():
            if line.startswith("decision="):
                decision = line.split("=", 1)[1]
            if line.startswith("reason="):
                reason = line.split("=", 1)[1]

        if decision == "reject" and reason:
            return f"[memory] Rejected before ({top.created_at[:10]}): {reason}"
        elif decision == "reject":
            return f"[memory] Rejected before ({top.created_at[:10]}), no reason given"
        else:
            return f"[memory] Accepted before ({top.created_at[:10]})"
    except Exception as e:
        _logger.warning("Feedback lookup failed for %r: %s", finding_key, e)
        return None
