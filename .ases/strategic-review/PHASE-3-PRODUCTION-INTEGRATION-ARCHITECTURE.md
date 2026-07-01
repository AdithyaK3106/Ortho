# Phase 3: Production Integration Architecture

**Date:** 2026-07-01  
**Purpose:** Design safest integration if Phase 2 approves GitNexus adoption  
**Constraint:** GitNexus must never leak into Ortho core. Everything through interfaces.  
**Status:** Roadmap design (execution only if Phase 2 GO decision)

---

## Core Principle

**Repository Intelligence becomes a pluggable provider.**

Rest of Ortho depends only on abstract interfaces, not on GitNexus directly.

---

## Architecture Pattern

```
┌─────────────────────────────────────────────────────┐
│           Ortho Engineering Intelligence             │
│  (ContextHub, Architecture Detection, ASES, Memory) │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
        ┌──────────────────────┐
        │ RepositoryAnalysis   │
        │ Provider Interface   │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┬──────────────────┐
        ↓                     ↓                  ↓
    ┌────────┐           ┌────────┐        ┌──────────┐
    │ Ortho  │           │GitNexus│        │ Hybrid / │
    │Provider│           │Provider│        │ Custom   │
    └────────┘           └────────┘        └──────────┘
        ↓                     ↓                  ↓
    ┌────────┐           ┌────────┐        ┌──────────┐
    │tree-   │           │GitNexus│        │Both      │
    │sitter  │           │library │        │systems   │
    └────────┘           └────────┘        └──────────┘
```

---

## Interface Definitions

### RepositoryAnalysisProvider (Core Interface)

```python
class RepositoryAnalysisProvider(ABC):
    """Abstract interface for repository analysis."""
    
    @abstractmethod
    def analyze(self, repo_path: Path) -> AnalysisResult:
        """Run full repository analysis."""
        pass
    
    @abstractmethod
    def extract_symbols(self, file_path: Path) -> List[Symbol]:
        """Extract symbols from single file."""
        pass
    
    @abstractmethod
    def extract_imports(self, file_path: Path) -> List[ImportEdge]:
        """Extract imports from single file."""
        pass
    
    @abstractmethod
    def extract_calls(self, file_path: Path) -> List[CallEdge]:
        """Extract call graph from single file."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, repo_path: Path) -> DependencyGraph:
        """Extract external dependencies."""
        pass
    
    @abstractmethod
    def get_incremental_update(
        self, 
        repo_path: Path, 
        changed_files: List[Path]
    ) -> AnalysisResult:
        """Get incremental update for changed files."""
        pass
    
    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Languages this provider supports."""
        pass
```

### Symbol Data Model (Shared)

```python
class Symbol:
    """Repository symbol (function, class, variable)."""
    id: str
    name: str
    qualified_name: str
    type: SymbolType  # function, class, variable
    location: Location
    docstring: Optional[str]
    metadata: Dict  # decorators, is_async, types, etc.
```

### Other Data Models

```python
class ImportEdge:
    source_module: str
    target_module: str
    import_type: str  # from, import, relative
    location: Location
    confidence: float

class CallEdge:
    caller: Symbol
    callee: Symbol
    location: Location
    confidence: float

class DependencyGraph:
    packages: List[Package]
    edges: List[Dependency]
```

---

## Implementation Adapters

### OrthoRepositoryAnalysisProvider

```python
class OrthoRepositoryAnalysisProvider(RepositoryAnalysisProvider):
    """Original Ortho implementation."""
    
    def __init__(self, repo_path: Path):
        self.repo = repo_path
        self.python_adapter = PythonAdapter(repo_path)
        self.symbol_extractor = SymbolExtractor()
        self.import_graph = ImportGraphBuilder()
        self.call_graph = CallGraphBuilder()
        self.deps = DependencyGraphBuilder()
    
    def analyze(self, repo_path: Path) -> AnalysisResult:
        # Original Ortho logic
        pass
    
    def supported_languages(self) -> List[str]:
        return ["python"]
```

### GitNexusRepositoryAnalysisProvider

```python
class GitNexusRepositoryAnalysisProvider(RepositoryAnalysisProvider):
    """GitNexus-based implementation."""
    
    def __init__(self, repo_path: Path, languages: List[str] = None):
        self.repo = GitNexusRepository(repo_path)
        self.languages = languages or ["python", "typescript", "go"]
    
    def analyze(self, repo_path: Path) -> AnalysisResult:
        # GitNexus analysis logic
        result = AnalysisResult()
        for lang in self.supported_languages:
            symbols = self.repo.get_symbols(language=lang)
            imports = self.repo.get_imports(language=lang)
            calls = self.repo.get_call_graph(language=lang)
            result.add_symbols(self._translate_symbols(symbols))
            result.add_imports(self._translate_imports(imports))
            result.add_calls(self._translate_calls(calls))
        return result
    
    def extract_symbols(self, file_path: Path) -> List[Symbol]:
        gn_symbols = self.repo.get_symbols(file_path)
        return [self._translate_symbol(s) for s in gn_symbols]
    
    def supported_languages(self) -> List[str]:
        return self.languages
    
    def _translate_symbol(self, gn_symbol) -> Symbol:
        """Translate GitNexus symbol to Ortho Symbol."""
        return Symbol(
            id=gn_symbol.id,
            name=gn_symbol.name,
            qualified_name=gn_symbol.qualified_name,
            type=SymbolType[gn_symbol.type],
            location=Location(
                file=gn_symbol.location.file,
                line=gn_symbol.location.line,
                column=gn_symbol.location.column,
            ),
            docstring=gn_symbol.docstring,
            metadata={
                "decorators": getattr(gn_symbol, "decorators", []),
                "is_async": getattr(gn_symbol, "is_async", False),
            }
        )
```

### HybridRepositoryAnalysisProvider

```python
class HybridRepositoryAnalysisProvider(RepositoryAnalysisProvider):
    """Use both providers, merge results."""
    
    def __init__(self, repo_path: Path):
        self.ortho = OrthoRepositoryAnalysisProvider(repo_path)
        self.gitnexus = GitNexusRepositoryAnalysisProvider(repo_path)
        self.primary = self.gitnexus  # primary
        self.fallback = self.ortho    # fallback
    
    def analyze(self, repo_path: Path) -> AnalysisResult:
        # Try primary first
        try:
            return self.primary.analyze(repo_path)
        except Exception as e:
            logger.warning(f"GitNexus failed: {e}, falling back to Ortho")
            return self.fallback.analyze(repo_path)
    
    def supported_languages(self) -> List[str]:
        # Union of both
        return sorted(set(self.ortho.supported_languages + 
                         self.gitnexus.supported_languages))
```

---

## Dependency Inversion

### Current (Tight Coupling) ❌

```
ContextHub
  ↓
IncrementalIndexer
  ↓
CallGraphBuilder
  ↓
PythonAdapter
  ↓
tree-sitter

(Hard dependency on specific implementation)
```

### Desired (Loose Coupling) ✅

```
ContextHub
  ↓
IncrementalIndexer
  ↓
RepositoryAnalysisProvider (interface)
  ↓
├─ OrthoProvider
├─ GitNexusProvider
└─ HybridProvider

(Depends on interface, not implementation)
```

### Implementation

```python
# OLD: Tight coupling
class IncrementalIndexer:
    def __init__(self, repo_path):
        self.call_graph = CallGraphBuilder()  # Hard dependency

# NEW: Loose coupling
class IncrementalIndexer:
    def __init__(self, repo_path, provider: RepositoryAnalysisProvider):
        self.provider = provider  # Depends on interface

    def update(self, changed_files):
        # Use provider, not hardcoded CallGraphBuilder
        result = self.provider.get_incremental_update(
            self.repo_path, 
            changed_files
        )
```

---

## Configuration & Selection

### config.toml

```toml
[repository_intelligence]
provider = "gitnexus"  # or "ortho" or "hybrid"
fallback_provider = "ortho"

[repository_intelligence.gitnexus]
languages = ["python", "typescript", "go"]
cache = true
timeout_seconds = 300

[repository_intelligence.ortho]
python_only = true
```

### Environment Variables

```bash
ORTHO_REPO_PROVIDER=gitnexus
ORTHO_REPO_FALLBACK=ortho
ORTHO_GITNEXUS_LANGUAGES=python,typescript,go
```

### Programmatic Selection

```python
config = load_config()

if config.feature_flags.use_gitnexus:
    provider = GitNexusRepositoryAnalysisProvider(repo_path)
else:
    provider = OrthoRepositoryAnalysisProvider(repo_path)

# ContextHub doesn't know which provider
incremental_indexer = IncrementalIndexer(repo_path, provider)
```

---

## Feature Flags & A/B Testing

### Feature Flag Structure

```python
class RepositoryFeatureFlags:
    use_gitnexus: bool = False
    gitnexus_languages: List[str] = ["python"]
    fallback_to_ortho_on_error: bool = True
    measure_both_providers: bool = False  # For A/B testing
    gitnexus_max_repo_size: int = 1_000_000  # files
    gitnexus_timeout: int = 300  # seconds
```

### A/B Testing

```python
class ABTestRepositoryProvider(RepositoryAnalysisProvider):
    """Run both providers, compare results."""
    
    def __init__(self, repo_path, test_config):
        self.ortho = OrthoRepositoryAnalysisProvider(repo_path)
        self.gitnexus = GitNexusRepositoryAnalysisProvider(repo_path)
        self.test_config = test_config
    
    def analyze(self, repo_path: Path) -> AnalysisResult:
        # Run both
        ortho_result = self.ortho.analyze(repo_path)
        gitnexus_result = self.gitnexus.analyze(repo_path)
        
        # Compare
        comparison = self._compare(ortho_result, gitnexus_result)
        
        # Log metrics
        telemetry.log_ab_test(
            ortho_symbols=len(ortho_result.symbols),
            gitnexus_symbols=len(gitnexus_result.symbols),
            accuracy_delta=comparison.accuracy_delta,
            latency_delta=comparison.latency_delta,
        )
        
        # Return primary
        return gitnexus_result if self.test_config.prefer_gitnexus else ortho_result
```

---

## Versioning & Upgrade Strategy

### Semantic Versioning

```
Ortho:     3.2.0  (major.minor.patch)
GitNexus:  1.5.0  (independent)
```

### Pinned Dependencies

```toml
[dependencies]
gitnexus = ">=1.5.0,<2.0.0"  # Allow minor/patch, block major
```

### Breaking Change Management

```python
class RepositoryAnalysisProvider:
    """Version 1 of interface."""
    
    @abstractmethod
    def analyze(self, repo_path: Path) -> AnalysisResult:
        pass
    
    def __version__(self):
        return 1
```

If GitNexus 2.0 changes API:
1. Create new interface version 2
2. Implement adapters for both 1 & 2
3. Version bump in Ortho
4. Deprecation window for old version

---

## Fallback & Rollback Strategy

### Graceful Degradation

```python
provider = GitNexusRepositoryAnalysisProvider(repo_path)

try:
    result = provider.analyze(repo_path)
except GitNexusError as e:
    logger.error(f"GitNexus failed: {e}")
    if config.fallback_provider == "ortho":
        logger.info("Falling back to Ortho")
        fallback = OrthoRepositoryAnalysisProvider(repo_path)
        result = fallback.analyze(repo_path)
    else:
        raise
```

### Feature Flag Rollback

```bash
# In production, if issues detected:
ORTHO_REPO_PROVIDER=ortho  # Revert to Ortho
# Restart Ortho
systemctl restart ortho
# Data untouched, just using different provider
```

### Zero-Downtime Rollback

```python
# Both providers can read same data
# Just switch which one writes
old_provider = current_provider
current_provider = fallback_provider

# New analysis uses fallback
# Old data still accessible
# No re-indexing needed
```

---

## Telemetry & Observability

### Metrics to Track

```python
class RepositoryAnalysisMetrics:
    provider_in_use: str  # "ortho", "gitnexus", "hybrid"
    symbols_extracted: int
    imports_found: int
    calls_found: int
    dependencies_found: int
    analysis_time_ms: int
    memory_used_mb: int
    error_rate: float  # % of requests failing
    provider_switch_count: int  # fallback invocations
    confidence_scores: List[float]  # for quality assessment
```

### Logging

```python
logger.info(
    "Repository analysis complete",
    extra={
        "provider": "gitnexus",
        "languages": ["python", "typescript"],
        "symbols": 45000,
        "duration_ms": 12500,
        "memory_peak_mb": 450,
    }
)
```

### Dashboards

Monitor:
- Analysis latency by provider
- Error rates by provider
- Fallback frequency
- Symbol count consistency (both providers should find similar)
- Memory usage trends
- Coverage by language

---

## Testing Strategy

### Unit Tests

```python
def test_ortho_provider_accuracy():
    provider = OrthoRepositoryAnalysisProvider(test_repo)
    result = provider.analyze(test_repo)
    assert len(result.symbols) == expected_symbol_count

def test_gitnexus_provider_accuracy():
    provider = GitNexusRepositoryAnalysisProvider(test_repo)
    result = provider.analyze(test_repo)
    assert len(result.symbols) == expected_symbol_count

def test_both_providers_same_result():
    ortho = OrthoRepositoryAnalysisProvider(test_repo)
    gitnexus = GitNexusRepositoryAnalysisProvider(test_repo)
    
    ortho_result = ortho.analyze(test_repo)
    gitnexus_result = gitnexus.analyze(test_repo)
    
    assert symbols_match(ortho_result, gitnexus_result)
```

### Integration Tests

```python
def test_contexthub_with_gitnexus():
    provider = GitNexusRepositoryAnalysisProvider(test_repo)
    hub = ContextHub(provider)
    
    hub.ingest_repository(test_repo)
    results = hub.search("find all classes")
    
    assert len(results) > 0
```

### Regression Tests

Run full test suite with each provider:
- All Phase 1 tests pass with GitNexusProvider?
- All Phase 1 tests pass with OrthoProvider?
- Both providers produce compatible results?

---

## Migration Path

### Week 1: Adapter Implementation
- [ ] Implement RepositoryAnalysisProvider interface
- [ ] Implement OrthoRepositoryAnalysisProvider (wrap existing code)
- [ ] Implement GitNexusRepositoryAnalysisProvider (wrap GitNexus)
- [ ] Write unit tests for each

### Week 2: Integration
- [ ] Update IncrementalIndexer to use provider
- [ ] Update ContextHub to use provider
- [ ] Update ArchitectureDetector to use provider
- [ ] Run existing tests with both providers

### Week 3: Rollout
- [ ] Deploy to staging with feature flag `use_gitnexus=false` (Ortho only)
- [ ] Test with Ortho provider for 1 week
- [ ] Gradually enable GitNexus (10% → 50% → 100% traffic)
- [ ] Monitor metrics

### Week 4: Verification
- [ ] A/B test both providers (measure_both_providers=true)
- [ ] Compare accuracy, latency, memory
- [ ] Confirm results match
- [ ] Document performance baseline

### Week 5: Stabilization
- [ ] Remove feature flag (GitNexus is default)
- [ ] Keep fallback to Ortho (automatic on error)
- [ ] Monitor for 2 weeks
- [ ] Decide: deprecate Ortho or keep both?

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **GitNexus API breaking change** | Version pinning, adapter pattern isolates |
| **Data incompatibility** | A/B testing proves compatibility before switch |
| **Performance regression** | Telemetry detects latency increases, automatic fallback |
| **Memory explosion** | Memory limits, large repo handling tested |
| **Silent data corruption** | Consistency checks, symbol count comparisons |
| **Confidence score miscalibration** | Manual validation, edge case testing |

---

## Rollback Procedure

If issues detected in production:

```bash
# Step 1: Identify issue
# (telemetry shows GitNexus error rate >5%)

# Step 2: Enable fallback
ORTHO_REPO_FALLBACK=ortho

# Step 3: Revert to Ortho
ORTHO_REPO_PROVIDER=ortho

# Step 4: Restart
systemctl restart ortho

# Step 5: Verify
curl http://localhost:8000/health
# Should return "ortho" as provider

# Step 6: Investigate
# Review logs, understand why GitNexus failed
# Fix and redeploy
```

**Total downtime:** <2 minutes (if graceful degradation implemented)

---

## Success Criteria

✅ All Phase 1 tests pass with GitNexusProvider  
✅ All Phase 1 tests pass with OrthoProvider  
✅ Both providers produce compatible results (symbol count within 5%)  
✅ GitNexus faster by >5% OR more accurate (benchmark dependent)  
✅ Fallback works (automatic failover to Ortho on error)  
✅ Feature flags work (can switch at runtime)  
✅ Telemetry shows no regressions  
✅ 2-week stable operation in production  

---

## Principles Maintained

✅ GitNexus never leaks into Ortho core  
✅ Everything goes through RepositoryAnalysisProvider interface  
✅ Ortho owns interface, GitNexus owns implementation  
✅ Both providers remain swappable  
✅ Fallback always available  
✅ Zero-downtime rollback possible  
✅ Long-term vendor independence preserved

