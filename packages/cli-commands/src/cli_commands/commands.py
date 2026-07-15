from pathlib import Path
from typing import Any

from arch_guardrails.enforcer import ArchitectureEnforcer
from arch_intelligence.model_adapter import ArchModelAdapter
from change_planner.predictor import ChangePredictor
from change_planner.types import ImpactPrediction
from decision_engine.engine import DecisionEngine
from feature_planner.planner import FeaturePlanner
from refactoring_advisor.advisor import RefactoringAdvisor

from cli_commands.dependency_graph_adapter import DependencyGraphAdapter
from cli_commands.feature_plan_adapter import FeaturePlannerArchModelAdapter
from cli_commands.refactor_adapter import CodeRepositoryAdapter
from cli_commands.repo_scanner import ScanResult, scan_repository
from cli_commands.types import CliReport
from cli_commands.workflow_capture import capture_workflow_run


class _CallGraphView:
    """Satisfies change_planner.predictor.CallGraph protocol over real call edges."""

    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import RepoGraphQueries

        self._queries = RepoGraphQueries(scan.call_edges, scan.import_edges_by_file)

    def find_callers(self, symbol: str, depth: int = 1) -> list[str]:
        return self._queries.find_callers(symbol, depth)  # type: ignore[no-any-return]


class _ImportGraphView:
    """Satisfies change_planner.predictor.ImportGraph protocol over real import edges."""

    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import RepoGraphQueries

        self._queries = RepoGraphQueries(scan.call_edges, scan.import_edges_by_file)

    def find_importers(self, file_path: str, include_type: bool = False) -> list[tuple[str, str]]:
        result = self._queries.find_importers(file_path, include_type=True)
        return result  # type: ignore[no-any-return]


class _SymbolRegistryView:
    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import SymbolIndex

        self._index = SymbolIndex(scan.symbols_by_file)

    def symbols_in_file(self, file_path: str) -> list[str]:
        return self._index.symbols_in_file(file_path)  # type: ignore[no-any-return]


class CliCommands:
    def plan(self, intent: str, **kwargs: Any) -> CliReport:
        """ortho plan <intent>"""
        if not intent or not isinstance(intent, str):
            # No real scan target exists for this call (it never got far
            # enough to resolve one) -- capturing against "." would write
            # into whatever directory the caller's process happens to be
            # running from (e.g. this repo's own .ortho/ during a test
            # run), not a meaningful scoped memory. Skip capture here.
            return CliReport(
                title="Feature Plan: (empty)",
                content="Cannot plan for an empty or non-string intent.",
                success=False,
            )

        scan_target = str(kwargs.get("scan_path", "."))
        try:
            scan = scan_repository(scan_target)
        except FileNotFoundError as e:
            report = CliReport(title=f"Feature Plan: {intent}", content=str(e), success=False)
            capture_workflow_run(scan_target, "plan", intent, report)
            return report
        except Exception as e:
            report = CliReport(title=f"Feature Plan: {intent}", content=f"Scan failed: {e}", success=False)
            capture_workflow_run(scan_target, "plan", intent, report)
            return report

        adapter = FeaturePlannerArchModelAdapter(scan.arch_model)
        plan = FeaturePlanner(adapter).plan_feature(intent)

        lines = [f"Feature type: {plan.feature_type}", ""]
        for path in plan.paths:
            lines.append(
                f"- {path.name} (effort={path.effort}, risk={path.risk}): "
                f"{path.description} -> {path.rationale}"
            )
        content = "\n".join(lines)

        report = CliReport(
            title=f"Feature Plan: {intent}",
            content=content,
            success=True,
        )
        capture_workflow_run(scan_target, "plan", intent, report)
        return report

    def refactor(self, path: str | None = None, **kwargs: Any) -> CliReport:
        """ortho refactor [path]"""
        target = path or "."
        try:
            scan = scan_repository(target)
        except FileNotFoundError as e:
            report = CliReport(title=f"Refactoring: {path or 'All'}", content=str(e), success=False)
            capture_workflow_run(target, "refactor", path or "All", report)
            return report
        except Exception as e:
            report = CliReport(title=f"Refactoring: {path or 'All'}", content=f"Scan failed: {e}", success=False)
            capture_workflow_run(target, "refactor", path or "All", report)
            return report

        repo = CodeRepositoryAdapter(scan)
        issues = RefactoringAdvisor(repo).find_issues()

        if not issues:
            content = "No refactoring issues found."
        else:
            lines = [
                f"[{i.severity}] {i.issue_type} at {i.location}: {i.recommendation} "
                f"(effort={i.estimated_effort}, confidence={i.confidence:.2f})"
                for i in issues
            ]
            content = "\n".join(lines)

        report = CliReport(
            title=f"Refactoring: {path or 'All'}",
            content=content,
            success=True,
        )
        capture_workflow_run(target, "refactor", path or "All", report)
        return report

    def guardrails(self, path: str | None = None, **kwargs: Any) -> CliReport:
        """ortho guardrails check [path]"""
        target = path or "."
        severity_filter = kwargs.get("severity_filter")
        if severity_filter is not None and severity_filter not in ("error", "warning"):
            raise ValueError(f"severity_filter must be 'error' or 'warning', got '{severity_filter}'")

        try:
            scan = scan_repository(target)
        except FileNotFoundError as e:
            report = CliReport(
                title=f"Architecture Check: {target}",
                content=str(e),
                success=False,
            )
            capture_workflow_run(target, "guardrails", target, report)
            return report
        except Exception as e:
            report = CliReport(
                title=f"Architecture Check: {target}",
                content=f"Scan failed: {e}",
                success=False,
            )
            capture_workflow_run(target, "guardrails", target, report)
            return report

        arch_model_adapter = ArchModelAdapter(scan.arch_model, scan.file_to_module)
        dep_graph = DependencyGraphAdapter(scan.import_edges_by_file, scan.file_to_module)
        from repo_intelligence.graph_queries import CodeMetricsAdapter

        metrics = CodeMetricsAdapter(scan.file_to_module)

        enforcer = ArchitectureEnforcer(arch_model_adapter, dep_graph, metrics)
        violations = enforcer.check_violations()

        # Filter violations if severity_filter is provided
        filtered_violations = violations
        filter_count = 0
        if severity_filter is not None:
            filtered_violations = [v for v in violations if v.severity == severity_filter]
            filter_count = len(violations) - len(filtered_violations)

        if not filtered_violations:
            content = f"Scanned {len(scan.file_to_module)} file(s). No violations found."
        else:
            lines = [
                f"[{v.severity}] {v.rule_id} at {v.location}: {v.message} -> {v.suggested_fix}"
                for v in filtered_violations
            ]
            content = "\n".join(lines)
            if filter_count > 0:
                content += f"\n\n(Scanned {len(scan.file_to_module)} file(s). {len(filtered_violations)} violation(s) found ({filter_count} filtered by severity).)"
            else:
                content = f"Scanned {len(scan.file_to_module)} file(s). {len(filtered_violations)} violation(s) found.\n\n" + content

        report = CliReport(
            title=f"Architecture Check: {target}",
            content=content,
            success=True,
            violations=filtered_violations,
        )
        capture_workflow_run(target, "guardrails", target, report)
        return report

    def decide(self, intent: str, **kwargs: Any) -> CliReport:
        """ortho decide <intent>"""
        if not intent:
            # See plan()'s identical early-return comment: no real scan
            # target exists yet, so skip capture rather than writing into
            # whatever directory the caller's cwd happens to be.
            return CliReport(
                title="Decision: (empty)",
                content="Cannot decide on an empty intent.",
                success=False,
            )

        confidence_threshold = kwargs.get("confidence_threshold")
        if confidence_threshold is not None:
            if not isinstance(confidence_threshold, float):
                raise ValueError(f"confidence_threshold must be a float, got {type(confidence_threshold).__name__}")
            if not (0.0 <= confidence_threshold <= 1.0):
                raise ValueError(f"confidence_threshold must be 0.0–1.0, got {confidence_threshold}")

        candidate_path = Path(intent)
        is_file_intent = candidate_path.is_file()

        scan_target = str(candidate_path.parent) if is_file_intent else str(kwargs.get("scan_path", "."))
        try:
            scan = scan_repository(scan_target)
        except FileNotFoundError as e:
            report = CliReport(title=f"Decision: {intent}", content=str(e), success=False)
            capture_workflow_run(scan_target, "decide", intent, report)
            return report
        except Exception as e:
            report = CliReport(title=f"Decision: {intent}", content=f"Scan failed: {e}", success=False)
            capture_workflow_run(scan_target, "decide", intent, report)
            return report

        arch_model_adapter = ArchModelAdapter(scan.arch_model, scan.file_to_module)
        dep_graph = DependencyGraphAdapter(scan.import_edges_by_file, scan.file_to_module)
        from repo_intelligence.graph_queries import CodeMetricsAdapter

        metrics = CodeMetricsAdapter(scan.file_to_module)
        enforcer = ArchitectureEnforcer(arch_model_adapter, dep_graph, metrics)
        violations = enforcer.check_violations()

        impact_predictions: list[ImpactPrediction] = []
        if is_file_intent:
            file_key = str(candidate_path.resolve())
            if file_key in scan.file_to_module:
                predictor = ChangePredictor(
                    call_graph=_CallGraphView(scan),
                    import_graph=_ImportGraphView(scan),
                    symbol_registry=_SymbolRegistryView(scan),
                    arch_model=arch_model_adapter,
                )
                impact_predictions = [predictor.predict_impact(file_key)]

        engine = DecisionEngine()
        decision = engine.decide(
            intent=intent,
            sources={
                "arch_guardrails": violations,
                "change_planner": impact_predictions,
            },
        )

        # Filter recommendations if confidence_threshold is provided
        filtered_options = decision.options
        filter_count = 0
        if confidence_threshold is not None:
            filtered_options = [r for r in decision.options if r.confidence >= confidence_threshold]
            filter_count = len(decision.options) - len(filtered_options)
            # If all filtered out, fall back to highest-confidence option
            if not filtered_options:
                filtered_options = [max(decision.options, key=lambda r: r.confidence)]

        recommended = filtered_options[0] if filtered_options else decision.recommended_option
        alt_titles = [opt.title for opt in filtered_options if opt is not recommended]

        content = f"Decision for: {intent}\n\nRecommended: {recommended.title}\n{decision.reasoning}"
        if alt_titles:
            content += f"\nAlternatives: {', '.join(alt_titles)}"
        if filter_count > 0:
            content += f"\n\n({filter_count} recommendation(s) filtered by confidence threshold.)"

        report = CliReport(
            title=f"Decision: {intent}",
            content=content,
            success=True,
            recommendations=filtered_options,
        )
        capture_workflow_run(scan_target, "decide", intent, report)
        return report

    def search_memory(self, repo_path: str, query: str) -> CliReport:
        """Search workflow_run artifacts in the repo's ContextHub memory."""
        repo_path_obj = Path(repo_path).resolve()

        # Reject empty queries
        if not query or not query.strip():
            return CliReport(
                title=f"Memory Search: {repo_path}",
                content="No artifacts found for empty query.",
                success=True,
            )

        # Check if repo exists
        if not repo_path_obj.is_dir():
            return CliReport(
                title=f"Memory Search: {repo_path}",
                content=f"Repo path does not exist: {repo_path}",
                success=False,
            )

        try:
            from storage import OrthoDatabase
            from context_hub.store import ArtifactStore
            from repo_intelligence.index_store import mint_repo_id

            db = OrthoDatabase(repo_path_obj)
            # Don't migrate — just read what exists
            if not db.db_path.exists():
                return CliReport(
                    title=f"Memory Search: {repo_path}",
                    content="No memory artifacts in this repo yet.",
                    success=True,
                )

            store = ArtifactStore(db, repo_id=mint_repo_id(repo_path_obj))
            results = store.search(query, artifact_type="workflow_run", limit=50)

            if not results:
                return CliReport(
                    title=f"Memory Search: {repo_path}",
                    content=f"No artifacts found matching '{query}'.",
                    success=True,
                )

            # Count by command from titles
            commands_found: dict[str, int] = {}
            for artifact in results:
                # Title format: "command: argument" from task-020
                title_parts = artifact.title.split(": ", 1)
                if title_parts:
                    cmd = title_parts[0].lower()
                    commands_found[cmd] = commands_found.get(cmd, 0) + 1

            # Build human-readable output
            lines = [f"Found {len(results)} workflow_run artifact(s) matching '{query}':"]
            lines.append("")

            for artifact in results:
                title_parts = artifact.title.split(": ", 1)
                cmd = title_parts[0] if title_parts else "unknown"
                arg = title_parts[1] if len(title_parts) > 1 else ""
                success_status = "✓" if "success=True" in artifact.content else "✗"
                lines.append(f"  {success_status} {cmd}: {arg[:60]}")

            lines.append("")
            breakdown = ", ".join(f"{count} {cmd} run(s)" for cmd, count in sorted(commands_found.items()))
            lines.append(f"Breakdown: {breakdown}")

            content = "\n".join(lines)

            return CliReport(
                title=f"Memory Search: {repo_path}",
                content=content,
                success=True,
                search_results=results,  # Structured results
            )

        except Exception as e:
            return CliReport(
                title=f"Memory Search: {repo_path}",
                content=f"Search failed: {e}",
                success=False,
            )
