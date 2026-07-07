"""Evidence Collection: Deterministic evidence artifacts per spec.md §3.3."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class EvidenceType(Enum):
    """Evidence type enumeration per spec.md §3.3."""
    AGENT_EXECUTION = "agent_execution"
    APPROVAL_GATE = "approval_gate"
    REJECTION = "rejection"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Evidence:
    """Deterministic evidence artifact per spec.md §3.3.

    One Evidence per ExecutionStep. Fields are deterministic given same inputs.
    """

    # Step metadata
    step_id: str                        # ExecutionStep.step_id
    step_name: str                      # ExecutionStep.agent_name
    evidence_type: EvidenceType         # Type of evidence

    # LLM Interaction (for evidence_type=AGENT_EXECUTION)
    system_prompt: str = ""
    user_message: str = ""
    agent_output: str = ""

    # Token Metrics
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Approval Gate Evidence
    approval_decision: Optional[str] = None  # approved | rejected | timeout
    approval_reason: Optional[str] = None

    # Metadata
    created_at: str = ""                # ISO-8601 UTC timestamp
    completed_at: Optional[str] = None  # ISO-8601 UTC timestamp (None if pending)
    duration_ms: int = 0                # Elapsed time in milliseconds
    status: str = "success"             # success | error | timeout | rejected
    error_message: Optional[str] = None

    def __post_init__(self):
        """Ensure timestamps are set."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


def create_agent_execution_evidence(
    step_id: str,
    step_name: str,
    system_prompt: str,
    user_message: str,
    agent_output: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
) -> Evidence:
    """Create agent execution evidence per spec.md §3.3."""
    return Evidence(
        step_id=step_id,
        step_name=step_name,
        evidence_type=EvidenceType.AGENT_EXECUTION,
        system_prompt=system_prompt,
        user_message=user_message,
        agent_output=agent_output,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),
        duration_ms=duration_ms,
        status="success",
    )


def create_approval_evidence(
    step_id: str,
    step_name: str,
    approved: bool,
    reason: str = "",
) -> Evidence:
    """Create approval gate evidence per spec.md §3.3."""
    return Evidence(
        step_id=step_id,
        step_name=step_name,
        evidence_type=EvidenceType.APPROVAL_GATE,
        approval_decision="approved" if approved else "rejected",
        approval_reason=reason,
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),
        status="success",
    )


def create_error_evidence(
    step_id: str,
    step_name: str,
    error_message: str,
    duration_ms: int = 0,
) -> Evidence:
    """Create error evidence per spec.md §3.3."""
    return Evidence(
        step_id=step_id,
        step_name=step_name,
        evidence_type=EvidenceType.ERROR,
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),
        duration_ms=duration_ms,
        status="error",
        error_message=error_message,
    )
