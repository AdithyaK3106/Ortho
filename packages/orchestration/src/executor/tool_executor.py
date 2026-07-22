"""Real, read-only tool execution for orchestration agent steps.

Every tool here is a thin wrapper around code that already works and is
already tested elsewhere in this codebase (repo_scanner.scan_repository,
CliCommands.guardrails/.refactor, repo_qa.find_existing_symbols) -- this
module adds no new analysis logic, only the OpenAI-style function-calling
schema and the dispatch that turns a model's tool_call into a real call
against that code, with the result serialized back for the model to read.

Read-only by design: no tool here can modify a file. A real write_file
tool is a distinct, larger, and riskier feature (agents modifying real
source) that is deliberately out of scope until this read-only loop has
been verified end-to-end.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MAX_FILE_BYTES = 40_000  # a tool result this large would dominate the next
# turn's token budget for no real benefit -- an agent asking for a whole
# 1600-line file doesn't need bytes 40,000 through 60,000 to plan a split.
_MAX_LIST_ENTRIES = 200
_MAX_SYMBOL_MATCHES = 20


def _resolve_within_repo(repo_root: Path, rel_path: str) -> Path:
    """Resolve rel_path against repo_root, refusing any path that escapes it.

    Agents are LLM output, not a trusted caller -- "../../etc/passwd" or an
    absolute path outside the repo must be rejected before touching the
    filesystem, not merely discouraged in a tool description.
    """
    candidate = (repo_root / rel_path).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        raise ValueError(f"Path escapes repository root: {rel_path}")
    return candidate


def read_file(repo_root: Path, path: str) -> dict[str, Any]:
    """Read a real file's content, truncated if large."""
    try:
        target = _resolve_within_repo(repo_root, path)
    except ValueError as e:
        return {"error": str(e)}
    if not target.is_file():
        return {"error": f"Not a file: {path}"}
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": f"Could not read {path}: {e}"}

    truncated = len(content) > _MAX_FILE_BYTES
    return {
        "path": path,
        "content": content[:_MAX_FILE_BYTES],
        "truncated": truncated,
        "total_bytes": len(content),
    }


def list_files(repo_root: Path, subpath: str = ".") -> dict[str, Any]:
    """List Python files under subpath (relative to repo root)."""
    try:
        target = _resolve_within_repo(repo_root, subpath)
    except ValueError as e:
        return {"error": str(e)}
    if not target.is_dir():
        return {"error": f"Not a directory: {subpath}"}

    files = sorted(
        str(p.relative_to(repo_root)).replace("\\", "/")
        for p in target.rglob("*.py")
        if not any(part.startswith(".") for part in p.parts)
    )
    truncated = len(files) > _MAX_LIST_ENTRIES
    return {
        "files": files[:_MAX_LIST_ENTRIES],
        "truncated": truncated,
        "total_count": len(files),
    }


def search_symbols(repo_root: Path, query: str) -> dict[str, Any]:
    """Find real symbols (classes/functions) whose name contains query.

    Reuses repo_qa.find_existing_symbols' exact keyword-fallback and
    substring-match discipline (same one ortho_ask/ortho_plan use) rather
    than a second, different search implementation.
    """
    from cli_commands.repo_qa import find_existing_symbols
    from cli_commands.repo_scanner import scan_repository

    scan = scan_repository(str(repo_root))
    matches = find_existing_symbols(query, scan.file_to_module, scan.symbols_by_file, limit=_MAX_SYMBOL_MATCHES)
    return {
        "matches": [
            {"module": m.module, "symbol": m.symbol_name, "matched_keyword": m.keyword}
            for m in matches
        ]
    }


def run_guardrails(repo_root: Path) -> dict[str, Any]:
    """Real architecture-violation check (layer boundaries, cycles, module size)."""
    from cli_commands.commands import CliCommands

    report = CliCommands().guardrails(str(repo_root))
    return {
        "success": report.success,
        "violation_count": len(report.violations or []),
        "violations": [
            {"rule_id": v.rule_id, "severity": v.severity, "message": v.message}
            for v in (report.violations or [])[:_MAX_SYMBOL_MATCHES]
        ],
    }


def run_refactor_check(repo_root: Path) -> dict[str, Any]:
    """Real refactoring findings (bloat, tight coupling, circular deps)."""
    from cli_commands.commands import CliCommands

    report = CliCommands().refactor(str(repo_root))
    return {"success": report.success, "content": report.content}


TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a real file's content from the repository, by path relative to the repo root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "File path relative to the repo root, e.g. 'src/flask/app.py'"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List Python files under a directory (relative to the repo root).",
            "parameters": {
                "type": "object",
                "properties": {"subpath": {"type": "string", "description": "Directory path relative to the repo root, e.g. 'src/flask'. Defaults to the repo root."}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_symbols",
            "description": "Find real classes/functions in the repo whose name matches a keyword.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Keyword to search for, e.g. 'rate_limit' or 'AppContext'"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_guardrails",
            "description": "Run the real architecture-violation check (layer boundaries, circular dependencies, oversized modules) on this repository.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_refactor_check",
            "description": "Run the real refactoring-opportunity check (bloat, tight coupling, circular dependencies) on this repository.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_DISPATCH = {
    "read_file": lambda repo_root, args: read_file(repo_root, args["path"]),
    "list_files": lambda repo_root, args: list_files(repo_root, args.get("subpath", ".")),
    "search_symbols": lambda repo_root, args: search_symbols(repo_root, args["query"]),
    "run_guardrails": lambda repo_root, args: run_guardrails(repo_root),
    "run_refactor_check": lambda repo_root, args: run_refactor_check(repo_root),
}


def execute_tool_call(repo_root: Path, name: str, arguments_json: str) -> str:
    """Execute one tool call and return its result as a JSON string.

    Never raises: a malformed arguments payload, an unknown tool name, or
    a real execution error all become a {"error": ...} JSON result fed
    back to the model, matching run_step()'s existing discipline of
    turning failures into real evidence rather than crashing the workflow.
    """
    handler = _DISPATCH.get(name)
    if handler is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        arguments = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid tool arguments JSON: {e}"})

    try:
        result = handler(repo_root, arguments)
    except Exception as e:
        result = {"error": f"Tool '{name}' failed: {e}"}

    return json.dumps(result)
