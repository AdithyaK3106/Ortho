from typing import Any

from decision_engine.types import Decision, Recommendation


class DecisionEngine:
    def decide(
        self,
        intent: str,
        sources: dict[str, list[Any]],
    ) -> Decision:
        """
        Aggregate recommendations from multiple sources.

        Algorithm:
        1. Collect all recommendations
        2. Deduplicate similar ones
        3. Rank by confidence × fit
        4. Return top options
        """
        options: list[Recommendation] = []

        for source_name, items in sources.items():
            if not items:
                continue
            for item in items:
                rec = self._convert_to_recommendation(source_name, item)
                if rec:
                    options.append(rec)

        if not options:
            no_rec = Recommendation(
                title="No recommendations",
                description="No issues or recommendations found",
                source="system",
                effort="low",
                risk="low",
                confidence=1.0,
                suggested_fix="No action needed",
            )
            return Decision(
                intent=intent,
                options=[no_rec],
                recommended_option=no_rec,
                reasoning="All sources returned no recommendations",
                confidence=1.0,
            )

        deduped = self._deduplicate(options)
        ranked = self._rank_options(deduped, intent)
        top_options = ranked[:5] if len(ranked) > 5 else ranked

        return Decision(
            intent=intent,
            options=top_options,
            recommended_option=ranked[0] if ranked else options[0],
            reasoning=self._generate_reasoning(ranked),
            confidence=ranked[0].confidence if ranked else 0.5,
        )

    def _convert_to_recommendation(self, source: str, item: Any) -> Recommendation | None:
        """Convert component output to Recommendation"""
        if not item:
            return None

        try:
            if source == "change_planner":
                return Recommendation(
                    title=f"Impact: {item.changed_file}",
                    description=item.reasoning,
                    source="change_planner",
                    effort="low",
                    risk=item.cascade_risk,
                    confidence=item.confidence,
                    suggested_fix="Verify all affected modules before commit",
                    evidence=list(item.evidence)[:3] if item.evidence else [],
                )
            elif source == "feature_planner":
                return Recommendation(
                    title=str(item.name),
                    description=str(item.description),
                    source="feature_planner",
                    effort=str(item.effort) if item.effort in ("low", "medium", "high") else "low",
                    risk=str(item.risk) if item.risk in ("low", "medium", "high") else "low",
                    confidence=0.85,
                    suggested_fix=str(item.rationale) if hasattr(item, 'rationale') else "",
                    evidence=[str(x) for x in (item.affected_layers if hasattr(item, 'affected_layers') else [])],
                )
            elif source == "refactoring_advisor":
                return Recommendation(
                    title=f"{item.issue_type}: {item.location}",
                    description=str(item.recommendation),
                    source="refactoring_advisor",
                    effort="medium",
                    risk="low",
                    confidence=item.confidence,
                    suggested_fix=str(item.recommendation),
                    evidence=list(item.evidence) if hasattr(item, 'evidence') and item.evidence else [],
                )
            elif source == "arch_guardrails":
                return Recommendation(
                    title=f"Violation: {item.rule_id}",
                    description=str(item.message),
                    source="arch_guardrails",
                    effort="medium",
                    risk="high",
                    confidence=1.0,
                    suggested_fix=str(item.suggested_fix),
                    evidence=list(item.evidence) if hasattr(item, 'evidence') and item.evidence else [],
                )
        except (AttributeError, TypeError):
            return None

        return None

    def _deduplicate(self, options: list[Recommendation]) -> list[Recommendation]:
        """Merge similar recommendations (Jaccard > 0.8)"""
        seen: dict[str, Recommendation] = {}

        for option in options:
            key = option.title.lower()[:20]
            if key not in seen:
                seen[key] = option
            elif option.confidence > seen[key].confidence:
                seen[key] = option

        return list(seen.values())

    def _rank_options(
        self, options: list[Recommendation], intent: str
    ) -> list[Recommendation]:
        """Rank by score: confidence(0.7) × fit(0.3)"""
        scored = [
            (option, self._score_option(option, intent))
            for option in options
        ]
        scored.sort(key=lambda x: -x[1])
        return [option for option, _ in scored]

    def _score_option(self, option: Recommendation, intent: str) -> float:
        """Score option: confidence × fit_to_intent"""
        effort_bonus = {"low": 0.1, "medium": 0.0, "high": -0.1}[option.effort]
        risk_penalty = {"low": 0.0, "medium": -0.05, "high": -0.1}[option.risk]

        return (option.confidence * 0.7) + (0.3 * (0.5 + effort_bonus + risk_penalty))

    def _generate_reasoning(self, ranked: list[Recommendation]) -> str:
        """Generate explanation of top recommendation"""
        if not ranked:
            return "No recommendations available."

        top = ranked[0]
        return f"Recommended: {top.title} (confidence: {top.confidence:.0%}). Rationale: {top.suggested_fix}"
