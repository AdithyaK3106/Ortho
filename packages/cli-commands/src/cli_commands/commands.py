from pathlib import Path
from typing import Any

from arch_guardrails.enforcer import ArchitectureEnforcer
from arch_intelligence.model_adapter import ArchModelAdapter
from change_planner.predictor import ChangePredictor
from change_planner.types import ImpactPrediction
from decision_engine.engine import DecisionEngine
from feature_planner.planner import FeaturePlanner
from refactoring_advisor.advisor import RefactoringAdvisor

from cli_commands.cross_repo import CrossRepoMatch, find_cross_repo_reuse
from cli_commands.dependency_graph_adapter import DependencyGraphAdapter
from cli_commands.feature_plan_adapter import FeaturePlannerArchModelAdapter
from cli_commands.feedback import lookup_feedback, record_feedback
from cli_commands.refactor_adapter import CodeRepositoryAdapter
from cli_commands.repo_qa import answer_question
from cli_commands.repo_scanner import ScanResult, scan_repository
from cli_commands.test_recommender import TestRecommendation, recommend_tests
from cli_commands.types import CliReport
from cli_commands.workflow_capture import capture_workflow_run, cite_prior_findings

# Evidence lines are capped per finding so one large finding (a 40-module
# cycle, a huge bloated file) can't drown a report meant to be human-readable.
_MAX_EVIDENCE_LINES = 5


def _format_evidence(evidence: Any) -> str:
    """Render a finding's evidence list as indented checkmark lines, per the
    product vision's evidence format ("Risk: High" must never stand alone --
    every claim needs a reason a reader can independently verify). Empty
    input renders nothing, not a placeholder -- an unpopulated evidence list
    should be visibly absent, not papered over."""
    if not evidence:
        return ""
    shown = list(evidence)[:_MAX_EVIDENCE_LINES]
    lines = "\n".join(f"    ✓ {e}" for e in shown)
    if len(evidence) > len(shown):
        lines += f"\n    ...and {len(evidence) - len(shown)} more"
    return lines


# Matches workflow_capture.cite_prior_findings' own cap -- a report is
# meant to be read, not drowned in memory citations regardless of which
# citation source (explicit feedback vs. fuzzy prior-run match) fired.
_MAX_TOTAL_CITATIONS = 3


def _citations_for(target: str, finding_keys: list[str]) -> list[str]:
    """Memory citations for a set of findings: exact accept/reject feedback
    first ("rejected before, here's why" -- the roadmap's stated moat),
    falling back to cite_prior_findings' fuzzy "seen before" for findings
    with no recorded feedback. A finding with both only shows the feedback
    line -- it's strictly more informative than "seen before" once a
    developer has actually made a decision on it."""
    lines: list[str] = []
    unresolved: list[str] = []
    for key in finding_keys:
        if len(lines) >= _MAX_TOTAL_CITATIONS:
            break
        feedback_line = lookup_feedback(target, key)
        if feedback_line:
            lines.append(feedback_line)
        else:
            unresolved.append(key)

    remaining = _MAX_TOTAL_CITATIONS - len(lines)
    if unresolved and remaining > 0:
        lines.extend(cite_prior_findings(target, unresolved)[:remaining])
    return lines


def _format_test_recommendations(recommendations: list[TestRecommendation]) -> str:
    """Test Intelligence output: which real tests exist for the affected
    modules, and which modules have none -- a coverage gap the reviewer
    should know about before merging, per the roadmap's Test Intelligence
    capability (recommended tests + missing coverage)."""
    covered = [r for r in recommendations if r.has_coverage]
    gaps = [r for r in recommendations if not r.has_coverage]

    lines = ["Recommended tests:"]
    if covered:
        for r in covered:
            lines.append(f"  - {r.affected_module}: run {', '.join(r.test_modules)}")
    if gaps:
        lines.append("  Coverage gaps (no test module found):")
        for r in gaps:
            lines.append(f"    - {r.affected_module}")
    if not covered and not gaps:
        return ""
    return "\n".join(lines)


# Cross-repo AST comparison is O(symbols^2) within similarity buckets across
# every repo combined -- caps output to a readable size regardless of how
# many clusters two large real repos happen to produce.
_MAX_CROSS_REPO_MATCHES = 20


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
            lines = []
            for i in issues:
                lines.append(
                    f"[{i.severity}] {i.issue_type} at {i.location}: {i.recommendation} "
                    f"(effort={i.estimated_effort}, confidence={i.confidence:.2f})"
                )
                evidence_block = _format_evidence(i.evidence)
                if evidence_block:
                    lines.append(evidence_block)
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
            lines = []
            for v in filtered_violations:
                lines.append(f"[{v.severity}] {v.rule_id} at {v.location}: {v.message} -> {v.suggested_fix}")
                evidence_block = _format_evidence(v.evidence)
                if evidence_block:
                    lines.append(evidence_block)
            content = "\n".join(lines)
            if filter_count > 0:
                content += f"\n\n(Scanned {len(scan.file_to_module)} file(s). {len(filtered_violations)} violation(s) found ({filter_count} filtered by severity).)"
            else:
                content = f"Scanned {len(scan.file_to_module)} file(s). {len(filtered_violations)} violation(s) found.\n\n" + content

            # Memory citations: has any of these findings shown up in a prior
            # run of this repo, or been explicitly accepted/rejected?
            # Queried BEFORE this run's own capture_workflow_run() call
            # below, so a finding never cites itself.
            queries = list(dict.fromkeys(f"{v.rule_id} {v.location}" for v in filtered_violations))
            citations = _citations_for(target, queries)
            if citations:
                content += "\n\n" + "\n".join(citations)

        report = CliReport(
            title=f"Architecture Check: {target}",
            content=content,
            success=True,
            violations=filtered_violations,
        )
        capture_workflow_run(target, "guardrails", target, report)
        return report

    def review(self, path: str | None = None, **kwargs: Any) -> CliReport:
        """ortho review [path] -- unified guardrails + decision summary, one scan."""
        target = path or "."
        severity_filter = kwargs.get("severity_filter")
        if severity_filter is not None and severity_filter not in ("error", "warning"):
            raise ValueError(f"severity_filter must be 'error' or 'warning', got '{severity_filter}'")

        try:
            scan = scan_repository(target)
        except FileNotFoundError as e:
            report = CliReport(title=f"Review: {target}", content=str(e), success=False)
            capture_workflow_run(target, "review", target, report)
            return report
        except Exception as e:
            report = CliReport(title=f"Review: {target}", content=f"Scan failed: {e}", success=False)
            capture_workflow_run(target, "review", target, report)
            return report

        arch_model_adapter = ArchModelAdapter(scan.arch_model, scan.file_to_module)
        dep_graph = DependencyGraphAdapter(scan.import_edges_by_file, scan.file_to_module)
        from repo_intelligence.graph_queries import CodeMetricsAdapter

        metrics = CodeMetricsAdapter(scan.file_to_module)
        enforcer = ArchitectureEnforcer(arch_model_adapter, dep_graph, metrics)
        violations = enforcer.check_violations()

        filtered_violations = violations
        filter_count = 0
        if severity_filter is not None:
            filtered_violations = [v for v in violations if v.severity == severity_filter]
            filter_count = len(violations) - len(filtered_violations)

        lines = [f"Scanned {len(scan.file_to_module)} file(s)."]
        if not filtered_violations:
            lines.append("No violations found.")
        else:
            lines.append(f"{len(filtered_violations)} violation(s) found" + (
                f" ({filter_count} filtered by severity)." if filter_count else "."
            ))
            lines.append("")
            for v in filtered_violations:
                lines.append(f"[{v.severity}] {v.rule_id} at {v.location}: {v.message} -> {v.suggested_fix}")
                evidence_block = _format_evidence(v.evidence)
                if evidence_block:
                    lines.append(evidence_block)

        if violations:
            engine = DecisionEngine()
            decision = engine.decide(
                intent=f"review {target}",
                sources={"arch_guardrails": violations},
            )
            lines.append("")
            lines.append(f"Recommended: {decision.recommended_option.title}\n{decision.reasoning}")
            evidence_block = _format_evidence(decision.recommended_option.evidence)
            if evidence_block:
                lines.append(evidence_block)

            # Test Intelligence: for the specific modules a violation was
            # found in (not every module in the repo -- that would be
            # expensive and unrelated to what's actually flagged), does a
            # real test module already exist? Location values include
            # multi-module cycle chains ("a → b → c"), so split on the
            # arrow and de-dup rather than treating the whole string as one
            # module name.
            def _is_test_module(module: str) -> bool:
                stem = module.rsplit(".", 1)[-1]
                return stem.startswith("test_") or stem.endswith("_test")

            flagged_modules = sorted({
                part.strip()
                for v in filtered_violations
                for part in v.location.split("→")
                if part.strip() in scan.file_to_module.values()
                # A module that IS itself a test file doesn't need a
                # recommended test -- excludes noise like "run a test for
                # this test module" when a violation's location includes a
                # test file (e.g. a real cycle running through the repo's
                # own test suite).
                and not _is_test_module(part.strip())
            })
            if flagged_modules:
                test_recs = recommend_tests(flagged_modules, scan.file_to_module)
                test_block = _format_test_recommendations(test_recs)
                if test_block:
                    lines.append("")
                    lines.append(test_block)

        # Memory citations, same discipline as guardrails()/decide(): queried
        # before this run's own capture_workflow_run() call so a finding
        # never cites itself.
        queries = list(dict.fromkeys(f"{v.rule_id} {v.location}" for v in filtered_violations))
        citations = _citations_for(target, queries)
        if citations:
            lines.append("")
            lines.extend(citations)

        report = CliReport(
            title=f"Review: {target}",
            content="\n".join(lines),
            success=True,
            violations=filtered_violations,
        )
        capture_workflow_run(target, "review", target, report)
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

        # An explicit scan_path from the caller always wins -- every real
        # caller (CLI, MCP server) passes --scan-path unconditionally, and
        # silently narrowing the scan to the changed file's own parent
        # directory instead ignores that explicit instruction. It also
        # breaks any repo where tests live in a sibling tests/ directory
        # (the common layout), since that directory falls outside the
        # narrowed scan and looks like a coverage gap that isn't real.
        # Falls back to the file's parent only when no scan_path was given
        # at all (bare programmatic call).
        explicit_scan_path = kwargs.get("scan_path")
        if explicit_scan_path is not None:
            scan_target = str(explicit_scan_path)
        elif is_file_intent:
            scan_target = str(candidate_path.parent)
        else:
            scan_target = "."
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
        test_recommendations: list[TestRecommendation] = []
        if is_file_intent:
            file_key = str(candidate_path.resolve())
            if file_key in scan.file_to_module:
                predictor = ChangePredictor(
                    call_graph=_CallGraphView(scan),
                    import_graph=_ImportGraphView(scan),
                    symbol_registry=_SymbolRegistryView(scan),
                    arch_model=arch_model_adapter,
                )
                prediction = predictor.predict_impact(file_key)
                impact_predictions = [prediction]
                changed_module = scan.file_to_module[file_key]
                test_recommendations = recommend_tests(
                    [changed_module, *prediction.affected_modules],
                    scan.file_to_module,
                )

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
        evidence_block = _format_evidence(recommended.evidence)
        if evidence_block:
            content += "\n" + evidence_block
        if test_recommendations:
            content += "\n\n" + _format_test_recommendations(test_recommendations)
        if alt_titles:
            content += f"\nAlternatives: {', '.join(alt_titles)}"
        if filter_count > 0:
            content += f"\n\n({filter_count} recommendation(s) filtered by confidence threshold.)"

        # Memory citations: same violations feed decide() as guardrails(), so
        # reuse them as citation queries -- has this repo's decision-relevant
        # evidence come up before, or been explicitly accepted/rejected?
        # Queried before this run's own capture_workflow_run() call below,
        # so a finding never cites itself.
        queries = list(dict.fromkeys(f"{v.rule_id} {v.location}" for v in violations))
        citations = _citations_for(scan_target, queries)
        if citations:
            content += "\n\n" + "\n".join(citations)

        report = CliReport(
            title=f"Decision: {intent}",
            content=content,
            success=True,
            recommendations=filtered_options,
        )
        capture_workflow_run(scan_target, "decide", intent, report)
        return report

    def feedback(
        self, repo_path: str, finding_key: str, decision: str, reason: str = ""
    ) -> CliReport:
        """ortho feedback accept|reject <finding_key> [--reason ...]

        finding_key should match the "{rule_id} {location}" text shown next
        to a finding in guardrails/decide/review output (e.g.
        "layer_boundaries src.api.views -> src.data.repo"). Recorded so a
        future run of the same finding cites the decision and reason
        directly ("rejected before, here's why"), not just "seen before".
        """
        if decision not in ("accept", "reject"):
            return CliReport(
                title=f"Feedback: {finding_key}",
                content=f"decision must be 'accept' or 'reject', got '{decision}'",
                success=False,
            )
        if not finding_key or not finding_key.strip():
            return CliReport(
                title="Feedback: (empty)",
                content="finding_key cannot be empty.",
                success=False,
            )

        repo_path_obj = Path(repo_path).resolve()
        if not repo_path_obj.is_dir():
            return CliReport(
                title=f"Feedback: {finding_key}",
                content=f"Repo path does not exist: {repo_path}",
                success=False,
            )

        ok = record_feedback(repo_path, finding_key, decision, reason)
        if not ok:
            return CliReport(
                title=f"Feedback: {finding_key}",
                content="Failed to record feedback (see logs).",
                success=False,
            )

        content = f"Recorded: {decision} for \"{finding_key}\""
        if reason:
            content += f"\nReason: {reason}"
        return CliReport(title=f"Feedback: {finding_key}", content=content, success=True)

    def ask(self, repo_path: str, question: str, **kwargs: Any) -> CliReport:
        """ortho ask <question> -- Repository Understanding: answer from
        real call/import graph structure, never fabricate. See repo_qa.py's
        module docstring for the design constraint this implements."""
        if not question or not question.strip():
            return CliReport(
                title="Ask: (empty)",
                content="Cannot answer an empty question.",
                success=False,
            )

        target = str(kwargs.get("scan_path", repo_path or "."))
        try:
            scan = scan_repository(target)
        except FileNotFoundError as e:
            report = CliReport(title=f"Ask: {question}", content=str(e), success=False)
            capture_workflow_run(target, "ask", question, report)
            return report
        except Exception as e:
            report = CliReport(title=f"Ask: {question}", content=f"Scan failed: {e}", success=False)
            capture_workflow_run(target, "ask", question, report)
            return report

        from repo_intelligence.graph_queries import RepoGraphQueries

        graph_queries = RepoGraphQueries(scan.call_edges, scan.import_edges_by_file)
        result = answer_question(question, scan.file_to_module, scan.symbols_by_file, graph_queries)

        if not result.answered:
            if result.keyword is None:
                content = "Could not extract a search term from that question."
            else:
                content = f"No evidence found for '{result.keyword}' in this repository."
            report = CliReport(title=f"Ask: {question}", content=content, success=True)
            capture_workflow_run(target, "ask", question, report)
            return report

        lines = [f"Matched {len(result.matched_files)} file(s) for '{result.keyword}':", ""]
        lines.extend(result.evidence)

        report = CliReport(title=f"Ask: {question}", content="\n".join(lines), success=True)
        capture_workflow_run(target, "ask", question, report)
        return report

    def cross_repo(self, repo_paths: list[str], **kwargs: Any) -> CliReport:
        """ortho cross-repo <path1> <path2> [...] -- shared/reusable code
        across 2-5 real repos, via real AST-structural similarity (never
        naming-based guesswork). See cross_repo.py's module docstring.
        No single scan_root exists for a multi-repo command, so this does
        not write a workflow_run memory artifact (same reasoning as plan()'s
        and decide()'s empty-intent early returns: capturing against one
        arbitrarily-chosen repo would misrepresent what was actually run)."""
        title = f"Cross-Repo: {', '.join(Path(p).name for p in repo_paths)}"

        try:
            matches = find_cross_repo_reuse(repo_paths, threshold=kwargs.get("threshold", 0.7))
        except ValueError as e:
            return CliReport(title=title, content=str(e), success=False)
        except FileNotFoundError as e:
            return CliReport(title=title, content=str(e), success=False)
        except Exception as e:
            return CliReport(title=title, content=f"Scan failed: {e}", success=False)

        if not matches:
            content = "No structurally similar code found across the given repositories."
        else:
            lines = [f"{len(matches)} cross-repo match(es):", ""]
            for m in matches[:_MAX_CROSS_REPO_MATCHES]:
                lines.append(
                    f"[{m.similarity:.0%}] {', '.join(m.repos)}: {' ~ '.join(m.symbol_ids[:2])}"
                    + (f" (+{len(m.symbol_ids) - 2} more)" if len(m.symbol_ids) > 2 else "")
                )
                evidence_block = _format_evidence(m.evidence)
                if evidence_block:
                    lines.append(evidence_block)
            if len(matches) > _MAX_CROSS_REPO_MATCHES:
                lines.append(f"...and {len(matches) - _MAX_CROSS_REPO_MATCHES} more match(es)")
            content = "\n".join(lines)

        return CliReport(title=title, content=content, success=True)

    def orchestrate(self, intent: str, **kwargs: Any) -> CliReport:
        """ortho orchestrate <intent> [--scan-path ...]

        Chains Ortho's own stages into one composed report: plan(intent)
        for implementation paths, decide(intent) for an architecture-aware
        recommendation, and review() for the current state of the target
        path's architecture health. This is NOT the roadmap's literal
        Planner->Architect->Builder->Reviewer->Verifier chain -- Ortho does
        not write code (Builder) or run tests against a real change
        (Verifier); those steps belong to the LLM/developer per the
        roadmap's own architecture diagram ("The LLM generates code. Ortho
        understands engineering."). What's real here is Ortho's own three
        stages run in sequence against one target, so a developer gets one
        report instead of three separate commands. The loop's final step
        (accept/reject via `feedback`) is deliberately NOT automated here:
        the roadmap's diagram shows "Developer approves" as an explicit
        human step, and Ortho advises, it does not decide for itself.
        """
        if not intent or not isinstance(intent, str) or not intent.strip():
            return CliReport(
                title="Orchestrate: (empty)",
                content="Cannot orchestrate for an empty or non-string intent.",
                success=False,
            )

        scan_target = str(kwargs.get("scan_path", "."))

        # Fail fast on an invalid target instead of running all three
        # stages just to report the same "path does not exist" error three
        # times, followed by human-next-step guidance that makes no sense
        # when nothing actually ran.
        if not Path(scan_target).is_dir():
            return CliReport(
                title=f"Orchestrate: {intent}",
                content=f"Path does not exist: {scan_target}",
                success=False,
            )

        plan_report = self.plan(intent, scan_path=scan_target)
        decide_report = self.decide(intent, scan_path=scan_target)
        review_report = self.review(scan_target)

        stages_ok = plan_report.success and decide_report.success and review_report.success

        lines = [
            f"Orchestration for: {intent}",
            f"Target: {scan_target}",
            "",
            "=== Stage 1: Plan (implementation paths) ===",
            plan_report.content,
            "",
            "=== Stage 2: Decide (architecture-aware recommendation) ===",
            decide_report.content,
            "",
            "=== Stage 3: Review (current architecture health) ===",
            review_report.content,
            "",
            "=== Next step (human decision, not automated) ===",
            "Ortho does not approve or merge changes. After implementing "
            "with your LLM of choice, re-run `ortho review` on the changed "
            "path, then record your decision on any finding with "
            "`ortho feedback accept|reject \"<rule_id> <location>\"` so "
            "future runs cite it.",
        ]

        report = CliReport(
            title=f"Orchestrate: {intent}",
            content="\n".join(lines),
            success=stages_ok,
        )
        # Each stage already called capture_workflow_run for itself (plan/
        # decide/review are real, independently-useful commands run here in
        # sequence) -- capturing the composed report too would duplicate
        # that memory under a fourth artifact for the same work, so this
        # wrapper intentionally does not call capture_workflow_run again.
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
