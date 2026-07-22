import re
from typing import Any

from decision_engine.types import Decision, Recommendation

_WORD_RE = re.compile(r"[a-z0-9_]+")


def _words(text: str) -> set[str]:
    """Lowercased word tokens, splitting on anything that isn't
    alnum/underscore -- so "auth)?" and "base_user" both yield "auth" /
    "base_user" instead of carrying along stray punctuation that would
    never match the same token in another string."""
    return set(_WORD_RE.findall(text.lower()))


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
                    # item.evidence is list[ImpactEdge] (a dataclass), not
                    # list[str] -- render each edge as a readable sentence
                    # instead of leaking its Python repr into report text.
                    evidence=[
                        f"{e.source} → {e.target} ({e.edge_type.value}, distance {e.distance})"
                        for e in list(item.evidence)[:3]
                    ] if item.evidence else [],
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
            elif source == "git_history":
                return Recommendation(
                    title=f"Prior commit: {item.title}",
                    description=item.description,
                    source="git_history",
                    effort="low",
                    risk="low",
                    confidence=item.confidence,
                    suggested_fix="Review this commit for prior context before proceeding.",
                    evidence=[f"{item.commit_hash[:8]} by {item.author} on {item.commit_date}"],
                )
        except (AttributeError, TypeError):
            return None

        return None

    def _dedup_text(self, option: Recommendation) -> str:
        """Text used to detect near-duplicate recommendations.

        Title alone is not enough: arch_guardrails builds every option's
        title as f"Violation: {rule_id}" (see _convert_to_recommendation),
        so two distinct dependency_direction cycles have byte-identical
        titles and only differ in `description` (the actual violation
        message, which names the specific modules/cycle). Combining title
        with description keeps genuine near-duplicates ("Extract interface"
        / "Extract interface pattern", same source, same/no description)
        mergeable while stopping same-rule-different-location findings
        from colliding just because their titles match.
        """
        return f"{option.title} {option.description}"

    def _deduplicate(self, options: list[Recommendation]) -> list[Recommendation]:
        """Merge recommendations that are near-duplicates (Jaccard > 0.8 over
        title+description words). A 20-char title prefix was the previous
        key: two distinct "Violation: dependency_direction" findings for
        different cycles both collapsed to "violation: dependenc" and
        silently dropped one, regardless of which cycle the caller's intent
        actually asked about.
        """
        kept: list[Recommendation] = []

        for option in options:
            words = _words(self._dedup_text(option))
            merged = False
            for i, existing in enumerate(kept):
                existing_words = _words(self._dedup_text(existing))
                union = words | existing_words
                jaccard = len(words & existing_words) / len(union) if union else 0.0
                if jaccard > 0.8:
                    if option.confidence > existing.confidence:
                        kept[i] = option
                    merged = True
                    break
            if not merged:
                kept.append(option)

        return kept

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
        """Score option: confidence(0.7) x fit(0.3).

        fit previously ignored `intent` entirely (a constant from
        effort/risk only), so every arch_guardrails violation -- same
        confidence=1.0, same effort/risk -- scored identically and ranking
        fell back to insertion order. An intent naming one specific cycle
        (e.g. "the auth cycle") would then get whichever violation
        check_violations() happened to find first, not the one asked about.
        fit now also rewards word overlap between the intent text and the
        option's title/description/evidence, so a specific intent surfaces
        the matching finding instead of an arbitrary same-scored one.
        """
        effort_bonus = {"low": 0.1, "medium": 0.0, "high": -0.1}[option.effort]
        risk_penalty = {"low": 0.0, "medium": -0.05, "high": -0.1}[option.risk]

        intent_words = _words(intent)
        option_words = _words(" ".join([option.title, option.description, *option.evidence]))
        overlap = len(intent_words & option_words) / len(intent_words) if intent_words else 0.0

        fit = 0.5 + effort_bonus + risk_penalty + (0.5 * overlap)
        return (option.confidence * 0.7) + (0.3 * fit)

    def _generate_reasoning(self, ranked: list[Recommendation]) -> str:
        """Generate explanation of top recommendation"""
        if not ranked:
            return "No recommendations available."

        top = ranked[0]
        return f"Recommended: {top.title} (confidence: {top.confidence:.0%}). Rationale: {top.suggested_fix}"
