"""Step Runner: Agent invocation, evidence generation per spec.md §5.4."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from packages.orchestration.src.selector.engine import ExecutionStep
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
    agent: any,  # AgentManifest
    skills: list = None,  # list[SkillManifest]
    context_package: any = None,  # ContextPackage (stubbed; token optimizer task-014)
    llm_client: any = None,  # LLM client
    timeout_seconds: int = 60,
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
            from packages.token_optimizer import assemble_prompt
            system_prompt, user_message = assemble_prompt(
                context_package=context_package,
                step=step,
                agent=agent,
                skills=skills,
            )
        else:
            # Fallback: assemble without context (for tests or when artifact_store unavailable)
            system_prompt = _assemble_system_prompt(agent, skills)
            user_message = _assemble_user_message(step, context_package)

        # Call LLM (with timeout)
        response = llm_client.complete(
            system=system_prompt,
            user=user_message,
            max_tokens=8192,
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


def _assemble_system_prompt(agent: any, skills: list) -> str:
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


def _assemble_user_message(step: ExecutionStep, context_package: any = None) -> str:
    """Assemble user message from step context.

    Stubbed: token optimizer (task-014) will provide full context_package.
    For now, return placeholder.
    """
    if context_package:
        return f"Execute step: {step.step_id}\nContext available for {step.agent_name}"
    else:
        return f"Execute step {step.step_id} for agent {step.agent_name}"
