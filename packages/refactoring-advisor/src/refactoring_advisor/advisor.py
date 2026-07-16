from typing import Protocol

from refactoring_advisor.types import RefactoringIssue


class CodeRepository(Protocol):  # pragma: no cover
    """Protocol for code analysis data"""

    def get_tight_couplings(self) -> list[tuple[str, str]]:
        """Get bidirectional dependencies"""
        ...

    def get_duplications(self) -> list[tuple[str, str, float]]:
        """Get similar code patterns (file, file, similarity)"""
        ...

    def get_bloated_modules(self) -> list[tuple[str, int, int]]:
        """Get oversized modules (module, lines, functions)"""
        ...

    def get_circular_deps(self) -> list[list[str]]:
        """Get circular dependency cycles"""
        ...

    def get_high_churn_modules(self) -> list[str]:
        """Get high-churn modules"""
        ...


class RefactoringAdvisor:
    def __init__(self, repo: CodeRepository) -> None:
        self.repo = repo

    def find_issues(self) -> list[RefactoringIssue]:
        """
        Find all refactoring opportunities.
        Returns high-confidence issues (>0.8).
        """
        issues: list[RefactoringIssue] = []

        # Detect tight coupling
        for module_a, module_b in self.repo.get_tight_couplings():
            issues.append(RefactoringIssue(
                issue_type="tight_coupling",
                location=f"{module_a} ↔ {module_b}",
                severity="high",
                recommendation="Extract shared interface",
                estimated_effort="4-8 hours",
                confidence=0.92,
                false_positive_risk="Low (explicit 2-way imports)",
                evidence=[
                    f"{module_a} imports {module_b}",
                    f"{module_b} imports {module_a}",
                    "bidirectional import edge found in the dependency graph",
                ],
            ))

        # Detect duplications
        for file_a, file_b, similarity in self.repo.get_duplications():
            if similarity >= 0.70:
                issues.append(RefactoringIssue(
                    issue_type="duplication",
                    location=f"{file_a} ↔ {file_b}",
                    severity="medium",
                    recommendation="Extract shared function",
                    estimated_effort="2-4 hours",
                    confidence=min(0.95, similarity),
                    false_positive_risk=f"Low ({similarity:.0%} match)",
                    evidence=[
                        f"structural similarity: {similarity:.0%}",
                        f"{file_a} and {file_b} matched by AST comparison",
                    ],
                ))

        # Detect bloat
        for module, lines, functions in self.repo.get_bloated_modules():
            severity = "high" if lines > 800 or functions > 50 else "medium"
            issues.append(RefactoringIssue(
                issue_type="bloat",
                location=module,
                severity=severity,
                recommendation="Split into focused modules",
                estimated_effort="1-2 days",
                confidence=1.0,
                false_positive_risk="Medium (well-structured large files OK)",
                evidence=[
                    f"{module} measured at {lines} lines",
                    f"{module} measured at {functions} functions",
                ],
            ))

        # Detect circular deps
        for cycle in self.repo.get_circular_deps():
            edges_in_cycle = [f"{cycle[i]} → {cycle[i + 1]}" for i in range(len(cycle) - 1)]
            shown_edges = edges_in_cycle[:10]
            cycle_evidence = [f"{len(cycle) - 1}-module cycle: {len(set(cycle))} distinct modules"]
            cycle_evidence.extend(f"real import edge: {edge}" for edge in shown_edges)
            if len(edges_in_cycle) > len(shown_edges):
                cycle_evidence.append(f"...and {len(edges_in_cycle) - len(shown_edges)} more edges in this cycle")
            issues.append(RefactoringIssue(
                issue_type="circular",
                location=" → ".join(cycle),
                severity="high",
                recommendation="Break cycle or extract abstraction",
                estimated_effort="4-8 hours",
                confidence=1.0,
                false_positive_risk="None (deterministic)",
                evidence=cycle_evidence,
            ))

        # Detect debt hotspots
        for module in self.repo.get_high_churn_modules():
            issues.append(RefactoringIssue(
                issue_type="debt",
                location=module,
                severity="medium",
                recommendation="Prioritize for refactoring",
                estimated_effort="TBD",
                confidence=0.85,
                false_positive_risk="Medium (new projects have low history)",
                evidence=[f"{module} flagged as high-churn (frequent recent changes)"],
            ))

        # Filter high-confidence only
        high_conf = [i for i in issues if i.confidence >= 0.8]

        # Sort by severity + confidence
        high_conf.sort(key=lambda i: (
            {"high": 0, "medium": 1, "low": 2}[i.severity],
            -i.confidence
        ))

        return high_conf
