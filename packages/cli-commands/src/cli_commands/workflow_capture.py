"""Best-effort ContextHub capture of CliCommands invocations.

Every guardrails()/decide()/plan()/refactor() call ingests a real
workflow_run artifact so ortho starts accumulating engineering memory
across runs. Capture must never affect the calling command's result --
any failure here (unwritable dir, corrupt db, invalid content) is logged
and swallowed, matching ArtifactStore._compute_embedding_async's own
"log and swallow" discipline for non-critical background writes.
"""

from __future__ import annotations

import logging
from pathlib import Path

from cli_commands.types import CliReport

_logger = logging.getLogger(__name__)

_CONTENT_EXCERPT_CHARS = 2000


def capture_workflow_run(
    scan_root: str,
    command: str,
    argument: str,
    report: CliReport,
) -> None:
    """Ingest a workflow_run artifact summarizing one CliCommands call.

    Never raises -- any failure is logged as a warning and swallowed.
    """
    try:
        resolved_root = Path(scan_root).resolve()
        if not resolved_root.is_dir():
            # OrthoDatabase.__init__ eagerly mkdir(parents=True)s its .ortho/
            # subdirectory -- constructing it against a nonexistent scan_root
            # would silently create the entire directory tree on disk as a
            # side effect of a failed/bad-path call. Bail out before that
            # constructor ever runs.
            return

        from repo_intelligence.index_store import mint_repo_id
        from storage import OrthoDatabase

        from context_hub.ingestion import ArtifactIngestionRequest
        from context_hub.store import ArtifactStore

        db = OrthoDatabase(resolved_root)
        db.migrate()
        repo_id = mint_repo_id(resolved_root)
        store = ArtifactStore(db, repo_id=repo_id)

        content = f"success={report.success}\n\n{report.content[:_CONTENT_EXCERPT_CHARS]}"
        req = ArtifactIngestionRequest(
            type="workflow_run",
            title=f"{command}: {argument}",
            content=content,
            source="cli",
            relevance_scope="project",
            tags=[command],
        )
        store.ingest_artifact(req)
    except Exception as e:
        _logger.warning("Workflow-run capture failed for %s(%r): %s", command, argument, e)


# Minimum BM25 relevance a prior workflow_run artifact must clear to be cited
# against a current finding. Below this, "rule_id location" keyword overlap
# is coincidental noise, not evidence of the same finding recurring.
_CITATION_MIN_RELEVANCE = 0.3
_CITATION_MAX_PER_REPORT = 3


def cite_prior_findings(scan_root: str, queries: list[str]) -> list[str]:
    """Search prior workflow_run artifacts for each query, return citation lines.

    This is the "you've seen this before" moat: a current guardrails/decide
    finding gets a one-line pointer to the closest matching prior run,
    instead of asserting the same violation fresh every time as if this
    were the first look at the repo. Read-only, best-effort, capped at
    _CITATION_MAX_PER_REPORT lines to avoid drowning the report in memory
    noise -- never raises, matching capture_workflow_run's discipline.
    """
    if not queries:
        return []

    try:
        resolved_root = Path(scan_root).resolve()
        if not resolved_root.is_dir():
            return []

        from storage import OrthoDatabase

        # Don't construct OrthoDatabase (which eagerly mkdirs .ortho/) against
        # a repo that has never been scanned before -- nothing to cite yet,
        # and this must stay a pure read, never a side-effecting write.
        db_path = resolved_root / ".ortho" / "ortho.db"
        if not db_path.exists():
            return []

        from repo_intelligence.index_store import mint_repo_id
        from context_hub.store import ArtifactStore

        db = OrthoDatabase(resolved_root)
        store = ArtifactStore(db, repo_id=mint_repo_id(resolved_root))

        citations: list[str] = []
        seen_artifact_ids: set[str] = set()
        for query in queries:
            if len(citations) >= _CITATION_MAX_PER_REPORT:
                break
            results = store.search(query, artifact_type="workflow_run", limit=1)
            if not results:
                continue
            top = results[0]
            if top.relevance_score < _CITATION_MIN_RELEVANCE or top.artifact_id in seen_artifact_ids:
                continue
            seen_artifact_ids.add(top.artifact_id)
            citations.append(f"[memory] Seen before: {top.title} ({top.created_at[:10]})")
        return citations
    except Exception as e:
        _logger.warning("Memory citation lookup failed for %s: %s", scan_root, e)
        return []
