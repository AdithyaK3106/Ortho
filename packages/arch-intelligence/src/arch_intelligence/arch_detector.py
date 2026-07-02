"""Core architecture pattern detection."""

from dataclasses import dataclass
from typing import Optional
from .types import ArchStyle, ArchitectureDetectionResult


# Type stubs for external types (from repo-intelligence)
@dataclass
class CallEdge:
    caller_id: str
    callee_id: str
    confidence: float = 0.8


@dataclass
class ImportEdge:
    importer_file_id: str
    imported_file_id: Optional[str] = None
    imported_module: str = ""
    is_external: bool = False


@dataclass
class Symbol:
    id: str
    name: str
    file_id: str


@dataclass
class File:
    id: str
    rel_path: str


class ArchitectureDetector:
    """Detects architectural style from call and import graphs."""

    TIE_BREAKER_ORDER = [
        ArchStyle.LAYERED,
        ArchStyle.MVC,
        ArchStyle.HEXAGONAL,
        ArchStyle.MICROSERVICES,
        ArchStyle.FLAT,
    ]

    def detect(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        files: list[File],
    ) -> ArchitectureDetectionResult:
        """Analyze graphs and return detected architectural style."""
        scores = {}

        scores[ArchStyle.LAYERED] = self._score_layered(import_graph, files)
        scores[ArchStyle.HEXAGONAL] = self._score_hexagonal(
            call_graph, import_graph, files
        )
        scores[ArchStyle.MVC] = self._score_mvc(call_graph, import_graph, files)
        scores[ArchStyle.MICROSERVICES] = self._score_microservices(
            call_graph, symbols, files
        )
        scores[ArchStyle.FLAT] = self._score_flat(call_graph, import_graph, files)

        winner = max(scores, key=scores.get)
        winner_score = scores[winner]

        alternatives = [
            s for s in scores if s != winner and scores[s] >= winner_score - 0.1
        ]
        alternative = alternatives[0] if alternatives else None
        alternative_score = scores[alternative] if alternative else None

        evidence = self._build_evidence(winner, winner_score, scores)

        return ArchitectureDetectionResult(
            style=winner,
            confidence=winner_score,
            evidence=evidence,
            alternative=alternative,
            alternative_confidence=alternative_score,
        )

    def _score_layered(self, import_graph: list, files: list) -> float:
        """Score layered architecture."""
        if not import_graph:
            return 0.0

        depth = len(set(e.importer_file_id for e in import_graph)) + 1
        base = 0.6 if depth >= 3 else 0.3

        has_cycles = any(
            e.importer_file_id == e.imported_file_id for e in import_graph
        )

        if has_cycles:
            return base - 0.25
        if depth >= 3:
            return min(base + 0.25, 0.95)
        return base

    def _score_hexagonal(
        self, call_graph: list, import_graph: list, files: list
    ) -> float:
        """Score hexagonal architecture."""
        if not files:
            return 0.0

        isolation_count = sum(
            1 for f in files if sum(1 for e in import_graph if e.importer_file_id == f.id) <= 2
        )
        isolation_ratio = isolation_count / len(files) if files else 0

        return min(0.65 + isolation_ratio * 0.15, 0.9)

    def _score_mvc(self, call_graph: list, import_graph: list, files: list) -> float:
        """Score MVC architecture."""
        if not files:
            return 0.0

        semantic_matches = sum(
            1
            for f in files
            if any(
                keyword in f.rel_path.lower()
                for keyword in ["controller", "view", "model", "service"]
            )
        )
        semantic_ratio = semantic_matches / len(files) if files else 0

        return min(0.7 + semantic_ratio * 0.15, 0.95)

    def _score_microservices(
        self, call_graph: list, symbols: list, files: list
    ) -> float:
        """Score microservices architecture."""
        if not files:
            return 0.0

        components = min(len(set(e.caller_id for e in call_graph)) // 3, 5)
        base = 0.6 if components >= 3 else 0.3

        if components < 3:
            return base - 0.2
        return min(base + 0.1 * components, 0.9)

    def _score_flat(self, call_graph: list, import_graph: list, files: list) -> float:
        """Score flat architecture."""
        if not import_graph or not files:
            return 0.55

        import_density = len(import_graph) / max(len(files) ** 2, 1)

        if import_density > 0.3:
            return min(0.55 + 0.2, 0.8)
        return 0.3

    def _build_evidence(
        self, winner: ArchStyle, score: float, scores: dict
    ) -> list[str]:
        """Build evidence list justifying the detection."""
        evidence = [f"Detected style: {winner.value}"]
        evidence.append(f"Confidence: {score:.2f}")

        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        if len(sorted_scores) > 1:
            second = sorted_scores[1]
            margin = score - second[1]
            if margin < 0.1:
                evidence.append(
                    f"Note: {second[0].value} also plausible (confidence: {second[1]:.2f})"
                )

        return evidence
