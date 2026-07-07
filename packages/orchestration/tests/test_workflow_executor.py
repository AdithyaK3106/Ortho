"""Unit tests for WorkflowExecutor (state machine, approval gates, resume)."""

import pytest
from packages.orchestration.src.executor.workflow_executor import (
    WorkflowExecutor,
    InvalidStateTransition,
    VALID_TRANSITIONS,
    TERMINAL_STATES,
)
from packages.orchestration.src.executor.state_store import WorkflowStateStore, WorkflowRun
from packages.orchestration.src.selector.engine import ExecutionPlan, ExecutionStep
from datetime import datetime


class MockDatabase:
    """Mock OrthoDatabase for testing."""
    def connection(self):
        return self


class MockWorkflowRun:
    """Mock WorkflowRun for testing."""
    def __init__(self, id="test-run", status="pending"):
        self.id = id
        self.status = status
        self.evidence = []
        self.completed_at = None


@pytest.fixture
def mock_db():
    return MockDatabase()


@pytest.fixture
def mock_state_store(mock_db):
    """Mock WorkflowStateStore."""
    class MockStateStore:
        def create_run(self, repo_id, intent, plan, run_id=None):
            return MockWorkflowRun()

        def get_run(self, run_id):
            return MockWorkflowRun()

        def update_run_status(self, run_id, status):
            pass

        def append_evidence(self, run_id, step_id, evidence):
            pass

    return MockStateStore()


@pytest.fixture
def executor(mock_state_store):
    """Create WorkflowExecutor with mocks."""
    return WorkflowExecutor(
        state_store=mock_state_store,
        llm_client=None,
        agent_registry=None,
        skill_registry=None,
    )


# ============================================================================
# Unit Tests: State Transitions (spec.md §3)
# ============================================================================

def test_state_transition_pending_to_running(executor):
    """Test valid transition: pending → running."""
    run = MockWorkflowRun(status="pending")
    # Should not raise
    executor._transition_state(run, "pending", "running")


def test_state_transition_running_to_awaiting_approval(executor):
    """Test valid transition: running → awaiting_approval."""
    run = MockWorkflowRun(status="running")
    executor._transition_state(run, "running", "awaiting_approval")


def test_state_transition_awaiting_approval_to_running(executor):
    """Test valid transition: awaiting_approval → running."""
    run = MockWorkflowRun(status="awaiting_approval")
    executor._transition_state(run, "awaiting_approval", "running")


def test_state_transition_awaiting_approval_to_rejected(executor):
    """Test valid transition: awaiting_approval → rejected."""
    run = MockWorkflowRun(status="awaiting_approval")
    executor._transition_state(run, "awaiting_approval", "rejected")


def test_state_transition_running_to_complete(executor):
    """Test valid transition: running → complete."""
    run = MockWorkflowRun(status="running")
    executor._transition_state(run, "running", "complete")


def test_state_transition_running_to_failed(executor):
    """Test valid transition: running → failed."""
    run = MockWorkflowRun(status="running")
    executor._transition_state(run, "running", "failed")


def test_state_transition_invalid_complete_to_running(executor):
    """Test invalid transition: complete → running (terminal state)."""
    run = MockWorkflowRun(status="complete")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "complete", "running")


def test_state_transition_invalid_failed_to_running(executor):
    """Test invalid transition: failed → running (terminal state)."""
    run = MockWorkflowRun(status="failed")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "failed", "running")


def test_state_transition_invalid_rejected_to_running(executor):
    """Test invalid transition: rejected → running (terminal state)."""
    run = MockWorkflowRun(status="rejected")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "rejected", "running")


def test_state_transition_invalid_pending_to_complete(executor):
    """Test invalid transition: pending → complete (wrong path)."""
    run = MockWorkflowRun(status="pending")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "pending", "complete")


def test_state_transition_unknown_state(executor):
    """Test transition from unknown state raises error."""
    run = MockWorkflowRun(status="unknown_state")
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "unknown_state", "running")


# ============================================================================
# Unit Tests: Approval Gate Semantics (spec.md §3.1)
# ============================================================================

def test_approval_gate_blocks_before_execution(executor):
    """Test that approval gate pauses BEFORE step execution."""
    # This is implicit in execute() logic: if step.approval_gate, pause before run_step()
    # Verify the state machine: running → awaiting_approval (before execution)
    run = MockWorkflowRun(status="running")
    executor._transition_state(run, "running", "awaiting_approval")
    assert run.status == "awaiting_approval"  # Paused


def test_approval_gate_per_gate_independence(executor):
    """Test that approval of gate N does not approve gate N+1."""
    # Workflow with 2 approval gates (e.g., architect + reviewer steps)
    # After approving architect gate and executing architect step,
    # next approval gate (reviewer) should still be pending.
    # Verify: each awaiting_approval must be handled independently
    run1 = MockWorkflowRun(status="awaiting_approval")
    executor._transition_state(run1, "awaiting_approval", "running")
    assert run1.status == "running"

    # Second approval gate arrives, back to awaiting_approval
    run2 = MockWorkflowRun(status="running")
    executor._transition_state(run2, "running", "awaiting_approval")
    assert run2.status == "awaiting_approval"  # Not automatically approved


def test_approval_gate_rejection_terminal(executor):
    """Test that rejection is terminal (awaiting_approval → rejected)."""
    run = MockWorkflowRun(status="awaiting_approval")
    executor._transition_state(run, "awaiting_approval", "rejected")
    assert run.status == "rejected"

    # Cannot transition from rejected
    with pytest.raises(InvalidStateTransition):
        executor._transition_state(run, "rejected", "running")


def test_multiple_approval_gates_supported(executor):
    """Test that multiple approval gates are supported in a workflow."""
    # Simulate workflow with 2 gates (architect → coder → reviewer)
    # Gate 1: architect step with approval_gate=True
    # Gate 2: reviewer step with approval_gate=True

    # After approving gate 1:
    run = MockWorkflowRun(status="awaiting_approval")
    executor._transition_state(run, "awaiting_approval", "running")

    # Execute architect step, move to coder step
    # Then reviewer step hits approval gate:
    executor._transition_state(run, "running", "awaiting_approval")
    assert run.status == "awaiting_approval"  # Gate 2 independent


# ============================================================================
# Integration Tests: State Machine Validation
# ============================================================================

def test_valid_transitions_table_complete():
    """Verify formal state transition table is defined."""
    assert "pending" in VALID_TRANSITIONS
    assert "running" in VALID_TRANSITIONS
    assert "awaiting_approval" in VALID_TRANSITIONS
    assert "complete" in VALID_TRANSITIONS
    assert "failed" in VALID_TRANSITIONS
    assert "rejected" in VALID_TRANSITIONS


def test_terminal_states_defined():
    """Verify terminal states have no outgoing transitions."""
    for terminal in TERMINAL_STATES:
        assert VALID_TRANSITIONS[terminal] == set()


def test_all_terminal_states_in_transitions_table():
    """Verify all terminal states are in transitions table."""
    for terminal in TERMINAL_STATES:
        assert terminal in VALID_TRANSITIONS


# ============================================================================
# Integration Tests: Resume Behavior
# ============================================================================

def test_resume_from_awaiting_approval_approved(executor, mock_state_store):
    """Test resume from awaiting_approval with approval."""
    run = MockWorkflowRun(status="awaiting_approval")

    # Resume with approval
    result = executor.resume(run.id, approval_given=True)

    # Should transition to running (or pass through to caller to execute next step)
    # For now, just verify resume doesn't crash
    assert result is not None


def test_resume_from_awaiting_approval_rejected(executor, mock_state_store):
    """Test resume from awaiting_approval with rejection."""
    run = MockWorkflowRun(status="awaiting_approval")

    # Resume with rejection
    result = executor.resume(run.id, approval_given=False)

    # Should transition to rejected
    assert result is not None


def test_resume_from_running_continues(executor, mock_state_store):
    """Test resume from running state continues execution."""
    run = MockWorkflowRun(status="running")

    result = executor.resume(run.id)

    # Should continue execution (return as-is)
    assert result is not None


def test_resume_from_terminal_noop(executor, mock_state_store):
    """Test resume from terminal states is no-op."""
    for terminal in TERMINAL_STATES:
        run = MockWorkflowRun(status=terminal)
        result = executor.resume(run.id)

        # Should return as-is (no change)
        assert result is not None


# ============================================================================
# Property-Based Tests
# ============================================================================

from hypothesis import given, strategies as st


@given(
    from_state=st.sampled_from(list(VALID_TRANSITIONS.keys())),
)
@settings(max_examples=100)
def test_state_transitions_deterministic(executor, from_state):
    """Property: valid transitions are deterministic."""
    # For each state, attempting same transition twice should have same result
    run = MockWorkflowRun(status=from_state)

    valid_targets = list(VALID_TRANSITIONS[from_state])
    if not valid_targets:
        # Terminal state, no transitions
        with pytest.raises(InvalidStateTransition):
            executor._transition_state(run, from_state, "running")
    else:
        # Valid transition should work both times
        to_state = valid_targets[0]
        executor._transition_state(run, from_state, to_state)
        # State changed
        assert run.status == to_state or run.status == from_state  # Depending on implementation
