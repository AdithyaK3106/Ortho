"""CLI bridge for ortho run/status/approve/reject/history (workflow orchestration).

Spawned as a bare script by the TS CLI — never depend on install state
(same idiom as scan_cli.py / context.py). Replaces the phantom HTTP API
the TS commands previously pointed at (no server ever implemented it).
"""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
for _p in (
    _PROJECT_ROOT,
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from storage import OrthoDatabase

from repo_intelligence.index_store import IndexStore, mint_repo_id

from packages.orchestration.src.executor.workflow_executor import WorkflowExecutor
from packages.orchestration.src.executor.state_store import WorkflowStateStore
from packages.orchestration.src.executor.step_runner import run_step
from packages.orchestration.src.executor.evidence_collector import (
    Evidence,
    EvidenceType,
    create_approval_evidence,
)
from packages.orchestration.src.selector.engine import SelectorEngine
from packages.orchestration.src.orchestration.selector.agent_registry import AgentRegistry
from packages.orchestration.src.orchestration.selector.skill_registry import SkillRegistry
from packages.orchestration.src.orchestration.intent.types import IntentClassification


def _reconfigure_streams() -> None:
    """Windows consoles default to cp1252; force UTF-8 like scan_cli.py."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


class StubLLMClient:
    """Deterministic offline LLM stand-in.

    ponytail: no live LLM is wired yet (documented task-012/013 limitation;
    real client lands with the token optimizer, task-014). Evidence records
    are real; agent_output is clearly marked as stub output.
    """

    def complete(self, system, user, max_tokens, temperature, timeout_seconds):
        content = f"[stub-llm] no live LLM configured; step acknowledged: {user}"
        return SimpleNamespace(
            content=content,
            input_tokens=(len(system) + len(user)) // 4,
            output_tokens=len(content) // 4,
        )


# Keyword fallback: used only when the semantic router (or its model) is
# unavailable, or when semantic confidence is below threshold. First matching
# class wins; order encodes precedence.
_INTENT_KEYWORDS = [
    ("bug_fix", ("bug", "fix", "crash", "broken", "debug", "error")),
    ("refactor", ("refactor", "restructure", "clean up", "cleanup", "simplify")),
    ("documentation", ("document", "docs", "readme", "docstring")),
    ("architecture_review", ("architecture", "adr", "design", "layer", "subsystem")),
    ("analysis", ("analyze", "analysis", "impact", "debt", "dependency", "understand", "review")),
    ("feature_development", ("add", "implement", "build", "create", "feature", "write")),
]

_semantic_router = None  # cached per process


def _keyword_classify(text: str) -> IntentClassification:
    lower = text.lower()
    for intent_type, keywords in _INTENT_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return IntentClassification(type=intent_type, confidence=0.9, method="keyword")
    return IntentClassification(type="analysis", confidence=0.5, method="keyword_default")


def classify_intent(text: str) -> IntentClassification:
    """Classify free text into a workflow intent class (spec.md §1).

    Semantic routing first (task-012 IntentRouter: semantic-router +
    BAAI/bge-small-en-v1.5, deterministic embeddings, threshold 0.7).
    Falls back to keyword matching when the router or its model is
    unavailable, or when semantic confidence is below threshold (the
    task-014 LLM fallback stays a stub and is not consumed for planning).
    """
    global _semantic_router
    if _semantic_router is False:  # earlier init failed; don't retry
        return _keyword_classify(text)
    try:
        if _semantic_router is None:
            from packages.orchestration.src.orchestration.intent.router import IntentRouter
            from packages.orchestration.src.orchestration.intent.corpus import (
                WORKFLOW_INTENT_UTTERANCES,
            )
            _semantic_router = IntentRouter(WORKFLOW_INTENT_UTTERANCES)
        result = _semantic_router.classify_intent(text)
        if result.method == "router":
            return result
    except (ImportError, RuntimeError) as e:
        print(f"(semantic router unavailable: {e}; using keyword routing)", file=sys.stderr)
        _semantic_router = False  # don't retry this process
    return _keyword_classify(text)


def _open_db(repo_root: Path):
    db = OrthoDatabase(repo_root)
    db.migrate()
    repo_id = mint_repo_id(repo_root)
    IndexStore(db, repo_id, repo_root).ensure_repository(repo_root.name)
    return db, repo_id


def _load_registries(repo_root: Path):
    """Repo-local .ases manifests win; fall back to the Ortho installation's."""
    ases_root = repo_root / ".ases"
    if not (ases_root / "agents" / "core").is_dir():
        ases_root = _PROJECT_ROOT / ".ases"
    agents = AgentRegistry(ases_root / "agents")
    skills = SkillRegistry(ases_root / "skills")
    return agents, skills


def _available_context(db, repo_id: str) -> list:
    """Report only context that actually exists in the repo database."""
    ctx = ["repo", "user_intent", "code"]
    conn = db.connection()
    try:
        if conn.execute(
            "SELECT 1 FROM symbols WHERE repo_id = ? LIMIT 1", (repo_id,)
        ).fetchone():
            ctx.append("repo_structure")
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "architecture_models" in tables and conn.execute(
            "SELECT 1 FROM architecture_models WHERE repo_id = ? LIMIT 1", (repo_id,)
        ).fetchone():
            ctx += ["architecture", "existing_architecture"]
    finally:
        conn.close()
    return ctx


def _print_plan(plan) -> None:
    print(f"Intent: {plan.intent_class}")
    print(f"Steps: {len(plan.steps)}")
    print(f"Estimated tokens: {plan.total_estimated_tokens}")
    print(f"Approval required: {plan.human_approval_required}")
    for idx, step in enumerate(plan.steps, 1):
        gate = " [approval gate]" if step.approval_gate else ""
        skills = ", ".join(step.skill_names) or "(no skills)"
        print(f"  {idx}. {step.agent_name} ({skills}){gate}")


def _print_run(run) -> None:
    print(f"Run ID: {run.id}")
    print(f"Intent: {run.intent_class}")
    print(f"Status: {run.status}")
    print(f"Started: {run.started_at}")
    if run.completed_at:
        print(f"Completed: {run.completed_at}")
    print(f"Evidence artifacts: {len(run.evidence)}")


def cmd_run(args) -> int:
    repo_root = Path(args.repo_root).resolve()
    db, repo_id = _open_db(repo_root)
    agents, skills = _load_registries(repo_root)

    intent = classify_intent(args.intent)
    print(
        f"Intent classified: {intent.type} "
        f"(confidence {intent.confidence:.2f}, method {intent.method})"
    )
    engine = SelectorEngine(agents, skills)
    plan = engine.build_plan(
        intent,
        available_context=_available_context(db, repo_id),
        token_budget=SimpleNamespace(remaining=100_000),
    )

    if not plan.steps:
        print(f"No agents matched intent '{intent.type}' — nothing to run.", file=sys.stderr)
        return 1

    _print_plan(plan)

    if args.dry_run:
        return 0

    has_gates = any(s.approval_gate for s in plan.steps)
    if has_gates and not args.yes and not sys.stdin.isatty():
        print(
            "Plan contains approval gates but stdin is not interactive.\n"
            "Re-run with --yes to auto-approve, or run from a terminal.",
            file=sys.stderr,
        )
        return 1

    def on_approval_gate(workflow_run) -> bool:
        if args.yes:
            print("Approval gate: auto-approved (--yes)")
            return True
        try:
            answer = input("Approval gate reached. Continue? [y/N] ")
        except EOFError:
            # Windows reports NUL/redirected stdin as a tty, so the isatty()
            # pre-check can't catch this; reject safely instead of crashing.
            print(
                "\nNo interactive input available; gate rejected. "
                "Use --yes to auto-approve.",
                file=sys.stderr,
            )
            return False
        return answer.strip().lower() in ("y", "yes")

    store = WorkflowStateStore(db)
    executor = WorkflowExecutor(
        state_store=store,
        llm_client=StubLLMClient(),
        agent_registry=agents,
        skill_registry=skills,
    )

    print("\nExecuting workflow...")
    run = executor.execute(plan, repo_id, on_approval_gate)
    print()
    # Re-read from the store: the in-memory object doesn't carry appended evidence.
    _print_run(store.get_run(run.id))
    return 0 if run.status in ("complete", "rejected") else 1


def _latest_run(store, repo_id: str, status: str = None):
    runs = store.list_runs(repo_id, limit=50)
    if status:
        runs = [r for r in runs if r.status == status]
    return runs[0] if runs else None


def cmd_status(args) -> int:
    repo_root = Path(args.repo_root).resolve()
    db, repo_id = _open_db(repo_root)
    store = WorkflowStateStore(db)
    run = _latest_run(store, repo_id)
    if run is None:
        print("No workflow runs for this repository. Start one with `ortho run \"<intent>\"`.")
        return 0
    _print_run(run)
    if run.status == "awaiting_approval":
        print("\nAwaiting approval. Use `ortho approve` or `ortho reject <reason>`.")
    return 0


def cmd_history(args) -> int:
    repo_root = Path(args.repo_root).resolve()
    db, repo_id = _open_db(repo_root)
    store = WorkflowStateStore(db)
    runs = store.list_runs(repo_id, limit=args.limit)
    if not runs:
        print("No workflow runs for this repository.")
        return 0
    for run in runs:
        completed = run.completed_at or "-"
        print(f"{run.id}  {run.status:18s}  {run.intent_class:22s}  started {run.started_at}  completed {completed}")
    return 0


def _find_awaiting(store, repo_id: str, run_id: str = None):
    if run_id:
        run = store.get_run(run_id)
        return run if run.status == "awaiting_approval" else None
    return _latest_run(store, repo_id, status="awaiting_approval")


def cmd_approve(args) -> int:
    repo_root = Path(args.repo_root).resolve()
    db, repo_id = _open_db(repo_root)
    store = WorkflowStateStore(db)
    agents, skills = _load_registries(repo_root)

    run = _find_awaiting(store, repo_id, args.run_id)
    if run is None:
        print("No workflow awaiting approval.", file=sys.stderr)
        return 1

    executor = WorkflowExecutor(
        state_store=store,
        llm_client=StubLLMClient(),
        agent_registry=agents,
        skill_registry=skills,
    )
    run = executor.resume(run.id, approval_given=True)

    # Continue execution: run plan steps that have no evidence yet.
    # (The executor's execute() only creates new runs; per-step resume state
    # is reconstructed from the append-only evidence list.)
    done_ids = {ev.step_id for ev in run.evidence}
    gate_recorded = False
    for step in run.execution_plan.steps:
        if step.step_id in done_ids:
            continue
        if step.approval_gate and not gate_recorded:
            # This is the gate just approved; record the decision once.
            store.append_evidence(
                run.id, step.step_id,
                create_approval_evidence(step.step_id, step.agent_name, approved=True),
            )
            gate_recorded = True
        elif step.approval_gate:
            # A later independent gate: pause again (per-gate approval semantics).
            store.update_run_status(run.id, "awaiting_approval")
            print(f"Approved. Next approval gate reached at step {step.step_id} ({step.agent_name}).")
            print("Use `ortho approve` again to continue.")
            return 0

        agent = agents.get_agent(step.agent_name)
        if agent is None:
            store.update_run_status(run.id, "failed")
            print(f"Agent not found: {step.agent_name}", file=sys.stderr)
            return 1
        step_skills = [s for s in (skills.get_skill(n) for n in step.skill_names) if s]
        result = run_step(step=step, agent=agent, skills=step_skills, llm_client=StubLLMClient())
        store.append_evidence(run.id, step.step_id, result.evidence)
        if result.status != "success":
            store.update_run_status(run.id, "failed")
            print(f"Step {step.step_id} failed: {result.error_message}", file=sys.stderr)
            return 1

    store.update_run_status(run.id, "complete")
    print("Workflow approved and completed.")
    _print_run(store.get_run(run.id))
    return 0


def cmd_reject(args) -> int:
    repo_root = Path(args.repo_root).resolve()
    db, repo_id = _open_db(repo_root)
    store = WorkflowStateStore(db)
    agents, skills = _load_registries(repo_root)

    run = _find_awaiting(store, repo_id, args.run_id)
    if run is None:
        print("No workflow awaiting approval.", file=sys.stderr)
        return 1

    executor = WorkflowExecutor(
        state_store=store,
        llm_client=StubLLMClient(),
        agent_registry=agents,
        skill_registry=skills,
    )
    executor.resume(run.id, approval_given=False)

    done_ids = {ev.step_id for ev in run.evidence}
    gate_step = next(
        (s for s in run.execution_plan.steps if s.approval_gate and s.step_id not in done_ids),
        None,
    )
    if gate_step is not None:
        store.append_evidence(
            run.id, gate_step.step_id,
            Evidence(
                step_id=gate_step.step_id,
                step_name=gate_step.agent_name,
                evidence_type=EvidenceType.REJECTION,
                approval_decision="rejected",
                approval_reason=args.reason,
                status="rejected",
            ),
        )
    print(f"Workflow {run.id} rejected: {args.reason}")
    return 0


def main() -> int:
    _reconfigure_streams()
    parser = argparse.ArgumentParser(prog="ortho workflow", description="Workflow orchestration")
    parser.add_argument("--repo-root", default=".", help="Repository root (default: cwd)")
    sub = parser.add_subparsers(dest="action", required=True)

    p_run = sub.add_parser("run", help="Execute orchestration workflow for intent")
    p_run.add_argument("intent", help="Intent text, e.g. \"analyze architecture\"")
    p_run.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    p_run.add_argument("--yes", action="store_true", help="Auto-approve all approval gates")

    sub.add_parser("status", help="Show current workflow state")

    p_hist = sub.add_parser("history", help="List past workflow runs")
    p_hist.add_argument("--limit", type=int, default=10)

    p_appr = sub.add_parser("approve", help="Approve pending gate and resume")
    p_appr.add_argument("--run-id", default=None)

    p_rej = sub.add_parser("reject", help="Reject pending gate")
    p_rej.add_argument("reason", help="Rejection reason")
    p_rej.add_argument("--run-id", default=None)

    args = parser.parse_args()
    handlers = {
        "run": cmd_run,
        "status": cmd_status,
        "history": cmd_history,
        "approve": cmd_approve,
        "reject": cmd_reject,
    }
    try:
        return handlers[args.action](args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
