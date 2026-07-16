from typing import Protocol

from feature_planner.types import FeaturePlan, ImplementationPath


class ArchitectureModel(Protocol):  # pragma: no cover
    """Protocol for architecture model."""

    def get_style(self) -> str:
        """Get architecture style (layered, microservices, etc.)"""
        ...


class FeaturePlanner:
    def __init__(self, arch_model: ArchitectureModel) -> None:
        self.arch_model = arch_model

    def plan_feature(self, intent: str) -> FeaturePlan:
        """
        Generate ≥3 distinct implementation paths for feature.

        Algorithm:
        1. Classify feature type (endpoint, service, data, cross-cutting)
        2. Generate candidate paths based on architecture
        3. Score paths (fit, effort, risk)
        4. Select 3+ distinct paths with variety
        5. Return FeaturePlan
        """
        feature_type = self._classify_feature_type(intent)
        candidates = self._generate_candidates(feature_type)
        scored = [
            (path, self._score_path(path))
            for path in candidates
        ]
        paths = self._select_diverse_paths(scored, min_count=3)

        return FeaturePlan(
            intent=intent,
            feature_type=feature_type,
            paths=paths,
        )

    def _classify_feature_type(self, intent: str) -> str:
        """Classify intent as bugfix, endpoint, service, data_layer, cross_cutting, infrastructure"""
        intent_lower = intent.lower()

        # Checked first: bugfix/refactor language should win over incidental
        # keyword overlap ("fix the auth caching bug" is a bugfix, not
        # cross_cutting) -- this repo's own architecture-review commands
        # (guardrails/decide/review) always describe findings in this
        # vocabulary ("Circular dependency: ... -> Break cycle by
        # extracting abstraction"), and orchestrate() feeds those finding
        # descriptions straight into plan_feature() as the intent. Without
        # this category every such call fell through to the generic
        # "infrastructure" bucket (Terraform/service-registry suggestions
        # for a one-file Python refactor) since none of the other four
        # categories are shaped like "fix a bug", only "add a feature".
        if any(word in intent_lower for word in ["fix", "bug", "break", "broken", "resolve", "refactor", "cycle", "circular"]):
            return "bugfix"
        elif any(word in intent_lower for word in ["auth", "logging", "caching", "feature flag", "monitoring", "rate limiting", "validation"]):
            return "cross_cutting"
        elif any(word in intent_lower for word in ["database", "schema", "migration", "data", "repository"]):
            return "data_layer"
        elif any(word in intent_lower for word in ["service", "processor", "worker", "job", "async"]):
            return "service"
        elif any(word in intent_lower for word in ["endpoint", "route", "api", "handler", "controller"]):
            return "endpoint"
        else:
            return "infrastructure"

    def _generate_candidates(self, feature_type: str) -> list[ImplementationPath]:
        """Generate candidate paths based on feature type and architecture"""
        style = self.arch_model.get_style()

        if feature_type == "bugfix":
            return self._bugfix_paths(style)
        elif feature_type == "endpoint":
            return self._endpoint_paths(style)
        elif feature_type == "service":
            return self._service_paths(style)
        elif feature_type == "data_layer":
            return self._data_paths(style)
        elif feature_type == "cross_cutting":
            return self._cross_cutting_paths(style)
        else:
            return self._infrastructure_paths(style)

    def _bugfix_paths(self, style: str) -> list[ImplementationPath]:
        """Generate bugfix/refactor implementation paths -- distinct from
        the feature-shaped categories above: no new capability is being
        added, so 'affected_layers' reflects where the fix lands, not a
        layer being extended."""
        paths = [
            ImplementationPath(
                name="Minimal Targeted Fix",
                description="Smallest change that resolves the issue in place",
                affected_layers=["business"],
                effort="low",
                risk="low",
                rationale="Lowest blast radius; preferred when the fix is well-understood",
            ),
            ImplementationPath(
                name="Extract Shared Abstraction",
                description="Break the coupling/cycle by extracting a shared interface or module",
                affected_layers=["business", "data"],
                effort="medium",
                risk="medium",
                rationale="Addresses the structural cause, not just the symptom -- standard fix for circular dependencies",
            ),
            ImplementationPath(
                name="Deprecate and Reroute",
                description="Mark the problematic path deprecated, route callers through a new one",
                affected_layers=["business", "presentation"],
                effort="medium",
                risk="low",
                rationale="Safer for widely-called code; avoids a single big-bang change",
            ),
            ImplementationPath(
                name="Full Rewrite of Affected Module",
                description="Rewrite the module cleanly instead of patching around the issue",
                affected_layers=["business"],
                effort="high",
                risk="high",
                rationale="Only worth it if the module has accumulated enough debt that patching keeps costing more",
            ),
        ]
        return paths

    def _endpoint_paths(self, style: str) -> list[ImplementationPath]:
        """Generate endpoint implementation paths"""
        paths = [
            ImplementationPath(
                name="Simple Route Handler",
                description="Add to existing routes/blueprint",
                affected_layers=["presentation", "business"],
                effort="low",
                risk="low",
                rationale="Fits existing architecture, reuses patterns",
            ),
            ImplementationPath(
                name="Microservice Pattern",
                description="Extract into new microservice",
                affected_layers=["infrastructure", "presentation"],
                effort="high",
                risk="high",
                rationale="For significant feature isolation",
            ),
            ImplementationPath(
                name="Caching Wrapper",
                description="Add caching layer over route",
                affected_layers=["presentation", "business"],
                effort="medium",
                risk="low",
                rationale="Improves performance, orthogonal to route logic",
            ),
            ImplementationPath(
                name="API Gateway Pattern",
                description="Route through centralized gateway",
                affected_layers=["infrastructure"],
                effort="medium",
                risk="medium",
                rationale="Centralized routing and policy enforcement",
            ),
        ]
        return paths

    def _service_paths(self, style: str) -> list[ImplementationPath]:
        """Generate service layer implementation paths"""
        paths = [
            ImplementationPath(
                name="Async Task",
                description="Add async task to existing job system",
                affected_layers=["business"],
                effort="low",
                risk="low",
                rationale="Fits async architecture patterns",
            ),
            ImplementationPath(
                name="Dedicated Worker",
                description="New dedicated worker process",
                affected_layers=["infrastructure", "business"],
                effort="medium",
                risk="medium",
                rationale="Isolated execution, separate scaling",
            ),
            ImplementationPath(
                name="Message Queue",
                description="Implement with message queue abstraction",
                affected_layers=["infrastructure"],
                effort="high",
                risk="medium",
                rationale="Decoupled, scalable, reliable delivery",
            ),
            ImplementationPath(
                name="Event-Driven",
                description="Publish/subscribe event pattern",
                affected_layers=["business"],
                effort="medium",
                risk="low",
                rationale="Loose coupling, reactive architecture",
            ),
        ]
        return paths

    def _data_paths(self, style: str) -> list[ImplementationPath]:
        """Generate data layer implementation paths"""
        paths = [
            ImplementationPath(
                name="Direct Schema Change",
                description="Simple migration + backfill",
                affected_layers=["data"],
                effort="low",
                risk="medium",
                rationale="Straightforward for backward-compatible changes",
            ),
            ImplementationPath(
                name="Versioned Migration",
                description="Backward-compatible with feature flags",
                affected_layers=["data", "business"],
                effort="medium",
                risk="low",
                rationale="Safer for live systems, enables rollback",
            ),
            ImplementationPath(
                name="Repository Pattern",
                description="Abstraction layer over data access",
                affected_layers=["data", "business"],
                effort="high",
                risk="low",
                rationale="Decouples business logic from persistence",
            ),
        ]
        return paths

    def _cross_cutting_paths(self, style: str) -> list[ImplementationPath]:
        """Generate cross-cutting concern paths"""
        paths = [
            ImplementationPath(
                name="Decorator/Middleware",
                description="Add via function decorator or middleware",
                affected_layers=["presentation", "business"],
                effort="low",
                risk="low",
                rationale="Minimal invasiveness, reusable",
            ),
            ImplementationPath(
                name="Centralized Service",
                description="Dedicated service instance",
                affected_layers=["business", "infrastructure"],
                effort="medium",
                risk="low",
                rationale="Centralized management and configuration",
            ),
            ImplementationPath(
                name="Aspect-Oriented",
                description="Aspect injection at runtime",
                affected_layers=["business"],
                effort="high",
                risk="medium",
                rationale="Complete separation, powerful but complex",
            ),
        ]
        return paths

    def _infrastructure_paths(self, style: str) -> list[ImplementationPath]:
        """Generate infrastructure implementation paths"""
        paths = [
            ImplementationPath(
                name="Configuration-Driven",
                description="Environment variables + config files",
                affected_layers=["infrastructure"],
                effort="low",
                risk="low",
                rationale="Simple, well-understood approach",
            ),
            ImplementationPath(
                name="Service Registry",
                description="Dynamic service discovery",
                affected_layers=["infrastructure"],
                effort="medium",
                risk="medium",
                rationale="Enables dynamic scaling and resilience",
            ),
            ImplementationPath(
                name="IaC (Infrastructure as Code)",
                description="Terraform/CloudFormation definitions",
                affected_layers=["infrastructure"],
                effort="high",
                risk="low",
                rationale="Reproducible, version-controlled infrastructure",
            ),
        ]
        return paths

    def _score_path(self, path: ImplementationPath) -> float:
        """Score path on fit, effort, and risk"""
        effort_score = {
            "low": 0.9,
            "medium": 0.7,
            "high": 0.5,
        }[path.effort]

        risk_score = {
            "low": 0.9,
            "medium": 0.6,
            "high": 0.3,
        }[path.risk]

        return (effort_score * 0.4) + (risk_score * 0.6)

    def _select_diverse_paths(
        self, scored: list[tuple[ImplementationPath, float]], min_count: int = 3
    ) -> list[ImplementationPath]:
        """
        Select ≥min_count distinct paths with variety.
        Different effort levels, risk profiles, and layers.
        """
        if len(scored) <= min_count:
            return [path for path, _ in scored]

        efforts = {"low": 0, "medium": 1, "high": 2}
        risks = {"low": 0, "medium": 1, "high": 2}

        selected: dict[tuple[int, int], tuple[ImplementationPath, float]] = {}

        for path, score in sorted(scored, key=lambda x: -x[1]):
            effort_idx = efforts[path.effort]
            risk_idx = risks[path.risk]
            key = (effort_idx, risk_idx)

            if key not in selected:
                selected[key] = (path, score)

            if len(selected) >= min_count:
                break

        result = [path for path, _ in selected.values()]

        if len(result) < min_count:
            result.extend([path for path, _ in scored[len(result):]])

        return result[:min_count + 1]
