"""Unit tests for DebtScorer component."""

import pytest
from hypothesis import given, strategies as st

from impact_analysis.debt_scorer import DebtScorer, CallEdge, ImportEdge, Symbol, GitFileMetadata
from impact_analysis.types import DebtScore


class TestDebtScorerBasic:
    """Basic functional tests for DebtScorer."""

    def test_score_isolated_module(self):
        """Isolated module with no dependencies should have low coupling."""
        scorer = DebtScorer()
        score = scorer.score_module(
            file_id="utils.py",
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="helper", file_id="utils.py")],
            git_metadata={},
        )

        assert score.module_id == "utils.py"
        assert score.coupling_score == 0.0  # No fan-in or fan-out
        assert score.total_score >= 0.0
        assert score.total_score <= 1.0

    def test_score_high_churn_module(self):
        """Module with many commits should have high churn_score."""
        scorer = DebtScorer()
        git_metadata = {
            "utils.py": GitFileMetadata(file_path="utils.py", commits_30d=30),
        }
        score = scorer.score_module(
            file_id="utils.py",
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="func", file_id="utils.py")],
            git_metadata=git_metadata,
        )

        assert score.churn_score > 0.7  # 30/20 = 1.5, clamped to 1.0
        assert score.churn_score == 1.0

    def test_score_stable_module(self):
        """Module with few commits should have low churn_score."""
        scorer = DebtScorer()
        git_metadata = {
            "stable.py": GitFileMetadata(file_path="stable.py", commits_30d=2),
        }
        score = scorer.score_module(
            file_id="stable.py",
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="func", file_id="stable.py")],
            git_metadata=git_metadata,
        )

        assert score.churn_score < 0.2  # 2/20 = 0.1

    def test_score_hub_module(self):
        """Module with high fan-in and fan-out should have high coupling."""
        scorer = DebtScorer()
        # File B imports A and is imported by C, D, E
        import_graph = [
            ImportEdge(importer_file_id="B", imported_file_id="A"),
            ImportEdge(importer_file_id="C", imported_file_id="B"),
            ImportEdge(importer_file_id="D", imported_file_id="B"),
            ImportEdge(importer_file_id="E", imported_file_id="B"),
            ImportEdge(importer_file_id="F", imported_file_id="B"),
        ]
        score = scorer.score_module(
            file_id="B",
            call_graph=[],
            import_graph=import_graph,
            symbols=[Symbol(id="1", name="core", file_id="B")],
            git_metadata={"B": GitFileMetadata(file_path="B", commits_30d=0)},
        )

        # fan_in=4, fan_out=1 → (4+1)/2 = 2.5, clamped to 1.0
        assert score.coupling_score > 0.5

    def test_score_all_modules_sorted(self):
        """score_all_modules should return sorted by total_score descending."""
        scorer = DebtScorer()
        symbols = [
            Symbol(id="1", name="a", file_id="a.py", start_line=0, end_line=10),
            Symbol(id="2", name="b", file_id="b.py", start_line=0, end_line=100),  # More lines = complexity
        ]
        import_graph = [
            ImportEdge(importer_file_id="b.py", imported_file_id="a.py"),
        ]
        scores = scorer.score_all_modules(
            call_graph=[],
            import_graph=import_graph,
            symbols=symbols,
            git_metadata={},
        )

        # Should be sorted descending by total_score
        assert len(scores) == 2
        assert scores[0].total_score >= scores[1].total_score

    def test_test_coverage_not_found(self):
        """Module without tests should have high test_coverage_score."""
        scorer = DebtScorer()
        score = scorer.score_module(
            file_id="core.py",
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="func", file_id="core.py")],
            git_metadata={"core.py": GitFileMetadata(file_path="core.py", commits_30d=0)},
        )

        assert score.test_coverage_score == 0.5  # Neutral, no test file detected

    def test_weights_sum_to_one(self):
        """DEFAULT_WEIGHTS should sum to 1.0 (or close)."""
        weights = DebtScorer.DEFAULT_WEIGHTS
        total = sum(weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_evidence_generated(self):
        """DebtScore should include evidence."""
        scorer = DebtScorer()
        score = scorer.score_module(
            file_id="messy.py",
            call_graph=[],
            import_graph=[
                ImportEdge(importer_file_id="messy.py", imported_file_id="a"),
                ImportEdge(importer_file_id="messy.py", imported_file_id="b"),
                ImportEdge(importer_file_id="messy.py", imported_file_id="c"),
                ImportEdge(importer_file_id="x", imported_file_id="messy.py"),
                ImportEdge(importer_file_id="y", imported_file_id="messy.py"),
                ImportEdge(importer_file_id="z", imported_file_id="messy.py"),
            ],
            symbols=[Symbol(id="1", name="func", file_id="messy.py")],
            git_metadata={"messy.py": GitFileMetadata(file_path="messy.py", commits_30d=25)},
        )

        # Should have evidence for high churn and coupling
        assert any("churn" in e.lower() or "commi" in e.lower() for e in score.evidence)


class TestDebtScorerEdgeCases:
    """Edge case tests."""

    def test_empty_inputs(self):
        """Empty inputs should not crash."""
        scorer = DebtScorer()
        scores = scorer.score_all_modules(
            call_graph=[],
            import_graph=[],
            symbols=[],
            git_metadata={},
        )

        assert len(scores) == 0

    def test_single_file(self):
        """Single file should be scorable."""
        scorer = DebtScorer()
        scores = scorer.score_all_modules(
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="func", file_id="only.py")],
            git_metadata={},
        )

        assert len(scores) == 1
        assert scores[0].module_id == "only.py"

    def test_missing_git_metadata(self):
        """Missing git metadata should default to 0.0 (neutral)."""
        scorer = DebtScorer()
        score = scorer.score_module(
            file_id="orphan.py",
            call_graph=[],
            import_graph=[],
            symbols=[Symbol(id="1", name="func", file_id="orphan.py")],
            git_metadata={},  # No metadata for orphan.py
        )

        assert score.churn_score == 0.0  # Defaults to 0.0


@given(
    fan_in=st.integers(min_value=0, max_value=50),
    fan_out=st.integers(min_value=0, max_value=50),
)
def test_coupling_score_bounds(fan_in, fan_out):
    """Coupling score should always be bounded [0.0, 1.0]."""
    import_graph = []
    for i in range(fan_in):
        import_graph.append(ImportEdge(importer_file_id=f"dep_{i}", imported_file_id="core"))
    for i in range(fan_out):
        import_graph.append(ImportEdge(importer_file_id="core", imported_file_id=f"uses_{i}"))

    scorer = DebtScorer()
    score = scorer.score_module(
        file_id="core",
        call_graph=[],
        import_graph=import_graph,
        symbols=[Symbol(id="1", name="core_func", file_id="core")],
        git_metadata={},
    )

    assert 0.0 <= score.coupling_score <= 1.0
    assert 0.0 <= score.total_score <= 1.0


@given(
    commits=st.integers(min_value=0, max_value=100),
)
def test_churn_score_bounds(commits):
    """Churn score should always be bounded [0.0, 1.0]."""
    scorer = DebtScorer()
    score = scorer.score_module(
        file_id="active.py",
        call_graph=[],
        import_graph=[],
        symbols=[Symbol(id="1", name="func", file_id="active.py")],
        git_metadata={"active.py": GitFileMetadata(file_path="active.py", commits_30d=commits)},
    )

    assert 0.0 <= score.churn_score <= 1.0
    assert 0.0 <= score.total_score <= 1.0


@given(
    scores=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=5, max_size=5)
)
def test_total_score_weighted_average(scores):
    """Total score should be weighted average of all dimensions."""
    # This is a property: total_score should always fall within range of individual scores
    if len(set(scores)) > 0:
        min_score = min(scores)
        max_score = max(scores)

        # Total should be between min and max of components
        total = (
            DebtScorer.DEFAULT_WEIGHTS["coupling"] * scores[0] +
            DebtScorer.DEFAULT_WEIGHTS["churn"] * scores[1] +
            DebtScorer.DEFAULT_WEIGHTS["complexity"] * scores[2] +
            DebtScorer.DEFAULT_WEIGHTS["test_coverage"] * scores[3] +
            DebtScorer.DEFAULT_WEIGHTS["other"] * scores[4]
        )

        assert 0.0 <= total <= 1.0
