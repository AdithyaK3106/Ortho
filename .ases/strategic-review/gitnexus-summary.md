# GitNexus: Technical Architecture Summary

**Repository:** https://github.com/abhigyanpatwari/GitNexus  
**Version:** 1.6.8  
**License:** PolyForm Noncommercial 1.0.0 (commercial licensing available)  
**Status:** Production-ready, actively maintained (daily commits)  
**Test Coverage:** 32+ test files, Vitest + Playwright

---

## Executive Summary

GitNexus is a production-grade knowledge graph system that indexes codebases and exposes them via MCP, CLI, and REST APIs. It supports 16 languages, extracts complete symbol lineage (imports, calls, inheritance), clusters code into functional communities, and enables AI agents to perform reliable impact analysis, multi-file rename, and cross-repo tracing.

**Core strength:** Precomputed relational intelligence — agents get complete blast-radius analysis in one tool call instead of chaining 10+ queries.

---

## Architecture Overview

### Indexing Pipeline (14 Phases, Typed DAG)

```
scan → structure → [markdown, cobol] → parse (worker-pool)
  → [routes, tools, orm] → crossFile → scopeResolution
  → pruneLocalSymbols → mro → communities (Leiden) → processes
```

Each phase is an immutable stage with explicit dependencies; runner validates topological sort and executes sequentially.

### Data Model

- **44 node types:** File, Folder, Function, Class, Interface, Method, Property, Const, Community, Process, Route, Tool, BasicBlock (PDG-optional), + more
- **21 relation types:** CONTAINS, DEFINES, CALLS, IMPORTS, EXTENDS, IMPLEMENTS, HAS_METHOD, METHOD_OVERRIDES, MEMBER_OF, STEP_IN_PROCESS, HANDLES_ROUTE, + PDG-optional (CFG, REACHING_DEF, CDG, TAINT, SANITIZES, TAINT_PATH)
- **Confidence tiering:** Same-file 0.95, import-scoped 0.9, global fallback 0.5 (agents filter by threshold)

### Storage: LadybugDB

- Native C++ graph DB (Apache 2.0) for CLI
- WASM variant for browser (in-memory per session)
- Separate node tables per type; single CodeRelation table with `type` property
- Git-diff-based incremental indexing; SHA1 content hash caching

### Language Support (16 Languages)

**Full support:** TypeScript, JavaScript, Python, Java, Kotlin, C#, Go, Rust, PHP, Ruby, Swift, C, C++, Dart

**Per-language extraction:**
- Imports (3-tier: same-file → import-scoped → global)
- Symbol definitions (functions, classes, methods, fields, constants)
- Call graph (with confidence scores)
- Inheritance (EXTENDS / IMPLEMENTS / HAS_METHOD)
- Type annotations (where available)
- Constructor inference (receiver type resolution)
- Framework detection (routes, tools, ORM)

**Known limitations:**
- C/C++: No import resolution (preprocessor `#include` not resolved)
- Python: Method ownership resolved during scope-resolution (reconciliation pass)
- Ruby/PHP: Dynamic receiver dispatch limited
- COBOL: Regex-based extraction only (no tree-sitter AST)

### Scope Resolution Pipeline (RFC #909 Ring 3)

Language-agnostic orchestrator with per-language `ScopeResolver` interface (12 hooks):
- `populateOwners` — fill deferred `ownerId` fields
- `buildMro` — method resolution order (C3 for Python, Ruby-mixin for Ruby, first-wins for others)
- `resolveImportTarget` — `(importPath, sourceFile) → targetFilePath`
- `mergeBindings` — handle shadowing / LEGB precedence
- `arityCompatibility` — overload resolution
- Hooks for implicit namespaces, type binding hoisting, cross-file return-type propagation

**Three resolution passes:**
1. Receiver-bound calls (`foo.bar()` via receiver type)
2. Free-call fallback (`bar()` via scope chain)
3. Reference lookup (property access resolution)

### Search & Retrieval

- **Hybrid ranking:** BM25 (SQLite FTS5) + semantic (Snowflake arctic-embed-xs 384D) merged via RRF (K=60)
- **Process-grouped results** — agents see execution-flow participation
- **Configurable FTS stemmer** — default Porter English; alternatives: french, german, spanish, none (CJK)
- **Incremental embeddings** — SHA1 content hash caching

### Community Detection & Process Tracing

- **Leiden algorithm** clusters symbols into functional communities
- **Process detection** traces entry points through call chains to terminal symbols
- **Repo-specific skills** — `gitnexus analyze --skills` generates per-community SKILL.md with targeted context

### MCP Server (3 Query Interfaces)

All three use the same `LocalBackend` implementation:

| Interface | Command | Role |
|-----------|---------|------|
| MCP (stdio) | `gitnexus mcp` | Model Context Protocol server for agents |
| HTTP API | `gitnexus serve` | REST backend for web UI + bridge mode |
| CLI direct | `gitnexus query\|context\|impact` | Command-line tools |

**16 MCP Tools:**
- `query` — hybrid BM25 + semantic search
- `context` — 360-degree symbol view (callers, callees, processes)
- `impact` — blast radius (upstream/downstream) with depth grouping
- `detect_changes` — git-diff impact analysis
- `rename` — multi-file coordinated rename
- `cypher` — raw graph queries
- `trace` — shortest path between symbols (call + class-member edges)
- `api_impact`, `route_map`, `tool_map`, `shape_check`, `explain` (PDG-dependent), `pdg_query`, `group_list`, `group_sync`

**7 Resources:** repos, clusters, processes, schema

**2 MCP Prompts:** detect_impact, generate_map

**4 Bundled Agent Skills:** Exploring, Debugging, Impact Analysis, Refactoring

### Multi-Repo Architecture (Groups)

- **Contract Registry** (`contracts.json`) — extracted API boundaries
- **Bridge database** — cross-repo link table
- **Cross-repo trace** — shortest path across repositories via Contract links
- **Cross-repo impact** — blast radius analysis across repos

### Web UI & Docker

- **Web:** React 18, TypeScript, Vite, Tailwind v4, Sigma.js (WebGL rendering), Tree-sitter WASM, LadybugDB WASM
- **Docker:** Two signed images (Cosign keyless), SBOM + provenance attestations
  - `ghcr.io/abhigyanpatwari/gitnexus:latest` — CLI/server
  - `ghcr.io/abhigyanpatwari/gitnexus-web:latest` — Web UI
  - Mirrors on Docker Hub (`akonlabs/gitnexus`, `akonlabs/gitnexus-web`)

---

## Key Architectural Patterns

1. **Typed pipeline DAG** — explicit dependencies, compile-time phase exhaustiveness
2. **Worker-pool parse** — workers serialize ParsedFile artifacts to disk; scope-resolution consumes pre-extracted data (prevents OOM on Linux-kernel-scale repos)
3. **Language-agnostic scope resolution** — single RFC #909 pipeline serves 16 languages via ScopeResolver interface contracts
4. **Single graph accumulator** — all phases mutate shared KnowledgeGraph; no inter-phase passing
5. **Confidence tiering on edges** — agents understand certainty (same-file 0.95 vs. global 0.5)
6. **Incremental indexing** — SHA1 content hash caching + git-diff-based; warm cache replay without worker spawning

---

## Strengths

1. **Production-grade** — daily commits, 20+ contributors, comprehensive testing (32+ test files, CI enforced)
2. **Precomputed intelligence** — agents get complete blast-radius in one call (no 10-query chains)
3. **Type-safe architecture** — TypeScript strict, typed pipeline DAG, compile-time phase dependencies
4. **Language-agnostic** — single scope-resolution RFC #909 for 16 languages via interface contracts
5. **Multi-repo aware** — Contract Registry + cross-repo trace/impact
6. **Privacy-first** — CLI = zero network, Web WASM = in-browser, bridge mode optional
7. **Confidence-tiered edges** — tools filter by threshold (0.5–1.0 scale)
8. **Incremental indexing** — git-diff + SHA1 content hash caching
9. **Hybrid search** — BM25 + semantic + RRF; configurable FTS stemmer
10. **Exceptional documentation** — ARCHITECTURE.md (detailed), RUNBOOK.md, GUARDRAILS.md, TESTING.md
11. **Framework detection** — routes (Next.js, Spring, FastAPI), tools (MCP, RPC), ORM (Prisma, Supabase)
12. **Agent hooks** — Claude Code (PreToolUse/PostToolUse), Antigravity (AfterTool), Cursor, Codex

---

## Weaknesses & Gaps

1. **License constraint** — PolyForm Noncommercial OSS; commercial licensing requires negotiation
2. **No C/C++ import resolution** — preprocessor `#include` not resolved to files
3. **PDG (control-flow/taint) TypeScript/JS only** — opt-in `--pdg` flag; other languages planned
4. **Overload ID stability risk** — adding an overload changes node IDs if types present (`save#1` → `save#1~int`)
5. **No sequential parse fallback** — worker pool is sole parse path; `--workers 0` rejected
6. **COBOL regex-based** — limited symbol extraction without tree-sitter AST
7. **Dynamic receiver dispatch limited** — Python/Ruby dynamic calls rely on annotations or constructor inference

---

## Dependencies

| Dependency | Version | License |
|-----------|---------|---------|
| @ladybugdb/core | ^0.17.0 | Apache 2.0 |
| tree-sitter | 0.21.1 | MIT |
| @modelcontextprotocol/sdk | ^1.0.0 | MIT (Anthropic) |
| @huggingface/transformers | ^4.1.0 | Apache 2.0 |
| graphology | ^0.26.0 | MIT |
| express | ^5.2.1 | MIT |
| commander | ^15.0.0 | MIT |

---

## Extension Points for Ortho

### 1. Adding Languages
- Implement `LanguageProvider` (tree-sitter queries, import semantics, type config, export checker, MRO strategy)
- Implement `ScopeResolver` (12 hooks for scope chain, method dispatch, import resolution)
- Register in `SCOPE_RESOLVERS` map
- ~200–500 LOC per language; CI auto-discovers

### 2. Custom Tools
- Implement in `local-backend.ts`
- Register in `tools.ts`
- ~100–200 LOC per tool

### 3. Custom Knowledge Graph Queries
- Via `cypher()` tool — agents write raw Cypher against full schema

### 4. Incremental Indexing Hooks
- Early exit if `lastCommit == HEAD` (unless `--force`)
- Parser cache keyed on file content SHA1
- Embeddings reuse prior content hash matches

### 5. Scope-Resolution Hooks (Per-Language)
- `populateNamespaceSiblings?` — cross-file implicit visibility
- `hoistTypeBindingsToModule?` — walk up to Module scope for type lookup
- `fieldFallbackOnMethodLookup?` — property fallback for method lookup
- `propagatesReturnTypesAcrossImports?` — opt out of cross-file type propagation

---

## Strategic Fit for Ortho

### Phase 1 (Weeks 1–8): Reference, Don't Integrate
- Study **ARCHITECTURE.md section 3** (scope-resolution) for week 3–4 Python adapter
- Reference **language provider pattern** for your LanguageAdapter
- Implement own scope-resolution per language (SQLite backend, learn from patterns)
- Defer clustering/processes to Phase 2

### Phase 2+ (If Licensing Clears): Integration Options
- Use GitNexus CLI/MCP for agent augmentation (`gitnexus impact()` for blast-radius)
- Embed as secondary indexer (run `gitnexus analyze` on top of Ortho for fallback)
- License enterprise version for commercial distribution (contact: founders@akonlabs.com)

### Recommendations
1. Adopt **typed pipeline DAG** from day one (compile-time exhaustiveness)
2. **Confidence-tier edges** (0.5–1.0) — helps agents distinguish certain vs. heuristic
3. **Language registry pattern** — one interface per language
4. **Incremental indexing** — SHA1 content hash caching beats full re-analysis
5. **Start with BM25** (SQLite FTS5); semantic embeddings in Phase 2
6. **Contact GitNexus early** if licensing is a concern (research vs. commercial)

---

## References

- **GitHub:** https://github.com/abhigyanpatwari/GitNexus
- **Documentation:** README.md, ARCHITECTURE.md, TESTING.md, RUNBOOK.md, GUARDRAILS.md
- **Enterprise:** https://akonlabs.com
- **Community:** https://discord.gg/MgJrmsqr62

---

*Analysis Date:* 2026-07-01  
*Reviewed Version:* 1.6.8  
*Artifacts:* README, ARCHITECTURE, TESTING, source, package.json, recent commits
