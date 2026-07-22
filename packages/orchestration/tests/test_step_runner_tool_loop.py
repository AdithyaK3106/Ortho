"""Integration test for run_step()'s real tool-execution loop.

Verifies the actual mechanics: a client that returns tool_calls, real
tools executed against a real small repo (tool_executor.py, already
unit-tested in test_tool_executor.py), results fed back, and a second
round that uses them -- not mocked at the tool layer, only the LLM
responses are scripted (there is no live model in a unit test).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json

from executor.step_runner import run_step
from selector.engine import ExecutionStep


class _FakeAgent:
    system_prompt = "You are a helpful coding agent."


class _ScriptedToolCallingClient:
    """Fake LLM client that scripts a real tool-call round-trip: first
    response asks to read a file, second response (after seeing the real
    tool result) gives a final answer referencing what it actually read.
    """

    def __init__(self):
        self.calls_seen = []

    def complete_with_tools(self, system, user, max_tokens, temperature, timeout_seconds, tools, tool_executor):
        # Round 1: model asks to read the file.
        call = {
            "id": "call-1",
            "function": {"name": "read_file", "arguments": json.dumps({"path": "pkg/mod.py"})},
        }
        result_json = tool_executor("read_file", call["function"]["arguments"])
        self.calls_seen.append((call["function"]["name"], result_json))
        parsed = json.loads(result_json)

        # Round 2: model uses the real file content to answer.
        final_content = f"The file has {len(parsed['content'].splitlines())} real lines."
        return SimpleNamespace(
            content=final_content,
            input_tokens=42,
            output_tokens=17,
            tool_calls_made=[{"name": "read_file", "arguments": call["function"]["arguments"]}],
        )


def test_run_step_executes_real_tool_call_and_uses_result(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "mod.py").write_text(
        "def a():\n    pass\n\ndef b():\n    pass\n", encoding="utf-8"
    )

    step = ExecutionStep(step_id="step-1", agent_name="coder", skill_names=[], approval_gate=False)
    client = _ScriptedToolCallingClient()

    result = run_step(
        step=step,
        agent=_FakeAgent(),
        skills=[],
        llm_client=client,
        intent_text="how many lines is pkg/mod.py?",
        repo_root=tmp_path,
    )

    assert result.status == "success"
    assert "5 real lines" in result.agent_output
    assert client.calls_seen[0][0] == "read_file"
    # The tool actually ran against the real file -- not a hallucinated
    # or fabricated result.
    assert "def a" in client.calls_seen[0][1]


def test_run_step_without_repo_root_never_offers_tools():
    """No repo_root -> single-shot complete(), same as before this
    feature existed. A client whose complete_with_tools would raise if
    called proves it wasn't."""

    class _NoToolsExpectedClient:
        def complete(self, system, user, max_tokens, temperature, timeout_seconds):
            return SimpleNamespace(content="plain answer", input_tokens=1, output_tokens=1)

        def complete_with_tools(self, *args, **kwargs):
            raise AssertionError("complete_with_tools should not be called without repo_root")

    step = ExecutionStep(step_id="step-1", agent_name="coder", skill_names=[], approval_gate=False)
    result = run_step(step=step, agent=_FakeAgent(), skills=[], llm_client=_NoToolsExpectedClient())

    assert result.status == "success"
    assert result.agent_output == "plain answer"


def test_run_step_with_repo_root_but_client_lacking_tool_support_falls_back():
    """A client that only implements complete() (e.g. StubLLMClient or an
    older test double) must not break just because repo_root is now
    passed everywhere -- hasattr() gates the tool path."""

    class _LegacyClient:
        def complete(self, system, user, max_tokens, temperature, timeout_seconds):
            return SimpleNamespace(content="legacy answer", input_tokens=1, output_tokens=1)

    step = ExecutionStep(step_id="step-1", agent_name="coder", skill_names=[], approval_gate=False)
    result = run_step(
        step=step, agent=_FakeAgent(), skills=[], llm_client=_LegacyClient(), repo_root=Path(".")
    )

    assert result.status == "success"
    assert result.agent_output == "legacy answer"
