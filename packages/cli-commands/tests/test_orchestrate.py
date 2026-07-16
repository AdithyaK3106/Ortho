"""ortho orchestrate: chains plan+decide+review into one composed report.

Honest scope check: this is NOT the roadmap's literal Planner->Architect->
Builder->Reviewer->Verifier pipeline -- Ortho doesn't write code or run
tests against a real change (that's the LLM's/developer's job). These
tests verify what's actually built: Ortho's own three stages composed into
one report, with no automated approve/merge anywhere in the output.
"""

from pathlib import Path

import pytest

from cli_commands.commands import CliCommands
from cli_commands.types import CliReport

_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO = str(_REPO_ROOT / "repos" / "click")


@pytest.fixture
def commands() -> CliCommands:
    return CliCommands()


class TestOrchestrate:
    def test_real_run_composes_all_three_stages(self, commands: CliCommands) -> None:
        """A real orchestrate() call against a real repo must reference
        all three stages by name, not silently drop one."""
        result = commands.orchestrate("add caching", scan_path=_FIXTURE_REPO)

        assert isinstance(result, CliReport)
        assert result.success
        assert "Stage 1: Plan" in result.content
        assert "Stage 2: Decide" in result.content
        assert "Stage 3: Review" in result.content

    def test_never_auto_approves_or_merges(self, commands: CliCommands) -> None:
        """Ortho advises, it does not act unilaterally -- the roadmap's own
        diagram shows 'Developer approves' as an explicit human step.
        The composed report must not claim to have approved or merged
        anything on the developer's behalf."""
        result = commands.orchestrate("add caching", scan_path=_FIXTURE_REPO)

        lowered = result.content.lower()
        assert "merged" not in lowered
        assert "approved automatically" not in lowered
        assert "auto-approve" not in lowered

    def test_ends_with_explicit_human_next_step(self, commands: CliCommands) -> None:
        """The loop's final step (feedback) must be presented as something
        the developer does, not something orchestrate() does for them."""
        result = commands.orchestrate("add caching", scan_path=_FIXTURE_REPO)

        assert "ortho feedback" in result.content
        assert "does not approve or merge" in result.content

    def test_empty_intent_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.orchestrate("", scan_path=_FIXTURE_REPO)
        assert isinstance(result, CliReport)
        assert result.success is False
        assert "empty" in result.content.lower()

    def test_whitespace_only_intent_fails_cleanly(self, commands: CliCommands) -> None:
        result = commands.orchestrate("   ", scan_path=_FIXTURE_REPO)
        assert result.success is False

    def test_nonexistent_scan_path_fails_without_crashing(self, commands: CliCommands) -> None:
        """A stage that can't scan the target must not crash the whole
        chain -- each stage's own FileNotFoundError handling should
        surface, not raise out of orchestrate()."""
        result = commands.orchestrate("add caching", scan_path="/definitely/not/a/real/path/xyz")
        assert isinstance(result, CliReport)
        assert result.success is False

    def test_nonexistent_scan_path_fails_fast_not_three_times(self, commands: CliCommands) -> None:
        """A totally invalid target should be rejected once, up front --
        not run through all three stages just to report the identical
        'path does not exist' error three times, followed by human-next-
        step guidance that makes no sense when nothing actually ran."""
        result = commands.orchestrate("add caching", scan_path="/definitely/not/a/real/path/xyz")
        assert result.content.count("does not exist") == 1
        assert "Next step" not in result.content

    def test_stage_with_nothing_to_report_does_not_break_chain(self, commands: CliCommands) -> None:
        """click is a clean repo (no guardrails violations) -- review()
        finding nothing must not prevent plan/decide from still appearing
        in the composed report."""
        result = commands.orchestrate("improve code quality", scan_path=_FIXTURE_REPO)

        assert result.success
        assert "Stage 1: Plan" in result.content
        assert "Stage 2: Decide" in result.content
        assert "Stage 3: Review" in result.content

    def test_does_not_double_capture_workflow_memory(self, commands: CliCommands) -> None:
        """Each of plan/decide/review already captures its own
        workflow_run artifact -- orchestrate() composing them must not
        also write a fourth, duplicate artifact for the same work."""
        from cli_commands.repo_scanner import scan_repository
        from storage import OrthoDatabase
        from context_hub.store import ArtifactStore
        from repo_intelligence.index_store import mint_repo_id

        commands.orchestrate("add caching", scan_path=_FIXTURE_REPO)

        repo_path_obj = Path(_FIXTURE_REPO).resolve()
        db = OrthoDatabase(repo_path_obj)
        store = ArtifactStore(db, repo_id=mint_repo_id(repo_path_obj))
        results = store.search("orchestrate", artifact_type="workflow_run", limit=50)

        assert results == []
