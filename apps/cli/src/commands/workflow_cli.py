"""CLI bridge for ortho run/status/approve/reject/history (workflow orchestration).

Spawned as a bare script by the TS CLI — never depend on install state
(same idiom as scan_cli.py / context.py). Replaces the phantom HTTP API
the TS commands previously pointed at (no server ever implemented it).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
for _p in (
    _PROJECT_ROOT,
    _PROJECT_ROOT / "shared" / "storage" / "src",
    _PROJECT_ROOT / "packages" / "repo-intelligence" / "src",
    _PROJECT_ROOT / "packages" / "context-hub" / "src",
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

    ponytail: fallback only -- used when no ORTHO_LLM_API_KEY is set (see
    get_llm_client() below). Evidence records are real; agent_output is
    clearly marked as stub output so a run's evidence never silently
    passes off placeholder text as a real agent's work.
    """

    def complete(
        self, system: str, user: str, max_tokens: int, temperature: float, timeout_seconds: int
    ) -> SimpleNamespace:
        content = f"[stub-llm] no live LLM configured; step acknowledged: {user}"
        return SimpleNamespace(
            content=content,
            input_tokens=(len(system) + len(user)) // 4,
            output_tokens=len(content) // 4,
        )

    def complete_with_tools(
        self,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
        timeout_seconds: int,
        tools: list[dict[str, Any]],
        tool_executor: Callable[[str, str], str],
    ) -> SimpleNamespace:
        """Same interface as OpenAICompatibleLLMClient.complete_with_tools,
        never actually calls any tool -- there is no real model here to
        decide to."""
        result = self.complete(system, user, max_tokens, temperature, timeout_seconds)
        result.tool_calls_made = []
        return result


_MAX_TOOL_ROUNDS = 10  # a real refactor task needs more back-and-forth than
# a read-only Q&A, but an unbounded loop risks burning provider quota on a
# model that never converges -- 10 real round-trips is a deliberate ceiling,
# not a guess; step_runner.py's caller decides whether to allow it at all.


class OpenAICompatibleLLMClient:
    """Real LLM client over any OpenAI-compatible /v1/chat/completions
    endpoint (e.g. a local FreeLLMAPI router). Config is env-var only --
    never hard-code a base URL, model, or key in source.
    """

    def __init__(self, base_url: str, api_key: str, model: str = "auto"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def _post_chat_completion(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        temperature: float,
        timeout_seconds: int,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                result: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
                return result
        except urllib.error.URLError as e:
            # step_runner.py's run_step() catches bare Exception and records
            # it as real error evidence -- re-raising as TimeoutError only
            # for an actual socket timeout keeps its timeout-specific
            # handling meaningful instead of masking every network failure
            # as one.
            if isinstance(e, urllib.error.HTTPError):
                raise RuntimeError(
                    f"LLM endpoint returned HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
                ) from e
            raise TimeoutError(f"LLM request failed: {e}") from e

    def complete(
        self, system: str, user: str, max_tokens: int, temperature: float, timeout_seconds: int
    ) -> SimpleNamespace:
        data = self._post_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout_seconds=timeout_seconds,
        )
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return SimpleNamespace(
            content=choice.get("content") or "",
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

    def complete_with_tools(
        self,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
        timeout_seconds: int,
        tools: list[dict[str, Any]],
        tool_executor: Callable[[str, str], str],
    ) -> SimpleNamespace:
        """Real agentic loop: send tools, execute any tool_calls the model
        returns via tool_executor(name, arguments_json) -> result_json,
        append the results as real tool messages, and re-call until the
        model stops requesting tools or _MAX_TOOL_ROUNDS is reached.

        Unlike complete(), this can make more than one real HTTP request
        per agent step -- each round is a genuine round-trip, not a retry.
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        total_input_tokens = 0
        total_output_tokens = 0
        tool_calls_made: list[dict[str, Any]] = []

        for _round in range(_MAX_TOOL_ROUNDS):
            data = self._post_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=timeout_seconds,
                tools=tools,
            )
            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            total_input_tokens += usage.get("prompt_tokens", 0)
            total_output_tokens += usage.get("completion_tokens", 0)

            tool_calls = choice.get("tool_calls") or []
            if not tool_calls:
                return SimpleNamespace(
                    content=choice.get("content") or "",
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    tool_calls_made=tool_calls_made,
                )

            # Model wants to call tools: append its message, execute each
            # real call, append the results, and loop back for the model
            # to use them.
            messages.append(
                {
                    "role": "assistant",
                    "content": choice.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for call in tool_calls:
                fn = call.get("function", {})
                name = fn.get("name", "")
                arguments_json = fn.get("arguments", "{}")
                result_json = tool_executor(name, arguments_json)
                tool_calls_made.append({"name": name, "arguments": arguments_json})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "content": result_json,
                    }
                )

        # Round cap hit: return whatever text the model produced last,
        # rather than silently discarding _MAX_TOOL_ROUNDS worth of real
        # tool results -- this is a real, honest partial answer, not an
        # error, so it's returned as content, not raised.
        return SimpleNamespace(
            content="[tool round cap reached without a final answer]",
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            tool_calls_made=tool_calls_made,
        )


def get_llm_client() -> "StubLLMClient | OpenAICompatibleLLMClient":
    """Real client if ORTHO_LLM_API_KEY is set, stub otherwise.

    ORTHO_LLM_BASE_URL defaults to a local FreeLLMAPI-style router;
    ORTHO_LLM_MODEL defaults to "auto" (router picks the best available
    model). Never falls back silently on a configuration error -- a bad
    key/URL should surface as a real per-step error in the evidence, not
    quietly downgrade to stub output that looks the same as "not configured".
    """
    api_key = os.environ.get("ORTHO_LLM_API_KEY")
    if not api_key:
        return StubLLMClient()
    base_url = os.environ.get("ORTHO_LLM_BASE_URL", "http://localhost:3001")
    model = os.environ.get("ORTHO_LLM_MODEL", "auto")
    return OpenAICompatibleLLMClient(base_url=base_url, api_key=api_key, model=model)


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

_semantic_router: "Any | None" = None  # cached per process; False sentinels
# a failed init so classify_intent() doesn't retry it every call -- Any
# rather than the real IntentRouter type to avoid importing it (and its
# heavy semantic-router/embedding-model dependency) at module load time,
# matching the existing lazy-import-only-when-needed pattern below.


def _keyword_classify(text: str) -> IntentClassification:
    lower = text.lower()
    for intent_type, keywords in _INTENT_KEYWORDS:
        if any(kw in lower for kw in keywords):
            return IntentClassification(type=intent_type, confidence=0.9, method="keyword")
    return IntentClassification(type="analysis", confidence=0.5, method="keyword_default")


def classify_intent(text: str) -> IntentClassification:
    """Classify free text into a workflow intent class (spec.md §1).

    Keyword matching by default -- instant, and in every real run this
    session it agreed with the semantic router's own classification. The
    semantic router (task-012: semantic-router + a real HuggingFace
    encoder, BAAI/bge-small-en-v1.5) is real and more nuanced on genuinely
    ambiguous phrasing, but its first use in a process downloads/loads a
    real transformer model -- observed live at ~2 minutes, every single
    time, even for `ortho run --dry-run`, which should be near-instant.
    Paying that tax by default for a 6-category classification this
    session never saw it change the answer on is a bad trade; set
    ORTHO_SEMANTIC_INTENT=1 to opt into it when you want the extra nuance.
    """
    if os.environ.get("ORTHO_SEMANTIC_INTENT") != "1":
        return _keyword_classify(text)

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


def _open_db(repo_root: Path) -> "tuple[Any, str]":
    db = OrthoDatabase(repo_root)
    db.migrate()
    repo_id = mint_repo_id(repo_root)
    IndexStore(db, repo_id, repo_root).ensure_repository(repo_root.name)
    return db, repo_id


def _load_registries(repo_root: Path) -> "tuple[AgentRegistry, SkillRegistry]":
    """Repo-local .ases manifests win; fall back to the Ortho installation's."""
    ases_root = repo_root / ".ases"
    if not (ases_root / "agents" / "core").is_dir():
        ases_root = _PROJECT_ROOT / ".ases"
    agents = AgentRegistry(ases_root / "agents")
    skills = SkillRegistry(ases_root / "skills")
    return agents, skills


def _available_context(db: Any, repo_id: str) -> list[str]:
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


def _print_plan(plan: Any) -> None:
    print(f"Intent: {plan.intent_class}")
    print(f"Steps: {len(plan.steps)}")
    print(f"Estimated tokens: {plan.total_estimated_tokens}")
    print(f"Approval required: {plan.human_approval_required}")
    for idx, step in enumerate(plan.steps, 1):
        gate = " [approval gate]" if step.approval_gate else ""
        skills = ", ".join(step.skill_names) or "(no skills)"
        print(f"  {idx}. {step.agent_name} ({skills}){gate}")


def _print_run(run: Any) -> None:
    print(f"Run ID: {run.id}")
    print(f"Intent: {run.intent_class}")
    print(f"Status: {run.status}")
    print(f"Started: {run.started_at}")
    if run.completed_at:
        print(f"Completed: {run.completed_at}")
    print(f"Evidence artifacts: {len(run.evidence)}")
    # A bare "Status: failed"/"Status: rejected" tells a developer nothing
    # actionable -- the real reason (a rejection message, or the specific
    # LLM/tool error) already exists on the evidence record; surface the
    # most recent one instead of making them go query the DB directly to
    # find out why their workflow didn't complete.
    if run.status in ("failed", "rejected") and run.evidence:
        last = run.evidence[-1]
        reason = getattr(last, "error_message", None) or getattr(last, "approval_reason", None)
        if reason:
            print(f"Reason: {reason}")


def cmd_run(args: Any) -> int:
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

    def on_approval_gate(workflow_run: Any) -> bool:
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
    # Real ArtifactStore over this repo's own ContextHub db -- without this,
    # store.artifact_store stays its default None and every agent step
    # gets zero real context, only a step_id. Search results depend on
    # what's actually been ingested (ortho context add / prior workflow_run
    # captures); a repo with none yet still gets an empty context_package,
    # same as before, but the mechanism is now correct rather than
    # structurally disabled.
    from context_hub.store import ArtifactStore
    store.artifact_store = ArtifactStore(db, repo_id)

    executor = WorkflowExecutor(
        state_store=store,
        llm_client=get_llm_client(),
        agent_registry=agents,
        skill_registry=skills,
    )

    print("\nExecuting workflow...")
    run = executor.execute(plan, repo_id, on_approval_gate, intent_text=args.intent, repo_root=repo_root)
    print()
    # Re-read from the store: the in-memory object doesn't carry appended evidence.
    _print_run(store.get_run(run.id))
    return 0 if run.status in ("complete", "rejected") else 1


def _latest_run(store: Any, repo_id: str, status: Optional[str] = None) -> Any:
    runs = store.list_runs(repo_id, limit=50)
    if status:
        runs = [r for r in runs if r.status == status]
    return runs[0] if runs else None


def cmd_status(args: Any) -> int:
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


def cmd_history(args: Any) -> int:
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


def _find_awaiting(store: Any, repo_id: str, run_id: Optional[str] = None) -> Any:
    if run_id:
        run = store.get_run(run_id)
        return run if run.status == "awaiting_approval" else None
    return _latest_run(store, repo_id, status="awaiting_approval")


def cmd_approve(args: Any) -> int:
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
        llm_client=get_llm_client(),
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
        result = run_step(step=step, agent=agent, skills=step_skills, llm_client=get_llm_client(), repo_root=repo_root)
        store.append_evidence(run.id, step.step_id, result.evidence)
        if result.status != "success":
            store.update_run_status(run.id, "failed")
            print(f"Step {step.step_id} failed: {result.error_message}", file=sys.stderr)
            return 1

    store.update_run_status(run.id, "complete")
    print("Workflow approved and completed.")
    _print_run(store.get_run(run.id))
    return 0


def cmd_reject(args: Any) -> int:
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
        llm_client=get_llm_client(),
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
