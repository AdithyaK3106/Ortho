task: task-002
title: Week 3–4 — Python Language Adapter
architect: ARCHITECT
created: 2026-06-30
status: PROPOSED

module_boundaries:
  new_modules:
    - repo-intelligence: package containing LanguageAdapter implementations (Python adapter, future Kotlin/Go adapters)
    - shared/types/src/adapter.ts: LanguageAdapter interface definition
  modified_modules:
    - shared/types: exports LanguageAdapter interface
  assessment: PASS — module boundaries are clear. repo-intelligence is cohesive (all language adapters live here). LanguageAdapter interface lives in shared/types for cross-package use. Single responsibility: repo-intelligence analyzes code, shared/types defines contracts.

dependency_analysis:
  graph: |
    PythonAdapter (repo-intelligence)
        ↓ (imports)
    LanguageAdapter interface (shared/types)
        ↓ (imports)
    shared/types (Symbol, ImportEdge dataclasses)
        ↓ (imports)
    tree-sitter (external dependency)
  circular_deps: PASS — no circular dependencies. repo-intelligence depends on shared/types only. No reverse dependency.
  assessment: PASS — dependency direction is one-way and intentional.

api_contracts:
  new_endpoints: None (internal API, not HTTP/CLI)
  new_interfaces:
    - LanguageAdapter: abstract interface with parse(file_path), extract_symbols(tree), analyze_dependencies(tree)
    - Symbol: dataclass with name, qualified_name, type (function|class|method), lineno, docstring
    - ImportEdge: dataclass with source_module, target_module, import_type (from|import|relative), lineno
  consistency: PASS — interfaces follow existing Ortho patterns (dataclasses for data, clear method signatures). Naming consistent (verb_noun: extract_symbols, analyze_dependencies).
  assessment: PASS — API contracts are clear and consistent.

data_flow:
  validation_layers:
    - Input validation: file paths validated by caller (BUILDER responsibility)
    - Parse layer: tree-sitter grammar validates Python syntax (external)
    - Symbol extraction: traverses AST, filters for relevant nodes
    - Import extraction: traverses AST, filters for import statements
  data_integrity:
    - Symbol objects immutable (dataclass, frozen=True recommended)
    - ImportEdge objects immutable (dataclass, frozen=True recommended)
    - No database writes (no integrity constraints needed at this layer)
  assessment: PASS — data flow is clear. Validation responsibilities appropriately distributed.

risk_flags:
  - risk: tree-sitter Python grammar not available — severity: MEDIUM — mitigation: grammar auto-installs with tree-sitter package; test will catch if missing
  - risk: Circular imports cause infinite loops in graph builder — severity: MEDIUM — mitigation: use set to track visited modules, detect cycles
  - risk: Symbol extraction incomplete (misses edge cases) — severity: LOW — mitigation: comprehensive tree-sitter query, tested with representative Python files
  - risk: Performance degrades on large files (1000+ lines) — severity: LOW — mitigation: acceptable for Phase 1 MVP; optimization deferred to Phase 2

adrs_created: None required. Task fits existing LanguageAdapter pattern defined in Ortho FRD. No new architectural decisions.

adrs_referenced: None (pattern is in FRD, not in ADR system yet)

verdict: APPROVED

rationale: Task implements first instance of existing LanguageAdapter pattern. No new architecture decisions. Boundaries clear. Dependencies one-way. API contracts explicit. Risks identified and mitigated. Ready for BUILDER.

---
