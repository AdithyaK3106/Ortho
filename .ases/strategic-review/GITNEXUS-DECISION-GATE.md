# GitNexus Integration: Decision Gate

**Date:** 2026-07-01  
**Status:** AWAITING DECISION  
**Blocker:** Commercial licensing must be resolved first

---

## Current Situation

Ortho has completed Phase 1 Foundation (100%, 343+ tests). The next strategic question is:

> **Can GitNexus become Ortho's Repository Intelligence backend?**

We've completed legal and feasibility analysis. The answer depends on one critical factor:

**Commercial Licensing.**

---

## The Core Issue

**GitNexus License:** PolyForm Noncommercial 1.0.0

**Prohibition:** Cannot use commercially (SaaS, SDK distribution, or any commercial product)

**Your Options:**

### Option A: Seek Commercial License (2-4 weeks, unknown outcome)

**Action:**
1. Contact Abhigyan Patwari with commercial licensing inquiry
2. Request explicit written commercial license for:
   - SaaS (Ortho Cloud for paying customers)
   - SDK (embedding in Ortho SDK)
   - Commercial product distribution

**Outcome if approved:**
- Proceed with GitNexus integration (Phases 2-5 architectural design)
- Multi-language support faster
- Less engineering cost
- External dependency (maintenance, upgrades)

**Outcome if declined:**
- Must pursue Option B (build custom)
- No licensing concerns
- Full ownership and control

**Timeline:** 1 week for response, decision in hand by end of week

---

### Option B: Build Custom Repository Intelligence (6-12 weeks, 100% yours)

**Action:**
1. Study GitNexus's architecture
2. Design Ortho's equivalent system
3. Implement original code (inspired by but not copying GitNexus)
4. Deploy internal implementation

**Advantages:**
- ✅ 100% legally clear (no license issues)
- ✅ Full ownership (can ship commercially)
- ✅ Vendor independent (no external dependencies)
- ✅ Customizable for Ortho's needs
- ✅ Learning investment (team understands code deeply)

**Disadvantages:**
- ❌ Takes longer (6-12 weeks vs. 2-4 weeks integration)
- ❌ More engineering cost
- ❌ Single-language for Phase 1 (TypeScript in Phase 2)

**Timeline:** 4 months to feature parity with GitNexus

---

## What You CAN Legally Take from GitNexus (Either Way)

Even if commercial license fails, Ortho can legally:

✅ **Learn GitNexus's architectural patterns**
✅ **Implement the same algorithms** (Tarjan's SCC, topological sort, BFS, Louvain clustering)
✅ **Use the same data structures** (Symbol, ImportEdge, CallEdge)
✅ **Implement RFC standards** (RFC #909 for scope resolution, PEP 420, etc.)
✅ **Adopt the same design philosophy** (language providers, incremental indexing)

**Cannot:** Copy source code, distribute GitNexus, or use commercially without license

**Result:** Ortho can build an equivalent system that's 100% legally owned.

See: `GITNEXUS-LEGAL-EXTRACTION-GUIDE.md` for details.

---

## Recommendation

**Pursue both options in parallel:**

1. **Contact maintainer THIS WEEK** (Option A)
   - Sends licensing inquiry
   - 1-week response window
   - Decision made by end of week

2. **Start architectural design** (Option B preparatory work)
   - Study GitNexus architecture
   - Design Ortho's equivalent
   - Don't wait—get ahead
   - If commercial license comes through, you pivot. If not, you're ready to build.

**Parallel approach means:**
- Fastest outcome if commercial license approved
- No stalled work if commercial license denied
- Team learning GitNexus patterns regardless

---

## Decision Points

### This Week (Decision Gate 1)

**Required:** Contact Abhigyan Patwari

```
Subject: Commercial Licensing for GitNexus Integration

Hi Abhigyan,

We're building Ortho, an Engineering Intelligence Platform. GitNexus's
architecture is excellent and we'd like to evaluate integration.

Your PolyForm Noncommercial license is great for open-source projects.
Do you offer commercial licensing options for:
- SaaS (server-side backend for paying customers)
- SDK (embedding in commercial SDK)
- Commercial product distribution

If yes, what are the terms? If no, understood—we'll build our own.

Thanks,
[Your team]
```

**Target:** Response within 1 week

### End of Week (Decision Gate 2)

**Outcome A:** Commercial license available
- ✅ GO to Phase 2: Architectural Integration Design
- Design RepositoryAnalysisProvider interface
- Plan GitNexus adapter layer
- Plan multi-language rollout

**Outcome B:** Commercial license NOT available
- ✅ GO to Option B: Build Custom
- You have design ready from parallel work
- Proceed with implementation
- 6-12 week timeline

**Outcome C:** Maintainer unclear or negotiating
- ⏸️ CONTINUE parallel work
- Clarify terms
- Make decision once terms clear

---

## What Happens Next (Per Outcome)

### If Commercial License Approved

**Phase 2: Architectural Integration (2-4 weeks)**
1. Design RepositoryAnalysisProvider interface (permanent Ortho abstraction)
2. Design GitNexusProvider adapter
3. Plan feature flags and gradual rollout
4. Design fallback/rollback strategy

**Phase 3: Implementation (4-6 weeks)**
1. Implement GitNexusProvider adapter
2. Integration testing
3. Feature flag rollout (1% → 10% → 50% → 100%)
4. Multi-language support (TypeScript, Go, Java)

**Outcome:** Ortho with GitNexus backend + multi-language support + lower maintenance

---

### If Commercial License NOT Approved

**Phase 2: Design Custom Implementation (2-4 weeks)**
- Finalize architecture design (already started)
- Design Ortho's language adapter system
- Plan implementation roadmap

**Phase 3: Implementation (8-12 weeks)**
1. Python adapter (Weeks 1-4)
2. TypeScript adapter (Weeks 5-8)
3. Testing and optimization (Weeks 9-12)

**Outcome:** Ortho with custom backend + full ownership + vendor independence

---

## Risk Assessment

### Option A (Commercial License) Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| License denied | Medium | Medium | Option B ready in parallel |
| Licensing terms unaffordable | Low | Medium | Negotiate or use Option B |
| Future license changes | Low | Low | Version pinning, adapter pattern |
| Maintenance burden | Low | Low | GitNexus actively maintained |

---

### Option B (Build Custom) Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Takes longer | High | Low | Already working on it |
| Team learning curve | Medium | Low | GitNexus serves as reference |
| Feature gaps vs GitNexus | Low | Low | Can improve over time |
| Single-language initially | High | Low | TypeScript in Phase 2 |

---

## Files Available for Decision

| Document | Purpose |
|----------|---------|
| `LEGAL-COMPATIBILITY-REPORT.md` | Commercial licensing analysis |
| `GITNEXUS-LEGAL-EXTRACTION-GUIDE.md` | What you can legally take from GitNexus |
| `GITNEXUS-DECISION-GATE.md` | This decision framework |

---

## Next Action

**YOU DECIDE:**

**Option 1:** Send licensing inquiry and proceed with parallel architectural design
- Fastest path if commercial license available
- Safe fallback if not

**Option 2:** Pursue Option B immediately (build custom)
- More control, no licensing uncertainty
- Longer timeline but 100% owned

**Option 3:** Something else
- Different direction?

**Recommendation:** Option 1 (pursue both in parallel). Lowest risk, fastest good outcome.

---

*Decision gate prepared by PRINCIPAL SYSTEMS ARCHITECT*  
*All analysis complete. Awaiting your decision.*
