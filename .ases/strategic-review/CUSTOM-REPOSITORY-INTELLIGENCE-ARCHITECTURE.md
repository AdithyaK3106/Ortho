# Ortho Custom Repository Intelligence: Architecture Specification

**Date:** 2026-07-01  
**Status:** Architecture Design Complete  
**Timeline:** 4-6 months (28 weeks), 8-10 person-months  
**Ownership:** 100% Ortho-owned, no external dependencies  

---

## Executive Summary

Ortho will build its own Repository Intelligence system. Learning from GitNexus's architectural patterns but writing 100% original code.

**Why custom?**
- Full ownership (no licensing constraints)
- Commercial viability (sell without restrictions)
- Vendor independence (can evolve independently)
- Learning investment (team understands code deeply)

**Scope:** Python, TypeScript, Go analysis by Week 28. Fully production-ready.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│        Ortho Engineering Intelligence       │
├─────────────────────────────────────────────┤
│  ContextHub │ ASES │ Architecture Intelligence
│  Search    │ Memory │ Orchestration Planning
└─────────────────┬───────────────────────────┘
                  │ depends on
                  ↓
┌─────────────────────────────────────────────┐
│    RepositoryAnalysisProvider (interface)   │
│         Ortho's Repository Intelligence     │
└─────────────────┬───────────────────────────┘
                  │ implemented by
                  ↓
┌─────────────────────────────────────────────┐
│  OrthoRepositoryAnalysisProvider (impl)     │
│                                             │
│  ├─ Language Adapter Registry               │
│  │  ├─ PythonAdapter (Weeks 5-8)           │
│  │  ├─ TypeScriptAdapter (Weeks 17-20)    │
│  │  └─ GoAdapter (Weeks 21-24)             │
│  │                                         │
│  ├─ Symbol/Import/Call Graph Builders      │
│  │                                         │
│  ├─ Incremental Indexer                    │
│  │                                         │
│  └─ Storage Layer (SQLite)                 │
└─────────────────────────────────────────────┘
```

---

## Core Components

### 1. RepositoryAnalysisProvider Interface

**Location:** `packages/repo-intelligence/provider.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import list, Optional

@dataclass
class ProviderCapabilities:
    """What languages and features this provider supports."""
    languages: list[str]  # ["python", "typescript", "go"]
    has_call_graph: bool = True
    has_import_graph: bool = True
    has_dependency_graph: bool = True
    has_incremental_update: bool = True
    confidence_scoring: bool = True
    supports_monorepo: bool = True
    max_repo_size_mb: Optional[int] = None

@dataclass
class ProviderHealth:
    """Health status of provider."""
    is_healthy: bool
    message: str
    version: str
    last_error: Optional[str] = None
    uptime_seconds: int = 0

class RepositoryAnalysisProvider(ABC):
    """
    Ortho's abstraction for repository code analysis.
    
    Responsibilities:
    - Parse code files
    - Extract symbols
    - Build graphs (import, call, dependency)
    - Detect repository structure
    - Support incremental updates
    
    NOT responsible for:
    - Storing artifacts (ContextHub)
    - Analyzing architecture (ArchitectureDetector)
    - Searching code (Search)
    - Orchestrating workflows (ASES)
    """
    
    @abstractmethod
    def get_capabilities(self) -> ProviderCapabilities:
        """Declare what languages and features are supported."""
        pass
    
    @abstractmethod
    def analyze(self, repo_path: Path) -> 'RepositoryAnalysis':
        """
        Analyze entire repository.
        
        Returns:
            Complete analysis (symbols, graphs, structure)
        """
        pass
    
    @abstractmethod
    def incremental_update(
        self, 
        repo_path: Path, 
        changed_files: list[Path]
    ) -> 'DeltaAnalysis':
        """
        Update for changed files (git-aware).
        
        Much faster than full analysis.
        Only re-analyzes changed files.
        """
        pass
    
    @abstractmethod
    def get_symbols(self, repo_path: Path) -> list['Symbol']:
        """All symbols in repository."""
        pass
    
    @abstractmethod
    def get_import_graph(self, repo_path: Path) -> 'ImportGraph':
        """All import relationships."""
        pass
    
    @abstractmethod
    def get_call_graph(self, repo_path: Path) -> 'CallGraph':
        """All function call relationships."""
        pass
    
    @abstractmethod
    def get_dependency_graph(self, repo_path: Path) -> 'DependencyGraph':
        """External dependencies."""
        pass
    
    @abstractmethod
    def get_file_tree(self, repo_path: Path) -> 'FileTree':
        """Repository structure (files, packages, modules)."""
        pass
    
    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Is provider healthy and ready?"""
        pass
    
    @abstractmethod
    def get_last_error(self) -> Optional['ProviderError']:
        """Last error encountered (if any)."""
        pass
```

**Key design:**
- Language-agnostic interface (same for Python, TS, Go)
- Incremental updates first-class (not bolted on)
- Health checks and error handling built-in
- Data models are Ortho-owned (not provider-specific)

---

### 2. Data Models (Ortho-Owned)

**Location:** `packages/repo-intelligence/types.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
from uuid import uuid4

class SymbolType(Enum):
    """Types of code symbols."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    MODULE = "module"
    PACKAGE = "package"
    INTERFACE = "interface"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"

@dataclass
class Location:
    """Position in source code."""
    file: str  # relative to repo root
    line: int  # 1-indexed
    column: int  # 0-indexed
    end_line: int | None = None
    end_column: int | None = None
    
    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
        }

@dataclass
class Symbol:
    """Canonical symbol representation."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str  # function name, class name, etc.
    qualified_name: str  # module.class.method
    type: SymbolType
    language: str  # python, typescript, go
    location: Location
    docstring: str | None = None
    metadata: dict = field(default_factory=dict)
    
    # metadata may contain:
    # - decorators: list[str]
    # - is_async: bool
    # - is_private: bool
    # - return_type: str | None
    # - parameters: list[dict]
    # - type_hints: dict

@dataclass
class ImportEdge:
    """Import relationship between modules."""
    source_module: str
    target_module: str
    import_type: str  # "from_import", "import", "require", "relative"
    location: Location
    confidence: float  # 0.0-1.0
    is_circular: bool = False
    
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.9

@dataclass
class CallEdge:
    """Function call relationship."""
    caller: str  # qualified name
    callee: str  # qualified name
    location: Location
    confidence: float  # 0.0-1.0
    call_count: int = 1
    
    def is_high_confidence(self) -> bool:
        return self.confidence >= 0.9

@dataclass
class Dependency:
    """External package dependency."""
    package: str  # numpy, react, etc.
    version: str  # exact version or constraint
    source: str  # requirements.txt, package.json, go.mod
    is_transitive: bool = False
    resolved_path: str | None = None  # path to installed package

@dataclass
class FileMetadata:
    """Metadata about a single file."""
    path: str  # relative to repo root
    language: str
    mtime: datetime
    content_hash: str
    symbol_count: int = 0
    import_count: int = 0
    call_count: int = 0

@dataclass
class FileTree:
    """Repository structure."""
    root: Path
    files: list[FileMetadata]
    packages: list[str]  # detected packages
    modules: list[str]  # detected modules
    
    def get_package_for_file(self, file_path: str) -> str | None:
        """Which package does this file belong to?"""
        # implementation

@dataclass
class RepositoryAnalysis:
    """Complete analysis of a repository."""
    repo_path: Path
    timestamp: datetime
    symbols: list[Symbol]
    import_edges: list[ImportEdge]
    call_edges: list[CallEdge]
    dependencies: list[Dependency]
    file_tree: FileTree
    metadata: dict = field(default_factory=dict)
    
    # metadata may contain:
    # - analysis_version: str
    # - languages_detected: list[str]
    # - scan_time_seconds: float
    # - total_files: int
    # - total_loc: int

@dataclass
class DeltaAnalysis:
    """Incremental update (changed files only)."""
    timestamp: datetime
    added_symbols: list[Symbol]
    removed_symbol_ids: list[str]
    updated_symbols: list[Symbol]
    added_edges: list[ImportEdge] | list[CallEdge]
    removed_edge_ids: list[str]
    deleted_files: list[str]

@dataclass
class ImportGraph:
    """All import relationships."""
    edges: list[ImportEdge]
    
    def find_cycles(self) -> list[list[str]]:
        """Find circular imports."""
        # implementation

@dataclass
class CallGraph:
    """All function call relationships."""
    edges: list[CallEdge]
    
    def find_callers(self, function: str) -> list[str]:
        """Who calls this function?"""
        # implementation

@dataclass
class DependencyGraph:
    """External dependencies."""
    dependencies: list[Dependency]
    
    def find_transitive(self, package: str) -> list[str]:
        """All transitive dependencies."""
        # implementation

class ProviderError(Exception):
    """Error from repository analysis provider."""
    def __init__(self, message: str, file: Path | None = None):
        self.message = message
        self.file = file
        super().__init__(message)
```

**Key design:**
- All models are dataclasses (serializable, clear structure)
- Confidence scoring on every edge (0.0-1.0)
- Metadata dict for provider-specific extensions
- All models are Ortho-owned (not provider-specific)

---

### 3. Component Architecture

**Location:** `packages/repo-intelligence/`

```
repo-intelligence/
├── __init__.py
├── provider.py              # RepositoryAnalysisProvider interface
├── types.py                 # Symbol, ImportEdge, CallEdge, etc.
├── config.py                # RepositoryIntelligenceConfig
├── errors.py                # ProviderError, AnalysisError
│
├── adapters/
│   ├── __init__.py
│   ├── base.py              # LanguageAdapter ABC
│   ├── python_adapter.py    # PythonAdapter implementation
│   ├── typescript_adapter.py # TypeScriptAdapter (Phase 2)
│   └── go_adapter.py        # GoAdapter (Phase 2)
│
├── extractors/
│   ├── __init__.py
│   ├── python/
│   │   ├── symbol_extractor.py
│   │   ├── import_extractor.py
│   │   ├── call_extractor.py
│   │   └── dependency_extractor.py
│   ├── typescript/
│   └── go/
│
├── builders/
│   ├── __init__.py
│   ├── import_graph.py
│   ├── call_graph.py
│   ├── dependency_graph.py
│   └── file_tree.py
│
├── indexing/
│   ├── __init__.py
│   ├── git_delta.py         # Detect changed files
│   ├── cache.py             # Cache management
│   └── incremental.py       # Incremental update logic
│
├── storage/
│   ├── __init__.py
│   ├── schema.py            # SQLite schema
│   ├── symbol_store.py      # Persist symbols
│   ├── graph_store.py       # Persist edges
│   └── metadata_store.py    # Persist analysis metadata
│
├── impl/
│   ├── __init__.py
│   └── ortho_provider.py    # OrthoRepositoryAnalysisProvider
│
└── tests/
    ├── conftest.py
    ├── test_types.py
    ├── test_adapters.py
    ├── test_extractors.py
    ├── test_builders.py
    ├── test_incremental.py
    ├── test_storage.py
    └── test_integration.py
```

**Key separation:**
- Adapters (language-specific, pluggable)
- Extractors (symbol, import, call, dependency—per language)
- Builders (aggregate across files)
- Indexing (incremental update logic)
- Storage (persistence, querying)
- Implementation (OrthoRepositoryAnalysisProvider ties it together)

---

### 4. Language Adapter Pattern

**Location:** `packages/repo-intelligence/adapters/base.py`

```python
from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum

class LanguageAdapter(ABC):
    """
    Language-specific code analysis.
    
    Each language (Python, TypeScript, Go) has one adapter.
    Adapters are plugged into OrthoRepositoryAnalysisProvider.
    Adding a new language = adding new adapter (no core changes).
    """
    
    @property
    @abstractmethod
    def language(self) -> str:
        """Language identifier: 'python', 'typescript', 'go'."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """File extensions: ['.py', '.pyi'] for Python."""
        pass
    
    @abstractmethod
    def extract_symbols(self, file_path: Path) -> list['Symbol']:
        """Extract all symbols from file."""
        pass
    
    @abstractmethod
    def extract_imports(self, file_path: Path) -> list['ImportEdge']:
        """Extract all imports from file."""
        pass
    
    @abstractmethod
    def extract_calls(self, file_path: Path) -> list['CallEdge']:
        """Extract all function calls from file."""
        pass
    
    @abstractmethod
    def detect_packages(self, repo_path: Path) -> list[str]:
        """Detect packages in repository."""
        pass
```

**Example: PythonAdapter**

```python
class PythonAdapter(LanguageAdapter):
    """Python code analysis using tree-sitter."""
    
    def __init__(self):
        self.parser = TreeSitterParser("python")
    
    @property
    def language(self) -> str:
        return "python"
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".py"]
    
    def extract_symbols(self, file_path: Path) -> list[Symbol]:
        """Parse Python file, extract functions, classes, variables."""
        tree = self.parser.parse(file_path)
        return PythonSymbolExtractor(tree, file_path).extract()
    
    def extract_imports(self, file_path: Path) -> list[ImportEdge]:
        """Parse imports (from/import statements)."""
        tree = self.parser.parse(file_path)
        return PythonImportExtractor(tree, file_path).extract()
    
    def extract_calls(self, file_path: Path) -> list[CallEdge]:
        """Parse function calls."""
        tree = self.parser.parse(file_path)
        return PythonCallExtractor(tree, file_path).extract()
    
    def detect_packages(self, repo_path: Path) -> list[str]:
        """Find Python packages (directories with __init__.py)."""
        packages = []
        for init_file in repo_path.rglob("__init__.py"):
            package_path = init_file.parent
            packages.append(str(package_path.relative_to(repo_path)))
        return packages
```

**Design principle:** New language = new adapter. Core system unchanged.

---

### 5. Storage Schema

**Location:** `packages/repo-intelligence/storage/schema.py`

```sql
-- Symbols
CREATE TABLE symbols (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- function, class, variable, etc.
    language TEXT NOT NULL,  -- python, typescript, go
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL,
    end_line INTEGER,
    end_column INTEGER,
    docstring TEXT,
    metadata JSON,
    content_hash TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_symbols_qname ON symbols(qualified_name);
CREATE INDEX idx_symbols_file ON symbols(file);
CREATE INDEX idx_symbols_repo ON symbols(repo_id);

-- Import edges
CREATE TABLE import_edges (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    source_module TEXT NOT NULL,
    target_module TEXT NOT NULL,
    import_type TEXT NOT NULL,  -- from_import, import, require, relative
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL,
    confidence REAL NOT NULL,  -- 0.0-1.0
    is_circular BOOLEAN DEFAULT FALSE,
    metadata JSON,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_imports_source ON import_edges(source_module);
CREATE INDEX idx_imports_target ON import_edges(target_module);
CREATE INDEX idx_imports_repo ON import_edges(repo_id);

-- Call edges
CREATE TABLE call_edges (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    caller TEXT NOT NULL,  -- qualified name
    callee TEXT NOT NULL,
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL,
    confidence REAL NOT NULL,  -- 0.0-1.0
    call_count INTEGER DEFAULT 1,
    metadata JSON,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_calls_caller ON call_edges(caller);
CREATE INDEX idx_calls_callee ON call_edges(callee);
CREATE INDEX idx_calls_repo ON call_edges(repo_id);

-- Dependencies
CREATE TABLE dependencies (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    package TEXT NOT NULL,
    version TEXT NOT NULL,
    source TEXT NOT NULL,  -- requirements.txt, package.json, go.mod
    is_transitive BOOLEAN DEFAULT FALSE,
    resolved_path TEXT,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_deps_package ON dependencies(package);
CREATE INDEX idx_deps_repo ON dependencies(repo_id);

-- Files
CREATE TABLE files (
    path TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    language TEXT NOT NULL,
    mtime INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    symbol_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    call_count INTEGER DEFAULT 0,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_files_repo ON files(repo_id);

-- Analysis metadata
CREATE TABLE analysis_metadata (
    id TEXT PRIMARY KEY,
    repo_id TEXT NOT NULL,
    repo_hash TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    analysis_version TEXT,
    languages_detected JSON,  -- ["python", "typescript"]
    scan_time_seconds REAL,
    total_files INTEGER,
    total_loc INTEGER,
    FOREIGN KEY (repo_id) REFERENCES repositories(id)
);
CREATE INDEX idx_metadata_repo ON analysis_metadata(repo_id);
```

**Design:**
- One set of tables per repository
- Foreign keys for referential integrity
- Indexes on frequently queried fields
- JSON for flexible metadata
- Version tracking for schema migrations

---

### 6. Incremental Indexing

**Location:** `packages/repo-intelligence/indexing/incremental.py`

```python
class IncrementalIndexer:
    """Update analysis for changed files."""
    
    def __init__(self, repo_path: Path, storage: GraphStore):
        self.repo_path = repo_path
        self.storage = storage
        self.git_delta = GitDeltaDetector(repo_path)
        self.cache = CacheManager(repo_path)
    
    def update(self) -> DeltaAnalysis:
        """
        Incremental update (very fast).
        
        Steps:
        1. Detect changed files (git diff)
        2. Re-extract symbols from changed files
        3. Remove old edges from changed/deleted files
        4. Add new edges from changed files
        5. Update transitive closures
        6. Cache results
        """
        
        # 1. Detect changes
        changed_files, deleted_files = self.git_delta.detect_changes()
        
        # 2. Re-extract
        new_symbols = []
        new_edges = []
        for file_path in changed_files:
            symbols = self.adapter.extract_symbols(file_path)
            edges = self.adapter.extract_calls(file_path)
            new_symbols.extend(symbols)
            new_edges.extend(edges)
        
        # 3. Remove old
        old_symbol_ids = self.storage.get_symbols_in_files(changed_files + deleted_files)
        old_edge_ids = self.storage.get_edges_in_files(changed_files + deleted_files)
        
        # 4. Persist
        self.storage.delete_symbols(old_symbol_ids)
        self.storage.delete_edges(old_edge_ids)
        self.storage.insert_symbols(new_symbols)
        self.storage.insert_edges(new_edges)
        
        # 5. Cache
        self.cache.update(new_symbols, new_edges)
        
        return DeltaAnalysis(
            timestamp=datetime.now(),
            added_symbols=new_symbols,
            removed_symbol_ids=old_symbol_ids,
            added_edges=new_edges,
            removed_edge_ids=old_edge_ids,
            deleted_files=deleted_files,
        )
```

**Performance target:** <100ms per file (vs. 500ms for full re-parse)

---

## Integration Points

### With ContextHub

```python
# ContextHub calls Repository Intelligence
provider = OrthoRepositoryAnalysisProvider()
analysis = provider.analyze(repo_path)

# ContextHub indexes symbols
for symbol in analysis.symbols:
    context_hub.index_artifact(
        type="code_symbol",
        id=symbol.id,
        content=symbol,
        searchable_text=symbol.qualified_name,
    )
```

### With Architecture Intelligence

```python
# Architecture Intelligence depends on Repository Intelligence
symbols = provider.get_symbols(repo_path)
call_graph = provider.get_call_graph(repo_path)

# Architecture detector analyzes structure
detector = ArchitectureDetector(symbols, call_graph)
architecture = detector.detect()
```

### With ASES

```python
# ASES uses Repository Intelligence for impact analysis
provider = OrthoRepositoryAnalysisProvider()
call_graph = provider.get_call_graph(repo_path)

# Estimate change impact
def find_impact(changed_functions: list[str]) -> set[str]:
    """Who calls these functions?"""
    impacted = set()
    for func in changed_functions:
        callers = call_graph.find_callers(func)
        impacted.update(callers)
    return impacted
```

---

## Configuration

**Location:** `ortho/config.toml`

```toml
[repository_intelligence]
enabled = true
cache_enabled = true
cache_max_mb = 500
timeout_seconds = 300
log_level = "INFO"

# Language support
languages = ["python", "typescript", "go"]

# Incremental indexing
[repository_intelligence.incremental]
enabled = true
git_aware = true
max_changed_files = 1000
cache_invalidation = "smart"  # smart or aggressive
```

---

## Error Handling

**Location:** `packages/repo-intelligence/errors.py`

```python
class ProviderError(Exception):
    """Unrecoverable provider error."""
    def __init__(self, message: str, file: Path | None = None):
        self.message = message
        self.file = file

class AnalysisError(Exception):
    """Recoverable error during file analysis."""
    def __init__(self, file: Path, line: int | None, reason: str):
        self.file = file
        self.line = line
        self.reason = reason

# Strategy: Continue on file errors, aggregate errors for reporting
def analyze_with_error_recovery(repo_path: Path) -> tuple[RepositoryAnalysis, list[AnalysisError]]:
    """Analyze repo, continue on file-level errors."""
    errors = []
    
    for file_path in repo_path.rglob("*.py"):
        try:
            symbols = adapter.extract_symbols(file_path)
        except AnalysisError as e:
            errors.append(e)
            continue  # skip this file, continue analysis
    
    # Return analysis even if some files failed
    return analysis, errors
```

---

## Testing Strategy

- **Unit tests:** 150+ (data models, extractors, builders)
- **Integration tests:** 100+ (end-to-end on real repos)
- **Edge cases:** Circular imports, monorepos, complex dispatch
- **Coverage target:** >90%

---

## Success Metrics

| Metric | Target | Week |
|--------|--------|------|
| Python parsing complete | ✓ | 8 |
| Full repo analysis <5 sec (10k LOC) | ✓ | 12 |
| Incremental update <100ms/file | ✓ | 12 |
| TypeScript support | ✓ | 20 |
| Go support | ✓ | 24 |
| 300+ tests passing | ✓ | 28 |
| Production ready | ✓ | 28 |

---

*Architecture specification for custom Repository Intelligence*  
*Designed for maintainability, extensibility, and full ownership*
