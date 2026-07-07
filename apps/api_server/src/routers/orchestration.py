"""FastAPI router for orchestration endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from packages.orchestration.src.intent.router import IntentRouter
from packages.orchestration.src.selector.engine import SelectorEngine
from packages.orchestration.src.executor.workflow_executor import WorkflowExecutor
from packages.orchestration.src.executor.state_store import WorkflowStateStore
from packages.shared.storage.database import OrthoDatabase
from pathlib import Path


# Request/Response models
class RunRequest(BaseModel):
    intent: str
    dryRun: bool = False


class ApproveRequest(BaseModel):
    reason: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str


class WorkflowRunResponse(BaseModel):
    id: str
    intent_class: str
    status: str
    started_at: str
    completed_at: Optional[str] = None


router = APIRouter(prefix="/api", tags=["orchestration"])

# Global state (in production, use dependency injection)
_db: Optional[OrthoDatabase] = None
_intent_router: Optional[IntentRouter] = None
_selector_engine: Optional[SelectorEngine] = None
_executor: Optional[WorkflowExecutor] = None
_state_store: Optional[WorkflowStateStore] = None
_current_approval_callback: Optional[callable] = None


def init_orchestration(
    db: OrthoDatabase,
    intent_router: IntentRouter,
    selector_engine: SelectorEngine,
    executor: WorkflowExecutor,
    agent_registry,
    skill_registry,
):
    """Initialize orchestration state (call on app startup)."""
    global _db, _intent_router, _selector_engine, _executor, _state_store
    _db = db
    _intent_router = intent_router
    _selector_engine = selector_engine
    _executor = executor
    _state_store = WorkflowStateStore(db)


@router.post("/run")
async def run_workflow(request: RunRequest, background_tasks: BackgroundTasks):
    """POST /api/run — Run orchestration workflow."""
    if not _intent_router or not _selector_engine or not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    try:
        # Step 1: Classify intent
        intent = _intent_router.classify(request.intent)

        if request.dryRun:
            # Dry-run: just build plan, don't execute
            from packages.shared.types import TokenBudget

            budget = TokenBudget(
                total=16000,
                used=0,
                model="claude-sonnet-4-6"
            )

            plan = _selector_engine.build_plan(
                intent=intent,
                available_context=["architecture_model", "dependency_graph"],
                token_budget=budget,
            )

            return {
                "plan": {
                    "intent_class": plan.intent_class,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "agent_name": s.agent_name,
                            "skill_names": s.skill_names,
                            "approval_gate": s.approval_gate,
                        }
                        for s in plan.steps
                    ],
                    "total_estimated_tokens": plan.total_estimated_tokens,
                    "human_approval_required": plan.human_approval_required,
                }
            }

        # Step 2: Build execution plan
        from packages.shared.types import TokenBudget

        budget = TokenBudget(
            total=16000,
            used=0,
            model="claude-sonnet-4-6"
        )

        plan = _selector_engine.build_plan(
            intent=intent,
            available_context=["architecture_model", "dependency_graph"],
            token_budget=budget,
        )

        # Step 3: Create workflow run (awaiting_approval if human_approval_required, else execute)
        repo_id = "repo-default"  # TODO: get from context

        if plan.human_approval_required:
            # Create run in awaiting_approval state (human must approve via /api/approve)
            workflow_run = _state_store.create_run(repo_id, plan.intent_class, plan)
            _state_store.update_run_status(workflow_run.id, "awaiting_approval")

            return {
                "plan": {
                    "intent_class": plan.intent_class,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "agent_name": s.agent_name,
                            "skill_names": s.skill_names,
                            "approval_gate": s.approval_gate,
                        }
                        for s in plan.steps
                    ],
                    "total_estimated_tokens": plan.total_estimated_tokens,
                    "human_approval_required": plan.human_approval_required,
                },
                "workflow_run": {
                    "id": workflow_run.id,
                    "intent_class": workflow_run.intent_class,
                    "status": workflow_run.status,
                    "started_at": workflow_run.started_at,
                    "completed_at": workflow_run.completed_at,
                }
            }
        else:
            # No approval required: execute immediately in background
            def execute_plan_no_approval():
                def approval_callback(workflow_run):
                    return True

                _executor.execute(
                    plan=plan,
                    repo_id=repo_id,
                    on_approval_gate=approval_callback,
                )

            workflow_run = _state_store.create_run(repo_id, plan.intent_class, plan)
            background_tasks.add_task(execute_plan_no_approval)

            return {
                "plan": {
                    "intent_class": plan.intent_class,
                    "steps": [
                        {
                            "step_id": s.step_id,
                            "agent_name": s.agent_name,
                            "skill_names": s.skill_names,
                            "approval_gate": s.approval_gate,
                        }
                        for s in plan.steps
                    ],
                    "total_estimated_tokens": plan.total_estimated_tokens,
                    "human_approval_required": plan.human_approval_required,
                },
                "workflow_run": {
                    "id": workflow_run.id,
                    "intent_class": workflow_run.intent_class,
                    "status": workflow_run.status,
                    "started_at": workflow_run.started_at,
                    "completed_at": workflow_run.completed_at,
                }
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_status():
    """GET /api/status — Get current workflow state."""
    if not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    # TODO: Get current workflow run from session/context
    return {"workflow_run": None}


@router.post("/approve")
async def approve_workflow(request: ApproveRequest):
    """POST /api/approve — Approve pending approval gate."""
    if not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    # TODO: Implement approval logic
    return {
        "workflow_run": {
            "status": "running",
        }
    }


@router.post("/reject")
async def reject_workflow(request: RejectRequest):
    """POST /api/reject — Reject workflow."""
    if not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    # TODO: Implement rejection logic
    return {
        "workflow_run": {
            "status": "rejected",
            "completed_at": "",
        }
    }


@router.get("/history")
async def get_history(id: Optional[str] = None, limit: int = 10):
    """GET /api/history — List or show workflow runs."""
    if not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    try:
        if id:
            # Show specific run
            workflow_run = _state_store.get_run(id)
            return {"workflow_run": workflow_run}
        else:
            # List runs
            runs = _state_store.list_runs("repo-default", limit=limit)
            return {
                "runs": [
                    {
                        "id": r.id,
                        "intent_class": r.intent_class,
                        "status": r.status,
                        "started_at": r.started_at,
                        "completed_at": r.completed_at,
                    }
                    for r in runs
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
