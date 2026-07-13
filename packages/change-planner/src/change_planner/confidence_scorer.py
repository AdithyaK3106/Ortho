from typing import Sequence

from change_planner.types import EdgeType, ImpactEdge


class ConfidenceScorer:
    def score_edge(self, edge: ImpactEdge) -> float:
        if edge.edge_type == EdgeType.DIRECT_CALL:
            return 1.0
        elif edge.edge_type == EdgeType.TRANSITIVE_CALL:
            return 0.9 / edge.distance
        elif edge.edge_type == EdgeType.IMPORT:
            return 0.8
        elif edge.edge_type == EdgeType.STAR_IMPORT:
            return 0.6
        elif edge.edge_type == EdgeType.DYNAMIC_IMPORT:
            return 0.4
        elif edge.edge_type == EdgeType.CONDITIONAL_IMPORT:
            return 0.7
        return 0.5

    def aggregate_confidence(self, edges: Sequence[ImpactEdge]) -> float:
        if not edges:
            return 0.0
        scores = [self.score_edge(edge) for edge in edges]
        return sum(scores) / len(scores)

    def assess_cascade_risk(self, affected_modules: list[str], cascade_depth: int) -> str:
        module_count = len(affected_modules)

        if module_count < 3 and cascade_depth <= 2:
            return "low"
        elif module_count < 10 and cascade_depth <= 5:
            return "medium"
        else:
            return "high"
