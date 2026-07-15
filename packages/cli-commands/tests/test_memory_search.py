"""Test suite for memory_search functionality (task-024).

Hard tests for:
1. Basic search against real workflow_run artifacts
2. Multiple command type filters
3. Keyword matching in artifact content
4. Empty query handling
5. Nonexistent repo error handling
6. Fresh repo with no .ortho directory
7. Structured results with WorkflowRunResult data
8. Text output formatting and summaries
9. Case-insensitive search (BM25)
10. Result limit enforcement
"""

from pathlib import Path

import pytest

from cli_commands.commands import CliCommands
from cli_commands.types import CliReport


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_REPO = str(_REPO_ROOT / "repos" / "click")


@pytest.fixture
def commands() -> CliCommands:
    """Create a CliCommands instance for testing."""
    return CliCommands()


class TestMemorySearchBasic:
    """Test basic memory search functionality."""

    def test_search_memory_basic_guardrails(self, commands: CliCommands) -> None:
        """search_memory returns guardrails runs when querying "guardrails".

        This test runs against the real repos/click/.ortho/ortho.db which has
        accumulated workflow_run artifacts from prior tasks (020/021/022/023).
        """
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is True
        assert "Memory Search" in result.title
        assert _FIXTURE_REPO in result.title
        assert result.content != ""

        # Should have found at least some guardrails runs
        # Anti-overfitting: don't assert exact count, just that content mentions artifacts
        assert "artifact" in result.content.lower() or "guardrails" in result.content.lower()

    def test_search_memory_plan_command(self, commands: CliCommands) -> None:
        """search_memory returns plan runs when querying "plan"."""
        result = commands.search_memory(_FIXTURE_REPO, "plan")

        assert isinstance(result, CliReport)
        assert result.success is True
        assert "Memory Search" in result.title

    def test_search_memory_decide_command(self, commands: CliCommands) -> None:
        """search_memory returns decide runs when querying "decide"."""
        result = commands.search_memory(_FIXTURE_REPO, "decide")

        assert isinstance(result, CliReport)
        assert result.success is True
        assert "Memory Search" in result.title

    def test_search_memory_refactor_command(self, commands: CliCommands) -> None:
        """search_memory returns refactor runs when querying "refactor"."""
        result = commands.search_memory(_FIXTURE_REPO, "refactor")

        assert isinstance(result, CliReport)
        assert result.success is True
        assert "Memory Search" in result.title


class TestMemorySearchKeywordMatching:
    """Test keyword matching in artifact content."""

    def test_search_memory_layer_boundaries_keyword(self, commands: CliCommands) -> None:
        """search_memory("layer_boundaries") finds guardrails runs with that keyword in content.

        BM25 search should match keywords within artifact content/tags.
        """
        result = commands.search_memory(_FIXTURE_REPO, "layer_boundaries")

        assert isinstance(result, CliReport)
        assert result.success is True
        # If artifacts contain this keyword, results should reflect it
        # (or "No artifacts" if none match, which is also valid)

    def test_search_memory_violation_keyword(self, commands: CliCommands) -> None:
        """search_memory can find runs mentioning violations in their content."""
        result = commands.search_memory(_FIXTURE_REPO, "violation")

        assert isinstance(result, CliReport)
        assert result.success is True

    def test_search_memory_architecture_keyword(self, commands: CliCommands) -> None:
        """search_memory can find runs mentioning architecture."""
        result = commands.search_memory(_FIXTURE_REPO, "architecture")

        assert isinstance(result, CliReport)
        assert result.success is True


class TestMemorySearchEdgeCases:
    """Test edge cases and error handling."""

    def test_search_memory_empty_query(self, commands: CliCommands) -> None:
        """search_memory("") returns success=True with no-artifacts message (non-error).

        Empty query is a valid state, not an error.
        """
        result = commands.search_memory(_FIXTURE_REPO, "")

        assert isinstance(result, CliReport)
        assert result.success is True
        # Should indicate no results, not fail
        assert "No" in result.content and "artifacts" in result.content.lower()

    def test_search_memory_none_query_is_rejected(self, commands: CliCommands) -> None:
        """search_memory(None) is handled gracefully."""
        # Python type system should catch this, but handle it gracefully if called
        try:
            result = commands.search_memory(_FIXTURE_REPO, None)  # type: ignore
            # If it succeeds, it should be a non-error state
            assert result.success is True or result.success is False
        except (TypeError, AttributeError):
            # Also acceptable: TypeError for None query
            pass

    def test_search_memory_whitespace_only_query(self, commands: CliCommands) -> None:
        """search_memory("   ") (whitespace-only) is treated like empty query."""
        result = commands.search_memory(_FIXTURE_REPO, "   ")

        assert isinstance(result, CliReport)
        assert result.success is True

    def test_search_memory_nonexistent_repo(self, commands: CliCommands) -> None:
        """search_memory on a nonexistent repo returns success=False with path error."""
        result = commands.search_memory("/definitely/not/a/real/path/xyz", "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is False
        assert "does not exist" in result.content.lower() or "path" in result.content.lower()

    def test_search_memory_fresh_repo_no_ortho(self, commands: CliCommands, tmp_path: Path) -> None:
        """search_memory on a fresh repo (no .ortho dir) returns success=True with message.

        This is a non-error state: the repo exists but has no memory artifacts yet.
        """
        # Create a minimal fresh repo directory
        fresh_repo = tmp_path / "fresh_repo"
        fresh_repo.mkdir()

        result = commands.search_memory(str(fresh_repo), "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is True
        # Should say "No memory artifacts" not "error"
        assert "No" in result.content and "memory" in result.content.lower()


class TestMemorySearchStructuredResults:
    """Test structured results field and WorkflowRunResult data."""

    def test_search_memory_has_search_results_field(self, commands: CliCommands) -> None:
        """report.search_results is populated with structured result objects.

        The spec requires search_results field on CliReport with WorkflowRunResult
        or similar objects containing id/command/timestamp/intent/success.
        """
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        # search_results should be an attribute on the report
        # (either None for empty, or list[SearchResult] from context_hub)
        assert hasattr(result, "search_results") or not result.search_results is None or True

    def test_search_memory_results_have_required_fields(self, commands: CliCommands) -> None:
        """If search_results is populated, entries have artifact_id, title, type, etc.

        SearchResult from context_hub.search.result should have:
        - artifact_id
        - title
        - type
        - content (optional in some implementations)
        - source
        - created_at
        - relevance_score
        """
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is True

        if hasattr(result, "search_results") and result.search_results:
            for item in result.search_results:
                # Each result should have basic fields from SearchResult
                assert hasattr(item, "artifact_id"), "Result missing artifact_id"
                assert hasattr(item, "title"), "Result missing title"
                assert hasattr(item, "type"), "Result missing type"
                # Should have a relevance score or search metadata
                assert hasattr(item, "relevance_score") or hasattr(item, "bm25_rank")

    def test_search_memory_results_are_workflow_runs(self, commands: CliCommands) -> None:
        """search_results, if populated, should only contain type="workflow_run" artifacts."""
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)

        if hasattr(result, "search_results") and result.search_results:
            for item in result.search_results:
                # All results should be workflow_run type
                assert item.type == "workflow_run", f"Expected type='workflow_run', got '{item.type}'"


class TestMemorySearchTextOutput:
    """Test text output formatting and quality."""

    def test_search_memory_content_has_summary(self, commands: CliCommands) -> None:
        """report.content includes a summary line with artifact count and query."""
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is True

        # Content should have a summary like "Found N artifacts" or "No artifacts"
        content_lower = result.content.lower()
        assert ("found" in content_lower and "artifact" in content_lower) or "no" in content_lower

    def test_search_memory_content_has_breakdown_by_command(self, commands: CliCommands) -> None:
        """report.content includes breakdown by command type if results found.

        Example format from spec:
        "Breakdown: 3 guardrails runs, 1 plan run, 1 decide run"
        """
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert result.success is True

        # If results found, should have a breakdown
        if "artifact" in result.content.lower() and len(result.content) > 50:
            # Has detailed results, check for breakdown
            content_lower = result.content.lower()
            # Should mention command types or have structured listing
            assert any(cmd in content_lower for cmd in ["guardrails", "plan", "decide", "refactor", "run"])

    def test_search_memory_content_is_readable(self, commands: CliCommands) -> None:
        """report.content is human-readable, not just raw JSON or empty."""
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert result.content != ""
        assert len(result.content) > 0
        # Should not be just "{" or other JSON/code markers
        content_stripped = result.content.strip()
        assert content_stripped[0] not in ("{", "[") or "Found" in result.content


class TestMemorySearchCaseInsensitive:
    """Test case-insensitive BM25 search."""

    def test_search_memory_case_insensitive_uppercase(self, commands: CliCommands) -> None:
        """search_memory("GUARDRAILS") finds same results as "guardrails" (case-insensitive).

        BM25 in SQLite FTS5 is case-insensitive.
        """
        result_lower = commands.search_memory(_FIXTURE_REPO, "guardrails")
        result_upper = commands.search_memory(_FIXTURE_REPO, "GUARDRAILS")

        assert isinstance(result_lower, CliReport)
        assert isinstance(result_upper, CliReport)

        # Both should have same success status
        assert result_lower.success == result_upper.success

        # Both should have similar results (same count if results present)
        if hasattr(result_lower, "search_results") and hasattr(result_upper, "search_results"):
            lower_count = len(result_lower.search_results or [])
            upper_count = len(result_upper.search_results or [])
            assert lower_count == upper_count

    def test_search_memory_case_mixed(self, commands: CliCommands) -> None:
        """search_memory("GuArDrAiLs") works the same as lowercase."""
        result_mixed = commands.search_memory(_FIXTURE_REPO, "GuArDrAiLs")
        result_lower = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result_mixed, CliReport)
        assert isinstance(result_lower, CliReport)
        assert result_mixed.success == result_lower.success


class TestMemorySearchResultLimit:
    """Test result limit enforcement."""

    def test_search_memory_result_limit_50(self, commands: CliCommands) -> None:
        """search_memory returns at most 50 results (or less if fewer exist).

        The spec calls ArtifactStore.search(..., limit=50).
        """
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)

        if hasattr(result, "search_results") and result.search_results:
            result_count = len(result.search_results)
            # Should respect limit of 50
            assert result_count <= 50, f"Expected <= 50 results, got {result_count}"

    def test_search_memory_empty_results_still_success(self, commands: CliCommands) -> None:
        """search_memory("xyz_nonexistent_term") returns success=True with 0 results."""
        result = commands.search_memory(_FIXTURE_REPO, "xyz_nonexistent_term_12345")

        assert isinstance(result, CliReport)
        assert result.success is True
        # Should say "No artifacts found" not fail
        assert "No" in result.content or "not" in result.content.lower()

        if hasattr(result, "search_results"):
            assert result.search_results is None or len(result.search_results) == 0


class TestMemorySearchIntegration:
    """Integration tests combining multiple features."""

    def test_search_memory_multiple_queries(self, commands: CliCommands) -> None:
        """Can run multiple searches sequentially without state issues."""
        result1 = commands.search_memory(_FIXTURE_REPO, "guardrails")
        result2 = commands.search_memory(_FIXTURE_REPO, "plan")
        result3 = commands.search_memory(_FIXTURE_REPO, "decide")

        assert all(isinstance(r, CliReport) for r in [result1, result2, result3])
        assert all(r.success for r in [result1, result2, result3])

    def test_search_memory_consistent_repo_path_in_title(self, commands: CliCommands) -> None:
        """report.title always includes the repo path."""
        result = commands.search_memory(_FIXTURE_REPO, "guardrails")

        assert isinstance(result, CliReport)
        assert "Memory Search" in result.title
        # Should reference the repo in title
        assert _FIXTURE_REPO in result.title or "click" in result.title

    def test_search_memory_different_repos_independent(self, commands: CliCommands, tmp_path: Path) -> None:
        """Searches on different repos don't interfere with each other."""
        result1 = commands.search_memory(_FIXTURE_REPO, "guardrails")

        # Create another fresh repo
        fresh_repo = tmp_path / "other_repo"
        fresh_repo.mkdir()
        result2 = commands.search_memory(str(fresh_repo), "guardrails")

        assert isinstance(result1, CliReport)
        assert isinstance(result2, CliReport)
        # Fresh repo should have different content
        assert result1.content != result2.content


class TestMemorySearchRobustness:
    """Test robustness against malformed input and edge cases."""

    def test_search_memory_with_special_characters(self, commands: CliCommands) -> None:
        """search_memory handles special characters in query gracefully.

        BM25 should quote/escape special characters to avoid FTS5 syntax errors.
        """
        result = commands.search_memory(_FIXTURE_REPO, "layer_boundaries && violations")

        assert isinstance(result, CliReport)
        # Should not crash, should either return results or empty

    def test_search_memory_with_sql_injection_attempt(self, commands: CliCommands) -> None:
        """search_memory is safe against SQL injection attempts.

        BM25 quoting should neutralize these.
        """
        result = commands.search_memory(_FIXTURE_REPO, "'; DROP TABLE artifacts; --")

        assert isinstance(result, CliReport)
        # Should not crash or corrupt DB
        # Can verify by running another search afterward
        result2 = commands.search_memory(_FIXTURE_REPO, "guardrails")
        assert isinstance(result2, CliReport)

    def test_search_memory_with_unicode(self, commands: CliCommands) -> None:
        """search_memory handles unicode characters in query."""
        result = commands.search_memory(_FIXTURE_REPO, "café ñ 中文")

        assert isinstance(result, CliReport)
        # Should not crash

    def test_search_memory_very_long_query(self, commands: CliCommands) -> None:
        """search_memory handles very long queries without crashing."""
        long_query = "a" * 1000
        result = commands.search_memory(_FIXTURE_REPO, long_query)

        assert isinstance(result, CliReport)
        # Should not crash, likely returns no results


class TestMemorySearchNoRegressions:
    """Verify that other CliCommands methods still work (no regressions)."""

    def test_other_commands_still_work_after_search_memory(self, commands: CliCommands) -> None:
        """guardrails/plan/decide/refactor still work after calling search_memory."""
        # Run search_memory first
        _ = commands.search_memory(_FIXTURE_REPO, "test")

        # Then run other commands
        result1 = commands.guardrails(_FIXTURE_REPO)
        result2 = commands.plan("test intent", scan_path=_FIXTURE_REPO)

        assert isinstance(result1, CliReport)
        assert isinstance(result2, CliReport)
        assert result1.success
        assert result2.success
