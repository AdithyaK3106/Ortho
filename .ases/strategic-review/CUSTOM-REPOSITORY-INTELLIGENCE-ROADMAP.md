# Ortho Custom Repository Intelligence: Implementation Roadmap

**Date:** 2026-07-01  
**Duration:** 28 weeks (7 phases)  
**Total Effort:** 8-10 person-months  
**Team:** 2-3 developers per phase  

---

## Phase Overview

```
Phase 1: Foundation (Weeks 1-4, 3 devs, 120 hours)
├─ Data models, interfaces, Python adapter skeleton
├─ 30+ unit tests
└─ Deliverable: OrthoRepositoryAnalysisProvider interface working

Phase 2: Python Intelligence (Weeks 5-8, 3 devs, 120 hours)
├─ Symbol extraction, imports, calls, dependencies
├─ 80+ tests
└─ Deliverable: Python repos fully analyzable

Phase 3: Incremental Indexing (Weeks 9-12, 2 devs, 80 hours)
├─ Git delta detection, caching, incremental updates
├─ 40+ tests
└─ Deliverable: Fast incremental updates (<100ms/file)

Phase 4: Storage & Optimization (Weeks 13-16, 2 devs, 80 hours)
├─ SQLite schema, query layer, indexing
├─ 50+ tests
└─ Deliverable: Persistent, queryable analysis

Phase 5: TypeScript Support (Weeks 17-20, 3 devs, 120 hours)
├─ TypeScript adapter, ES6 imports, npm deps
├─ 60+ tests
└─ Deliverable: Python + TypeScript repos analyzable

Phase 6: Go Support (Weeks 21-24, 3 devs, 120 hours)
├─ Go adapter, package resolution, go.mod parsing
├─ 50+ tests
└─ Deliverable: Python + TS + Go repos analyzable

Phase 7: Polish & Production (Weeks 25-28, 3 devs, 120 hours)
├─ Integration testing, optimization, documentation
├─ 100+ integration tests
└─ Deliverable: Production-ready system, 350+ tests total
```

---

## Phase 1: Foundation (Weeks 1-4)

**Objective:** Core infrastructure, interfaces, one language (Python) skeleton

### Week 1: Data Models & Types

**Tasks:**
- 1.1: Define Symbol, ImportEdge, CallEdge, Dependency, RepositoryAnalysis dataclasses
- 1.2: Define Location, SymbolType, LanguageAdapter base class
- 1.3: Type stubs for all models (mypy --strict)
- 1.4: Unit tests for data models (20 tests)

**Owner:** Lead Dev  
**Effort:** 40 hours  
**Deliverable:** All types defined, passing mypy --strict

**Files created:**
- `packages/repo-intelligence/types.py` (400 LOC)
- `packages/repo-intelligence/adapter.py` (100 LOC)
- `tests/test_types.py` (200 LOC)

---

### Week 2: RepositoryAnalysisProvider Interface

**Tasks:**
- 2.1: Define RepositoryAnalysisProvider abstract base class
- 2.2: Define ProviderCapabilities, ProviderHealth, ProviderError
- 2.3: Document interface contract (docstrings)
- 2.4: Unit tests for interface (10 tests)

**Owner:** Lead Dev  
**Effort:** 30 hours  
**Deliverable:** Interface fully specified, documented

**Files created:**
- `packages/repo-intelligence/provider.py` (300 LOC)
- `tests/test_provider.py` (150 LOC)

---

### Week 3: Configuration & Error Handling

**Tasks:**
- 3.1: RepositoryIntelligenceConfig (TOML-based)
- 3.2: Configuration loader (env + file)
- 3.3: ProviderError, AnalysisError exception classes
- 3.4: Error logging & reporting framework
- 3.5: Unit tests (15 tests)

**Owner:** Dev 2  
**Effort:** 30 hours  
**Deliverable:** Config system working, error handling in place

**Files created:**
- `packages/repo-intelligence/config.py` (150 LOC)
- `packages/repo-intelligence/errors.py` (100 LOC)
- `tests/test_config.py` (100 LOC)

---

### Week 4: Python Adapter Skeleton + OrthoRepositoryAnalysisProvider

**Tasks:**
- 4.1: PythonAdapter class (inherit LanguageAdapter)
- 4.2: OrthoRepositoryAnalysisProvider implementation skeleton
- 4.3: tree-sitter integration (parsing Python files)
- 4.4: Basic error handling
- 4.5: Integration tests (10 tests)

**Owner:** Dev 2  
**Effort:** 30 hours  
**Deliverable:** Can parse Python files, extract basic metadata

**Files created:**
- `packages/repo-intelligence/adapters/base.py` (150 LOC)
- `packages/repo-intelligence/adapters/python_adapter.py` (200 LOC)
- `packages/repo-intelligence/impl/ortho_provider.py` (300 LOC)
- `tests/test_adapters.py` (150 LOC)

---

### Phase 1 Milestone

**Tests passing:** 30+  
**Code coverage:** >80%  
**Status:** RepositoryAnalysisProvider interface working, PythonAdapter can parse files

---

## Phase 2: Python Intelligence (Weeks 5-8)

**Objective:** Complete Python analysis (symbols, imports, calls, dependencies)

### Week 5: Python Symbol Extraction

**Tasks:**
- 5.1: PythonSymbolExtractor (functions, classes, methods)
- 5.2: Qualified name generation (module.class.method)
- 5.3: Docstring extraction
- 5.4: Type hint parsing (basic)
- 5.5: Unit tests (25 tests)

**Owner:** Dev 1  
**Effort:** 40 hours  
**Deliverable:** All Python symbols extracted with metadata

**Files created:**
- `packages/repo-intelligence/extractors/python/symbol_extractor.py` (300 LOC)
- `tests/test_symbol_extraction.py` (250 LOC)

---

### Week 6: Python Import Graph

**Tasks:**
- 6.1: PythonImportExtractor (from/import statements)
- 6.2: Circular import detection
- 6.3: Relative import resolution
- 6.4: Star import handling (basic)
- 6.5: Unit tests (20 tests)

**Owner:** Dev 2  
**Effort:** 40 hours  
**Deliverable:** Complete import graph with cycle detection

**Files created:**
- `packages/repo-intelligence/extractors/python/import_extractor.py` (250 LOC)
- `packages/repo-intelligence/builders/import_graph.py` (150 LOC)
- `tests/test_import_extraction.py` (200 LOC)

---

### Week 7: Python Call Graph + Dependency Graph

**Tasks:**
- 7.1: PythonCallExtractor (function calls, method dispatch)
- 7.2: Confidence scoring (direct: 1.0, decorator: 0.9, dynamic: 0.5)
- 7.3: PythonDependencyExtractor (requirements.txt, pyproject.toml, setup.py)
- 7.4: Version extraction
- 7.5: Unit tests (20 tests)

**Owner:** Dev 1  
**Effort:** 40 hours  
**Deliverable:** Call graph + dependency graph complete

**Files created:**
- `packages/repo-intelligence/extractors/python/call_extractor.py` (250 LOC)
- `packages/repo-intelligence/extractors/python/dependency_extractor.py` (200 LOC)
- `packages/repo-intelligence/builders/call_graph.py` (150 LOC)
- `packages/repo-intelligence/builders/dependency_graph.py` (150 LOC)
- `tests/test_graph_extraction.py` (250 LOC)

---

### Week 8: File Tree + Integration

**Tasks:**
- 8.1: FileTreeBuilder (detect packages, modules, structure)
- 8.2: Namespace package detection (PEP 420)
- 8.3: Integration test (analyze real Python repo)
- 8.4: Performance benchmark (target: <5 sec for 10k LOC)
- 8.5: Unit tests (20 tests)

**Owner:** Lead Dev  
**Effort:** 40 hours  
**Deliverable:** Python analysis complete, benchmarks met

**Files created:**
- `packages/repo-intelligence/builders/file_tree.py` (150 LOC)
- `tests/test_integration_python.py` (250 LOC)

---

### Phase 2 Milestone

**Tests passing:** 80+  
**Code coverage:** >85%  
**Performance:** 10k LOC Python repo analyzed in <5 sec  
**Status:** Python fully supported

---

## Phase 3: Incremental Indexing (Weeks 9-12)

**Objective:** Fast git-aware delta updates

### Week 9: Git Delta Detection

**Tasks:**
- 9.1: GitDeltaDetector (identify changed/deleted files)
- 9.2: Content hashing (detect true changes vs. touch)
- 9.3: File rename detection
- 9.4: Unit tests (15 tests)

**Owner:** Dev 3  
**Effort:** 30 hours  
**Deliverable:** Accurate change detection

**Files created:**
- `packages/repo-intelligence/indexing/git_delta.py` (200 LOC)
- `tests/test_git_delta.py` (150 LOC)

---

### Week 10: Cache Management

**Tasks:**
- 10.1: CacheManager (cache symbols, edges, metadata)
- 10.2: Cache invalidation strategy
- 10.3: Cache persistence (SQLite)
- 10.4: Cache statistics / health check
- 10.5: Unit tests (15 tests)

**Owner:** Dev 3  
**Effort:** 30 hours  
**Deliverable:** Efficient caching in place

**Files created:**
- `packages/repo-intelligence/indexing/cache.py` (250 LOC)
- `tests/test_cache.py` (150 LOC)

---

### Week 11: Incremental Update Logic

**Tasks:**
- 11.1: IncrementalIndexer (orchestrate updates)
- 11.2: Delta computation (what changed, what to update)
- 11.3: Merge new results with existing
- 11.4: Unit tests (15 tests)

**Owner:** Dev 1  
**Effort:** 30 hours  
**Deliverable:** Incremental updates working

**Files created:**
- `packages/repo-intelligence/indexing/incremental.py` (250 LOC)
- `tests/test_incremental.py` (200 LOC)

---

### Week 12: Performance Optimization

**Tasks:**
- 12.1: Profiling (identify bottlenecks)
- 12.2: Parallel processing (if applicable)
- 12.3: Memory efficiency improvements
- 12.4: Performance benchmarking
- 12.5: Integration test (target: <100ms per file)

**Owner:** Lead Dev  
**Effort:** 30 hours  
**Deliverable:** Incremental <100ms/file, full scan <5 sec for 10k LOC

---

### Phase 3 Milestone

**Tests passing:** 120+  
**Performance:** 1 file change: <100ms update  
**Status:** Incremental indexing production-ready

---

## Phase 4: Storage & Retrieval (Weeks 13-16)

**Objective:** Persistent, queryable analysis

### Week 13: SQLite Schema Design

**Tasks:**
- 13.1: Schema design (symbols, edges, files, metadata)
- 13.2: Migrations framework
- 13.3: Foreign keys, constraints, indexes
- 13.4: Unit tests (10 tests)

**Owner:** Dev 2  
**Effort:** 30 hours  
**Deliverable:** Schema complete, migrations working

**Files created:**
- `packages/repo-intelligence/storage/schema.py` (400 LOC)
- `packages/repo-intelligence/storage/migrations.py` (150 LOC)

---

### Week 14: Storage Abstraction

**Tasks:**
- 14.1: SymbolStore (CRUD for symbols)
- 14.2: GraphStore (CRUD for edges)
- 14.3: MetadataStore (analysis metadata)
- 14.4: Transaction support
- 14.5: Unit tests (20 tests)

**Owner:** Dev 2  
**Effort:** 40 hours  
**Deliverable:** All storage layers implemented

**Files created:**
- `packages/repo-intelligence/storage/symbol_store.py` (250 LOC)
- `packages/repo-intelligence/storage/graph_store.py` (250 LOC)
- `packages/repo-intelligence/storage/metadata_store.py` (150 LOC)
- `tests/test_storage.py` (300 LOC)

---

### Week 15: Query Optimization

**Tasks:**
- 15.1: Index tuning
- 15.2: Query optimization (common patterns)
- 15.3: Transitive closure queries
- 15.4: Path-finding queries
- 15.5: Unit tests (15 tests)

**Owner:** Dev 1  
**Effort:** 30 hours  
**Deliverable:** Efficient querying

**Files created:**
- `packages/repo-intelligence/storage/queries.py` (250 LOC)
- `tests/test_queries.py` (200 LOC)

---

### Week 16: Version Management

**Tasks:**
- 16.1: Schema versioning
- 16.2: Data migrations
- 16.3: Backwards compatibility
- 16.4: Unit tests (10 tests)

**Owner:** Dev 2  
**Effort:** 20 hours  
**Deliverable:** Can upgrade schema safely

---

### Phase 4 Milestone

**Tests passing:** 170+  
**Storage:** Production SQLite schema with migrations  
**Status:** Persistence layer complete

---

## Phase 5: TypeScript Support (Weeks 17-20)

**Objective:** Multi-language (TypeScript/JavaScript)

### Week 17: TypeScript Adapter

**Tasks:**
- 17.1: TypeScriptAdapter (inherit LanguageAdapter)
- 17.2: tree-sitter TypeScript parser integration
- 17.3: Parse .ts, .js, .jsx, .tsx files
- 17.4: Basic testing

**Owner:** Dev 3  
**Effort:** 30 hours  
**Deliverable:** TypeScript files parseable

---

### Week 18: TypeScript Symbol Extraction

**Tasks:**
- 18.1: TypeScriptSymbolExtractor (functions, classes, interfaces, exports)
- 18.2: Type annotation handling
- 18.3: JSDoc comment parsing
- 18.4: Unit tests (20 tests)

**Owner:** Dev 3  
**Effort:** 40 hours  
**Deliverable:** TS symbols extracted

---

### Week 19: TypeScript Import/Call Graphs

**Tasks:**
- 19.1: TypeScript import extraction (ES6, CommonJS)
- 19.2: npm package resolution
- 19.3: TypeScript call graph (function + method calls)
- 19.4: Unit tests (20 tests)

**Owner:** Dev 1  
**Effort:** 40 hours  
**Deliverable:** TS graphs working

---

### Week 20: TypeScript Dependencies + Integration

**Tasks:**
- 20.1: package.json parsing (dependencies, devDependencies, peerDependencies)
- 20.2: Lock file parsing (package-lock.json)
- 20.3: Integration test (analyze real TS repo)
- 20.4: Unit tests (20 tests)

**Owner:** Lead Dev  
**Effort:** 30 hours  
**Deliverable:** TypeScript fully supported, benchmarks met

---

### Phase 5 Milestone

**Tests passing:** 230+  
**Languages:** Python + TypeScript/JavaScript  
**Status:** Multi-language support live

---

## Phase 6: Go Support (Weeks 21-24)

**Objective:** Multi-language (Go)

### Week 21: Go Adapter

**Tasks:**
- 21.1: GoAdapter (inherit LanguageAdapter)
- 21.2: tree-sitter Go parser or native go/parser
- 21.3: Parse .go files
- 21.4: Basic testing

**Owner:** Dev 2  
**Effort:** 30 hours  
**Deliverable:** Go files parseable

---

### Week 22: Go Symbol Extraction

**Tasks:**
- 22.1: GoSymbolExtractor (functions, structs, interfaces)
- 22.2: Receiver type handling (methods)
- 22.3: Package identification
- 22.4: Unit tests (15 tests)

**Owner:** Dev 2  
**Effort:** 30 hours  
**Deliverable:** Go symbols extracted

---

### Week 23: Go Import/Call Graphs

**Tasks:**
- 23.1: Go import extraction (import statements)
- 23.2: Package resolution
- 23.3: Go call graph (function + method calls)
- 23.4: Unit tests (15 tests)

**Owner:** Dev 1  
**Effort:** 30 hours  
**Deliverable:** Go graphs working

---

### Week 24: Go Dependencies + Integration

**Tasks:**
- 24.1: go.mod parsing (module, require directives)
- 24.2: Indirect dependency tracking
- 24.3: Integration test (analyze real Go repo)
- 24.4: Unit tests (20 tests)

**Owner:** Dev 3  
**Effort:** 30 hours  
**Deliverable:** Go fully supported

---

### Phase 6 Milestone

**Tests passing:** 280+  
**Languages:** Python + TypeScript + Go  
**Status:** Three languages supported

---

## Phase 7: Testing & Production Readiness (Weeks 25-28)

**Objective:** Production-ready system

### Week 25: Integration Testing

**Tasks:**
- 25.1: End-to-end tests (real repositories)
- 25.2: Monorepo support validation
- 25.3: Complex import patterns
- 25.4: 30+ integration tests

**Owner:** All  
**Effort:** 40 hours  
**Deliverable:** All subsystems tested together

---

### Week 26: Performance & Optimization

**Tasks:**
- 26.1: Full benchmark suite
- 26.2: Bottleneck identification
- 26.3: Optimization (parallel, caching)
- 26.4: Target: 50k LOC <30 sec, 10k LOC <5 sec

**Owner:** Lead Dev  
**Effort:** 40 hours  
**Deliverable:** Performance targets met

---

### Week 27: Documentation & ADRs

**Tasks:**
- 27.1: Architecture documentation
- 27.2: API documentation (docstrings + guide)
- 27.3: Extension guide (add new language)
- 27.4: Troubleshooting guide
- 27.5: ADRs (why we built this way)

**Owner:** Lead Dev + Dev 1  
**Effort:** 40 hours  
**Deliverable:** Complete documentation

---

### Week 28: Final Testing & Polish

**Tasks:**
- 28.1: Regression testing (all 350+ tests pass)
- 28.2: Final optimization
- 28.3: Production deployment checklist
- 28.4: Release notes
- 28.5: 70+ final integration tests

**Owner:** All  
**Effort:** 40 hours  
**Deliverable:** Production-ready, 350+ tests

---

### Phase 7 Milestone

**Tests passing:** 350+  
**Coverage:** >90%  
**Status:** Production-ready

---

## Team Structure & Capacity

### Phase 1-2 (Weeks 1-8)

**Team:** 3 developers (240 hours)
- **Lead Dev (120 hrs):** Architecture, Python adapter, file tree
- **Dev 1 (60 hrs):** Symbol extraction, call graph
- **Dev 2 (60 hrs):** Config, imports, dependencies

### Phase 3-4 (Weeks 9-16)

**Team:** 2 developers (160 hours)
- **Lead Dev (80 hrs):** Incremental indexing, optimization
- **Dev 1 (80 hrs):** Storage, caching, queries

### Phase 5-7 (Weeks 17-28)

**Team:** 3 developers (360 hours)
- **Lead Dev (120 hrs):** TS adapter, documentation
- **Dev 1 (120 hrs):** Go adapter, call graphs
- **Dev 2 (120 hrs):** Dependencies, integration tests

**Total:** ~8-10 person-months

---

## Risks & Mitigations

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| tree-sitter parser unreliable | Low | Use native parsers as backup |
| Performance doesn't meet targets | Medium | Profile early (Week 12), optimize incrementally |
| Type hint parsing complexity | Medium | Start basic, enhance iteratively |
| Complex multi-file dependencies | Medium | Build test corpus early, test frequently |

---

## Success Criteria

✅ Phase 1: RepositoryAnalysisProvider interface working  
✅ Phase 2: Python fully analyzable, benchmarks met  
✅ Phase 3: Incremental updates <100ms/file  
✅ Phase 4: Persistent, queryable storage  
✅ Phase 5: TypeScript/JavaScript support  
✅ Phase 6: Go support  
✅ Phase 7: 350+ tests, production-ready, documented  

---

*Roadmap for custom Repository Intelligence implementation*  
*28 weeks, 8-10 person-months, production-ready by Week 28*
