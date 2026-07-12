"""FastAPI router for orchestration endpoints (task-013 workflow commands)."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

# ponytail: conditional imports for optional orchestration features
try:
    from packages.orchestration.src.orchestration.intent.router import IntentRouter
    from packages.orchestration.src.orchestration.selector.engine import SelectorEngine
    from packages.orchestration.src.executor.workflow_executor import WorkflowExecutor
    from packages.orchestration.src.executor.state_store import WorkflowStateStore
except ImportError:
    # If packages not available, define stub interfaces
    IntentRouter = None
    SelectorEngine = None
    WorkflowExecutor = None
    WorkflowStateStore = None

try:
    from shared.storage.src.storage.database import OrthoDatabase
except ImportError:
    OrthoDatabase = None
from pathlib import Path


# Request/Response models
class RunRequest(BaseModel):
    intent: str
    dryRun: bool = False
    repo_id: str = "repo-default"


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
_current_workflow_run_id: Optional[str] = None


def init_orchestration(
    db: OrthoDatabase,
    intent_router: IntentRouter,
    selector_engine: SelectorEngine,
    executor: WorkflowExecutor,
    agent_registry,
    skill_registry,
):
    """Initialize orchestration state (call on app startup)."""
    global _db, _intent_router, _selector_engine, _executor, _state_store, _current_workflow_run_id
    _db = db
    _intent_router = intent_router
    _selector_engine = selector_engine
    _executor = executor
    _state_store = WorkflowStateStore(db)
    _current_workflow_run_id = None


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
            from packages.token_optimizer.src.token_optimizer.budget import TokenBudget

            budget = TokenBudget(total=16000, used=0, model="claude-sonnet-4-6")
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
        from packages.token_optimizer.src.token_optimizer.budget import TokenBudget

        budget = TokenBudget(total=16000, used=0, model="claude-sonnet-4-6")
        plan = _selector_engine.build_plan(
            intent=intent,
            available_context=["architecture_model", "dependency_graph"],
            token_budget=budget,
        )

        # Step 3: Create workflow run in pending state
        workflow_run = _state_store.create_run(request.repo_id, plan.intent_class, plan)
        _current_workflow_run_id = workflow_run.id

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
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def get_status():
    """GET /api/status — Get current workflow state."""
    if not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    global _current_workflow_run_id
    if not _current_workflow_run_id:
        return {"workflow_run": None}

    try:
        workflow_run = _state_store.get_run(_current_workflow_run_id)
        return {
            "workflow_run": {
                "id": workflow_run.id,
                "intent_class": workflow_run.intent_class,
                "status": workflow_run.status,
                "started_at": workflow_run.started_at,
                "completed_at": workflow_run.completed_at,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/approve")
async def approve_workflow(request: ApproveRequest):
    """POST /api/approve — Approve pending approval gate and resume workflow."""
    if not _executor or not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    global _current_workflow_run_id
    if not _current_workflow_run_id:
        raise HTTPException(status_code=400, detail="No workflow run in progress")

    try:
        # Resume workflow with approval decision
        workflow_run = _executor.resume(_current_workflow_run_id, approval_given=True)

        return {
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


@router.post("/reject")
async def reject_workflow(request: RejectRequest):
    """POST /api/reject — Reject pending approval gate and mark workflow as failed."""
    if not _executor or not _state_store:
        raise HTTPException(status_code=500, detail="Orchestration not initialized")

    global _current_workflow_run_id
    if not _current_workflow_run_id:
        raise HTTPException(status_code=400, detail="No workflow run in progress")

    try:
        # Resume workflow with rejection decision
        workflow_run = _executor.resume(_current_workflow_run_id, approval_given=False)

        return {
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


@router.get("/history")
async def get_history(
    id: Optional[str] = None, repo_id: Optional[str] = None, limit: int = 10
):
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
            runs = _state_store.list_runs(repo_id or "repo-default", limit=limit)
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
