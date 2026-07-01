# Architecture Decision: Ortho + GitNexus Integration

**Decision Date:** 2026-07-01  
**Decision Maker:** LEAD SYSTEM ARCHITECT  
**Status:** RECOMMENDATION (awaiting approval)

---

## Decision Statement

**Ortho should adopt GitNexus as an optional backend for Repository Intelligence (Pillar 1), not attempt to replace or fork it.**

Specifically:
1. **Create GitNexusAdapter** implementing Ortho's LanguageAdapter interface
2. **Make it optional** via configuration (default: Python, alternative: GitNexus)
3. **Keep Ortho's Python implementation as fallback** during transition
4. **Deprecate (not delete) Ortho's Python adapter** after GitNexus proven stable
5. **Preserve all Ortho-unique components** (ContextHub, architecture detection, ASES)

---

## Options Considered

### Option A: Fork & Modify GitNexus (REJECTED)

**Approach:** Clone GitNexus, customize for Ortho

**Pros:**
- Full control over codebase
- Can add Ortho-specific features directly

**Cons:**
- Maintenance burden (forked code must track upstream)
- License tracking complexity
- Duplicates work (reimplementing features GitNexus already has)
- Abandons external maintenance (GitNexus maintainers won't help)

**Verdict:** ❌ REJECTED — Too much maintenance burden for commoditized repo intelligence.

---

### Option B: Vendor GitNexus as Git Subtree (REJECTED)

**Approach:** `git subtree add` GitNexus into packages/

**Pros:**
- Unified codebase
- Can make local patches

**Cons:**
- Harder to take upstream updates
- Merging upstream changes is complex
- Confuses git history
- Still maintains local fork mentally

**Verdict:** ❌ REJECTED — Subtree pattern is outdated. Use dependencies instead.

---

### Option C: Direct Integration (REJECTED)

**Approach:** Replace Ortho's Python adapter by calling GitNexus directly throughout codebase

```python
# BAD: GitNexus logic scattered everywhere
from gitnexus import Repository
repo = Repository(path)
symbols = repo.get_symbols()  # Direct coupling
```

**Pros:**
- Immediate performance gains

**Cons:**
- Couples entire codebase to GitNexus
- Makes GitNexus impossible to replace later
- Breaks LanguageAdapter abstraction
- Creates tight coupling across pillars

**Verdict:** ❌ REJECTED — Violates separation of concerns.

---

### Option D: Create Adapter Layer (RECOMMENDED) ✅

**Approach:** Implement GitNexusAdapter matching LanguageAdapter interface

```python
# GOOD: Adapter pattern
class GitNexusAdapter(LanguageAdapter):
    def __init__(self, languages: list[str] = ["python"]):
        self.gitnexus = GitNexusRepository()
        self.languages = languages
    
    def extract_symbols(self, file: Path) -> list[Symbol]:
        # Translate GitNexus output to Ortho Symbol
        gn_symbols = self.gitnexus.get_symbols(file)
        return [self._translate(s) for s in gn_symbols]
    
    def extract_imports(self, file: Path) -> list[Import]:
        # Translate GitNexus imports to Ortho Import
        gn_imports = self.gitnexus.get_imports(file)
        return [self._translate(i) for i in gn_imports]
```

**Pros:**
- Keeps GitNexus isolated behind adapter interface
- Repository Intelligence remains pluggable/replaceable
- Easy to compare with PythonAdapter (A/B testing)
- Easy to rollback if issues arise
- Gradual migration possible (feature flag)
- Other pillars unaffected by swap

**Cons:**
- Adapter translation layer adds small overhead (~1-2ms per file)
- Requires maintaining adapter code

**Verdict:** ✅ APPROVED — Best long-term architecture.

---

### Option E: Extract GitNexus Features into Ortho (REJECTED)

**Approach:** Copy useful GitNexus code, integrate directly

**Pros:**
- Full control
- No external dependency

**Cons:**
- Duplicates maintenance work GitNexus team does
- License compliance (must track attribution)
- Can't take future GitNexus improvements
- Intellectual property issues (unless MIT/Apache licensed)

**Verdict:** ❌ REJECTED — Unnecessary code duplication.

---

### Option F: Reuse Ideas Only (REJECTED)

**Approach:** Keep using Ortho's Python adapter, but redesign it based on GitNexus architecture

**Pros:**
- No external dependency
- Full control

**Cons:**
- Slow (no speed benefit)
- Duplicates work
- Still missing multi-language support
- Rebuilds what GitNexus already has

**Verdict:** ❌ REJECTED — Why reinvent?

---

## Recommended Approach: Option D (Adapter Pattern)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Ortho v3 Platform                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐   ┌──────────────────────┐        │
│  │   ContextHub         │   │   Architecture       │        │
│  │   (artifact store)   │   │   Intelligence       │        │
│  │                      │   │   (detector)         │        │
│  └──────────────────────┘   └──────────────────────┘        │
│           ▲                          ▲                       │
│           └──────────────┬───────────┘                       │
│                          │                                   │
│                   ┌──────▼──────┐                            │
│                   │SymbolGraph  │                            │
│                   │ CallGraph    │                           │
│                   │ImportGraph   │                           │
│                   └──────▲──────┘                            │
│                          │                                   │
│                   ┌──────┴──────┐                            │
│                   │LanguageAdapter Interface                │
│                   │ (plugin boundary)                        │
│                   └──────┬──────┐                            │
│                          │      │                            │
│        ┌─────────────────┘      └──────────────────┐        │
│        │                                           │        │
│  ┌─────▼──────────┐                        ┌──────▼────┐   │
│  │ PythonAdapter  │                        │ GitNexus  │   │
│  │ (fallback)     │                        │Adapter    │   │
│  │ [DEPRECATED]   │◄─────────────┬────────►│(preferred)│   │
│  └────────────────┘              │         └───────────┘   │
│                                  │                          │
│                          ┌────────┴────────┐               │
│                          │ Config toggle   │               │
│                          │ (phase 2)       │               │
│                          └─────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
    ┌─────────┐          ┌──────────────────────┐
    │Ortho    │          │GitNexus (external)   │
    │Storage  │          │Python + TS + Go +... │
    │(SQLite) │          │(separate library)    │
    └─────────┘          └──────────────────────┘
```

### Key Architectural Principles

1. **LanguageAdapter is the boundary** — Everything beyond this interface is pluggable
2. **GitNexus is external** — Do not vendor it, use as a library dependency
3. **Data model translation** — Adapter handles GitNexus → Ortho Symbol/Import/Call translations
4. **Config-driven selection** — Users (or code) choose which adapter to use
5. **Fallback capability** — PythonAdapter remains runnable (in case of issues)
6. **No coupling beyond interface** — Rest of codebase talks to LanguageAdapter, not GitNexus

---

## Implementation Plan Summary

### Phase 1: Preparation (1 week, end of Phase 1 cleanup)

- [ ] Verify GitNexus license (MIT/Apache)
- [ ] Add GitNexus to pyproject.toml dependencies
- [ ] Document LanguageAdapter interface more thoroughly
- [ ] Create adapter base class tests

### Phase 2: Implementation (Weeks 9-16, Task 4-7)

**Task 4: GitNexusAdapter Implementation (2 weeks)**
- Implement GitNexusAdapter class
- Create data model translation layer
- Write adapter tests (verify output matches PythonAdapter)
- A/B test performance (baseline vs GitNexus)
- Keep PythonAdapter as fallback

**Task 5: Integration Testing (2 weeks)**
- ContextHub tests with GitNexus backend
- Architecture detection tests
- Incremental indexing tests
- End-to-end CLI → API → storage tests

**Task 6: Transition to Default (2 weeks)**
- Add config toggle (default: GitNexus, fallback: Python)
- Monitor performance in test
- Collect test results
- Run full test suite

**Task 7: Multi-language Support (2 weeks)**
- TypeScript adapter (add language="typescript" to config)
- Go adapter (add language="go" to config)
- Update docs and roadmap

### Phase 3+: Cleanup (1-2 months after Phase 2)

- Monitor GitNexus in production (1+ month)
- Archive PythonAdapter code to .ases/deprecated/ (once stable)
- Remove PythonAdapter from active code (not yet)
- Document decision in ADR

---

## Success Criteria

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **Adapter tests pass** | 100% | Test suite runs green |
| **Data compatibility** | 100% | GitNexus output → Ortho symbols matches 1:1 |
| **Performance** | ≥2x for Python | Benchmark: 100ms → ≤50ms per file |
| **ContextHub integration** | 100% | All ContextHub tests pass with GitNexus |
| **Architecture detection** | 100% | All arch-intelligence tests pass |
| **Multi-language** | Python + TS + Go | CLI supports --language flag |
| **Zero regressions** | 100% | All Phase 1 tests still pass |
| **Rollback readiness** | Full | Can switch back to PythonAdapter in 5 minutes |

---

## Risk Mitigation

### Risk 1: GitNexus API Breaking Changes

**Probability:** Low (stable library)  
**Impact:** High (adapter breaks)

**Mitigation:**
- Pin GitNexus version in pyproject.toml
- Monitor GitNexus releases
- Adapter pattern isolates change to one file
- Keep PythonAdapter as fallback

---

### Risk 2: Data Model Incompatibility

**Probability:** Low (compared schemas, very similar)  
**Impact:** High (silent data corruption)

**Mitigation:**
- Run comprehensive adapter tests
- Compare output for 100+ sample files
- A/B test with both adapters simultaneously
- Verify every field maps correctly

---

### Risk 3: Performance Regression

**Probability:** Very low (GitNexus is faster)  
**Impact:** Medium (CLI becomes slower)

**Mitigation:**
- Baseline performance before integration
- Measure adapter overhead (should be <5%)
- Profile end-to-end (CLI → API → storage)
- Keep PythonAdapter fallback if needed

---

### Risk 4: License Compatibility

**Probability:** Very low (GitNexus is likely MIT/Apache)  
**Impact:** High (legal issue)

**Mitigation:**
- Verify GitNexus license before committing
- Document in LICENSE file
- Review dependency tree for transitive licenses

---

### Risk 5: Maintenance Burden

**Probability:** Low (adapter is simple code)  
**Impact:** Medium (ongoing work)

**Mitigation:**
- Adapter is ~200 LOC (easy to maintain)
- Offload parsing to GitNexus team
- Monitor GitNexus releases quarterly

---

## Why NOT Fork/Vendor/Replace

### Why Not Fork GitNexus?

- **Maintenance:** Forking means maintaining a separate codebase
- **Upstream updates:** Can't easily take improvements from GitNexus
- **License tracking:** Must track attribution separately
- **Community:** Lose benefits of external team maintaining it

### Why Not Vendor as Subtree?

- **Update complexity:** git subtree is complex and error-prone
- **History pollution:** Subtrees add ~1000s of commits to history
- **Deprecation:** Subtree pattern is outdated (use dependencies instead)

### Why Not Replace Ortho with GitNexus?

- **Loss of unique features:** Ortho has ContextHub, architecture detection, ASES
- **Loss of engineering intelligence:** Ortho is not just repo scanning
- **Different design goals:** GitNexus is repo-centric, Ortho is engineering-centric

### Why Adapter Pattern?

- **Minimal coupling:** Only LanguageAdapter interface exposed
- **Easy to switch:** Can replace GitNexus backend tomorrow if needed
- **Easy to test:** Can A/B test both implementations
- **Easy to rollback:** PythonAdapter still available as fallback
- **Modular:** Rest of system unaware of which adapter is used

---

## Long-term Vision

By end of Phase 2:
- **Repository Intelligence is commoditized** (delegated to GitNexus)
- **Ortho focuses on higher-level features** (Architectural Intelligence, Context Assembly, Orchestration)
- **Multi-language support is unlocked** (Python + TypeScript + Go analyzed)
- **Architecture detection remains unique** (Ortho's differentiator)
- **Engineering orchestration is the focus** (ASES workflows, agent selection, evidence collection)

This frees Ortho's engineering team to focus on what matters:
- Architectural intelligence (unique to Ortho)
- Engineering orchestration (unique to Ortho)
- Token optimization (unique to Ortho)
- Planning and verification (unique to Ortho)

Rather than rebuilding:
- Python parsing (GitNexus does this)
- Import analysis (GitNexus does this)
- Call graph generation (GitNexus does this)
- Dependency parsing (GitNexus does this)

---

## Decision

### Approved Approach

**Option D: Adapter Pattern**

1. Create GitNexusAdapter implementing LanguageAdapter
2. Make it optional via configuration
3. Keep PythonAdapter as fallback
4. Integrate in Phase 2 (Tasks 4-7)
5. Transition to default after testing
6. Deprecate (not delete) PythonAdapter after 1+ months in production

### Rejected Approaches

- ❌ Option A: Fork GitNexus
- ❌ Option B: Vendor as subtree
- ❌ Option C: Direct integration
- ❌ Option E: Extract features
- ❌ Option F: Reuse ideas only

---

## Approval Checklist

- [ ] Lead Architect approves adapter pattern
- [ ] License verified (GitNexus is legal to use)
- [ ] FRD updated to reflect GitNexus dependency (not done yet)
- [ ] Phase 2 roadmap updated to include GitNexusAdapter tasks
- [ ] PythonAdapter kept as fallback (explicit decision)
- [ ] LanguageAdapter interface documented (for adapter implementers)

---

*Decision document prepared by LEAD SYSTEM ARCHITECT*  
*Recommendation: Proceed with Option D (Adapter Pattern)*  
*Next step: Start Phase 2 Task 4 (GitNexusAdapter Implementation)*
