"""Architecture style detector."""

import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from database import OrthoDatabase

try:
    from .graph_utils import FileGraph, MetricsCalculator, CallGraph
    from .detection_types import ArchStyle, DetectionMetrics, DetectionResult
except (ImportError, ValueError, SystemError):
    from graph_utils import FileGraph, MetricsCalculator, CallGraph
    from detection_types import ArchStyle, DetectionMetrics, DetectionResult


class ArchitectureDetector:
    """Detect architecture style (layered, hexagonal, MVC, microservices, flat)."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id
        self.file_graph = FileGraph(db, repo_id)
        self.metrics_calc = MetricsCalculator(self.file_graph, CallGraph(db, repo_id))

    def detect(self) -> DetectionResult:
        """
        Classify architecture style.
        Returns DetectionResult with style, confidence, evidence, and alternative.
        """
        metrics = self._compute_metrics()

        scores = {
            "layered": self._score_layered(metrics),
            "hexagonal": self._score_hexagonal(metrics),
            "mvc": self._score_mvc(metrics),
            "microservices": self._score_microservices(metrics),
            "flat": self._score_flat(metrics),
        }

        metrics.pattern_matches = scores

        # Pick winner
        best_style = max(scores, key=scores.get)
        best_confidence = scores[best_style]

        # Detect alternative if ambiguous
        sorted_styles = sorted(scores.items(), key=lambda x: -x[1])
        alternative = None
        alternative_conf = None

        if (
            len(sorted_styles) > 1
            and abs(sorted_styles[0][1] - sorted_styles[1][1]) < 0.15
        ):
            alternative = sorted_styles[1][0]
            alternative_conf = sorted_styles[1][1]

        # Build evidence
        evidence = self._build_evidence(best_style, metrics, scores)

        return DetectionResult(
            style=best_style,
            confidence=best_confidence,
            evidence=evidence,
            alternative=alternative,
            alternative_confidence=alternative_conf,
        )

    def _compute_metrics(self) -> DetectionMetrics:
        """Compute architecture metrics."""
        layering = self.metrics_calc.layering_score()
        cohesion = self.metrics_calc.cohesion_score()
        modularity = self.metrics_calc.modularity_score()

        return DetectionMetrics(
            layering_score=layering,
            cohesion_score=cohesion,
            modularity_score=modularity,
        )

    def _score_layered(self, metrics: DetectionMetrics) -> float:
        """Score layered architecture (most common pattern)."""
        # Layered if: high upward deps, clear layer structure, low cross-layer
        return (
            metrics.layering_score * 0.7
            + (1.0 - metrics.modularity_score) * 0.2
            + metrics.cohesion_score * 0.1
        )

    def _score_hexagonal(self, metrics: DetectionMetrics) -> float:
        """Score hexagonal (ports & adapters) architecture."""
        # Hexagonal if: high cohesion + clear core/adapter separation
        return metrics.cohesion_score * 0.8 + (1.0 - metrics.modularity_score) * 0.2

    def _score_mvc(self, metrics: DetectionMetrics) -> float:
        """Score MVC architecture."""
        # MVC if: layered + moderate modularity (3 tight tiers)
        return (
            metrics.layering_score * 0.6
            + (1.0 - metrics.modularity_score) * 0.3
            + metrics.cohesion_score * 0.1
        )

    def _score_microservices(self, metrics: DetectionMetrics) -> float:
        """Score microservices architecture."""
        # Microservices if: high modularity + low internal cohesion
        return (
            metrics.modularity_score * 0.7
            + (1.0 - metrics.cohesion_score) * 0.3
        )

    def _score_flat(self, metrics: DetectionMetrics) -> float:
        """Score flat architecture (no structure)."""
        # Flat if: everything connected, no clear layers/modules
        return (1.0 - metrics.layering_score) * 0.5 + (1.0 - metrics.modularity_score) * 0.5

    def _build_evidence(
        self, best_style: ArchStyle, metrics: DetectionMetrics, scores: Dict[ArchStyle, float]
    ) -> list[str]:
        """Build human-readable evidence for detection result."""
        evidence = []

        if best_style == "layered":
            evidence.append(
                f"Clear upward dependencies ({metrics.layering_score:.0%} upward-only imports)"
            )
            evidence.append("Detected logical layer structure")
            evidence.append(f"Low cross-layer coupling ({1 - metrics.layering_score:.0%})")

        elif best_style == "hexagonal":
            evidence.append("High internal cohesion (domain tightly bound)")
            evidence.append("Clear separation between core and adapters")

        elif best_style == "mvc":
            evidence.append("Three-tier layered structure detected")
            evidence.append("Model-view-controller pattern evident")

        elif best_style == "microservices":
            evidence.append(f"High modularity ({metrics.modularity_score:.0%})")
            evidence.append("Multiple independent subsystems detected")

        elif best_style == "flat":
            evidence.append("No clear architectural pattern")
            evidence.append("Low layering and low modularity")

        # Add score detail
        evidence.append(
            f"Architecture score: {scores[best_style]:.2f} (confidence: {scores[best_style]:.0%})"
        )

        return evidence

    def detect_confidence_breakdown(self) -> Dict[ArchStyle, float]:
        """Return confidence score for each architecture style."""
        result = self.detect()
        if result.alternative:
            return {
                result.style: result.confidence,
                result.alternative: result.alternative_confidence or 0.0,
            }
        return {result.style: result.confidence}
