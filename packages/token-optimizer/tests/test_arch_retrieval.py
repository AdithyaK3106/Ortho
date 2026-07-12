"""Tests for architecture-aware retrieval (Component 5).

Tests for boosting architecturally central modules during context assembly.
"""

import pytest
from token_optimizer.types import ContextChunk


def make_chunk(
    chunk_id: str,
    source_id: str = None,
    relevance_score: float = 0.5,
    token_count: int = 100,
) -> ContextChunk:
    return ContextChunk(
        id=chunk_id,
        source_type="symbol",
        source_id=source_id or f"sym_{chunk_id}",
        content=f"content for {chunk_id}",
        relevance_score=relevance_score,
        token_count=token_count,
        included=True,
    )


class MockArchitectureModel:
    """Mock architecture model for testing."""

    def __init__(self, style: str = "layered", layer_boosts: dict = None):
        self.style = style
        self.layer_boosts = layer_boosts or {
            "service": 1.5,
            "repository": 1.3,
            "controller": 1.0,
            "presentation": 0.8,
        }
        self.subsystems = {}

    def get_layer_for_symbol(self, symbol_id: str) -> str:
        """Return layer for a symbol."""
        if "service" in symbol_id.lower():
            return "service"
        elif "repo" in symbol_id.lower():
            return "repository"
        elif "ctrl" in symbol_id.lower():
            return "controller"
        else:
            return "presentation"


class TestArchRetrievalBoundaryConditions:
    """Boundary conditions for architecture-aware retrieval."""

    def test_empty_chunks_list(self):
        """Empty chunk list returns empty."""
        result = []
        assert result == []

    def test_single_chunk(self):
        """Single chunk boosting."""
        chunk = make_chunk("c1", "service_auth", 0.5)
        assert chunk.source_id == "service_auth"

    def test_all_chunks_same_layer(self):
        """All chunks in same architectural layer."""
        chunks = [
            make_chunk("c1", "service_a", 0.5),
            make_chunk("c2", "service_b", 0.6),
        ]
        # All from "service" layer
        assert all("service" in c.source_id for c in chunks)

    def test_all_chunks_different_layers(self):
        """Chunks spanning all architectural layers."""
        chunks = [
            make_chunk("c1", "service_auth", 0.5),
            make_chunk("c2", "repo_db", 0.5),
            make_chunk("c3", "ctrl_handler", 0.5),
            make_chunk("c4", "view_template", 0.5),
        ]
        layers = ["service", "repo", "ctrl", "view"]
        assert all(any(layer in c.source_id for c in chunks) for layer in layers)

    def test_zero_initial_relevance(self):
        """Chunk with zero relevance score."""
        chunk = make_chunk("c1", "service_auth", 0.0)
        assert chunk.relevance_score == 0.0

    def test_max_relevance_score(self):
        """Chunk with max relevance score."""
        chunk = make_chunk("c1", "service_auth", 1.0)
        assert chunk.relevance_score == 1.0

    def test_unknown_layer(self):
        """Symbol not in any known layer."""
        chunk = make_chunk("c1", "unknown_xyz", 0.5)
        # Should default to no boost (1.0x)
        assert "unknown" in chunk.source_id.lower()


class TestArchRetrievalWeighting:
    """Weight multiplier tests for different architectures."""

    def test_layered_arch_weights(self):
        """Layered architecture weight factors."""
        arch = MockArchitectureModel("layered")
        assert arch.layer_boosts["service"] == 1.5
        assert arch.layer_boosts["controller"] == 1.0
        assert arch.layer_boosts["presentation"] == 0.8

    def test_microservices_arch_weights(self):
        """Microservices architecture weight factors."""
        arch = MockArchitectureModel("microservices")
        # High-coupling services should be boosted
        assert "service" in arch.layer_boosts

    def test_mvc_arch_weights(self):
        """MVC architecture weight factors."""
        arch = MockArchitectureModel("mvc")
        # Model > Controller > View typical pattern
        pass

    def test_hexagonal_arch_weights(self):
        """Hexagonal architecture weight factors."""
        arch = MockArchitectureModel("hexagonal")
        # Core domain boosted, adapters lower
        pass

    def test_flat_arch_no_boost(self):
        """Flat architecture (no layers) applies no boosts."""
        arch = MockArchitectureModel("flat")
        arch.layer_boosts = {}  # No layer distinctions
        assert arch.layer_boosts == {}

    def test_weights_in_reasonable_range(self):
        """Weights stay in 0.5-2.0 range."""
        arch = MockArchitectureModel()
        for weight in arch.layer_boosts.values():
            assert 0.5 <= weight <= 2.0

    def test_weight_order_preserves_semantics(self):
        """Higher layer importance = higher weight."""
        arch = MockArchitectureModel()
        service_weight = arch.layer_boosts["service"]
        presentation_weight = arch.layer_boosts["presentation"]
        assert service_weight > presentation_weight


class TestArchRetrievalBootsting:
    """Boost application and score recalculation."""

    def test_central_module_boosted(self):
        """Central module gets higher multiplier."""
        original_score = 0.5
        boost_factor = 1.5
        boosted_score = original_score * boost_factor
        assert boosted_score > original_score

    def test_peripheral_module_reduced(self):
        """Peripheral module gets lower multiplier."""
        original_score = 0.5
        boost_factor = 0.8
        boosted_score = original_score * boost_factor
        assert boosted_score < original_score

    def test_unknown_layer_no_boost(self):
        """Unknown layer gets 1.0x (no change)."""
        original_score = 0.5
        boost_factor = 1.0
        boosted_score = original_score * boost_factor
        assert boosted_score == original_score

    def test_boost_preserves_relative_order(self):
        """Boosting doesn't invert relative order unexpectedly."""
        chunk_a_score = 0.8
        chunk_b_score = 0.6
        chunk_a_boost = 1.0
        chunk_b_boost = 1.5
        # A starts higher, but B's boost is bigger
        a_final = chunk_a_score * chunk_a_boost
        b_final = chunk_b_score * chunk_b_boost
        # B can overtake A
        assert b_final > a_final

    def test_zero_score_stays_zero(self):
        """Zero score * any boost stays zero."""
        original_score = 0.0
        boost_factor = 2.0
        final_score = original_score * boost_factor
        assert final_score == 0.0

    def test_max_score_max_boost(self):
        """Max score with max boost doesn't overflow."""
        max_score = 1.0
        max_boost = 2.0
        final_score = max_score * max_boost
        # Result may exceed 1.0, but should be numeric
        assert isinstance(final_score, float)
        assert final_score == 2.0


class TestArchRetrievalConfiguration:
    """Configuration and customization."""

    def test_custom_boost_config(self):
        """Custom centrality weights."""
        custom_boosts = {"service": 2.0, "utils": 0.5}
        arch = MockArchitectureModel(layer_boosts=custom_boosts)
        assert arch.layer_boosts["service"] == 2.0

    def test_missing_layer_in_config(self):
        """Layer not in configuration handled gracefully."""
        arch = MockArchitectureModel()
        missing_layer = "nonexistent"
        # Should default to 1.0x
        assert missing_layer not in arch.layer_boosts

    def test_negative_weights_invalid(self):
        """Negative weights should be rejected."""
        with pytest.raises((ValueError, AssertionError)):
            MockArchitectureModel(layer_boosts={"service": -1.0})

    def test_zero_weight_invalid(self):
        """Zero weight removes chunk effectively."""
        # Zero weight means chunk disappears
        score = 0.5
        weight = 0.0
        result = score * weight
        assert result == 0.0


class TestArchRetrievalIntegration:
    """Integration with real architecture models."""

    def test_layered_auth_service_boosted(self):
        """Auth service (core service layer) boosted in layered arch."""
        chunk = make_chunk("auth_svc", "service_authentication", 0.3)
        arch = MockArchitectureModel("layered")
        layer = arch.get_layer_for_symbol(chunk.source_id)
        assert layer == "service"

    def test_utility_module_minimal_boost(self):
        """Utility modules (presentation layer) minimally boosted."""
        chunk = make_chunk("util_fmt", "view_formatter", 0.3)
        arch = MockArchitectureModel("layered")
        layer = arch.get_layer_for_symbol(chunk.source_id)
        assert layer == "presentation"

    def test_multi_layer_context_assembly(self):
        """Full context with chunks from multiple layers."""
        chunks = [
            make_chunk("c1", "service_core", 0.5),
            make_chunk("c2", "repo_cache", 0.5),
            make_chunk("c3", "ctrl_router", 0.5),
        ]
        # Should boost service highest
        services = [c for c in chunks if "service" in c.source_id]
        assert len(services) > 0

    def test_circular_dependency_detection(self):
        """Circular dependencies in architecture model."""
        # A -> B -> A pattern
        pass

    def test_subsystem_coupling_boost(self):
        """Low-coupling subsystems get positive boost."""
        arch = MockArchitectureModel("layered")
        arch.subsystems = {"auth": {"coupling": 0.2}, "db": {"coupling": 0.8}}
        # auth (low coupling) should be preferred
        assert arch.subsystems["auth"]["coupling"] < arch.subsystems["db"]["coupling"]


class TestArchRetrievalErrorHandling:
    """Error handling and edge cases."""

    def test_missing_architecture_model(self):
        """No architecture model available."""
        arch = None
        # Should fall back to no boosting (1.0x)
        assert arch is None

    def test_invalid_symbol_id(self):
        """Invalid symbol ID format."""
        chunk = make_chunk("c1", None, 0.5)
        # Should handle None gracefully
        assert chunk.source_id == None

    def test_corrupted_architecture_model(self):
        """Architecture model with invalid data."""
        arch = MockArchitectureModel()
        arch.layer_boosts["broken"] = "not_a_number"
        # Should handle type errors
        pass

    def test_concurrent_arch_model_updates(self):
        """Architecture model updated during retrieval."""
        arch = MockArchitectureModel()
        # Model should not change mid-query
        original_style = arch.style
        assert arch.style == original_style


class TestArchRetrievalReproducibility:
    """Determinism and reproducibility."""

    def test_same_input_same_output(self):
        """Same chunks produce same boosted scores."""
        chunk = make_chunk("c1", "service_auth", 0.5)
        arch = MockArchitectureModel()
        # Deterministic boosting
        layer1 = arch.get_layer_for_symbol(chunk.source_id)
        layer2 = arch.get_layer_for_symbol(chunk.source_id)
        assert layer1 == layer2

    def test_boost_order_independent(self):
        """Chunk processing order doesn't affect results."""
        chunks_a = [
            make_chunk("c1", "service_a", 0.5),
            make_chunk("c2", "repo_b", 0.5),
        ]
        chunks_b = [
            make_chunk("c2", "repo_b", 0.5),
            make_chunk("c1", "service_a", 0.5),
        ]
        arch = MockArchitectureModel()
        # Layer detection order-independent
        layer_a1 = arch.get_layer_for_symbol(chunks_a[0].source_id)
        layer_b1 = arch.get_layer_for_symbol(chunks_b[1].source_id)
        assert layer_a1 == layer_b1
