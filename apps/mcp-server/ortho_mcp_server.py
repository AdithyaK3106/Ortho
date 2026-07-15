#!/usr/bin/env python
"""
Ortho MCP Server — exposes Ortho's engineering intelligence to Claude Code.

This server bridges Claude Code's MCP protocol to Ortho's Python CliCommands engine.
No auth, no cloud, no setup — just local engineering intelligence in your chat.

Exposed tools:
  - ortho_guardrails: Check architecture violations
  - ortho_decide: Change impact + strategy
  - ortho_plan: Feature planning
  - ortho_refactor: Refactoring opportunities
  - ortho_memory_search: Query what you've learned

See docs/mcp-server-contract.md for schemas.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add packages to path (same pattern as CLI bridges)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # ortho/
for _p in (
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "cli-commands" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mcp.types as types
from mcp.server import Server
from cli_commands.commands import CliCommands

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Server instance
server = Server("ortho")

# CliCommands engine (initialized once, reused for all tool calls)
_commands = None


def get_commands() -> CliCommands:
    """Lazy-init CliCommands instance."""
    global _commands
    if _commands is None:
        _commands = CliCommands()
    return _commands


# ============================================================================
# Tool Handlers
# ============================================================================


async def handle_guardrails(arguments: dict) -> list[types.TextContent]:
    """ortho_guardrails — Check architecture violations."""
    logger.info(f"ortho_guardrails: {arguments}")

    path = arguments.get("path", ".")
    severity = arguments.get("severity")  # task-023: optional filter

    try:
        commands = get_commands()
        kwargs = {"severity_filter": severity} if severity else {}
        report = commands.guardrails(path, **kwargs)

        output = f"**{report.title}**\n\n{report.content}"
        if not report.success:
            output += f"\n\n**Status:** Failed"

        # If structured violations exist (task-022), include them too
        if report.violations:
            output += f"\n\n**Structured Violations ({len(report.violations)}):**\n"
            for v in report.violations:
                output += f"- [{v.severity}] {v.rule_id}: {v.message}\n"

        return [types.TextContent(type="text", text=output)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def handle_decide(arguments: dict) -> list[types.TextContent]:
    """ortho_decide — Change impact + strategy."""
    logger.info(f"ortho_decide: {arguments}")

    intent = arguments.get("intent", "").strip()
    scan_path = arguments.get("scan_path", ".")
    confidence_threshold = arguments.get("confidence_threshold")  # task-023: optional filter

    if not intent:
        return [types.TextContent(type="text", text="Error: intent must be non-empty")]

    try:
        commands = get_commands()
        kwargs = {"scan_path": scan_path}
        if confidence_threshold is not None:
            kwargs["confidence_threshold"] = confidence_threshold
        report = commands.decide(intent, **kwargs)

        output = f"**{report.title}**\n\n{report.content}"
        if not report.success:
            output += f"\n\n**Status:** Failed"

        # If structured recommendations exist (task-022), include them too
        if report.recommendations:
            output += f"\n\n**Structured Recommendations ({len(report.recommendations)}):**\n"
            for r in report.recommendations:
                output += f"- {r.title} (confidence: {r.confidence:.2f}, effort: {r.effort})\n"

        return [types.TextContent(type="text", text=output)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def handle_plan(arguments: dict) -> list[types.TextContent]:
    """ortho_plan — Feature planning."""
    logger.info(f"ortho_plan: {arguments}")

    intent = arguments.get("intent", "").strip()
    scan_path = arguments.get("scan_path", ".")

    if not intent:
        return [types.TextContent(type="text", text="Error: intent must be non-empty")]

    try:
        commands = get_commands()
        report = commands.plan(intent, scan_path=scan_path)

        output = f"**{report.title}**\n\n{report.content}"
        if not report.success:
            output += f"\n\n**Status:** Failed"

        return [types.TextContent(type="text", text=output)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def handle_refactor(arguments: dict) -> list[types.TextContent]:
    """ortho_refactor — Refactoring opportunities."""
    logger.info(f"ortho_refactor: {arguments}")

    path = arguments.get("path", ".")

    try:
        commands = get_commands()
        report = commands.refactor(path)

        output = f"**{report.title}**\n\n{report.content}"
        if not report.success:
            output += f"\n\n**Status:** Failed"

        return [types.TextContent(type="text", text=output)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def handle_memory_search(arguments: dict) -> list[types.TextContent]:
    """ortho_memory_search — Query what you've learned (task-024)."""
    logger.info(f"ortho_memory_search: {arguments}")

    query = arguments.get("query", "").strip()
    repo_path = arguments.get("repo_path", ".")

    if not query:
        return [types.TextContent(type="text", text="Error: query must be non-empty")]

    try:
        commands = get_commands()
        report = commands.search_memory(repo_path, query)

        output = f"**{report.title}**\n\n{report.content}"

        # If structured results exist (task-024), include them
        if report.search_results:
            output += f"\n\n**Detailed Results ({len(report.search_results)}):**\n"
            for result in report.search_results[:10]:  # First 10 results
                output += f"- {result.title} (relevance: {result.relevance_score:.2f})\n"

        return [types.TextContent(type="text", text=output)]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


# Dispatch table: MCP tool name -> handler
_TOOL_HANDLERS = {
    "ortho_guardrails": handle_guardrails,
    "ortho_decide": handle_decide,
    "ortho_plan": handle_plan,
    "ortho_refactor": handle_refactor,
    "ortho_memory_search": handle_memory_search,
}


@server.call_tool()
async def dispatch_tool_call(name: str, arguments: dict) -> list[types.TextContent]:
    """Single MCP call_tool handler — routes to the right Ortho tool by name.

    The SDK only honors the *last* @server.call_tool()-decorated function
    (each call to the decorator overwrites the single registered handler),
    so all 5 tools must be dispatched from here rather than each carrying
    its own decorator.
    """
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        return [types.TextContent(type="text", text=f"Error: unknown tool '{name}'")]
    return await handler(arguments)


# ============================================================================
# Tool Definitions (MCP Protocol)
# ============================================================================


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available Ortho tools."""
    return [
        types.Tool(
            name="ortho_guardrails",
            description="Check architecture violations: layer boundaries, circular dependencies, module size. Returns real violations found in the scanned repository.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to repository (defaults to current directory)",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["error", "warning"],
                        "description": "Optional: filter to only error or warning violations (task-023)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="ortho_decide",
            description="Analyze change impact + get strategy. Provide a file path to get blast radius, or free text to get guardrails + feature planning combined. Returns recommended decision with alternatives.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "Either a file path (triggers change-impact analysis) or free-text description of intended change. Must be non-empty.",
                    },
                    "scan_path": {
                        "type": "string",
                        "description": "Directory to scan when intent is free text (defaults to current directory). Ignored if intent is a file path.",
                    },
                    "confidence_threshold": {
                        "type": "number",
                        "description": "Optional: minimum confidence 0.0–1.0 to include (task-023). Recommendations below this are filtered.",
                    },
                },
                "required": ["intent"],
            },
        ),
        types.Tool(
            name="ortho_plan",
            description="Plan a feature: intent classification + implementation paths. Returns 3+ distinct options ranked by effort/risk. Input: free-text feature description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "description": "Free-text description of feature to plan (e.g., 'add user authentication'). Must be non-empty.",
                    },
                    "scan_path": {
                        "type": "string",
                        "description": "Directory to scan (defaults to current directory). Recommended to avoid scanning large monorepos.",
                    },
                },
                "required": ["intent"],
            },
        ),
        types.Tool(
            name="ortho_refactor",
            description="Find refactoring opportunities: bloated modules, tight coupling, circular dependencies. Returns real findings with effort/confidence.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to repository (defaults to current directory)",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="ortho_memory_search",
            description="Search your accumulated engineering memory: all workflow_run artifacts from past guardrails/decide/plan/refactor calls. Query by keyword (e.g., 'layer_boundaries', 'high confidence').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword (e.g., 'guardrails', 'refactor', 'layer_boundaries', 'high confidence'). Must be non-empty.",
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Repository path where memory is stored (defaults to current directory)",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


# ============================================================================
# Main
# ============================================================================


async def main():
    """Start the MCP server over stdio (the transport Claude Code uses)."""
    import mcp.server.stdio

    logger.info("Starting Ortho MCP Server...")
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Ortho MCP Server is ready. Connect from Claude Code.")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
