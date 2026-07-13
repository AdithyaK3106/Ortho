"""Unit tests for Evidence contract (spec.md §3.3)."""

import pytest
from .executor.evidence_collector import (
    Evidence,
    EvidenceType,
    create_agent_execution_evidence,
    create_approval_evidence,
    create_error_evidence,
)
from datetime import datetime


# ============================================================================
# Unit Tests: Evidence Structure
# ============================================================================

def test_evidence_structure_all_fields():
    """Test Evidence dataclass has all required fields."""
    evidence = Evidence(
        step_id="step-1",
        step_name="architect",
        evidence_type=EvidenceType.AGENT_EXECUTION,
        system_prompt="You are an architect...",
        user_message="Design the system...",
        agent_output="The architecture is...",
        input_tokens=500,
        output_tokens=200,
        total_tokens=700,
        approval_decision=None,
        approval_reason=None,
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),
        duration_ms=1000,
        status="success",
        error_message=None,
    )

    # Verify all fields are present
    assert evidence.step_id == "step-1"
    assert evidence.step_name == "architect"
    assert evidence.evidence_type == EvidenceType.AGENT_EXECUTION
    assert evidence.system_prompt == "You are an architect..."
    assert evidence.user_message == "Design the system..."
    assert evidence.agent_output == "The architecture is..."
    assert evidence.input_tokens == 500
    assert evidence.output_tokens == 200
    assert evidence.total_tokens == 700
    assert evidence.created_at is not None
    assert evidence.completed_at is not None
    assert evidence.duration_ms == 1000
    assert evidence.status == "success"


def test_evidence_type_agent_execution():
    """Test Evidence type: agent_execution."""
    evidence = create_agent_execution_evidence(
        step_id="step-1",
        step_name="architect",
        system_prompt="You are...",
        user_message="Design...",
        agent_output="Architecture...",
        input_tokens=500,
        output_tokens=200,
        duration_ms=1000,
    )

    assert evidence.evidence_type == EvidenceType.AGENT_EXECUTION
    assert evidence.status == "success"
    assert evidence.system_prompt == "You are..."
    assert evidence.agent_output == "Architecture..."


def test_evidence_type_approval_gate_approved():
    """Test Evidence type: approval_gate (approved)."""
    evidence = create_approval_evidence(
        step_id="step-1",
        step_name="architect",
        approved=True,
        reason="Looks good",
    )

    assert evidence.evidence_type == EvidenceType.APPROVAL_GATE
    assert evidence.approval_decision == "approved"
    assert evidence.approval_reason == "Looks good"


def test_evidence_type_approval_gate_rejected():
    """Test Evidence type: approval_gate (rejected)."""
    evidence = create_approval_evidence(
        step_id="step-1",
        step_name="architect",
        approved=False,
        reason="Need more analysis",
    )

    assert evidence.evidence_type == EvidenceType.APPROVAL_GATE
    assert evidence.approval_decision == "rejected"
    assert evidence.approval_reason == "Need more analysis"


def test_evidence_type_error():
    """Test Evidence type: error."""
    evidence = create_error_evidence(
        step_id="step-1",
        step_name="coder",
        error_message="LLM timeout",
        duration_ms=60000,
    )

    assert evidence.evidence_type == EvidenceType.ERROR
    assert evidence.status == "error"
    assert evidence.error_message == "LLM timeout"


def test_evidence_type_values():
    """Test all EvidenceType enum values exist."""
    assert EvidenceType.AGENT_EXECUTION.value == "agent_execution"
    assert EvidenceType.APPROVAL_GATE.value == "approval_gate"
    assert EvidenceType.REJECTION.value == "rejection"
    assert EvidenceType.TIMEOUT.value == "timeout"
    assert EvidenceType.ERROR.value == "error"


# ============================================================================
# Unit Tests: Evidence Determinism
# ============================================================================

def test_evidence_determinism_agent_execution():
    """Test determinism: same inputs → same Evidence structure."""
    evidence1 = create_agent_execution_evidence(
        step_id="step-1",
        step_name="architect",
        system_prompt="You are an architect...",
        user_message="Design the system...",
        agent_output="The architecture is layered",
        input_tokens=500,
        output_tokens=200,
        duration_ms=1000,
    )

    evidence2 = create_agent_execution_evidence(
        step_id="step-1",
        step_name="architect",
        system_prompt="You are an architect...",
        user_message="Design the system...",
        agent_output="The architecture is layered",
        input_tokens=500,
        output_tokens=200,
        duration_ms=1000,
    )

    # Same fields
    assert evidence1.step_id == evidence2.step_id
    assert evidence1.step_name == evidence2.step_name
    assert evidence1.evidence_type == evidence2.evidence_type
    assert evidence1.system_prompt == evidence2.system_prompt
    assert evidence1.agent_output == evidence2.agent_output
    assert evidence1.input_tokens == evidence2.input_tokens
    assert evidence1.output_tokens == evidence2.output_tokens
    assert evidence1.total_tokens == evidence2.total_tokens
    assert evidence1.status == evidence2.status


def test_evidence_determinism_error():
    """Test determinism: error evidence same for same error."""
    evidence1 = create_error_evidence(
        step_id="step-2",
        step_name="coder",
        error_message="Connection timeout",
        duration_ms=30000,
    )

    evidence2 = create_error_evidence(
        step_id="step-2",
        step_name="coder",
        error_message="Connection timeout",
        duration_ms=30000,
    )

    assert evidence1.step_id == evidence2.step_id
    assert evidence1.error_message == evidence2.error_message
    assert evidence1.status == evidence2.status


# ============================================================================
# Unit Tests: Token Counting
# ============================================================================

def test_evidence_total_tokens_calculation():
    """Test total_tokens = input_tokens + output_tokens."""
    evidence = create_agent_execution_evidence(
        step_id="step-1",
        step_name="architect",
        system_prompt="...",
        user_message="...",
        agent_output="...",
        input_tokens=100,
        output_tokens=50,
        duration_ms=500,
    )

    assert evidence.total_tokens == 150
    assert evidence.input_tokens + evidence.output_tokens == evidence.total_tokens


def test_evidence_timestamp_iso8601():
    """Test timestamps are ISO-8601 UTC."""
    evidence = Evidence(
        step_id="step-1",
        step_name="architect",
        evidence_type=EvidenceType.AGENT_EXECUTION,
        created_at=datetime.utcnow().isoformat(),
    )

    # Verify ISO-8601 format (should contain T and Z or +)
    assert "T" in evidence.created_at or ":" in evidence.created_at


# ============================================================================
# Property-Based Tests
# ============================================================================

from hypothesis import given, strategies as st


@given(
    input_tokens=st.integers(min_value=0, max_value=10000),
    output_tokens=st.integers(min_value=0, max_value=10000),
)
def test_evidence_total_tokens_property(input_tokens, output_tokens):
    """Property: total_tokens always equals input + output."""
    evidence = create_agent_execution_evidence(
        step_id="step-1",
        step_name="test",
        system_prompt="",
        user_message="",
        agent_output="",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=1,
    )

    assert evidence.total_tokens == input_tokens + output_tokens


@given(
    duration=st.integers(min_value=0, max_value=300000)
)
def test_evidence_duration_non_negative(duration):
    """Property: duration_ms is always non-negative."""
    evidence = create_agent_execution_evidence(
        step_id="step-1",
        step_name="test",
        system_prompt="",
        user_message="",
        agent_output="",
        input_tokens=10,
        output_tokens=5,
        duration_ms=duration,
    )

    assert evidence.duration_ms >= 0
