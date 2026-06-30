---
status: accepted
date: 2026-06-30
deciders: ARCHITECT (task-004)
---

# ADR-006: EmbeddingProvider Abstraction for ContextHub

## Status

Accepted (GATE-2, task-004 architecture review)

## Context

ContextHub (Pillar 2) must support multiple embedding providers (Anthropic, local models, Ollama) to serve different deployment environments and cost constraints. The initial implementation should not assume a specific provider, nor should it create tight coupling to any vendor's SDK.

FRD principle #7 states: "Model-agnostic architecture" — the system should work with any embedding provider.

## Problem

If ArtifactStore directly imports and uses Anthropic's SDK:
1. Hard dependency on Anthropic (vendor lock-in)
2. Cannot easily swap providers
3. Testing requires API credentials (integration tests harder)
4. Future provider additions require modifying core code

## Decision

Introduce `EmbeddingProvider` abstract base class. ArtifactStore depends on this abstraction, not concrete implementations.

```python
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """Abstraction for embedding computation. Implementations handle specific providers."""
    
    @abstractmethod
    async def embed(self, text: str, artifact_type: str) -> list[float]:
        """Compute embedding for text."""
        ...
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings from this provider."""
        ...


class ArtifactStore:
    def __init__(
        self,
        db: OrthoDatabase,
        embedding_provider: EmbeddingProvider | None = None
    ):
        self.embedding_provider = embedding_provider or NullEmbedding()
```

**Implementations:**
- `NullEmbedding` — no-op provider (Phase 1 default, testing)
- `AnthropicEmbedding` — uses Anthropic API (optional, configurable)
- `LocalEmbedding` — uses local `.gguf` model (optional, extensible)

## Rationale

1. **Decoupling:** ArtifactStore never imports Anthropic SDK. SDK is encapsulated in AnthropicEmbedding only.
2. **Testability:** Unit tests use NullEmbedding; no API credentials needed.
3. **Extensibility:** New providers added without modifying ArtifactStore.
4. **FRD Compliance:** Satisfies principle #7 (model-agnostic architecture).
5. **Cost Control:** Phase 1 uses free NullEmbedding. Phase 2+ can opt-in to paid providers.

## Consequences

### Positive
- ArtifactStore is provider-agnostic
- Easy to test (mock providers, no API calls)
- Easy to extend (add new providers by extending interface)
- Configuration-driven (provider selected via `.ortho/config.toml`)
- Phase 4 Token Optimizer can add smart provider selection

### Negative
- Slight indirection (abstraction layer)
- Requires concrete provider implementation choice
- Adds one more module (`embedding/provider.py`)

## Alternatives Considered

### 1. Direct Anthropic SDK Dependency
```python
from anthropic import Anthropic

class ArtifactStore:
    def __init__(self, db, anthropic_key: str):
        self.client = Anthropic(api_key=anthropic_key)
```

**Rejected:** Tight coupling, vendor lock-in, hard to test, Phase 4 restricted.

### 2. String-Based Provider Selection
```python
class ArtifactStore:
    def __init__(self, db, provider: str = "null"):
        if provider == "anthropic":
            from anthropic import Anthropic
            self.embed_fn = ...
        elif provider == "local":
            ...
```

**Rejected:** Less type-safe, runtime errors possible, code harder to follow.

### 3. Abstract Base Class (Chosen)
Clean, type-safe, testable, extensible. No downsides.

## Implementation Notes

**Provider discovery:**
```python
# In config.toml
[context_hub]
embedding_provider = "null"              # null | anthropic | local | ollama
embedding_model = "voyage-3-lite"
embedding_local_path = null
```

**Factory (optional, Phase 3):**
```python
def create_embedding_provider(config: OrthoConfig) -> EmbeddingProvider:
    if config.context_hub.embedding_provider == "null":
        return NullEmbedding()
    elif config.context_hub.embedding_provider == "anthropic":
        return AnthropicEmbedding(model=config.context_hub.embedding_model)
    elif config.context_hub.embedding_provider == "local":
        return LocalEmbedding(path=config.context_hub.embedding_local_path)
    else:
        raise ValueError(f"Unknown provider: {config.context_hub.embedding_provider}")
```

## Evidence

- ✅ FRD principle #7 (model-agnostic architecture) satisfied
- ✅ No circular dependencies introduced
- ✅ Verified with task-001/002/003 interfaces (compatible)
- ✅ Testable without API credentials (NullEmbedding)
- ✅ Standard Python ABC pattern (idiomatic)

## See Also

- FRD §2 (Architecture Rules, principle #7)
- FRD §7 (Pillar 2 — ContextHub)
- ADR-007 (FTS5 Triggers)
- Task-004 spec.md §Embedding Provider Abstraction
