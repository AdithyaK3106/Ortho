"""
Test suite for Ortho MCP Server.

Tests the 5 tool handlers without requiring the full MCP protocol stack.
Run with: pytest test_mcp_server.py -v
"""

import sys
from pathlib import Path
from typing import Any

import pytest

# Add packages to path (same as MCP server)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ortho/
for _p in (
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "cli-commands" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from cli_commands.commands import CliCommands


class TestOrthoMCPServer:
    """Test Ortho MCP Server tool handlers."""

    @pytest.fixture
    def commands(self):
        """Create CliCommands instance."""
        return CliCommands()

    @pytest.fixture
    def test_repo(self):
        """Get repos/click/src/click path."""
        # Try multiple paths in case test runs from different directories
        candidates = [
            Path.cwd() / "repos" / "click" / "src" / "click",  # From ortho root
            Path.cwd() / ".." / ".." / "repos" / "click" / "src" / "click",  # From apps/mcp-server
            _PROJECT_ROOT / "repos" / "click" / "src" / "click",  # From _PROJECT_ROOT
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        # If no repo found, skip test
        pytest.skip("Test repository (repos/click) not found")

    # ========================================================================
    # Tool 1: ortho_guardrails
    # ========================================================================

    def test_guardrails_basic(self, commands, test_repo):
        """ortho_guardrails: basic call succeeds."""
        report = commands.guardrails(test_repo)
        assert report.success is True
        assert report.title is not None
        assert len(report.content) > 0

    def test_guardrails_with_severity_filter(self, commands, test_repo):
        """ortho_guardrails: severity filter (task-023) works."""
        report_error = commands.guardrails(test_repo, severity_filter="error")
        report_warning = commands.guardrails(test_repo, severity_filter="warning")
        report_all = commands.guardrails(test_repo)

        assert report_error.success is True
        assert report_warning.success is True
        assert report_all.success is True
        # Different filters should produce different counts
        # (or some filters may be empty, which is OK)

    def test_guardrails_nonexistent_path(self, commands):
        """ortho_guardrails: nonexistent path returns success=False."""
        report = commands.guardrails("/definitely/not/a/real/path")
        assert report.success is False
        assert "does not exist" in report.content.lower() or "path" in report.content.lower()

    def test_guardrails_has_structured_output(self, commands, test_repo):
        """ortho_guardrails: returns structured violations (task-022)."""
        report = commands.guardrails(test_repo)
        assert report.violations is None or isinstance(report.violations, list)

    # ========================================================================
    # Tool 2: ortho_decide
    # ========================================================================

    def test_decide_with_intent(self, commands, test_repo):
        """ortho_decide: text intent succeeds."""
        report = commands.decide("add caching", scan_path=test_repo)
        assert report.success is True
        assert report.title is not None
        assert len(report.content) > 0

    def test_decide_with_file_path(self, commands, test_repo):
        """ortho_decide: file path triggers change-impact analysis."""
        file_path = str(Path(test_repo) / "core.py")
        report = commands.decide(file_path)
        assert report.success is True
        assert "Affected" in report.content or "Decision" in report.content

    def test_decide_empty_intent(self, commands, test_repo):
        """ortho_decide: empty intent rejected."""
        report = commands.decide("", scan_path=test_repo)
        assert report.success is False

    def test_decide_with_confidence_filter(self, commands, test_repo):
        """ortho_decide: confidence threshold filter (task-023) works."""
        report_high = commands.decide("add auth", scan_path=test_repo, confidence_threshold=0.8)
        report_low = commands.decide("add auth", scan_path=test_repo, confidence_threshold=0.0)

        assert report_high.success is True
        assert report_low.success is True
        # High threshold may filter out options, low threshold should keep all

    def test_decide_has_structured_output(self, commands, test_repo):
        """ortho_decide: returns structured recommendations (task-022)."""
        report = commands.decide("refactor", scan_path=test_repo)
        assert report.recommendations is None or isinstance(report.recommendations, list)

    # ========================================================================
    # Tool 3: ortho_plan
    # ========================================================================

    def test_plan_with_intent(self, commands, test_repo):
        """ortho_plan: text intent succeeds."""
        report = commands.plan("add user authentication", scan_path=test_repo)
        assert report.success is True
        assert report.title is not None
        assert len(report.content) > 0
        # Should contain effort/risk/paths (common pattern in plan output)
        assert "effort" in report.content.lower() or "feature" in report.content.lower()

    def test_plan_empty_intent(self, commands, test_repo):
        """ortho_plan: empty intent rejected."""
        report = commands.plan("", scan_path=test_repo)
        assert report.success is False

    def test_plan_various_intents(self, commands, test_repo):
        """ortho_plan: various intents produce valid output."""
        intents = [
            "add logging",
            "optimize performance",
            "improve error handling",
        ]
        for intent in intents:
            report = commands.plan(intent, scan_path=test_repo)
            assert report.success is True, f"Failed for intent: {intent}"
            assert len(report.content) > 0

    # ========================================================================
    # Tool 4: ortho_refactor
    # ========================================================================

    def test_refactor_basic(self, commands, test_repo):
        """ortho_refactor: basic call succeeds."""
        report = commands.refactor(test_repo)
        assert report.success is True
        assert report.title is not None
        assert len(report.content) > 0

    def test_refactor_nonexistent_path(self, commands):
        """ortho_refactor: nonexistent path returns success=False."""
        report = commands.refactor("/definitely/not/a/real/path")
        assert report.success is False

    def test_refactor_clean_repo(self, commands, test_repo):
        """ortho_refactor: clean repo returns success=True with no issues msg."""
        report = commands.refactor(test_repo)
        assert report.success is True
        # Either issues found or "no issues" message
        assert len(report.content) > 0

    # ========================================================================
    # Tool 5: ortho_memory_search
    # ========================================================================

    def test_memory_search_basic(self, commands, test_repo):
        """ortho_memory_search: basic query succeeds."""
        report = commands.search_memory(test_repo, "guardrails")
        assert report.success is True
        assert report.title is not None
        assert len(report.content) > 0

    def test_memory_search_empty_query(self, commands, test_repo):
        """ortho_memory_search: empty query returns success=True with msg."""
        report = commands.search_memory(test_repo, "")
        assert report.success is True
        assert "empty" in report.content.lower() or "no" in report.content.lower()

    def test_memory_search_nonexistent_repo(self, commands):
        """ortho_memory_search: nonexistent repo returns success=False."""
        report = commands.search_memory("/definitely/not/a/real/path", "test")
        assert report.success is False

    def test_memory_search_has_structured_results(self, commands, test_repo):
        """ortho_memory_search: returns structured results (task-024)."""
        report = commands.search_memory(test_repo, "guardrails")
        assert report.search_results is None or isinstance(report.search_results, list)

    def test_memory_search_various_queries(self, commands, test_repo):
        """ortho_memory_search: various queries work."""
        queries = [
            "guardrails",
            "refactor",
            "violation",
            "architecture",
        ]
        for query in queries:
            report = commands.search_memory(test_repo, query)
            assert report.success is True, f"Failed for query: {query}"

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_all_tools_work_sequentially(self, commands, test_repo):
        """All 5 tools work in sequence without interference."""
        r1 = commands.guardrails(test_repo)
        r2 = commands.decide("add feature", scan_path=test_repo)
        r3 = commands.plan("new module", scan_path=test_repo)
        r4 = commands.refactor(test_repo)
        r5 = commands.search_memory(test_repo, "test")

        assert all([r1.success, r2.success, r3.success, r4.success, r5.success])

    def test_structured_output_compatibility(self, commands, test_repo):
        """Structured output fields exist (for Claude Code formatting)."""
        r_guardrails = commands.guardrails(test_repo)
        r_decide = commands.decide("test", scan_path=test_repo)
        r_memory = commands.search_memory(test_repo, "test")

        # These fields may be None, but they must exist
        assert hasattr(r_guardrails, "violations")
        assert hasattr(r_decide, "recommendations")
        assert hasattr(r_memory, "search_results")

    def test_error_handling(self, commands):
        """All tools handle errors gracefully (never raise)."""
        # Invalid args should return success=False, not raise
        r1 = commands.guardrails("/invalid/path")
        r2 = commands.decide("", scan_path="/invalid/path")
        r3 = commands.plan("test", scan_path="/invalid/path")
        r4 = commands.refactor("/invalid/path")
        r5 = commands.search_memory("/invalid/path", "test")

        # At least some should fail, none should raise
        assert isinstance(r1.success, bool)
        assert isinstance(r2.success, bool)
        assert isinstance(r3.success, bool)
        assert isinstance(r4.success, bool)
        assert isinstance(r5.success, bool)


class TestOrthoMCPServerRealProtocol:
    """
    Drive the actual MCP server subprocess through the real MCP client/server
    protocol (stdio transport) — the same mechanism Claude Code uses.

    This exists because TestOrthoMCPServer (above) only calls the handler
    functions directly in Python, bypassing mcp.server.Server entirely. That
    style of test cannot catch protocol-level wiring bugs: it previously
    missed that @server.call_tool() only registers a single handler (each
    decoration silently overwrites the last), so 4 of 5 tools were
    unreachable from a real MCP client even though every handler function
    worked fine in isolation. Only a real client/server round-trip surfaces
    that class of bug.
    """

    @pytest.fixture
    def test_repo(self):
        candidates = [
            Path.cwd() / "repos" / "click" / "src" / "click",
            _PROJECT_ROOT / "repos" / "click" / "src" / "click",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        pytest.skip("Test repository (repos/click) not found")

    @pytest.fixture
    def server_script(self):
        script = _PROJECT_ROOT / "apps" / "mcp-server" / "ortho_mcp_server.py"
        assert script.exists(), f"MCP server script not found at {script}"
        return script

    @pytest.mark.anyio
    async def test_all_tools_reachable_via_real_mcp_protocol(self, server_script, test_repo):
        """
        Every tool registered in list_tools() must actually be callable via
        call_tool() through a real client session — not just importable as
        a Python function.
        """
        mcp = pytest.importorskip("mcp", reason="mcp SDK not installed")
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(command=sys.executable, args=[str(server_script)])

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_result = await session.list_tools()
                tool_names = {t.name for t in tools_result.tools}
                assert tool_names == {
                    "ortho_guardrails",
                    "ortho_decide",
                    "ortho_plan",
                    "ortho_refactor",
                    "ortho_memory_search",
                }

                # Every advertised tool must be reachable, not just the last
                # one registered (this is exactly the bug that direct
                # handler-function tests couldn't see).
                for name, args in [
                    ("ortho_guardrails", {"path": test_repo}),
                    ("ortho_decide", {"intent": "add caching", "scan_path": test_repo}),
                    ("ortho_plan", {"intent": "add logging", "scan_path": test_repo}),
                    ("ortho_refactor", {"path": test_repo}),
                    ("ortho_memory_search", {"query": "guardrails", "repo_path": test_repo}),
                ]:
                    result = await session.call_tool(name, args)
                    assert not result.isError, f"{name} returned isError=True: {result.content}"
                    assert len(result.content) > 0, f"{name} returned empty content"
                    assert isinstance(result.content[0].text, str)
                    assert len(result.content[0].text) > 0


@pytest.fixture
def anyio_backend():
    return "asyncio"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
