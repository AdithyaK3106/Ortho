# GitNexus Integration Plan

**Date:** 2026-07-01  
**Scope:** Phase 2 (Weeks 9-16)  
**Deliverable:** Multi-language repository intelligence via GitNexus adapter

---

## Overview

This plan describes how to integrate GitNexus as the backend for Ortho's Repository Intelligence pillar while maintaining architectural integrity and backward compatibility.

**Key principle:** GitNexus plugs into Ortho via adapter pattern. Other pillars unaware of swap.

---

## Phase 0: Preparation (Week 8, End of Phase 1)

### Objectives

- Verify GitNexus is safe to use (license, API maturity)
- Establish baseline performance metrics
- Document LanguageAdapter interface for adapter implementers

### Tasks

#### 0.1: License & Legal Review

**Effort:** 2 hours  
**Owner:** Tech Lead

**Steps:**
1. Clone GitNexus from https://github.com/abhigyanpatwari/GitNexus
2. Check LICENSE file (expected: MIT or Apache 2.0)
3. Check dependencies (run `pip list` for transitive licenses)
4. Document findings in `.ases/strategic-review/gitnexus-license-check.md`
5. Get legal sign-off if needed

**Acceptance criteria:**
- LICENSE file verified
- Transitive dependencies reviewed
- No GPL or restrictive licenses
- Can proceed with integration

---

#### 0.2: API Stability Assessment

**Effort:** 4 hours  
**Owner:** Senior Developer

**Steps:**
1. Read GitNexus documentation (README, API docs, examples)
2. Identify core APIs (Repository, Parser, Symbol, etc.)
3. Check version number (should be 1.0+, not 0.x)
4. Review recent commits (active maintenance?)
5. Document API contracts in `.ases/strategic-review/gitnexus-api-reference.md`

**Acceptance criteria:**
- API is documented
- Version is stable (1.0+)
- Recent activity in repo (commits in last 3 months)
- Can proceed with adapter

---

#### 0.3: Baseline Performance Measurement

**Effort:** 6 hours  
**Owner:** Performance Engineer

**Steps:**
1. Create test suite: run PythonAdapter on 50 Python files of varying size
2. Measure time per file, total time, memory usage
3. Test on files: 10 LOC, 100 LOC, 500 LOC, 2000 LOC
4. Document baseline in `.ases/strategic-review/perf-baseline-python-adapter.txt`
5. Note results (target: GitNexus should be 2x faster)

**Acceptance criteria:**
- Baseline measured (min 50 files)
- Results documented with timestamps
- Results available for Phase 2 comparison

---

#### 0.4: LanguageAdapter Interface Documentation

**Effort:** 3 hours  
**Owner:** Senior Architect

**Steps:**
1. Read current LanguageAdapter interface in `shared/types/src/adapter.ts`
2. Read Python side: `packages/repo-intelligence/adapters/python_adapter.py`
3. Document required methods, input/output types, error handling
4. Create `shared/adapters/ADAPTER_SPEC.md` with:
   - Required methods (extract_symbols, extract_imports, etc.)
   - Input types (file path, language)
   - Output types (Symbol, Import, CallEdge)
   - Confidence scoring
   - Error handling
   - Adapter lifecycle (init, cleanup)
5. Add examples for implementing a new adapter

**Acceptance criteria:**
- Interface fully documented
- Examples provided
- Future adapter implementers have clear spec

---

## Phase 1: Inventory & Analysis (Week 9, Task 4 Planning)

### Objectives

- Map existing Ortho Python adapter in detail
- Understand all integration points
- Plan for data model translation

### Tasks

#### 1.1: Code Inventory

**Effort:** 8 hours  
**Owner:** Senior Developer

**Steps:**
1. Read and document all Python adapter files:
   - `packages/repo-intelligence/adapters/python_adapter.py`
   - `packages/repo-intelligence/symbol_extractor.py`
   - `packages/repo-intelligence/import_graph.py`
   - `packages/repo-intelligence/call_graph.py`
   - `packages/repo-intelligence/dependency_graph.py`
   - `packages/repo-intelligence/module_detector.py`

2. For each file, document:
   - Public API methods
   - Internal helpers
   - External dependencies
   - Test coverage
   - Known limitations

3. Create `packages/repo-intelligence/PYTHON_ADAPTER_INVENTORY.md`

**Acceptance criteria:**
- All files inventoried
- Public APIs documented
- Test coverage understood

---

#### 1.2: Integration Points Analysis

**Effort:** 6 hours  
**Owner:** Senior Architect

**Steps:**
1. Trace how PythonAdapter is called:
   - From incremental indexer?
   - From ContextHub?
   - From architecture detector?
   - Direct from CLI/API?

2. Document call chain for each use case

3. Identify which outputs must match exactly:
   - Symbol schema (must match for ContextHub)
   - Import schema (must match for architecture detection)
   - Call graph schema (must match for orchestration)

4. Create `packages/repo-intelligence/INTEGRATION_POINTS.md`

**Acceptance criteria:**
- All call chains documented
- Output schemas identified
- Translation requirements clear

---

#### 1.3: Data Model Mapping

**Effort:** 4 hours  
**Owner:** Data Architect

**Steps:**
1. Read Ortho Symbol schema (from task-002 spec)
2. Read GitNexus Symbol schema (from GitNexus API docs)
3. Create comparison table:
   - Ortho field → GitNexus field
   - Type mappings (str, int, list)
   - Missing fields (what GitNexus has that Ortho doesn't)
   - Extra fields (what Ortho has that GitNexus doesn't)

4. Same for Import, Call, Dependency

5. Document in `packages/repo-intelligence/DATA_MODEL_MAPPING.md`

**Acceptance criteria:**
- Complete mapping for each model
- Translation strategy clear
- Edge cases identified

---

## Phase 2: Adapter Implementation (Weeks 10-11, Task 4)

### Objectives

- Implement GitNexusAdapter
- Create compatibility tests
- Verify A/B parity

### Tasks

#### 2.1: GitNexusAdapter Class

**Effort:** 12 hours  
**Owner:** Lead Developer

**Location:** `packages/repo-intelligence/adapters/gitnexus_adapter.py`

**Steps:**
1. Create GitNexusAdapter class implementing LanguageAdapter interface
2. Initialize GitNexus repository on construction
3. Implement extract_symbols() → translate GitNexus output to Ortho Symbol
4. Implement extract_imports() → translate GitNexus imports to Ortho Import
5. Implement language property (return supported languages)
6. Add error handling (GitNexus failures → clear error messages)
7. Add logging (trace execution path)

**Code outline:**
```python
class GitNexusAdapter(LanguageAdapter):
    def __init__(self, repo_path: Path, cache: bool = True):
        self.repo = GitNexusRepository(path=repo_path)
        self.cache = cache
        self._symbol_cache = {}
    
    @property
    def languages(self) -> list[str]:
        return ["python", "typescript", "go", "java", "rust"]  # From GitNexus
    
    def extract_symbols(self, file: Path) -> list[Symbol]:
        """Extract symbols from file using GitNexus."""
        try:
            gn_symbols = self.repo.get_symbols(str(file))
            return [self._translate_symbol(s) for s in gn_symbols]
        except Exception as e:
            logger.error(f"GitNexus symbol extraction failed for {file}: {e}")
            raise AdapterError(f"Failed to extract symbols: {e}")
    
    def extract_imports(self, file: Path) -> list[Import]:
        """Extract imports from file using GitNexus."""
        gn_imports = self.repo.get_imports(str(file))
        return [self._translate_import(i) for i in gn_imports]
    
    def _translate_symbol(self, gn_symbol) -> Symbol:
        """Translate GitNexus symbol to Ortho Symbol."""
        return Symbol(
            id=gn_symbol.id,
            name=gn_symbol.name,
            qualified_name=gn_symbol.qualified_name,
            type=gn_symbol.type,
            location=Location(
                file=gn_symbol.location.file,
                line=gn_symbol.location.line,
                column=gn_symbol.location.column,
            ),
            docstring=gn_symbol.docstring,
            metadata={
                "decorators": gn_symbol.metadata.decorators,
                "is_async": gn_symbol.metadata.is_async,
                "is_private": gn_symbol.metadata.is_private,
            }
        )
    
    def _translate_import(self, gn_import) -> Import:
        """Translate GitNexus import to Ortho Import."""
        return Import(
            source_module=gn_import.source,
            target_module=gn_import.target,
            import_type=gn_import.type,
            location=Location(file=gn_import.file, line=gn_import.line),
        )
```

**Acceptance criteria:**
- Adapter class compiles (mypy --strict passes)
- All methods implemented
- Error handling in place
- Logging added

---

#### 2.2: Adapter Tests

**Effort:** 10 hours  
**Owner:** QA Engineer

**Location:** `packages/repo-intelligence/tests/test_gitnexus_adapter.py`

**Steps:**
1. Create test file with 20+ test cases
2. For each test case:
   - Create a sample Python file
   - Run both PythonAdapter and GitNexusAdapter on same file
   - Compare output (symbols, imports, counts)
   - Assert they match (or document differences)

3. Test cases should cover:
   - Simple functions
   - Classes and methods
   - Decorators
   - Async functions
   - Imports (from, import, relative)
   - Circular imports
   - Syntax errors (error handling)
   - Empty files
   - Large files (2000+ LOC)

**Sample test:**
```python
def test_simple_function():
    """Both adapters should extract same symbols from simple function."""
    code = """
def hello(name: str) -> str:
    '''Say hello.'''
    return f"Hello, {name}"
"""
    file_path = create_test_file(code)
    
    ortho_symbols = PythonAdapter().extract_symbols(file_path)
    gn_symbols = GitNexusAdapter(repo_path).extract_symbols(file_path)
    
    assert len(ortho_symbols) == len(gn_symbols)
    assert ortho_symbols[0].name == gn_symbols[0].name
    assert ortho_symbols[0].qualified_name == gn_symbols[0].qualified_name
```

**Acceptance criteria:**
- 20+ tests written
- 100% test pass rate
- A/B parity confirmed (symbols match)

---

#### 2.3: Configuration Support

**Effort:** 4 hours  
**Owner:** Lead Developer

**Location:** `shared/storage/config.py` (update), `apps/cli/config.ts` (update)

**Steps:**
1. Add config option `adapter` to OrthoConfig:
   ```toml
   [repository_intelligence]
   adapter = "python"  # or "gitnexus"
   gitnexus_languages = ["python", "typescript"]  # if adapter="gitnexus"
   ```

2. Update config loader to:
   - Parse `adapter` field
   - Instantiate correct adapter class
   - Validate adapter choice

3. Update CLI to accept `--adapter` flag:
   ```bash
   ortho scan --adapter gitnexus --languages python,typescript
   ```

4. Document in config spec

**Acceptance criteria:**
- Config option works
- CLI flag works
- Defaults to PythonAdapter (backward compatible)

---

#### 2.4: Performance Comparison

**Effort:** 6 hours  
**Owner:** Performance Engineer

**Steps:**
1. Run same 50 Python files through both adapters
2. Measure time per file
3. Calculate average, median, p95, p99
4. Compare to baseline
5. Document in `packages/repo-intelligence/PERF_COMPARISON.txt`

**Expected results:**
- PythonAdapter: ~100ms/file (baseline)
- GitNexusAdapter: ~50ms/file (2x faster)

**Acceptance criteria:**
- Performance measured
- Results documented
- No regressions in output quality

---

## Phase 3: Integration Testing (Weeks 12-13, Task 5)

### Objectives

- Verify GitNexusAdapter works with all downstream components
- Ensure no regressions

### Tasks

#### 3.1: ContextHub Integration Tests

**Effort:** 8 hours  
**Owner:** QA Engineer

**Location:** `packages/context-hub/tests/test_with_gitnexus_adapter.py`

**Steps:**
1. Create integration test:
   - Use GitNexusAdapter to extract symbols
   - Ingest symbols into ContextHub
   - Run search queries (BM25, semantic, hybrid)
   - Verify results are correct

2. Run same test with PythonAdapter
3. Compare results (should be identical or very similar)

**Acceptance criteria:**
- ContextHub tests pass with GitNexus
- Search results match (symbols findable)
- No performance regression

---

#### 3.2: Architecture Detection Integration Tests

**Effort:** 8 hours  
**Owner:** QA Engineer

**Location:** `packages/arch-intelligence/tests/test_with_gitnexus_adapter.py`

**Steps:**
1. Run architecture detector with GitNexusAdapter backend
2. Test on same repos as Phase 1 tests
3. Compare confidence scores (should match or be slightly higher)
4. Compare detected patterns (should match)

**Acceptance criteria:**
- Arch-intelligence tests pass
- Confidence scores >= baseline
- No false positives

---

#### 3.3: Incremental Indexing with GitNexus

**Effort:** 6 hours  
**Owner:** Developer

**Location:** `packages/repo-intelligence/tests/test_incremental_with_gitnexus.py`

**Steps:**
1. Create test repo with Python files
2. Run full indexing with GitNexusAdapter
3. Modify one file, run incremental update
4. Verify only changed symbols updated
5. Compare to PythonAdapter results

**Acceptance criteria:**
- Incremental indexing works
- Only changed symbols updated
- Performance comparable

---

#### 3.4: End-to-End CLI Tests

**Effort:** 8 hours  
**Owner:** QA Engineer

**Steps:**
1. Run CLI with GitNexusAdapter:
   ```bash
   ortho init --adapter gitnexus
   ortho scan --languages python,typescript
   ortho context search "find all classes"
   ortho analyze --architecture
   ```

2. Verify each command works
3. Check output quality
4. Compare to PythonAdapter flow

**Acceptance criteria:**
- All CLI commands work
- Output is correct
- No crashes or errors

---

## Phase 4: Production Transition (Weeks 14-15, Task 6)

### Objectives

- Make GitNexus default
- Monitor for issues
- Decide on deprecation timeline

### Tasks

#### 4.1: Make GitNexus Default

**Effort:** 3 hours  
**Owner:** Tech Lead

**Steps:**
1. Change default in config: `adapter = "gitnexus"`
2. Update documentation
3. Update examples
4. Keep PythonAdapter available via config

**Acceptance criteria:**
- Default changed
- No breaking changes (PythonAdapter still available)
- Tests pass with new default

---

#### 4.2: Monitoring & Feedback

**Effort:** 4 weeks (ongoing)  
**Owner:** DevOps/Platform team

**Steps:**
1. Run Ortho in production with GitNexus
2. Monitor performance metrics:
   - Indexing time per file
   - Memory usage
   - Error rates
3. Collect user feedback
4. Log any issues

**Acceptance criteria:**
- 1+ month of stable operation
- No critical bugs
- Performance meets expectations
- User feedback positive

---

#### 4.3: Deprecation Decision

**Effort:** 2 hours  
**Owner:** Tech Lead

**Steps:**
1. Review monitoring data
2. Review test results
3. Decide: deprecate PythonAdapter or keep both?
4. Document decision in ADR

**Possible outcomes:**
- ✅ Keep both (PythonAdapter as fallback)
- ✅ Deprecate PythonAdapter (mark for removal in 6 months)
- ❌ Revert to PythonAdapter (if GitNexus issues found)

**Acceptance criteria:**
- Decision documented
- Roadmap updated

---

## Phase 5: Multi-language Support (Weeks 16-17, Task 7)

### Objectives

- Add TypeScript and Go support
- Unlock multi-language analysis

### Tasks

#### 5.1: TypeScript Adapter

**Effort:** 4 hours  
**Owner:** Lead Developer

**Location:** `packages/repo-intelligence/adapters/gitnexus_typescript_adapter.py`

**Steps:**
1. Create TypeScriptAdapter extending GitNexusAdapter
2. Override language selection: `["typescript", "javascript"]`
3. Test on TypeScript files
4. Verify all integration tests pass

**Acceptance criteria:**
- TypeScript files parseable
- Symbols extracted correctly
- Integration tests pass

---

#### 5.2: Go Adapter

**Effort:** 4 hours  
**Owner:** Lead Developer

**Location:** `packages/repo-intelligence/adapters/gitnexus_go_adapter.py`

**Steps:**
1. Create GoAdapter extending GitNexusAdapter
2. Override language selection: `["go"]`
3. Test on Go files
4. Verify all integration tests pass

**Acceptance criteria:**
- Go files parseable
- Symbols extracted correctly
- Integration tests pass

---

#### 5.3: CLI Multi-language Support

**Effort:** 3 hours  
**Owner:** Lead Developer

**Steps:**
1. Add `--languages` flag to `ortho scan`:
   ```bash
   ortho scan --languages python,typescript,go
   ```

2. CLI detects file extensions and routes to appropriate adapter
3. Update documentation
4. Test end-to-end

**Acceptance criteria:**
- CLI supports multiple languages
- Files routed to correct adapter
- Mixed-language repos work

---

## Quality Gates

### Gate: Code Quality

- [ ] All new code passes mypy --strict
- [ ] All new code passes pylint
- [ ] No circular imports
- [ ] Type annotations complete

### Gate: Test Coverage

- [ ] Adapter tests: 100% pass rate
- [ ] Integration tests: 100% pass rate
- [ ] End-to-end tests: 100% pass rate
- [ ] No new TODOs or FIXMEs

### Gate: Performance

- [ ] GitNexus adapter ≥2x faster than Python for Python files
- [ ] No memory regressions
- [ ] Incremental indexing still fast (<100ms per file)

### Gate: Backward Compatibility

- [ ] PythonAdapter still runnable (fallback available)
- [ ] Config remains backward compatible
- [ ] No breaking changes to LanguageAdapter interface
- [ ] Existing projects still work

### Gate: Documentation

- [ ] Adapter spec updated (ADAPTER_SPEC.md)
- [ ] ADR written (ADR-XXX-gitnexus-integration.md)
- [ ] README updated (mention multi-language support)
- [ ] Troubleshooting guide (what to do if issues)

---

## Risk Mitigation Timeline

| Week | Risk | Mitigation | Owner |
|------|------|-----------|-------|
| 9 | GitNexus not available | Verify source, check license | Tech Lead |
| 10 | Adapter API mismatch | Test A/B on 50 files | QA |
| 11 | Performance regression | Measure baseline + compare | DevOps |
| 12 | Integration breaks | Run full test suite | QA |
| 13 | Arch detector fails | Run 50 test cases | QA |
| 14 | Production issues | Monitor 1 week before making default | DevOps |
| 15 | User complaints | Have rollback plan ready | Tech Lead |
| 16 | Multi-language bugs | Test each language separately | Developer |

---

## Success Criteria (Phase 2 Completion)

- [ ] GitNexus license verified and approved
- [ ] GitNexusAdapter implemented and tested
- [ ] ContextHub works with GitNexus backend
- [ ] Architecture detection works with GitNexus backend
- [ ] CLI supports `--adapter` flag
- [ ] Performance: 2x faster for Python files
- [ ] A/B test shows parity (same symbols extracted)
- [ ] Multi-language support (Python + TypeScript + Go)
- [ ] All 6 ASES gates passed for Phase 2 work
- [ ] PythonAdapter available as fallback
- [ ] FRD updated to reflect GitNexus dependency

---

## Rollback Plan

If at any point GitNexus integration fails:

1. **Days 1-7 (during Task 4):** Simply don't merge GitNexusAdapter
2. **Days 8-14 (during Task 5):** Keep PythonAdapter, revert config default to "python"
3. **After production (Week 14+):** Switch config back to PythonAdapter (5-minute rollback)

**Rollback procedure:**
```bash
# In config.toml
[repository_intelligence]
adapter = "python"  # revert from "gitnexus"

# Restart Ortho
ortho restart
```

**Estimated downtime:** < 5 minutes (no data loss, pure config change)

---

## Team & Resources

| Role | Name | Weeks | Hours/Week |
|------|------|-------|-----------|
| Tech Lead | TBD | 9-16 | 4 |
| Lead Developer | TBD | 10-17 | 8 |
| QA Engineer | TBD | 10-17 | 10 |
| Performance Engineer | TBD | 9, 11-12 | 6 |
| DevOps | TBD | 14-15 | 4 |
| **Total** | | | ~50 hrs/week |

---

## Approval & Sign-off

- [ ] Tech Lead approves plan
- [ ] Architecture review approves plan
- [ ] QA lead approves test strategy
- [ ] License/Legal approves GitNexus usage

---

*Integration plan prepared by ARCHITECT*  
*Next step: Proceed to Phase 0 (Preparation) at end of Week 8*
