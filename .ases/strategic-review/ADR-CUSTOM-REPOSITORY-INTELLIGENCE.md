# ADR: Build Custom Repository Intelligence Instead of Integrating GitNexus

**Status:** ACCEPTED  
**Date:** 2026-07-01  
**Scope:** Ortho's Repository Intelligence subsystem (Pillar 1)  
**Decision Maker:** Principal Systems Architect  

---

## Context

Ortho is an Engineering Intelligence Platform with multiple pillars:
1. Repository Intelligence (code analysis)
2. ContextHub (artifact storage)
3. Architecture Intelligence (architectural analysis)
4. Retrieval & Search
5. Engineering Memory
6. ASES (workflow system)
7. Orchestration

GitNexus is a mature, high-quality repository intelligence library. It offers:
- Multi-language support (Python, TypeScript, Go, Java, Rust, C++, Ruby)
- Fast AST parsing
- Comprehensive graph construction
- Proven architecture

**The question:** Should Ortho integrate GitNexus or build its own Repository Intelligence?

---

## Options Considered

### Option A: Integrate GitNexus as Embedded Library

**How:** Implement RepositoryAnalysisProvider adapter that wraps GitNexus

**Advantages:**
- Fast integration (2-4 weeks)
- Multi-language support immediately
- Proven, battle-tested code
- Reduced maintenance burden

**Disadvantages:**
- ❌ **BLOCKING:** PolyForm Noncommercial license prohibits commercial use
- ❌ Cannot ship in Ortho SDK (license violation)
- ❌ Cannot use in SaaS (commercial use forbidden)
- ⚠️ Vendor lock-in (GitNexus license, upgrades, breaking changes)
- ⚠️ External dependency (maintenance outside Ortho's control)

**Verdict:** ❌ **NOT VIABLE** — License incompatibility is a blocker for commercial Ortho.

---

### Option B: Fork GitNexus

**How:** Clone GitNexus, modify for Ortho, maintain separately

**Advantages:**
- Full ownership
- No licensing constraints
- Can modify freely

**Disadvantages:**
- ❌ Maintenance burden (track upstream, merge updates)
- ❌ License compliance required (must reproduce GitNexus license, track attribution)
- ❌ Intellectual property complexity
- ❌ Code duplication (why maintain a fork of maintained code?)

**Verdict:** ❌ **NOT RECOMMENDED** — Too much maintenance burden. If we're maintaining a fork, we might as well write original code.

---

### Option C: Learn from GitNexus Architecture, Build Custom

**How:** Study GitNexus design, implement equivalent system from scratch in Ortho's codebase

**Advantages:**
- ✅ 100% ownership (no licensing, no external deps)
- ✅ Commercial viability (sell without restrictions)
- ✅ Vendor independence (can evolve independently)
- ✅ Learning investment (team understands code deeply)
- ✅ Design for Ortho's needs (tight integration with ContextHub, ASES, etc.)
- ✅ Full control over roadmap

**Disadvantages:**
- ⚠️ Takes longer (4-6 months vs. 2 weeks integration)
- ⚠️ More engineering effort (8-10 person-months)
- ⚠️ Single-language initially (Python first, TypeScript/Go in Phase 2)
- ⚠️ Must match GitNexus quality (higher bar)

**Verdict:** ✅ **RECOMMENDED** — Best fit for Ortho's long-term goals.

---

## Decision

**BUILD CUSTOM Repository Intelligence** (Option C)

Ortho will design and implement its own Repository Intelligence system, learning from GitNexus's architectural patterns but writing 100% original code.

---

## Rationale

### 1. License is a Hard Blocker

GitNexus uses **PolyForm Noncommercial 1.0.0**, which explicitly prohibits:
- Commercial SaaS use (Ortho Cloud would be illegal)
- Distributing as part of SDK (commercial product violation)
- Any commercial use without explicit license

**Solution:** Build custom code that Ortho owns completely.

### 2. Ortho is NOT Just a Code Parser

Ortho's differentiator is **Engineering Intelligence**, not Repository Intelligence.

Repository Intelligence is one pillar. The others are:
- ContextHub (long-term artifact storage)
- Architecture Intelligence (style detection, layer extraction)
- ASES (workflow governance)
- Planning, Review, Verification

**Benefit of building custom:**
- Tight integration with ContextHub (artifacts indexed immediately)
- Integration with Architecture Intelligence (no data translation layer)
- Alignment with ASES workflows (native error handling, resumability)
- One data model (Ortho-owned) instead of two (Ortho + GitNexus)

### 3. Quality Can Match GitNexus

GitNexus is excellent, but not magic. It's well-engineered but not proprietary.

**What we're building:**
- Same architectural patterns (language adapters, incremental indexing, storage abstraction)
- Same algorithms (published algorithms—Tarjan's SCC, topological sort, Louvain clustering)
- Same data structures (Symbol, ImportEdge, CallEdge)
- Same RFCs (RFC #909 for scope resolution, PEP 420 for namespaces)

**Why we can do this:**
- Algorithms are mathematical (not owned by GitNexus)
- Data structures are designs (not creative works)
- RFCs are public standards (not GitNexus property)

**Timeline:** 4-6 months to match GitNexus quality (28 weeks, Phase 1-7)

### 4. Long-Term Vendor Independence

Building custom means:
- ✅ No licensing uncertainty (future versions, maintainer decisions)
- ✅ Can evolve independently (not constrained by GitNexus roadmap)
- ✅ Can optimize for Ortho's specific needs
- ✅ Can replace with future provider without changing Ortho core

### 5. Learning Investment

Team that builds Repository Intelligence understands:
- Code parsing and analysis deeply
- Ortho's architecture deeply
- Integration points across subsystems
- Where optimizations matter most

**Value:** Can maintain, improve, and extend system indefinitely.

---

## Consequences

### Positive

✅ **Full ownership** — No licensing constraints, can sell commercially  
✅ **Vendor independence** — Not tied to GitNexus roadmap/decisions  
✅ **Tight integration** — Native integration with ContextHub, ASES, Architecture  
✅ **Long-term evolution** — Can improve independently  
✅ **Team expertise** — Deep understanding of subsystem  
✅ **Commercial viability** — No restrictions on SaaS, SDK, or usage  

### Negative

❌ **Longer timeline** — 4-6 months vs. 2 weeks for integration  
❌ **More effort** — 8-10 person-months vs. 2-3 person-months  
❌ **Single-language initially** — Python first, TS/Go in Phase 2  
❌ **Maintenance burden** — Our team owns the code forever  
❌ **Quality bar is higher** — Must match GitNexus standard  

### Mitigation

- **Timeline:** Acceptable because Repository Intelligence is not Ortho's differentiator
- **Effort:** 8-10 person-months is 2-3 developer-months (Phase 1-7 overlaps other work)
- **Single-language:** Can start Python-only, add TS/Go in Phase 2 (weeks 17-24)
- **Maintenance:** Self-service (our code, our choices)
- **Quality:** Leverage GitNexus design patterns, proven algorithms, existing test repos

---

## Implementation Strategy

### Phase 1-2: Foundation + Python (Weeks 1-8)

1. Study GitNexus architecture
2. Design equivalent system (adapters, builders, storage)
3. Implement Python support (symbols, imports, calls, dependencies)
4. Tests: 80+ 

**Deliverable:** Python repos fully analyzable

### Phase 3-4: Incremental + Storage (Weeks 9-16)

1. Implement git-aware incremental indexing
2. SQLite storage layer with migrations
3. Query optimization

**Deliverable:** Persistent, fast (incremental <100ms/file)

### Phase 5-6: Multi-Language (Weeks 17-24)

1. TypeScript/JavaScript support
2. Go support

**Deliverable:** Python + TS + Go repos analyzable

### Phase 7: Production Readiness (Weeks 25-28)

1. Integration testing (real repos)
2. Performance optimization
3. Documentation
4. 350+ tests

**Deliverable:** Production-ready system

---

## Alternatives Explicitly Rejected

| Alternative | Why Not |
|-------------|---------|
| Integrate GitNexus | License violation for commercial use |
| Fork GitNexus | Too much maintenance burden |
| Use GitNexus as reference only (no integration) | Loses all benefits; might as well build custom |
| Wait for GitNexus commercial license | Unknown timeline, maintainer may decline, still external dependency |

---

## Success Criteria

By Week 28:
- ✅ Python, TypeScript, Go support
- ✅ Symbol extraction, import/call graphs, dependencies
- ✅ Incremental indexing (git-aware)
- ✅ SQLite storage
- ✅ 350+ tests, >90% coverage
- ✅ Production-ready, documented
- ✅ Integrated with ContextHub, ASES, Architecture Intelligence

---

## Architecture Boundaries

**Repository Intelligence owns:**
- Language parsing (tree-sitter, native parsers)
- Symbol extraction
- Graph construction (import, call, dependency)
- Repository structure analysis
- Incremental indexing
- Storage persistence

**Repository Intelligence does NOT own:**
- ContextHub (artifact storage, versioning, search)
- Architecture detection (pattern recognition)
- ASES workflows (orchestration)
- Retrieval ranking (Search subsystem)
- Engineering memory (fact store)

**Interface:** RepositoryAnalysisProvider (Ortho-owned, provider-agnostic)

---

## Future Flexibility

This design preserves future options:

**Tomorrow, we could:**
- Swap out custom implementation for alternative provider
- Integrate GitNexus if license changes
- Add specialized provider for specific language
- Use both providers (custom + GitNexus) simultaneously

**Mechanism:** RepositoryAnalysisProvider interface (pluggable)

**Cost of switching:** Days, not months (clean interface, no tight coupling)

---

## Related Decisions

- **ADR-005:** Language adapter plugin model (existing)
- **ADR-004:** SQLite local-first storage (existing, applies here too)
- **LEGAL-COMPATIBILITY-REPORT:** GitNexus licensing analysis
- **GITNEXUS-LEGAL-EXTRACTION-GUIDE:** What we CAN legally learn from GitNexus
- **CUSTOM-REPOSITORY-INTELLIGENCE-ARCHITECTURE:** Full system design
- **CUSTOM-REPOSITORY-INTELLIGENCE-ROADMAP:** Implementation plan

---

## Sign-Off

This decision is **ACCEPTED** by:
- Principal Systems Architect (decision maker)
- Engineering leadership (endorsing timeline)
- Team leads (commitment to 8-10 person-months)

**Start date:** Immediately (Week 1, 2026-07-08)

---

*Architecture Decision Record*  
*Ortho will build custom Repository Intelligence for full ownership and commercial viability*  
*Timeline: 28 weeks, production-ready by end of Phase 1-2 (Week 28)*
