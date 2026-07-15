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
