"""WorkflowStateStore: SQLite persistence for workflows, steps, approval gates."""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    # Real imports only for the type checker -- a real module-level import
    # here would risk the same circular-import selector.engine <-> executor
    # relationship _deserialize_plan's own lazy import already works around
    # (see its docstring). TYPE_CHECKING-guarded imports are invisible at
    # runtime, so they can't reintroduce that cycle.
    from selector.engine import ExecutionPlan
    from .evidence_collector import Evidence


@dataclass
class WorkflowRun:
    """Persisted workflow run with status and evidence."""
    id: str
    repo_id: str
    intent_class: str
    execution_plan: Any  # ExecutionPlan
    status: str  # pending, running, awaiting_approval, rejected, complete, failed
    started_at: str
    completed_at: Optional[str] = None
    evidence: Optional[list[Any]] = None

    def __post_init__(self) -> None:
        if self.evidence is None:
            self.evidence = []


class WorkflowStateStore:
    """SQLite backend for workflow state persistence and resumability."""

    def __init__(self, db: Any):  # OrthoDatabase
        self.db = db
        self._ensure_schema()
        # Real ArtifactStore, set by the caller (see workflow_cli.py's
        # cmd_run) when real context assembly is wanted. None means
        # workflow_executor.execute()'s hasattr(store, "artifact_store")
        # check still behaves exactly as before this was a declared
        # attribute -- callers that never set it get context_package=None,
        # same as when the attribute didn't exist on the class at all.
        self.artifact_store: Optional[Any] = None

    def _ensure_schema(self) -> None:
        """Ensure Migration 003 schema exists (idempotent)."""
        conn = self.db.connection()
        cursor = conn.cursor()

        # Check if tables exist
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('workflow_runs', 'execution_steps', 'approval_gates')"
        ).fetchall()

        if len(tables) == 3:
            return  # Schema already exists

        # Create tables (idempotent with IF NOT EXISTS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL REFERENCES repositories(id),
                intent TEXT NOT NULL,
                intent_class TEXT NOT NULL,
                execution_plan_json TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending','running','awaiting_approval','rejected','complete','failed')),
                started_at TEXT NOT NULL,
                completed_at TEXT,
                evidence_json TEXT NOT NULL DEFAULT '[]',
                created_by TEXT NOT NULL DEFAULT 'orchestration'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_steps (
                id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                step_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                skill_names TEXT NOT NULL,
                approval_gate INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL CHECK(status IN ('pending','pending_approval','running','complete','failed','rejected')),
                result_json TEXT,
                evidence_json TEXT NOT NULL DEFAULT '[]',
                started_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_gates (
                id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
                step_id TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','timeout')),
                decision_reason TEXT,
                created_at TEXT NOT NULL,
                decided_at TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_repo ON workflow_runs(repo_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_execution_steps_workflow ON execution_steps(workflow_run_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_approval_gates_workflow ON approval_gates(workflow_run_id)")

        conn.commit()

    def create_run(
        self,
        repo_id: str,
        intent_class: str,
        plan: ExecutionPlan,
        run_id: Optional[str] = None,
    ) -> WorkflowRun:
        """Create new workflow run in DB."""
        if run_id is None:
            run_id = str(uuid.uuid4())

        now = datetime.utcnow().isoformat()
        conn = self.db.connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO workflow_runs (id, repo_id, intent, intent_class, execution_plan_json, status, started_at, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            repo_id,
            plan.intent_class,
            intent_class,
            json.dumps(self._serialize_plan(plan)),
            "pending",
            now,
            "[]"
        ))

        conn.commit()

        return WorkflowRun(
            id=run_id,
            repo_id=repo_id,
            intent_class=intent_class,
            execution_plan=plan,
            status="pending",
            started_at=now,
        )

    def get_run(self, run_id: str) -> WorkflowRun:
        """Load workflow run from DB with all evidence."""
        conn = self.db.connection()
        cursor = conn.cursor()

        row = cursor.execute("""
            SELECT id, repo_id, intent, intent_class, execution_plan_json, status, started_at, completed_at, evidence_json
            FROM workflow_runs
            WHERE id = ?
        """, (run_id,)).fetchone()

        if not row:
            raise ValueError(f"Workflow run not found: {run_id}")

        id_, repo_id, intent, intent_class, plan_json, status, started_at, completed_at, evidence_json = row

        plan = self._deserialize_plan(json.loads(plan_json))
        evidence_dicts = json.loads(evidence_json) if evidence_json else []
        evidence = [self._deserialize_evidence(ev) for ev in evidence_dicts]

        return WorkflowRun(
            id=id_,
            repo_id=repo_id,
            intent_class=intent_class,
            execution_plan=plan,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            evidence=evidence,
        )

    def update_run_status(self, run_id: str, status: str) -> None:
        """Update workflow run status."""
        conn = self.db.connection()
        cursor = conn.cursor()

        completed_at = None
        if status in {"complete", "failed", "rejected"}:
            completed_at = datetime.utcnow().isoformat()

        cursor.execute("""
            UPDATE workflow_runs
            SET status = ?, completed_at = ?
            WHERE id = ?
        """, (status, completed_at, run_id))

        conn.commit()

    def append_evidence(self, run_id: str, step_id: str, evidence: Evidence) -> None:
        """Append evidence to workflow run."""
        conn = self.db.connection()
        cursor = conn.cursor()

        # Get current evidence
        row = cursor.execute("""
            SELECT evidence_json FROM workflow_runs WHERE id = ?
        """, (run_id,)).fetchone()

        if not row:
            raise ValueError(f"Workflow run not found: {run_id}")

        evidence_list = json.loads(row[0]) if row[0] else []

        # Append new evidence
        evidence_list.append(self._serialize_evidence(evidence))

        # Update
        cursor.execute("""
            UPDATE workflow_runs
            SET evidence_json = ?
            WHERE id = ?
        """, (json.dumps(evidence_list), run_id))

        conn.commit()

    def list_runs(self, repo_id: str, limit: int = 10) -> list[WorkflowRun]:
        """List past workflow runs for repo."""
        conn = self.db.connection()
        cursor = conn.cursor()

        rows = cursor.execute("""
            SELECT id, repo_id, intent, intent_class, execution_plan_json, status, started_at, completed_at, evidence_json
            FROM workflow_runs
            WHERE repo_id = ?
            ORDER BY started_at DESC
            LIMIT ?
        """, (repo_id, limit)).fetchall()

        runs = []
        for row in rows:
            id_, repo_id, intent, intent_class, plan_json, status, started_at, completed_at, evidence_json = row
            plan = self._deserialize_plan(json.loads(plan_json))
            evidence_dicts = json.loads(evidence_json) if evidence_json else []
            evidence = [self._deserialize_evidence(ev) for ev in evidence_dicts]

            runs.append(WorkflowRun(
                id=id_,
                repo_id=repo_id,
                intent_class=intent_class,
                execution_plan=plan,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                evidence=evidence,
            ))

        return runs

    @staticmethod
    def _serialize_plan(plan: Any) -> dict[str, Any]:  # ExecutionPlan
        """Serialize ExecutionPlan to JSON-compatible dict."""
        return {
            "intent_class": plan.intent_class,
            "steps": [
                {
                    "step_id": step.step_id,
                    "agent_name": step.agent_name,
                    "skill_names": step.skill_names,
                    "approval_gate": step.approval_gate,
                    "receives_from": step.receives_from,
                    "produces": step.produces,
                    "status": step.status,
                }
                for step in plan.steps
            ],
            "total_estimated_tokens": plan.total_estimated_tokens,
            "human_approval_required": plan.human_approval_required,
        }

    @staticmethod
    def _deserialize_plan(data: dict[str, Any]) -> "ExecutionPlan":
        """Deserialize JSON dict to ExecutionPlan.

        ExecutionStep/ExecutionPlan live in src/selector/engine.py, not in
        the separate src/orchestration/selector/ sub-package (which only
        holds agent_registry.py/skill_registry.py) -- "orchestration.
        selector.engine" was importing the wrong tree and 404ing the
        moment src/ was on sys.path but packages.orchestration.src.
        orchestration had already been imported under its dotted name
        elsewhere in the process (e.g. workflow_cli.py's own imports),
        which is exactly the case right after an approval-gate rejection
        calls get_run() to print the final state.
        """
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from selector.engine import ExecutionStep, ExecutionPlan

        steps = [
            ExecutionStep(
                step_id=s["step_id"],
                agent_name=s["agent_name"],
                skill_names=s["skill_names"],
                approval_gate=s["approval_gate"],
                receives_from=s.get("receives_from"),
                produces=s.get("produces", ""),
                status=s.get("status", "pending"),
            )
            for s in data.get("steps", [])
        ]

        return ExecutionPlan(
            intent_class=data["intent_class"],
            steps=steps,
            total_estimated_tokens=data.get("total_estimated_tokens", 0),
            human_approval_required=data.get("human_approval_required", False),
        )

    @staticmethod
    def _serialize_evidence(evidence: Any) -> dict[str, Any]:  # Evidence
        """Serialize Evidence to JSON-compatible dict."""
        return {
            "step_id": evidence.step_id,
            "step_name": evidence.step_name,
            "evidence_type": evidence.evidence_type.value if hasattr(evidence.evidence_type, 'value') else str(evidence.evidence_type),
            "system_prompt": evidence.system_prompt,
            "user_message": evidence.user_message,
            "agent_output": evidence.agent_output,
            "input_tokens": evidence.input_tokens,
            "output_tokens": evidence.output_tokens,
            "total_tokens": evidence.total_tokens,
            "approval_decision": evidence.approval_decision,
            "approval_reason": evidence.approval_reason,
            "created_at": evidence.created_at,
            "completed_at": evidence.completed_at,
            "duration_ms": evidence.duration_ms,
            "status": evidence.status,
            "error_message": evidence.error_message,
        }

    @staticmethod
    def _deserialize_evidence(data: dict[str, Any]) -> "Evidence":
        """Deserialize JSON dict to Evidence dataclass per spec.md §3.3.

        Ensures Evidence is always deserialized into Evidence dataclass instances,
        never exposed as raw dictionaries internally.
        """
        from executor.evidence_collector import Evidence, EvidenceType

        # Map evidence_type string back to enum (stored as lowercase value, e.g., "agent_execution")
        evidence_type_str = data.get("evidence_type", "agent_execution")
        try:
            # Try to match by value (e.g., "agent_execution" matches EvidenceType.AGENT_EXECUTION)
            evidence_type = EvidenceType(evidence_type_str)
        except ValueError:
            # Fallback to AGENT_EXECUTION if unrecognized
            evidence_type = EvidenceType.AGENT_EXECUTION

        # Evidence is imported locally (circular-import avoidance, same
        # pattern as _deserialize_plan's ExecutionPlan import), which mypy
        # cannot resolve to the same module identity as the TYPE_CHECKING
        # import above -- the same executor/selector/orchestration
        # multi-path naming ambiguity documented on _deserialize_plan,
        # here surfacing as an unresolvable Any instead of a runtime
        # crash. The constructor genuinely returns a real Evidence at
        # runtime (exercised by test_evidence.py and this file's own
        # round-trip tests); this silences the resulting false positive
        # rather than a real return-type problem.
        return Evidence(  # type: ignore[no-any-return]
            step_id=data.get("step_id", ""),
            step_name=data.get("step_name", ""),
            evidence_type=evidence_type,
            system_prompt=data.get("system_prompt", ""),
            user_message=data.get("user_message", ""),
            agent_output=data.get("agent_output", ""),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            approval_decision=data.get("approval_decision"),
            approval_reason=data.get("approval_reason"),
            created_at=data.get("created_at", ""),
            completed_at=data.get("completed_at"),
            duration_ms=data.get("duration_ms", 0),
            status=data.get("status", "success"),
            error_message=data.get("error_message"),
        )
