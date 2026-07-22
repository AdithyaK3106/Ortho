"""Tests for real, read-only tool execution (tool_executor.py).

Each tool wraps already-tested code (repo_scanner, CliCommands, repo_qa)
-- these tests verify the wrapping (path safety, JSON shape, truncation,
error handling), not the underlying analysis logic itself.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json

import pytest
from executor.tool_executor import (
    TOOL_SCHEMAS,
    execute_tool_call,
    list_files,
    read_file,
)


@pytest.fixture
def small_repo(tmp_path: Path) -> Path:
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "mod.py").write_text(
        "class RateLimiter:\n    def check(self):\n        pass\n", encoding="utf-8"
    )
    return tmp_path


class TestReadFile:
    def test_reads_real_file_content(self, small_repo: Path):
        result = read_file(small_repo, "pkg/mod.py")
        assert "class RateLimiter" in result["content"]
        assert result["truncated"] is False

    def test_nonexistent_file_returns_error_not_raise(self, small_repo: Path):
        result = read_file(small_repo, "pkg/does_not_exist.py")
        assert "error" in result

    def test_path_escaping_repo_root_is_rejected(self, small_repo: Path):
        result = read_file(small_repo, "../../../../etc/passwd")
        assert "error" in result
        assert "escapes" in result["error"].lower()

    def test_large_file_is_truncated(self, tmp_path: Path):
        big_file = tmp_path / "big.py"
        big_file.write_text("x = 1\n" * 20_000, encoding="utf-8")
        result = read_file(tmp_path, "big.py")
        assert result["truncated"] is True
        assert len(result["content"]) < result["total_bytes"]


class TestListFiles:
    def test_lists_real_python_files(self, small_repo: Path):
        result = list_files(small_repo, ".")
        assert "pkg/mod.py" in result["files"]
        assert "pkg/__init__.py" in result["files"]

    def test_nonexistent_dir_returns_error_not_raise(self, small_repo: Path):
        result = list_files(small_repo, "does_not_exist")
        assert "error" in result

    def test_path_escaping_repo_root_is_rejected(self, small_repo: Path):
        result = list_files(small_repo, "../../../..")
        assert "error" in result


class TestExecuteToolCall:
    def test_dispatches_to_real_read_file(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "read_file", json.dumps({"path": "pkg/mod.py"}))
        parsed = json.loads(raw)
        assert "class RateLimiter" in parsed["content"]

    def test_unknown_tool_returns_error_not_raise(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "delete_everything", "{}")
        parsed = json.loads(raw)
        assert "error" in parsed
        assert "Unknown tool" in parsed["error"]

    def test_malformed_arguments_json_returns_error_not_raise(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "read_file", "{not valid json")
        parsed = json.loads(raw)
        assert "error" in parsed

    def test_missing_required_argument_returns_error_not_raise(self, small_repo: Path):
        # read_file requires "path" -- omitting it must not crash the loop
        raw = execute_tool_call(small_repo, "read_file", "{}")
        parsed = json.loads(raw)
        assert "error" in parsed

    def test_search_symbols_finds_real_class(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "search_symbols", json.dumps({"query": "RateLimiter"}))
        parsed = json.loads(raw)
        assert any(m["symbol"] == "RateLimiter" for m in parsed["matches"])

    def test_run_guardrails_returns_real_report_shape(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "run_guardrails", "{}")
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert "violation_count" in parsed

    def test_run_refactor_check_returns_real_report_shape(self, small_repo: Path):
        raw = execute_tool_call(small_repo, "run_refactor_check", "{}")
        parsed = json.loads(raw)
        assert parsed["success"] is True
        assert "content" in parsed


class TestToolSchemas:
    def test_every_schema_is_valid_openai_function_shape(self):
        for schema in TOOL_SCHEMAS:
            assert schema["type"] == "function"
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert schema["function"]["parameters"]["type"] == "object"

    def test_schema_names_match_dispatch_table(self):
        from executor.tool_executor import _DISPATCH

        schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
        assert schema_names == set(_DISPATCH.keys())
