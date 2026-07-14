from pathlib import Path
from typing import Any

from arch_guardrails.enforcer import ArchitectureEnforcer
from arch_intelligence.model_adapter import ArchModelAdapter
from change_planner.predictor import ChangePredictor
from change_planner.types import ImpactPrediction
from decision_engine.engine import DecisionEngine

from cli_commands.dependency_graph_adapter import DependencyGraphAdapter
from cli_commands.repo_scanner import ScanResult, scan_repository
from cli_commands.types import CliReport


class _CallGraphView:
    """Satisfies change_planner.predictor.CallGraph protocol over real call edges."""

    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import RepoGraphQueries

        self._queries = RepoGraphQueries(scan.call_edges, scan.import_edges_by_file)

    def find_callers(self, symbol: str, depth: int = 1) -> list[str]:
        return self._queries.find_callers(symbol, depth)


class _ImportGraphView:
    """Satisfies change_planner.predictor.ImportGraph protocol over real import edges."""

    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import RepoGraphQueries

        self._queries = RepoGraphQueries(scan.call_edges, scan.import_edges_by_file)

    def find_importers(self, file_path: str, include_type: bool = False) -> list[tuple[str, str]]:
        result = self._queries.find_importers(file_path, include_type=True)
        return result  # type: ignore[return-value]


class _SymbolRegistryView:
    def __init__(self, scan: ScanResult) -> None:
        from repo_intelligence.graph_queries import SymbolIndex

        self._index = SymbolIndex(scan.symbols_by_file)

    def symbols_in_file(self, file_path: str) -> list[str]:
        return self._index.symbols_in_file(file_path)


class CliCommands:
    def plan(self, intent: str, **kwargs: Any) -> CliReport:
        """ortho plan <intent>"""
        return CliReport(
            title=f"Feature Plan: {intent}",
            content=f"Planning feature: {intent}\n\nPath 1: Simple approach\nPath 2: Robust approach\nPath 3: Optimized approach",
            success=True,
        )

    def refactor(self, path: str = None, **kwargs: Any) -> CliReport:
        """ortho refactor [path]"""
        return CliReport(
            title=f"Refactoring: {path or 'All'}",
            content=f"Refactoring recommendations for {path or 'entire codebase'}:\n\n[HIGH] Issue 1\n[MEDIUM] Issue 2",
            success=True,
        )

    def guardrails(self, path: str | None = None, **kwargs: Any) -> CliReport:
        """ortho guardrails check [path]"""
        target = path or "."
        try:
            scan = scan_repository(target)
        except FileNotFoundError as e:
            return CliReport(
                title=f"Architecture Check: {target}",
                content=str(e),
                success=False,
            )
        except Exception as e:
            return CliReport(
                title=f"Architecture Check: {target}",
                content=f"Scan failed: {e}",
                success=False,
            )

        arch_model_adapter = ArchModelAdapter(scan.arch_model, scan.file_to_module)
        dep_graph = DependencyGraphAdapter(scan.import_edges_by_file, scan.file_to_module)
        from repo_intelligence.graph_queries import CodeMetricsAdapter

        metrics = CodeMetricsAdapter(scan.file_to_module)

        enforcer = ArchitectureEnforcer(arch_model_adapter, dep_graph, metrics)
        violations = enforcer.check_violations()

        if not violations:
            content = f"Scanned {len(scan.file_to_module)} file(s). No violations found."
        else:
            lines = [
                f"[{v.severity}] {v.rule_id} at {v.location}: {v.message} -> {v.suggested_fix}"
                for v in violations
            ]
            content = "\n".join(lines)

        return CliReport(
            title=f"Architecture Check: {target}",
            content=content,
            success=True,
        )

    def decide(self, intent: str, **kwargs: Any) -> CliReport:
        """ortho decide <intent>"""
        if not intent:
            return CliReport(
                title="Decision: (empty)",
                content="Cannot decide on an empty intent.",
                success=False,
            )

        candidate_path = Path(intent)
        is_file_intent = candidate_path.is_file()

        scan_target = str(candidate_path.parent) if is_file_intent else str(kwargs.get("scan_path", "."))
        try:
            scan = scan_repository(scan_target)
        except FileNotFoundError as e:
            return CliReport(title=f"Decision: {intent}", content=str(e), success=False)
        except Exception as e:
            return CliReport(title=f"Decision: {intent}", content=f"Scan failed: {e}", success=False)

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

        alt_titles = [opt.title for opt in decision.options if opt is not decision.recommended_option]
        content = f"Decision for: {intent}\n\nRecommended: {decision.recommended_option.title}\n{decision.reasoning}"
        if alt_titles:
            content += f"\nAlternatives: {', '.join(alt_titles)}"

        return CliReport(
            title=f"Decision: {intent}",
            content=content,
            success=True,
        )
