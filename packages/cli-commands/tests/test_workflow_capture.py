"""Hard tests / edge cases for task-020-contexthub-capture.

Written BLIND from spec.md/plan.md/rollback-plan.md/architecture-review.md
as TEST-DESIGNER, in parallel with BUILDER. Only import paths, constructor
signatures, and attribute names were confirmed against real code (per this
project's shadow-parallel discipline) — no test *assertions* here were
shaped by reading BUILDER's implementation.

Confirmed-real plumbing (read directly, not guessed):
- `cli_commands.types.CliReport` is a dataclass:
  `CliReport(title: str, content: str, format: str = "text", success: bool = True)`.
- `cli_commands.commands.CliCommands` has no custom `__init__` (no args).
- `storage.database.OrthoDatabase(project_root: Path)`; `.migrate()` creates
  `<project_root>/.ortho/ortho.db` (via `db_path.parent.mkdir(parents=True,
  exist_ok=True)` in `__init__`, then runs migrations in `.migrate()`).
- `context_hub.store.ArtifactStore(db: OrthoDatabase, repo_id: str,
  embedding_provider: Optional[EmbeddingProvider] = None)`.
  `.ingest_artifact(req: ArtifactIngestionRequest) -> str` raises
  `ValueError` on validation failure (see `ingestion.py::validate_ingestion`).
  `.get_artifact(artifact_id: str) -> Optional[Artifact]`.
- `context_hub.ingestion.ArtifactIngestionRequest(type, title, content,
  source, relevance_scope, tags, related_symbols=None)`;
  `ARTIFACT_TYPES` includes `"workflow_run"`.
- `repo_intelligence.index_store.mint_repo_id(repo_root: Path) -> str`
  returns a 16-hex-char sha256-derived id, stable for a given resolved path.
- Fixture repo: `repos/click` lives at the monorepo root, i.e.
  `Path(__file__).resolve().parents[3] / "repos" / "click"` from this test
  file's location (packages/cli-commands/tests/) — matches the pattern
  already used in test_commands.py.

ASSUMPTION FLAGGED (not confirmed against real code, per instructions --
BUILDER's file existed on disk when this was written but its body was
deliberately not read): the public entry point under test is
`cli_commands.workflow_capture.capture_workflow_run(scan_root: str,
command: str, argument: str, report: CliReport) -> None`, taken verbatim
from spec.md's contract. If BUILDER's actual signature/param names differ,
these tests' import line and direct-call tests (not the CliCommands
end-to-end ones) will need adjusting.
"""
from __future__ import annotations

import os
import sqlite3
import stat
from pathlib import Path
from typing import Any

import pytest

from cli_commands.commands import CliCommands
from cli_commands.types import CliReport
from cli_commands.workflow_capture import capture_workflow_run

from storage import OrthoDatabase
from context_hub.store import ArtifactStore
from repo_intelligence.index_store import mint_repo_id


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO = str(_REPO_ROOT / "repos" / "click")


def _open_store(scan_root: str) -> ArtifactStore:
    """Open the real ArtifactStore backing `scan_root`'s .ortho/ortho.db.
    No mocking -- this is the same construction path spec.md prescribes for
    capture_workflow_run itself."""
    db = OrthoDatabase(Path(scan_root))
    db.migrate()
    return ArtifactStore(db, repo_id=mint_repo_id(Path(scan_root).resolve()))


def _workflow_run_rows(scan_root: str) -> list[tuple]:
    """Raw query against the real sqlite file, bypassing ArtifactStore, so
    that a test verifying "a row landed" isn't relying on the same code
    path that wrote it to also read it back correctly."""
    db_path = Path(scan_root) / ".ortho" / "ortho.db"
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT id, repo_id, type, title, content, tags FROM artifacts WHERE type = 'workflow_run'"
        ).fetchall()
    finally:
        conn.close()
    return rows


# ---------------------------------------------------------------------------
# 1. capture_workflow_run must never raise and never affect report.success
# ---------------------------------------------------------------------------

class TestNeverRaisesNeverFlipsSuccess:
    def test_nonexistent_scan_root_does_not_raise(self) -> None:
        report = CliReport(title="t", content="c", success=True)
        # Should be a no-op / swallowed failure, not an exception.
        capture_workflow_run("/definitely/does/not/exist/xyz123", "guardrails", "somearg", report)
        assert report.success is True  # untouched

    def test_nonexistent_scan_root_does_not_raise_on_failure_report(self) -> None:
        report = CliReport(title="t", content="c", success=False)
        capture_workflow_run("/definitely/does/not/exist/xyz123", "guardrails", "somearg", report)
        assert report.success is False  # untouched, still false, not further corrupted

    def test_corrupt_existing_db_does_not_raise(self, tmp_path: Path) -> None:
        """A pre-existing, garbage .ortho/ortho.db (not a valid sqlite file)
        should cause OrthoDatabase.migrate() to raise internally -- capture
        must catch that, not propagate it."""
        ortho_dir = tmp_path / ".ortho"
        ortho_dir.mkdir(parents=True)
        (ortho_dir / "ortho.db").write_bytes(b"this is not a sqlite database, just garbage bytes")

        report = CliReport(title="t", content="c", success=True)
        capture_workflow_run(str(tmp_path), "plan", "add caching", report)
        assert report.success is True

    def test_malformed_content_does_not_raise(self, tmp_path: Path) -> None:
        """Whitespace-only content (fails ingestion validation per
        ingestion.py: 'content cannot be whitespace only') must be caught
        inside capture_workflow_run, not bubble up as ValueError."""
        report = CliReport(title="t", content="   \n\t  ", success=True)
        capture_workflow_run(str(tmp_path), "decide", "   ", report)
        assert report.success is True

    def test_empty_argument_does_not_raise(self, tmp_path: Path) -> None:
        """An empty `argument` could make `title = f'{command}: {argument}'`
        degenerate, but title is never fully empty (command is always
        non-empty per the 4 fixed call sites) so this should still succeed
        or at worst be silently swallowed -- never raise."""
        report = CliReport(title="t", content="some real content here", success=True)
        capture_workflow_run(str(tmp_path), "refactor", "", report)
        assert report.success is True

    def test_returns_none(self, tmp_path: Path) -> None:
        """Contract says -> None."""
        report = CliReport(title="t", content="valid content", success=True)
        result = capture_workflow_run(str(tmp_path), "guardrails", "x", report)
        assert result is None


# ---------------------------------------------------------------------------
# 2. repo_id stability/uniqueness (anti-overfitting: no hardcoded hashes)
# ---------------------------------------------------------------------------

class TestRepoIdStabilityAndUniqueness:
    def test_same_directory_yields_same_repo_id_across_calls(self, tmp_path: Path) -> None:
        id_a = mint_repo_id(Path(tmp_path).resolve())
        id_b = mint_repo_id(Path(tmp_path).resolve())
        assert id_a == id_b

    def test_different_directories_yield_different_repo_ids(self, tmp_path: Path) -> None:
        dir_1 = tmp_path / "repo_one"
        dir_2 = tmp_path / "repo_two"
        dir_1.mkdir()
        dir_2.mkdir()
        assert mint_repo_id(dir_1.resolve()) != mint_repo_id(dir_2.resolve())

    def test_capture_against_same_dir_twice_uses_same_repo_id(self, tmp_path: Path) -> None:
        """End-to-end: two captures against the identical real directory
        must land under the same repo_id in the artifacts table (no
        cross-call repo_id drift)."""
        report = CliReport(title="t", content="first run content", success=True)
        capture_workflow_run(str(tmp_path), "guardrails", "arg1", report)
        report2 = CliReport(title="t", content="second run content", success=True)
        capture_workflow_run(str(tmp_path), "guardrails", "arg2", report2)

        rows = _workflow_run_rows(str(tmp_path))
        repo_ids = {row[1] for row in rows}
        assert len(repo_ids) == 1

    def test_capture_against_two_dirs_uses_different_repo_ids(self, tmp_path: Path) -> None:
        dir_1 = tmp_path / "repo_a"
        dir_2 = tmp_path / "repo_b"
        dir_1.mkdir()
        dir_2.mkdir()

        report_1 = CliReport(title="t", content="content for repo a", success=True)
        capture_workflow_run(str(dir_1), "guardrails", "x", report_1)
        report_2 = CliReport(title="t", content="content for repo b", success=True)
        capture_workflow_run(str(dir_2), "guardrails", "x", report_2)

        rows_1 = _workflow_run_rows(str(dir_1))
        rows_2 = _workflow_run_rows(str(dir_2))
        assert len(rows_1) == 1
        assert len(rows_2) == 1
        assert rows_1[0][1] != rows_2[0][1]  # repo_id column differs


# ---------------------------------------------------------------------------
# 3. Captured artifact is real and queryable (no mocking of ArtifactStore)
# ---------------------------------------------------------------------------

class TestArtifactIsRealAndQueryable:
    def test_capture_workflow_run_writes_real_row(self, tmp_path: Path) -> None:
        report = CliReport(
            title="Architecture Guardrails",
            content="Scanned 3 files. No violations found.",
            success=True,
        )
        capture_workflow_run(str(tmp_path), "guardrails", str(tmp_path), report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        _id, repo_id, type_, title, content, tags = rows[0]
        assert type_ == "workflow_run"
        assert "guardrails" in title
        assert repo_id == mint_repo_id(Path(tmp_path).resolve())

    def test_artifact_queryable_via_artifact_store_get_artifact(self, tmp_path: Path) -> None:
        """Not just raw-sqlite-visible -- also readable through the real
        ArtifactStore API, proving the row is well-formed (valid JSON tags,
        etc.), not just present."""
        report = CliReport(title="Feature Plan", content="Plan: do the thing", success=True)
        capture_workflow_run(str(tmp_path), "plan", "do the thing", report)

        store = _open_store(str(tmp_path))
        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        artifact_id = rows[0][0]

        artifact = store.get_artifact(artifact_id)
        assert artifact is not None
        assert artifact.type == "workflow_run"
        assert "plan" in artifact.tags

    def test_tags_contain_command_name(self, tmp_path: Path) -> None:
        report = CliReport(title="Refactoring Advice", content="Extract method X", success=True)
        capture_workflow_run(str(tmp_path), "refactor", str(tmp_path), report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        import json
        tags = json.loads(rows[0][5])
        assert tags == ["refactor"]

    def test_title_includes_command_and_argument(self, tmp_path: Path) -> None:
        report = CliReport(title="Decision", content="Recommended approach: X", success=True)
        capture_workflow_run(str(tmp_path), "decide", "improve code quality", report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        title = rows[0][3]
        assert "decide" in title
        assert "improve code quality" in title


# ---------------------------------------------------------------------------
# 4. Content excerpt bounding (2000-char rule)
# ---------------------------------------------------------------------------

class TestContentExcerptBounding:
    def test_huge_content_is_bounded_not_stored_unbounded(self, tmp_path: Path) -> None:
        """spec.md: content = f"success={report.success}\n\n{report.content[:2000]}".
        We don't hardcode the exact stored length (blind to whether BUILDER's
        slice math, prefix text, or newline handling shifts the byte count
        by a few chars) -- we assert the stored content is dramatically
        shorter than the original 50,000-char input and comfortably under a
        generous safety-margin bound (2200 chars: 2000 + room for the
        "success=True\n\n" prefix and any incidental formatting)."""
        huge_content = "x" * 50_000
        report = CliReport(title="Architecture Guardrails", content=huge_content, success=True)
        capture_workflow_run(str(tmp_path), "guardrails", "big-repo", report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        stored_content = rows[0][4]
        assert len(stored_content) < len(huge_content)
        assert len(stored_content) <= 2200  # 2000-char excerpt + small safety margin

    def test_short_content_is_not_truncated(self, tmp_path: Path) -> None:
        """A short, normal-sized content string should survive intact (aside
        from the success= prefix spec.md prescribes) -- bounding logic must
        not also mangle content that never needed truncation."""
        short_content = "Scanned 2 files. 1 violation found: layer_boundaries."
        report = CliReport(title="Architecture Guardrails", content=short_content, success=False)
        capture_workflow_run(str(tmp_path), "guardrails", "small-repo", report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        stored_content = rows[0][4]
        assert short_content in stored_content

    def test_content_reflects_report_success_value(self, tmp_path: Path) -> None:
        """spec.md's content format embeds `success={report.success}` --
        verify captured content distinguishes success vs failure runs, since
        plan.md acceptance criterion 1 explicitly cares about failed calls
        being useful memory too."""
        fail_report = CliReport(title="Decision", content="scan failed: bad path", success=False)
        capture_workflow_run(str(tmp_path), "decide", "bad-arg", fail_report)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 1
        stored_content = rows[0][4]
        assert "False" in stored_content


# ---------------------------------------------------------------------------
# 5. CliCommands behavior unaffected by capture (real fixture repo)
# ---------------------------------------------------------------------------

class TestExistingCommandBehaviorUnaffectedByCapture:
    """Runs against repos/click (bounded, real, already the standard fixture
    per test_commands.py). These assert the same properties test_commands.py
    already asserts pre-task-020 -- if capture wiring changed any of these,
    that's a regression regardless of whether capture itself succeeded."""

    def test_guardrails_success_and_title_unaffected(self) -> None:
        result = CliCommands().guardrails(_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Architecture" in result.title

    def test_plan_success_and_title_unaffected(self) -> None:
        result = CliCommands().plan("add user search endpoint", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Feature Plan" in result.title

    def test_refactor_success_and_title_unaffected(self) -> None:
        result = CliCommands().refactor(_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Refactoring" in result.title

    def test_decide_success_and_title_unaffected(self) -> None:
        result = CliCommands().decide("improve code quality", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success
        assert "Decision" in result.title

    def test_guardrails_bad_path_still_fails_cleanly(self) -> None:
        """Early-failure path (nonexistent path) must still return success=False,
        not be accidentally flipped to True by capture, and must not crash --
        even though spec.md says capture runs on this path too."""
        result = CliCommands().guardrails("/definitely/not/a/real/path/xyz")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_decide_empty_intent_still_fails_cleanly(self) -> None:
        result = CliCommands().decide("")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_guardrails_content_matches_precapture_expectation(self) -> None:
        """Same content assertion test_commands.py makes -- content shape
        must not change due to capture being appended as a side effect."""
        result = CliCommands().guardrails(_FIXTURE_REPO)
        assert (
            "Scanned" in result.content
            or "violation" in result.content.lower()
            or "layer_boundaries" in result.content
        )


# ---------------------------------------------------------------------------
# 6. Two different intents/paths on the SAME repo -> two separate artifacts
# ---------------------------------------------------------------------------

class TestMultipleRunsProduceSeparateArtifacts:
    def test_two_different_commands_same_repo_produce_two_rows(self, tmp_path: Path) -> None:
        report_a = CliReport(title="Architecture Guardrails", content="no violations", success=True)
        capture_workflow_run(str(tmp_path), "guardrails", str(tmp_path), report_a)

        report_b = CliReport(title="Feature Plan", content="plan content", success=True)
        capture_workflow_run(str(tmp_path), "plan", "add caching", report_b)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 2
        titles = {row[3] for row in rows}
        assert len(titles) == 2  # not collapsed into one row

    def test_same_command_different_arguments_same_repo_produce_two_rows(self, tmp_path: Path) -> None:
        """Same command, same repo, different argument/content -> still two
        distinct artifacts (ArtifactStore's content-hash versioning only
        collapses byte-identical content, not merely same-type same-repo)."""
        report_a = CliReport(title="Decision", content="decision content run 1", success=True)
        capture_workflow_run(str(tmp_path), "decide", "improve code quality", report_a)

        report_b = CliReport(title="Decision", content="decision content run 2 -- different", success=True)
        capture_workflow_run(str(tmp_path), "decide", "add caching layer", report_b)

        rows = _workflow_run_rows(str(tmp_path))
        assert len(rows) == 2

    def test_running_all_four_commands_against_click_yields_four_rows(self) -> None:
        """Real-repo verification target from spec.md: run guardrails, plan,
        refactor, decide once each against repos/click and confirm 4 real
        rows land in that repo's .ortho/ortho.db. Uses the full CliCommands
        wiring (not direct capture_workflow_run calls) so this also proves
        BUILDER's 4 call sites are actually wired, not just that
        capture_workflow_run works in isolation.

        NOTE: repos/click's .ortho/ortho.db is a real, persistent file under
        the fixture repo (not a tmp_path). Prior test runs (including
        test_commands.py's own calls to the same fixture, and reruns of this
        very test) may have already populated rows there from earlier
        sessions. We therefore assert '>= 4 new-looking rows in total' is
        too fragile across reruns -- instead assert each of the 4 commands
        is represented by at least one row (a weaker but still meaningful,
        rerun-safe property), rather than asserting an exact total count.
        """
        commands = CliCommands()
        commands.guardrails(_FIXTURE_REPO)
        commands.plan("add user search endpoint", scan_path=_FIXTURE_REPO)
        commands.refactor(_FIXTURE_REPO)
        commands.decide("improve code quality", scan_path=_FIXTURE_REPO)

        rows = _workflow_run_rows(_FIXTURE_REPO)
        import json
        seen_commands = set()
        for row in rows:
            tags = json.loads(row[5]) if row[5] else []
            seen_commands.update(tags)

        assert {"guardrails", "plan", "refactor", "decide"}.issubset(seen_commands)


# ---------------------------------------------------------------------------
# 7. Read-only / nonexistent .ortho parent path (permission/IO edge case)
# ---------------------------------------------------------------------------

class TestPermissionAndIoEdgeCases:
    def test_nonexistent_parent_directory_does_not_crash(self) -> None:
        """scan_root itself doesn't exist (and can't be auto-created) --
        OrthoDatabase's mkdir(parents=True) would need scan_root to be
        creatable; if scan_root's parent chain is bogus/unreachable this
        must still be swallowed."""
        bogus_root = "Z:\\this\\path\\tree\\should\\not\\exist\\anywhere\\12345"
        report = CliReport(title="t", content="valid content", success=True)
        capture_workflow_run(bogus_root, "guardrails", "x", report)
        assert report.success is True

    @pytest.mark.skipif(
        os.name == "nt",
        reason=(
            "True read-only-directory permission-denied simulation is not "
            "reliably cross-platform on Windows/git-bash (chmod bits are "
            "largely ignored by NTFS for the owning user, so this would not "
            "actually reproduce a permission error in CI here). Per the "
            "TEST-DESIGNER brief, this one specific sub-case is documented "
            "and skipped on Windows rather than faked; the corrupt-db and "
            "malformed-content failure-mode tests above are NOT skipped and "
            "cover the same 'capture must swallow the exception' contract "
            "through a reliably-reproducible path instead."
        ),
    )
    def test_readonly_ortho_dir_does_not_crash(self, tmp_path: Path) -> None:
        ortho_dir = tmp_path / ".ortho"
        ortho_dir.mkdir(parents=True)
        os.chmod(ortho_dir, stat.S_IREAD)
        try:
            report = CliReport(title="t", content="valid content", success=True)
            capture_workflow_run(str(tmp_path), "guardrails", "x", report)
            assert report.success is True
        finally:
            os.chmod(ortho_dir, stat.S_IWRITE | stat.S_IREAD)
