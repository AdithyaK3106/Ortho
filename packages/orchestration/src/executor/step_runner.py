"""Step Runner: Agent invocation, evidence generation per spec.md §5.4."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
from selector.engine import ExecutionStep
from .evidence_collector import Evidence, create_agent_execution_evidence, create_error_evidence


@dataclass
class StepResult:
    """Result of executing a single orchestration step."""
    agent_output: str               # LLM response (raw or parsed)
    evidence: Evidence              # Captured evidence artifact
    status: str                     # success | error
    error_message: Optional[str] = None


def run_step(
    step: ExecutionStep,
    agent: Any,  # AgentManifest
    skills: Optional[list[Any]] = None,  # list[SkillManifest]
    context_package: Any = None,  # ContextPackage from token optimizer
    llm_client: Any = None,  # LLM client
    timeout_seconds: int = 120,
    intent_text: str = "",
    repo_root: Optional[Path] = None,  # enables real tool execution
) -> StepResult:
    """Run a single orchestration step per spec.md §5.4.

    Invokes agent with assembled context and skills. Captures evidence.
    Returns StepResult or raises exception on timeout/error.

    Args:
        step: ExecutionStep to run
        agent: AgentManifest (system prompt, intent triggers)
        skills: Selected SkillManifest objects
        context_package: ContextPackage from token optimizer (stubbed)
        llm_client: LLM client (Claude, etc.)
        timeout_seconds: Execution timeout (default 60s)
        intent_text: The user's original request text (e.g. "refactor
            flask/app.py..."). Without this, the no-context fallback
            message named only the step_id ("Execute step step-1 for
            agent architect") -- a real LLM has no way to know what the
            step is actually for and can only ask for more information.
            Defaults to "" so existing callers/tests are unaffected.
        repo_root: Real filesystem path to the repo being worked on. When
            given and llm_client exposes complete_with_tools, the agent
            gets real read-only tools (read_file, list_files,
            search_symbols, run_guardrails, run_refactor_check) instead of
            a single one-shot completion. None (the default) preserves
            the existing single-shot behavior for callers/tests that
            don't pass it.

    Returns:
        StepResult (agent_output, evidence, status)

    Raises:
        TimeoutError: If execution exceeds timeout_seconds
        LLMError: If LLM call fails
    """
    if skills is None:
        skills = []

    start_time = datetime.utcnow()

    try:
        # Assemble prompts (task-014: token optimizer)
        if context_package:
            # Use real assembler for proper context assembly
            from token_optimizer import assemble_prompt
            system_prompt, user_message = assemble_prompt(
                context_package=context_package,
                step=step,
                agent=agent,
                skills=skills,
                intent_text=intent_text,
            )
        else:
            # Fallback: assemble without context (for tests or when artifact_store unavailable)
            system_prompt = _assemble_system_prompt(agent, skills)
            user_message = _assemble_user_message(step, context_package, intent_text)

        # Call LLM (with timeout). max_tokens=2048 balances real agent-step
        # output (a plan/review is not a novel-length response) against
        # provider latency: a live run against a local FreeLLMAPI router
        # showed max_tokens=8192 reliably routing to slow free-tier
        # providers (observed 80-90s+ per attempt, occasionally exceeding
        # the router's own upstream timeout) where max_tokens=500 completed
        # in ~6s on the same router -- 2048 leaves real headroom for
        # substantive output without provoking the worst-case routing path.
        #
        # With a real repo_root and a client that supports it, give the
        # agent real read-only tools instead of one blind completion --
        # without this, a live run showed agents emitting hallucinated,
        # never-executed tool-call-shaped text ("[TOOL_CALL] ContextRetriever
        # ...") because nothing was actually wired to run what they asked for.
        if repo_root is not None and hasattr(llm_client, "complete_with_tools"):
            from .tool_executor import TOOL_SCHEMAS, execute_tool_call

            def _tool_executor(name: str, arguments_json: str) -> str:
                return execute_tool_call(repo_root, name, arguments_json)

            response = llm_client.complete_with_tools(
                system=system_prompt,
                user=user_message,
                max_tokens=2048,
                temperature=0.7,
                timeout_seconds=timeout_seconds,
                tools=TOOL_SCHEMAS,
                tool_executor=_tool_executor,
            )
        else:
            response = llm_client.complete(
                system=system_prompt,
                user=user_message,
                max_tokens=2048,
                temperature=0.7,
                timeout_seconds=timeout_seconds,
            )

        agent_output = response.content
        input_tokens = response.input_tokens
        output_tokens = response.output_tokens

        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # Create evidence
        evidence = create_agent_execution_evidence(
            step_id=step.step_id,
            step_name=step.agent_name,
            system_prompt=system_prompt,
            user_message=user_message,
            agent_output=agent_output,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
        )

        return StepResult(
            agent_output=agent_output,
            evidence=evidence,
            status="success",
        )

    except TimeoutError as e:
        # Timeout error
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        evidence = create_error_evidence(
            step_id=step.step_id,
            step_name=step.agent_name,
            error_message=f"LLM timeout after {timeout_seconds}s",
            duration_ms=duration_ms,
        )

        return StepResult(
            agent_output="",
            evidence=evidence,
            status="error",
            error_message=str(e),
        )

    except Exception as e:
        # LLM error or parsing error
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        evidence = create_error_evidence(
            step_id=step.step_id,
            step_name=step.agent_name,
            error_message=str(e),
            duration_ms=duration_ms,
        )

        return StepResult(
            agent_output="",
            evidence=evidence,
            status="error",
            error_message=str(e),
        )


def _assemble_system_prompt(agent: Any, skills: list[Any]) -> str:
    """Assemble system prompt from agent.md + skills.md content."""
    # Agent system prompt (from agent.md)
    prompt = agent.system_prompt if hasattr(agent, 'system_prompt') else ""

    # Append skills content
    if skills:
        prompt += "\n\n## Available Skills\n\n"
        for skill in skills:
            prompt += f"### {skill.display_name}\n"
            # Real Skill manifests (task-012) carry the .md body as system_prompt;
            # older test doubles used .content. Accept either.
            body = getattr(skill, "content", None) or getattr(skill, "system_prompt", "")
            prompt += f"{body}\n\n"

    return prompt


def _assemble_user_message(
    step: ExecutionStep, context_package: Any = None, intent_text: str = ""
) -> str:
    """Assemble user message from step context.

    When context_package is None (no artifact store available), includes
    the user's original intent_text if given -- without it, the message
    named only the step_id, so a real LLM had no way to know what the
    step was actually for (observed live: every agent response asked
    "what am I reviewing/building?" when only the step_id was sent).
    For real runs, context_package is provided by the token optimizer
    (task-014).
    """
    if context_package:
        return f"Execute step: {step.step_id}\nContext available for {step.agent_name}"
    else:
        base = f"Execute step {step.step_id} for agent {step.agent_name}"
        if intent_text:
            return f"{base}\n\nOriginal request: {intent_text}"
        return base
