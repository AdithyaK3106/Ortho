"""Phase 5.3 Extended Coverage — Hard Benchmark Tests (TEST-DESIGNER Suite 4)."""
from pathlib import Path
import pytest
from repo_intelligence.indexer import Indexer
from arch_intelligence.arch_detector import ArchitectureDetector


class TestPhase53Benchmarks:
    """Full repository benchmark tests for Phase 5.3."""

    def _run_benchmark(self, repo_name):
        """Run benchmark on a single repo."""
        repo_path = Path(f"repos/{repo_name}")
        if not repo_path.exists():
            return None

        indexer = Indexer(repo_path)
        result = indexer.index_repository()
        detector = ArchitectureDetector()
        prediction = detector.detect(
            call_graph=result.calls or [],
            import_graph=result.imports or [],
            symbols=result.symbols or [],
            files=result.files or [],
        )
        return prediction

    def test_sqlalchemy_benchmark(self):
        """SQLAlchemy benchmark — expect flat architecture (high coupling)."""
        prediction = self._run_benchmark('sqlalchemy')
        if prediction is None:
            pytest.skip("SQLAlchemy not cloned")

        print(f"\nSQLAlchemy: {prediction.style} (confidence: {prediction.confidence:.2f})")
        assert prediction.style == 'flat', f"Expected flat, got {prediction.style}"
        assert prediction.confidence > 0.65, f"Confidence {prediction.confidence} too low"

    def test_celery_benchmark(self):
        """Celery benchmark — expect microservices architecture (distinct services)."""
        prediction = self._run_benchmark('celery')
        if prediction is None:
            pytest.skip("Celery not cloned")

        print(f"\nCelery: {prediction.style} (confidence: {prediction.confidence:.2f})")
        assert prediction.style == 'microservices', f"Expected microservices, got {prediction.style}"
        assert prediction.confidence > 0.65, f"Confidence {prediction.confidence} too low"

    def test_all_8_repos_benchmark(self):
        """All 8 repos — accuracy and calibration metrics."""
        repos = {
            'flask': 'LAYERED',
            'click': 'FLAT',
            'django': 'LAYERED',
            'fastapi': 'LAYERED',
            'langchain': 'LAYERED',
            'requests': 'FLAT',
            'sqlalchemy': 'FLAT',
            'celery': 'MICROSERVICES',
        }

        results = {}
        for repo_name, expected_style in repos.items():
            prediction = self._run_benchmark(repo_name)
            if prediction is None:
                continue

            predicted_style = prediction.style.name  # ArchStyle enum to string name
            results[repo_name] = {
                'predicted': predicted_style,
                'expected': expected_style,
                'confidence': prediction.confidence,
                'correct': predicted_style == expected_style,
            }

            status = 'PASS' if results[repo_name]['correct'] else 'FAIL'
            print(f"{repo_name}: {predicted_style} (conf: {prediction.confidence:.2f}) — {status}")

        if not results:
            pytest.skip("No repositories found")

        # Compute metrics
        correct = sum(1 for r in results.values() if r['correct'])
        total = len(results)
        accuracy = correct / total if total > 0 else 0

        # Verify: ≥85% accuracy or maintain 83.3%
        print(f"\nAccuracy: {correct}/{total} ({accuracy:.1%})")
        assert accuracy >= 0.833, f"Accuracy {accuracy:.1%} below target (need ≥83.3%)"
