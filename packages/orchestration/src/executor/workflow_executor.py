"""WorkflowExecutor: State machine, step execution, approval gate handling per spec.md §3."""

from dataclasses import dataclass, field
from typing import Callable, Optional, Any
from datetime import datetime
import uuid


# Formal State Transition Table (spec.md §3)
VALID_TRANSITIONS = {
    "pending": {"running"},
    "running": {"awaiting_approval", "complete", "failed"},
    "awaiting_approval": {"running", "rejected"},
    "complete": set(),  # Terminal
    "failed": set(),  # Terminal
    "rejected": set(),  # Terminal
}

TERMINAL_STATES = {"complete", "failed", "rejected"}


class InvalidStateTransition(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


@dataclass
class WorkflowExecutor:
    """Execute orchestration plans with formal state machine and approval gates."""

    state_store: Any  # WorkflowStateStore
    llm_client: Any  # LLM client (Claude, etc.)
    agent_registry: Any  # AgentRegistry
    skill_registry: Any  # SkillRegistry
    approval_timeout_seconds: int = 300

    def execute(
        self,
        plan: Any,  # ExecutionPlan
        repo_id: str,
        on_approval_gate: Callable[[Any], bool],  # Returns: approved (True) or rejected (False)
        intent_text: str = "",
        repo_root: Any = None,  # pathlib.Path -- enables real tool execution
    ) -> Any:  # WorkflowRun
        """Execute plan step by step per spec.md §3.2.

        State transitions:
        - pending → running (first step)
        - running → awaiting_approval (approval gate hit)
        - awaiting_approval → running (approved)
        - awaiting_approval → rejected (rejected)
        - running → complete (all steps done)
        - running → failed (step error)

        Args:
            plan: ExecutionPlan to execute
            repo_id: Repository ID (for persistence)
            on_approval_gate: Callback for approval decision (blocks until human decides)
            intent_text: The user's original request text. plan.intent_class
                is only the classified category ("refactor", "analysis",
                ...); without the raw text, run_step()'s no-context fallback
                could only tell an agent its step_id, never what the user
                actually asked for. Defaults to "" so existing callers/tests
                are unaffected.
            repo_root: Real filesystem path to the repo (not repo_id, which
                is a content hash/mint string with no filesystem meaning).
                Passed through to run_step() so agents get real read-only
                tools when the LLM client supports them. None (default)
                preserves existing behavior for callers/tests that don't
                pass it.

        Returns:
            WorkflowRun (status, evidence, completed_at)
        """
        # Lazy imports to avoid circular dependencies
        from .evidence_collector import Evidence, EvidenceType
        from .step_runner import run_step
        from token_optimizer import assemble_context, TokenBudget

        # Create workflow run
        run_id = str(uuid.uuid4())
        workflow_run = self.state_store.create_run(repo_id, plan.intent_class, plan, run_id)

        try:
            # Transition: pending → running
            self._transition_state(workflow_run, "pending", "running")
            workflow_run.status = "running"
            self.state_store.update_run_status(run_id, "running")

            # Execute steps
            for step in plan.steps:
                step_start_time = datetime.utcnow()  # Track per-step timing for evidence
                # If approval gate required: pause and wait for human decision
                if step.approval_gate:
                    workflow_run.status = "awaiting_approval"
                    self.state_store.update_run_status(run_id, "awaiting_approval")

                    # Call approval callback (blocks)
                    approved = on_approval_gate(workflow_run)

                    if not approved:
                        # Rejection: awaiting_approval → rejected
                        self._transition_state(workflow_run, "awaiting_approval", "rejected")
                        workflow_run.status = "rejected"
                        workflow_run.completed_at = datetime.utcnow().isoformat()
                        self.state_store.update_run_status(run_id, "rejected")

                        # Record rejection evidence
                        rejection_evidence = Evidence(
                            step_id=step.step_id,
                            step_name=step.agent_name,
                            evidence_type=EvidenceType.REJECTION,
                            approval_decision="rejected",
                            approval_reason="User rejected workflow",
                            created_at=datetime.utcnow().isoformat(),
                            status="rejected",
                        )
                        self.state_store.append_evidence(run_id, step.step_id, rejection_evidence)

                        return workflow_run

                    # Approved: awaiting_approval → running
                    self._transition_state(workflow_run, "awaiting_approval", "running")
                    workflow_run.status = "running"
                    self.state_store.update_run_status(run_id, "running")

                # Execute step
                try:
                    # Assemble context for step (task-014: token optimizer).
                    # query was step.step_id ("step-1") -- a search query
                    # that can never match real repo content, since nothing
                    # in a scanned repo's artifacts is titled "step-1". The
                    # user's actual intent_text is what real context
                    # retrieval needs to search for.
                    # getattr(..., None), not hasattr(): WorkflowStateStore
                    # now always declares .artifact_store (defaulting to
                    # None when the caller never sets one), so hasattr()
                    # alone would always be True and call assemble_context()
                    # with artifact_store=None, which crashes the moment it
                    # calls artifact_store.search(...) on a None.
                    real_artifact_store = getattr(self.state_store, "artifact_store", None)
                    budget = TokenBudget(total=8192, used=0, model="claude")
                    context_package = assemble_context(
                        query=intent_text or step.step_id,
                        repo_id=repo_id,
                        artifact_store=real_artifact_store,
                        budget=budget,
                        step_id=step.step_id,
                        workflow_run_id=run_id,
                        model="claude",
                    ) if real_artifact_store is not None else None

                    step_result = run_step(
                        step=step,
                        agent=self.agent_registry.get_agent(step.agent_name),
                        skills=[self.skill_registry.get_skill(name) for name in step.skill_names],
                        context_package=context_package,
                        llm_client=self.llm_client,
                        intent_text=intent_text,
                        repo_root=repo_root,
                    )

                    # Collect evidence
                    self.state_store.append_evidence(run_id, step.step_id, step_result.evidence)

                    # run_step() catches its own LLM/timeout errors internally
                    # and returns StepResult(status="error", ...) rather than
                    # raising -- this except block only ever sees an exception
                    # from context assembly or evidence persistence above, not
                    # a real agent-step failure. Invisible with the stub LLM
                    # client (which never errors), but a live LLM client
                    # surfaced it immediately: 2 of 3 steps in a real run
                    # timed out against a free-tier provider, were correctly
                    # recorded as real error evidence, and the workflow still
                    # finished as "complete" because nothing here ever
                    # inspected step_result.status.
                    if step_result.status != "success":
                        self._transition_state(workflow_run, "running", "failed")
                        workflow_run.status = "failed"
                        workflow_run.completed_at = datetime.utcnow().isoformat()
                        self.state_store.update_run_status(run_id, "failed")
                        return workflow_run

                except Exception as e:
                    # Step error: running → failed
                    self._transition_state(workflow_run, "running", "failed")
                    workflow_run.status = "failed"
                    error_time = datetime.utcnow()
                    workflow_run.completed_at = error_time.isoformat()
                    self.state_store.update_run_status(run_id, "failed")

                    # Record error evidence (with actual duration)
                    duration_ms = int((error_time - step_start_time).total_seconds() * 1000)
                    error_evidence = Evidence(
                        step_id=step.step_id,
                        step_name=step.agent_name,
                        evidence_type=EvidenceType.ERROR,
                        status="error",
                        error_message=str(e),
                        created_at=step_start_time.isoformat(),
                        completed_at=error_time.isoformat(),
                        duration_ms=duration_ms,
                    )
                    self.state_store.append_evidence(run_id, step.step_id, error_evidence)

                    return workflow_run

            # All steps complete: running → complete
            self._transition_state(workflow_run, "running", "complete")
            workflow_run.status = "complete"
            workflow_run.completed_at = datetime.utcnow().isoformat()
            self.state_store.update_run_status(run_id, "complete")

            return workflow_run

        except Exception as e:
            # Unexpected error: mark failed
            workflow_run.status = "failed"
            workflow_run.completed_at = datetime.utcnow().isoformat()
            self.state_store.update_run_status(run_id, "failed")
            raise

    def resume(self, run_id: str, approval_given: Optional[bool] = None) -> Any:  # WorkflowRun
        """Resume interrupted workflow per spec.md §3.2.

        Behavior depends on current state:
        - awaiting_approval: re-prompt for decision (or use approval_given if provided)
        - running: resume from next pending step
        - complete/failed/rejected: return as-is

        Args:
            run_id: Workflow run ID to resume
            approval_given: Optional pre-decision (True=approve, False=reject)

        Returns:
            Updated WorkflowRun
        """
        workflow_run = self.state_store.get_run(run_id)

        if workflow_run.status == "awaiting_approval":
            # Re-process approval gate
            if approval_given is None:
                return workflow_run  # Still awaiting

            if approval_given:
                # Approve: awaiting_approval → running
                self._transition_state(workflow_run, "awaiting_approval", "running")
                workflow_run.status = "running"
                self.state_store.update_run_status(run_id, "running")
            else:
                # Reject: awaiting_approval → rejected
                self._transition_state(workflow_run, "awaiting_approval", "rejected")
                workflow_run.status = "rejected"
                workflow_run.completed_at = datetime.utcnow().isoformat()
                self.state_store.update_run_status(run_id, "rejected")

            return workflow_run

        # If running, return as-is (caller will continue execution)
        return workflow_run

    def _transition_state(self, workflow_run: Any, from_state: str, to_state: str) -> None:  # WorkflowRun
        """Validate state transition against formal table per spec.md §3 and apply it."""
        if from_state not in VALID_TRANSITIONS:
            raise InvalidStateTransition(f"Unknown state: {from_state}")

        if to_state not in VALID_TRANSITIONS[from_state]:
            raise InvalidStateTransition(
                f"Invalid transition: {from_state} → {to_state}"
            )

        if workflow_run is not None:
            workflow_run.status = to_state
