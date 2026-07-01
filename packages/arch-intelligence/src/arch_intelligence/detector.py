"""Architecture style detector."""

import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from storage import OrthoDatabase

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
            and abs(sorted_styles[0][1] - sorted_styles[1][1]) < 0.12
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

    def _hub_score(self) -> float:
        """
        Detect hub-and-spoke pattern (hexagonal signature).
        Returns how many imports concentrate on few files (0.0 = even distribution, 1.0 = star pattern).
        """
        g = self.file_graph.build_from_imports()
        if len(g) < 3:
            return 0.0

        # Count in-degree for each file
        in_degrees = [g.in_degree(node) for node in g.nodes()]
        if not in_degrees or sum(in_degrees) == 0:
            return 0.0

        # Calculate concentration: high if few nodes have high in-degree
        total_in = sum(in_degrees)
        in_degrees_sorted = sorted(in_degrees, reverse=True)

        # Top 2 files account for what % of all imports?
        top_2_in = sum(in_degrees_sorted[:2])
        concentration = top_2_in / total_in if total_in > 0 else 0.0

        # Hub score: high if top files dominate
        return min(1.0, concentration)

    def _tier_count(self) -> int:
        """Count distinct topological levels (tiers/layers) in the architecture."""
        levels = self.file_graph.topological_levels()
        if not levels:
            return 1
        return len(set(levels.values()))

    def _files_per_tier(self) -> float:
        """Average files per tier. MVC is small (~2-3), layered is larger (>3)."""
        levels = self.file_graph.topological_levels()
        if not levels:
            return 1.0

        tier_count = len(set(levels.values()))
        if tier_count == 0:
            return 1.0

        return len(levels) / tier_count

    def _score_layered(self, metrics: DetectionMetrics) -> float:
        """Score layered architecture (most common pattern)."""
        # Layered if: high upward deps (clear layer structure) + many files
        # Characteristic: layering_score high, multiple tiers, many files per tier
        layered_base = (
            metrics.layering_score * 0.85
            + (1.0 - metrics.modularity_score) * 0.10
            + metrics.cohesion_score * 0.05
        )

        # Mild penalty if looks like MVC (small # of files per tier, exactly 3 tiers)
        # Only penalize if VERY small (< 2), not at 2-3 files
        files_per_tier = self._files_per_tier()
        tier_count = self._tier_count()
        if tier_count == 3 and files_per_tier < 1.8:
            layered_base *= 0.7  # Very small tiers, more likely MVC

        # CRITICAL: Penalize if modularity is high (independent services, not layered)
        if metrics.modularity_score > 0.65:
            layered_base *= 0.6

        # Penalize if edge density is VERY high (looks like flat/monolithic, not structured)
        g = self.file_graph.build_from_imports()
        num_nodes = len(g)
        if num_nodes > 1:
            num_edges = g.number_of_edges()
            edge_density = num_edges / (num_nodes * (num_nodes - 1))
            if edge_density > 0.33:  # Very high interconnectedness
                layered_base *= 0.50  # Penalty for flat-like density

        # CRITICAL: Penalize if pattern suggests hexagonal (hub-and-spoke)
        # Hexagonal has VERY high cohesion (core modules tightly coupled) and LOW modularity
        if (metrics.cohesion_score > 0.65 and
            metrics.modularity_score < 0.35 and
            metrics.cohesion_score > metrics.modularity_score * 2.0):
            layered_base *= 0.6

        return layered_base

    def _score_hexagonal(self, metrics: DetectionMetrics) -> float:
        """Score hexagonal (ports & adapters) architecture."""
        # Hexagonal if: VERY strong hub-and-spoke pattern (nearly all imports go to few core files)
        # + low modularity (adapters aren't independent services)

        if metrics.cohesion_score < 0.3:
            return 0.1  # Can't be hexagonal without some core cohesion

        # CRITICAL: Hub-and-spoke must be VERY strong (>0.80) to distinguish from MVC
        # In hexagonal, adapters all import from core; in MVC, distribution is wider
        hub = self._hub_score()

        if hub < 0.75:
            return 0.1  # Not strong enough hub pattern - likely MVC not hexagonal

        # Combine very strong hub pattern with low modularity
        score = (
            hub * 0.70
            + (1.0 - metrics.modularity_score) * 0.30
        )

        return min(1.0, score)

    def _score_mvc(self, metrics: DetectionMetrics) -> float:
        """Score MVC architecture."""
        # MVC if: exactly 3 tiers (model/controller/view) with moderate-high layering
        # Key: NOT microservices (which have high modularity ~>0.6) and NOT hexagonal (hub > 0.75)
        tier_count = self._tier_count()

        # MVC MUST have 3 tiers or very close to 3
        if tier_count < 2 or tier_count > 4:
            return 0.2  # Disqualified if not 3-tier

        # CRITICAL: MVC requires LOWER modularity (tight coupling) unlike microservices
        if metrics.modularity_score > 0.65:
            return 0.2  # Too modular to be MVC - looks like microservices

        # Layering must be high (MVC is layered, not modular like microservices)
        if metrics.layering_score < 0.7:
            return 0.1  # Not layered enough to be MVC

        mvc_base = (
            metrics.layering_score * 0.65
            + (1.0 - metrics.modularity_score) * 0.25
            + metrics.cohesion_score * 0.10
        )

        # Bonus for exactly 3 tiers (strong MVC signal)
        # Stronger bonus if files per tier is small (2-3), weaker if larger (4+)
        files_per_tier = self._files_per_tier()
        if tier_count == 3:
            if files_per_tier < 3.0:
                mvc_base *= 1.25  # Strong MVC (small tiers)
            else:
                mvc_base *= 1.10  # Mild bonus for 3 tiers even if larger

        # Penalty if hub pattern is very strong (that's hexagonal, not MVC)
        hub = self._hub_score()
        if hub > 0.75:
            mvc_base *= 0.5

        return min(1.0, mvc_base)

    def _score_microservices(self, metrics: DetectionMetrics) -> float:
        """Score microservices architecture."""
        # Microservices if: high modularity (independent services, low coupling)
        # Each service can have internal layering, so layering_score is not a blocker
        microservices_base = (
            metrics.modularity_score * 0.85
            + (1.0 - metrics.cohesion_score) * 0.15
        )
        # Mild penalty only if VERY layered and VERY cohesive (looks monolithic layered)
        if metrics.layering_score > 0.9 and metrics.cohesion_score > 0.7:
            microservices_base *= 0.65
        return microservices_base

    def _score_flat(self, metrics: DetectionMetrics) -> float:
        """Score flat architecture (no structure)."""
        # Flat if: highly interconnected with low structure
        # Look for: high edge density (many edges relative to nodes) + low modularity
        g = self.file_graph.build_from_imports()
        num_nodes = len(g)
        num_edges = g.number_of_edges()
        max_edges = num_nodes * (num_nodes - 1)  # Complete graph

        if max_edges == 0:
            edge_density = 0.0
        else:
            edge_density = num_edges / max_edges

        # Flat score: high edge density + low modularity
        # High interconnectedness = no clear module boundaries
        flat_base = (
            edge_density * 0.75
            + (1.0 - metrics.modularity_score) * 0.25
        )

        return flat_base

    def _build_evidence(
        self, best_style: ArchStyle, metrics: DetectionMetrics, scores: Dict[ArchStyle, float]
    ) -> list[str]:
        """Build human-readable evidence for detection result."""
        evidence = []

        if best_style == "layered":
            evidence.append(
                f"Strict layering detected: {metrics.layering_score:.0%} of imports flow upward between tiers"
            )
            evidence.append("Clear layer separation (presentation -> business -> data)")
            evidence.append("Low cross-layer coupling enforced")

        elif best_style == "hexagonal":
            evidence.append("High domain cohesion: core modules tightly coupled")
            evidence.append("Adapter pattern: external interfaces depend on core domain")
            evidence.append("Isolated dependencies: adapters do not cross-import")

        elif best_style == "mvc":
            evidence.append("Three-tier model-view-controller layered structure")
            evidence.append("MVC pattern: view layer depends on controller layer depends on model layer")
            evidence.append("Tight coupling between layers (pattern characteristic of MVC)")

        elif best_style == "microservices":
            evidence.append(f"Service modularity: {metrics.modularity_score:.0%} of code organized into independent modules")
            evidence.append("Low inter-service coupling (services minimize cross-boundary dependencies)")
            evidence.append("Multiple independent subsystems detected")

        elif best_style == "flat":
            evidence.append("Monolithic structure: no clear architectural layers")
            evidence.append(f"High interconnectedness: {1 - metrics.layering_score:.0%} non-hierarchical imports")
            evidence.append("Tightly coupled components across system")

        # Add score detail
        evidence.append(
            f"Architecture score: {scores[best_style]:.2f} (confidence: {scores[best_style]:.0%})"
        )

        return evidence

    def detect_confidence_breakdown(self) -> Dict[str, float]:
        """Return confidence score for each architecture style (all 5 styles)."""
        metrics = self._compute_metrics()
        return {
            "layered": self._score_layered(metrics),
            "hexagonal": self._score_hexagonal(metrics),
            "mvc": self._score_mvc(metrics),
            "microservices": self._score_microservices(metrics),
            "flat": self._score_flat(metrics),
        }
