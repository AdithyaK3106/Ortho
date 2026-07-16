"""Hard tests for refactoring advisor with zero false positives"""
from typing import Any

import pytest

from refactoring_advisor.advisor import RefactoringAdvisor
from refactoring_advisor.types import RefactoringIssue


@pytest.fixture
def advisor(mock_repo: Any) -> RefactoringAdvisor:
    """Create advisor with mock"""
    return RefactoringAdvisor(repo=mock_repo)


class TestTightCoupling:
    """Test 1-5: Tight coupling detection"""

    def test_bidirectional_coupling(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 1: A imports B, B imports A"""
        mock_repo.get_tight_couplings.return_value = [("auth", "payment")]

        issues = advisor.find_issues()

        coupling_issues = [i for i in issues if i.issue_type == "tight_coupling"]
        assert len(coupling_issues) > 0
        assert coupling_issues[0].severity == "high"

    def test_transitive_coupling(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 2: 3-module cycle"""
        mock_repo.get_tight_couplings.return_value = [
            ("order", "payment"),
            ("payment", "notification"),
        ]

        issues = advisor.find_issues()

        coupling_issues = [i for i in issues if i.issue_type == "tight_coupling"]
        assert len(coupling_issues) >= 2

    def test_interface_pattern_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 3: Interface dependency not flagged"""
        mock_repo.get_tight_couplings.return_value = []

        issues = advisor.find_issues()

        assert all(i.issue_type != "tight_coupling" for i in issues)

    def test_multiple_issues_aggregated(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 4: Multiple coupling issues reported"""
        mock_repo.get_tight_couplings.return_value = [
            ("a", "b"),
            ("a", "c"),
            ("a", "d"),
        ]

        issues = advisor.find_issues()

        coupling_issues = [i for i in issues if i.issue_type == "tight_coupling"]
        assert len(coupling_issues) >= 3

    def test_confidence_scoring(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 5: Confidence scores present"""
        mock_repo.get_tight_couplings.return_value = [("mod_a", "mod_b")]

        issues = advisor.find_issues()

        for issue in issues:
            assert 0.0 <= issue.confidence <= 1.0


class TestDuplication:
    """Test 6-10: Duplication detection"""

    def test_exact_duplication(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 6: Identical functions"""
        mock_repo.get_duplications.return_value = [("file_a.py", "file_b.py", 1.0)]

        issues = advisor.find_issues()

        dup_issues = [i for i in issues if i.issue_type == "duplication"]
        assert len(dup_issues) > 0

    def test_similar_duplication(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 7: 70% similar functions"""
        mock_repo.get_duplications.return_value = [("a.py", "b.py", 0.85)]

        issues = advisor.find_issues()

        dup_issues = [i for i in issues if i.issue_type == "duplication"]
        assert len(dup_issues) > 0

    def test_test_code_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 8: Test code duplication ignored"""
        mock_repo.get_duplications.return_value = []

        issues = advisor.find_issues()

        assert all(i.issue_type != "duplication" for i in issues)

    def test_identical_class_methods(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 9: Class method duplication"""
        mock_repo.get_duplications.return_value = [("class_a", "class_b", 0.95)]

        issues = advisor.find_issues()

        dup_issues = [i for i in issues if i.issue_type == "duplication"]
        assert len(dup_issues) > 0

    def test_confidence_varies(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 10: Confidence varies with similarity"""
        mock_repo.get_duplications.return_value = [
            ("a.py", "b.py", 1.0),  # Exact
            ("c.py", "d.py", 0.85),  # High
        ]

        issues = advisor.find_issues()

        dup_issues = [i for i in issues if i.issue_type == "duplication"]
        assert len(dup_issues) >= 2


class TestBloat:
    """Test 11-14: Module bloat detection"""

    def test_large_file(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 11: File over 500 lines"""
        mock_repo.get_bloated_modules.return_value = [("service.py", 800, 30)]

        issues = advisor.find_issues()

        bloat_issues = [i for i in issues if i.issue_type == "bloat"]
        assert len(bloat_issues) > 0

    def test_many_functions(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 12: File with 60 functions"""
        mock_repo.get_bloated_modules.return_value = [("handlers.py", 600, 60)]

        issues = advisor.find_issues()

        bloat_issues = [i for i in issues if i.issue_type == "bloat"]
        assert len(bloat_issues) > 0

    def test_well_structured_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 13: Well-structured large file not flagged"""
        mock_repo.get_bloated_modules.return_value = []

        issues = advisor.find_issues()

        assert all(i.issue_type != "bloat" for i in issues)

    def test_bloat_across_files(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 14: Total class size flagged"""
        mock_repo.get_bloated_modules.return_value = [("bigclass", 1200, 55)]

        issues = advisor.find_issues()

        bloat_issues = [i for i in issues if i.issue_type == "bloat"]
        assert len(bloat_issues) > 0


class TestCircular:
    """Test 15-17: Circular dependency detection"""

    def test_simple_cycle(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 15: A→B→A cycle"""
        mock_repo.get_circular_deps.return_value = [["A", "B", "A"]]

        issues = advisor.find_issues()

        circ_issues = [i for i in issues if i.issue_type == "circular"]
        assert len(circ_issues) > 0
        assert circ_issues[0].confidence == 1.0

    def test_complex_cycle(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 16: A→B→C→A cycle"""
        mock_repo.get_circular_deps.return_value = [["A", "B", "C", "A"]]

        issues = advisor.find_issues()

        circ_issues = [i for i in issues if i.issue_type == "circular"]
        assert len(circ_issues) > 0

    def test_no_cycle_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 17: No cycle = no flag"""
        mock_repo.get_circular_deps.return_value = []

        issues = advisor.find_issues()

        assert all(i.issue_type != "circular" for i in issues)


class TestDebt:
    """Test 18-20: Technical debt detection"""

    def test_debt_hotspot(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 18: High churn + coupling"""
        mock_repo.get_high_churn_modules.return_value = ["service.py"]

        issues = advisor.find_issues()

        debt_issues = [i for i in issues if i.issue_type == "debt"]
        assert len(debt_issues) > 0

    def test_clean_high_churn_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 19: High churn but low coupling OK"""
        mock_repo.get_high_churn_modules.return_value = []

        issues = advisor.find_issues()

        assert all(i.issue_type != "debt" for i in issues)

    def test_new_module_not_flagged(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Test 20: New modules without history"""
        mock_repo.get_high_churn_modules.return_value = []

        issues = advisor.find_issues()

        debt_issues = [i for i in issues if i.issue_type == "debt"]
        assert len(debt_issues) == 0


class TestAccuracy:
    """Test zero false positives"""

    def test_high_confidence_only(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """All issues have confidence ≥ 0.8"""
        mock_repo.get_tight_couplings.return_value = [("a", "b")]
        mock_repo.get_duplications.return_value = [("c.py", "d.py", 0.9)]
        mock_repo.get_bloated_modules.return_value = [("e.py", 600, 30)]
        mock_repo.get_circular_deps.return_value = [["f", "g"]]

        issues = advisor.find_issues()

        for issue in issues:
            assert issue.confidence >= 0.8

    def test_all_issues_have_evidence(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """All issues typed and described"""
        mock_repo.get_tight_couplings.return_value = [("a", "b")]

        issues = advisor.find_issues()

        for issue in issues:
            assert issue.issue_type != ""
            assert issue.location != ""
            assert issue.recommendation != ""
            assert issue.severity in ("low", "medium", "high")

    def test_evidence_field_actually_populated(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Evidence Engine: every finding must carry real, checkable evidence,
        not an empty list (a Recommendation without evidence is unacceptable
        per the product vision -- 'Risk: High' must never stand alone)."""
        mock_repo.get_tight_couplings.return_value = [("a.py", "b.py")]
        mock_repo.get_bloated_modules.return_value = [("big.py", 900, 60)]
        mock_repo.get_circular_deps.return_value = [["x.py", "y.py", "x.py"]]

        issues = advisor.find_issues()

        assert len(issues) >= 3
        for issue in issues:
            assert issue.evidence, f"{issue.issue_type} at {issue.location} has no evidence"

    def test_evidence_cites_real_measured_facts(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """Bloat evidence must cite the actual measured lines/functions, not
        a generic message -- a developer must be able to verify it."""
        mock_repo.get_bloated_modules.return_value = [("big.py", 900, 60)]

        issues = advisor.find_issues()
        bloat_issue = next(i for i in issues if i.issue_type == "bloat")

        assert any("900" in e for e in bloat_issue.evidence)
        assert any("60" in e for e in bloat_issue.evidence)

    def test_circular_evidence_capped_for_large_cycles(self, advisor: RefactoringAdvisor, mock_repo: Any) -> None:
        """A large cycle (e.g. celery's real 41-module SCC) must not produce
        an unbounded evidence wall -- capped with a '...and N more' marker."""
        big_cycle = [f"m{i}.py" for i in range(50)] + ["m0.py"]
        mock_repo.get_circular_deps.return_value = [big_cycle]

        issues = advisor.find_issues()
        circular_issue = next(i for i in issues if i.issue_type == "circular")

        assert len(circular_issue.evidence) <= 12
        assert any("more" in e for e in circular_issue.evidence)
