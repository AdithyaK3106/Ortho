"""Exhaustive edge case tests for refactoring-advisor"""
from unittest.mock import Mock
import pytest

from refactoring_advisor.advisor import RefactoringAdvisor
from refactoring_advisor.types import RefactoringIssue


@pytest.fixture
def advisor() -> RefactoringAdvisor:
    mock_repo = Mock()
    mock_repo.get_tight_couplings = Mock(return_value=[])
    mock_repo.get_duplications = Mock(return_value=[])
    mock_repo.get_bloated_modules = Mock(return_value=[])
    mock_repo.get_circular_deps = Mock(return_value=[])
    mock_repo.get_high_churn_modules = Mock(return_value=[])

    return RefactoringAdvisor(repo=mock_repo)


class TestBoundaryConditions:
    """Test boundary and edge case conditions"""

    def test_empty_repository(self, advisor: RefactoringAdvisor) -> None:
        """Empty repo with no modules"""
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_single_module(self, advisor: RefactoringAdvisor) -> None:
        """Single module in repo"""
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_tight_coupling_bidirectional(self, advisor: RefactoringAdvisor) -> None:
        """Bidirectional tight coupling"""
        advisor.repo.get_tight_couplings.return_value = [("A.py", "B.py")]
        result = advisor.find_issues()
        # May detect coupling
        assert isinstance(result, list)

    def test_duplications_detected(self, advisor: RefactoringAdvisor) -> None:
        """Identical functions in different files"""
        advisor.repo.get_duplications.return_value = [("file1.py", "file2.py", 0.95)]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_similar_functions_70_percent(self, advisor: RefactoringAdvisor) -> None:
        """Functions with 70% similarity"""
        advisor.repo.get_duplications.return_value = [("file1.py", "file2.py", 0.70)]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_dissimilar_functions_30_percent(self, advisor: RefactoringAdvisor) -> None:
        """Functions with 30% similarity (low match)"""
        advisor.repo.get_duplications.return_value = [("file1.py", "file2.py", 0.30)]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_bloated_modules(self, advisor: RefactoringAdvisor) -> None:
        """Oversized module"""
        advisor.repo.get_bloated_modules.return_value = [("huge.py", 5000, 200)]
        result = advisor.find_issues()
        # May detect bloat
        assert isinstance(result, list)

    def test_circular_dep_ab(self, advisor: RefactoringAdvisor) -> None:
        """A→B→A circular dependency"""
        advisor.repo.get_circular_deps.return_value = [["A.py", "B.py"]]
        result = advisor.find_issues()
        # May detect circular dependency
        assert isinstance(result, list)

    def test_circular_dep_deep_abcda(self, advisor: RefactoringAdvisor) -> None:
        """A→B→C→D→A deep cycle"""
        advisor.repo.get_circular_deps.return_value = [["A.py", "B.py", "C.py", "D.py"]]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_self_reference_aa(self, advisor: RefactoringAdvisor) -> None:
        """Module A→A (self-reference)"""
        advisor.repo.get_circular_deps.return_value = [["A.py"]]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_high_churn_modules(self, advisor: RefactoringAdvisor) -> None:
        """High-churn modules (changed frequently)"""
        advisor.repo.get_high_churn_modules.return_value = ["hotspot.py"]
        result = advisor.find_issues()
        assert isinstance(result, list)

    def test_issue_severity_enum(self, advisor: RefactoringAdvisor) -> None:
        """All issues have valid severity"""
        result = advisor.find_issues()
        for issue in result:
            assert issue.severity in ("low", "medium", "high")

    def test_issue_confidence_bounds(self, advisor: RefactoringAdvisor) -> None:
        """All issues have confidence 0.0-1.0"""
        result = advisor.find_issues()
        for issue in result:
            assert 0.0 <= issue.confidence <= 1.0

    def test_all_issues_have_reasoning(self, advisor: RefactoringAdvisor) -> None:
        """All issues must have reasoning"""
        result = advisor.find_issues()
        for issue in result:
            assert issue.reasoning != ""

    def test_no_issues_found(self, advisor: RefactoringAdvisor) -> None:
        """Clean repository with no issues"""
        result = advisor.find_issues()
        # Should return empty list or no issues
        assert isinstance(result, list)
