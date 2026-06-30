# ADR-005: Language Adapter Plugin Model — Extensible Source Code Analysis

**Status:** PROPOSED  
**Date:** 2026-06-30  
**Author:** ARCHITECT  
**Approved by:** [Pending human approval]

---

## Context

Ortho's Pillar 1 (Repository Intelligence) must extract and analyze source code from multiple programming languages:
- **Phase 1:** Python (Week 3–6)
- **Phase 2:** TypeScript/JavaScript (Week 3–6)
- **Phase 3+:** Go, Java, Rust, C++, Ruby, PHP, others

Each language has unique syntax, AST structure, symbol representation, and call graph semantics. The system needs a clean, extensible architecture for adding language support without monolithic code or tight coupling.

---

## Problem Statement

**How should Ortho support multiple programming languages?**

Key requirements from FRD:
- Section 6: "LanguageAdapter interface" defines the contract
- Principle 5: "Small composable modules" — each language should be independent
- Principle 8: "Every capability independently usable" — adapters should be swappable

Options:
1. **Monolithic with if-statements:** Single file, language conditionals everywhere (NOT RECOMMENDED)
2. **Abstract LanguageAdapter plugin model:** Separate class per language, registry mapping
3. **External LSP (Language Server Protocol):** Delegate to language-specific servers (overcomplicated)

---

## Alternatives Considered

### Option A: Monolithic with Language Conditionals

**Description:** Single analyzer file with if-statements for each language.

```python
def extract_symbols(file_path, source, language):
    if language == "python":
        # 200 lines of Python-specific AST logic
    elif language == "typescript":
        # 250 lines of TypeScript-specific logic
    elif language == "go":
        # 180 lines of Go-specific logic
    # ... 20+ more branches
```

**Pros:**
- Simple to start with (one file)
- Fewer abstractions initially

**Cons:**
- ❌ Unmaintainable at scale (1000+ lines, hard to change without breaking others)
- ❌ Violates FRD Principle 5 (not small, not composable)
- ❌ Hard to test (coupled logic, all-or-nothing testing)
- ❌ Hard to delegate (can't ask different expert to own Go adapter)
- ❌ Performance: unnecessary branches checked for every file
- ❌ No true independence (one language's changes affect all)

**Verdict:** ❌ **Rejected** — Fails FRD principles at scale.

---

### Option C: External LSP (Language Server Protocol)

**Description:** Use industry-standard Language Server Protocol to delegate parsing to language-specific servers.

**Pros:**
- Industry standard (vscode uses this)
- Any LSP-compatible language server works
- No re-implementation needed (leverage existing tools)

**Cons:**
- ❌ Overkill for Phase 1 (adds JSON-RPC complexity)
- ❌ Requires external process management (LSP servers are separate executables)
- ❌ Network round-trips (higher latency than in-process)
- ❌ Harder to debug (communication across process boundaries)
- ❌ Not all languages have quality LSP servers
- ❌ More dependencies to manage

**Verdict:** ❌ **Rejected** — Over-engineered for Phase 1; revisit in Phase 3+ if team grows.

---

### Option B: Abstract LanguageAdapter Plugin Model (Chosen)

**Description:** Define abstract `LanguageAdapter` base class in Repo Intelligence. Each language implements concrete subclass. Registry maps file extensions to adapter instances.

**Architecture:**

```python
# Base class (abstract)
class LanguageAdapter(ABC):
    @property
    def language(self) -> str: ...
    
    @property
    def file_extensions(self) -> list[str]: ...
    
    @abstractmethod
    def extract_symbols(self, file_path, source) -> list[Symbol]: ...
    
    @abstractmethod
    def extract_imports(self, file_path, source) -> list[ImportEdge]: ...
    
    @abstractmethod
    def extract_calls(self, file_path, source, symbols) -> list[CallEdge]: ...
    
    @abstractmethod
    def chunk(self, file_path, source, max_size) -> list[ContextChunk]: ...

# Concrete implementations
class PythonAdapter(LanguageAdapter):
    language = "python"
    file_extensions = [".py", ".pyi"]
    # 200 lines of Python-specific logic
    
class TypeScriptAdapter(LanguageAdapter):
    language = "typescript"
    file_extensions = [".ts", ".tsx", ".js", ".jsx"]
    # 250 lines of TypeScript-specific logic

class GoAdapter(LanguageAdapter):
    language = "go"
    file_extensions = [".go"]
    # 180 lines of Go-specific logic

# Registry (lazy-loads adapters)
class AdapterRegistry:
    adapters = {
        ".py": PythonAdapter(),
        ".ts": TypeScriptAdapter(),
        ".go": GoAdapter(),
    }
    
    @classmethod
    def get_adapter(cls, file_path: str) -> LanguageAdapter:
        ext = Path(file_path).suffix
        return cls.adapters.get(ext, None)
```

**Pros:**
- ✅ Clean separation of concerns (each adapter handles one language)
- ✅ Easy to add new language (write adapter, register in registry)
- ✅ Independent testing (each adapter has dedicated test suite)
- ✅ Clear responsibility boundary (adapter owns all language-specific logic)
- ✅ FRD Principle 5: Small, composable modules
- ✅ FRD Principle 8: Each adapter independently usable
- ✅ Supports delegation (Python expert owns PythonAdapter, TypeScript expert owns TypeScriptAdapter)
- ✅ No shared monolithic state (each adapter manages its own dependencies)

**Cons:**
- ❌ More files (one per language + base class)
- ❌ Must maintain interface compatibility (if LanguageAdapter changes, all adapters must update)
- ❌ Limited code sharing (avoid sharing logic between adapters to maintain independence)

**Verdict:** ✅ **Selected** — Best alignment with FRD principles, scales cleanly to 10+ languages.

---

## Decision

**Ortho uses abstract LanguageAdapter plugin model for language-specific code analysis.**

### Core Components

1. **Base Class:** `packages/repo-intelligence/src/adapters/language_adapter.py`
   - Abstract class defining required methods
   - Imported by all concrete adapters
   - Lives in `repo-intelligence` package (Pillar 1)

2. **Concrete Adapters:** One file per language
   - `packages/repo-intelligence/src/adapters/python_adapter.py` (PythonAdapter)
   - `packages/repo-intelligence/src/adapters/typescript_adapter.py` (TypeScriptAdapter)
   - `packages/repo-intelligence/src/adapters/go_adapter.py` (GoAdapter — Phase 3+)
   - (Future: Java, Rust, C++, etc.)

3. **Registry:** `packages/repo-intelligence/src/adapter_registry.py`
   - Maps file extensions to adapter instances
   - Lazy loads adapters (instantiated on first use)
   - Public API: `AdapterRegistry.get_adapter(file_path) -> LanguageAdapter`

4. **Testing:** One test suite per adapter
   - `packages/repo-intelligence/tests/test_python_adapter.py`
   - `packages/repo-intelligence/tests/test_typescript_adapter.py`
   - Uses fixture repositories (sample Python, TypeScript projects) in `tests/fixtures/`

### Interface Contract

```python
class LanguageAdapter(ABC):
    @property
    def language(self) -> str:
        """Language identifier: 'python', 'typescript', 'go'"""
        
    @property
    def file_extensions(self) -> list[str]:
        """Supported file extensions: ['.py', '.pyi']"""
        
    @abstractmethod
    def extract_symbols(
        self, 
        file_path: Path, 
        source: str
    ) -> list[Symbol]:
        """Extract all symbols (functions, classes, variables) from source.
        Must return stable Symbol IDs (see FRD Section 6 for ID stability rule).
        """
        
    @abstractmethod
    def extract_imports(
        self, 
        file_path: Path, 
        source: str
    ) -> list[ImportEdge]:
        """Extract all import statements and module dependencies."""
        
    @abstractmethod
    def extract_calls(
        self, 
        file_path: Path, 
        source: str,
        symbols: list[Symbol]
    ) -> list[CallEdge]:
        """Extract function call relationships.
        May have confidence < 1.0 (static analysis is probabilistic).
        """
        
    @abstractmethod
    def chunk(
        self, 
        file_path: Path, 
        source: str, 
        max_chunk_size: int = 1500
    ) -> list[ContextChunk]:
        """Split source into AST-aware chunks for context retrieval.
        Uses astchunk library for syntax-aware splitting.
        """
```

### Instantiation

```python
# Phase 1 Week 3 (BUILDER implements PythonAdapter)
# Phase 2 Week 1 (BUILDER implements TypeScriptAdapter)
# Phase 3+ (add more adapters as needed)

# Usage in repo scanner:
for file_path in repo.iter_files():
    adapter = AdapterRegistry.get_adapter(file_path)
    if adapter:
        symbols = adapter.extract_symbols(file_path, source)
        imports = adapter.extract_imports(file_path, source)
        calls = adapter.extract_calls(file_path, source, symbols)
```

---

## Rationale

1. **FRD Principle 5 Compliance:** "Small composable modules"
   - Each adapter is a small, focused module
   - Can be composed into larger system (repo scanner, indexer)
   - Changes to Python adapter don't affect TypeScript adapter

2. **FRD Principle 8 Compliance:** "Every capability independently usable"
   - PythonAdapter can be imported and used independently
   - Can unit-test Python symbol extraction without TypeScript logic
   - Can deploy Python support separately from TypeScript

3. **FRD Section 6:** Defines LanguageAdapter interface — ADR documents why this design
   - Concrete implementations follow abstract contract
   - Enables independent language support without core changes

4. **Scalability:** Clean addition of new languages
   - Adding Go (Phase 3+) = write GoAdapter(LanguageAdapter), register in registry
   - No core changes, no risk of breaking Python/TypeScript
   - Future team member can own specific language

5. **Testing:** Each adapter independently testable
   - Unit tests for PythonAdapter use Python fixtures (small, fast)
   - Unit tests for TypeScriptAdapter use TypeScript fixtures
   - No all-or-nothing testing

6. **Developer Experience:** Clear responsibility boundaries
   - Errors in Python adapter don't hide TypeScript issues
   - Easier to debug language-specific problems
   - New language expert can focus on one adapter

---

## Consequences

### Positive

- **Extensibility:** Adding 5th language takes 1 day (write adapter, test, register)
- **Independence:** Language experts can work in parallel (Python expert owns PythonAdapter, TypeScript expert owns TypeScriptAdapter)
- **Maintainability:** Changes to Python logic don't risk TypeScript (orthogonal)
- **Testing:** Can test each language separately (smaller test suites, faster CI)
- **Clarity:** Clear separation of concerns (who owns what?)

### Negative

- **File Count:** More files (one base class + N adapters + N test files)
  - *Acceptable* (standard OOP pattern, manageable)
  
- **Interface Stability:** If LanguageAdapter interface changes, all adapters must update
  - *Mitigation*: Finalize interface by end of Phase 1; only add methods (never remove) for backwards compatibility
  
- **Limited Code Sharing:** Avoid shared code between adapters (maintains independence)
  - *Acceptable*: Can extract small utilities (e.g., AST traversal helpers) into shared module if needed
  
- **Upfront Complexity:** More code structure (interfaces, registries, factories)
  - *Acceptable* (complexity is intentional, solves real problem)

### Neutral

- **Performance:** No overhead from abstraction (single dispatch, no performance tax)
- **Dependency Injection:** Registry can be configured/mocked for testing (minor benefit)

---

## Future Considerations

### If Adapter Count Grows (10+ adapters in Phase 4+)

**Scenario:** Ortho supports 15 languages, adapter directory becomes unwieldy.

**Mitigation Options:**
1. **Group by family:** Statically-typed (Go, Java, Rust) vs dynamically-typed (Python, JavaScript, Ruby)
   - Share common AST patterns within family
   - Update ADR documenting grouping strategy

2. **Separate package:** Move adapters to `packages/repo-intelligence-adapters/`
   - Keeps core clean
   - Adapters can be optional dependencies (Phase 1: required, Phase 3+: swappable)

3. **Plugin discovery:** Automatic adapter registration (scan directory for `*_adapter.py`)
   - Reduces manual registry maintenance
   - More flexible deployment

**Current decision:** Simple registry, linear search. Revisit if >10 adapters confirmed.

### If Adapter Performance Degrades (Phase 3+)

**Scenario:** TypeScript adapter gets slow due to large repos (1M+ symbols).

**Mitigation Options:**
1. **Caching:** Memoize symbol extraction results per commit hash
2. **Incremental:** Modify adapter interface to support incremental extraction (only changed files)
3. **Async:** Use asyncio for concurrent extraction across files
4. **Profiling:** Benchmark each adapter, identify hotspots

**Current decision:** No optimization needed for Phase 1. Monitor and act if metrics show issues.

---

## Related Tasks

- **task-001:** Phase 1 Week 1–2 Shared Foundation (defines LanguageAdapter interface in types)
- **task-003-repo-intelligence-python:** Phase 1 Week 3–4 (implements PythonAdapter)
- **task-004-repo-intelligence-typescript:** Phase 2 Week 3–4 (implements TypeScriptAdapter)

---

## Related ADRs

- **ADR-001:** ASES Multi-Agent Orchestration
  - *Relationship*: Language adapter expert (future specialist role) can be delegated to dedicated agent

- **ADR-003:** Evidence Capture Strategy
  - *Relationship*: Adapter correctness verified via test output (logs from test runner)

- **ADR-004:** Storage Strategy (SQLite)
  - *Relationship*: Adapters extract data, storage layer persists; loosely coupled via shared types

---

*End of ADR-005*
