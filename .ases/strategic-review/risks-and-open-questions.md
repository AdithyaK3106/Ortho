# Risks & Open Questions

**Date:** 2026-07-01  
**Prepared for:** Ortho v3 GitNexus Integration Decision  
**Status:** Strategic-level risk assessment

---

## Top 10 Risks (Ranked by Impact × Probability)

### Risk 1: Data Model Incompatibility

**Severity:** HIGH  
**Probability:** LOW  
**Impact:** HIGH (silent data corruption)  
**Trigger:** GitNexus Symbol format doesn't match Ortho expectations

**Symptoms:**
- ContextHub search returns wrong results
- Architecture detection confidence scores wrong
- Symbols missing metadata (decorators, types)

**Mitigation:**
- [ ] Thoroughly compare data schemas before integration
- [ ] A/B test on 100+ diverse Python files
- [ ] Create field mapping table (GitNexus → Ortho)
- [ ] Run same searches with both adapters, compare results
- [ ] Unit tests that verify every field translates

**Contingency:**
- Keep PythonAdapter runnable (fallback to known-good)
- Document data mapping in ADR
- If incompatibility found: Fix adapter translation layer (quick fix)

---

### Risk 2: GitNexus Breaking Changes

**Severity:** MEDIUM  
**Probability:** LOW  
**Impact:** MEDIUM (adapter breaks, but isolated)

**Trigger:** GitNexus 2.0 releases incompatible API

**Symptoms:**
- GitNexusAdapter fails to instantiate
- GitNexus method signatures changed
- Return types different

**Mitigation:**
- [ ] Pin GitNexus version in pyproject.toml: `gitnexus>=1.5,<2.0`
- [ ] Monitor GitNexus releases quarterly
- [ ] Adapter pattern isolates change to one file
- [ ] Maintain version matrix (which GitNexus versions work)

**Contingency:**
- Update adapter to new GitNexus API (usually 2-4 hours)
- Keep old adapter version as fallback
- Test thoroughly before upgrading

---

### Risk 3: Performance Regression

**Severity:** MEDIUM  
**Probability:** VERY LOW  
**Impact:** MEDIUM (CLI becomes slower)

**Trigger:** Adapter translation overhead is higher than expected

**Symptoms:**
- Indexing slower than PythonAdapter
- Memory usage increases
- Timeouts on large repos (>10k files)

**Mitigation:**
- [ ] Measure adapter overhead before integration (target: <5%)
- [ ] Profile end-to-end (CLI → API → storage)
- [ ] Benchmark on large repos (10k, 50k, 100k files)
- [ ] Set performance SLA (must be 2x faster than Python adapter)

**Contingency:**
- Optimize adapter translation layer (cache results, batch operations)
- Reduce GitNexus calls (pre-filter files)
- Profile and fix bottlenecks
- Keep PythonAdapter fallback if optimization fails

---

### Risk 4: License Incompatibility

**Severity:** HIGH  
**Probability:** VERY LOW  
**Impact:** HIGH (legal issue)

**Trigger:** GitNexus is GPL, AGPL, or proprietary

**Symptoms:**
- Legal department rejects GitNexus
- Can't distribute Ortho (license violation)
- Patent issues

**Mitigation:**
- [ ] Verify GitNexus license before ANY code integration (Week 8)
- [ ] Check transitive dependencies for restrictive licenses
- [ ] Run FOSSA or Black Duck scan
- [ ] Get legal sign-off in writing
- [ ] Document license in Ortho LICENSE file

**Contingency:**
- If license is incompatible: don't integrate (keep using PythonAdapter)
- Consider forking GitNexus under compatible license (if code is good enough)
- Build own adapter from scratch (fallback, weeks 9-14)

---

### Risk 5: Integration Complexity (Time Overrun)

**Severity:** MEDIUM  
**Probability:** MEDIUM  
**Impact:** MEDIUM (Phase 2 delayed)

**Trigger:** GitNexusAdapter takes longer than 12 hours to implement

**Symptoms:**
- Task 4 slips past Week 10
- Too many incompatibilities to translate
- Testing takes longer than expected

**Mitigation:**
- [ ] Break GitNexusAdapter into small 2-hour chunks
- [ ] Daily standup during implementation (identify blockers early)
- [ ] Buffer: estimate 20 hours instead of 12 hours
- [ ] Have PythonAdapter code available (known backup)

**Contingency:**
- If slipping past Week 11: Decide to defer GitNexus to Phase 3 (stick with Python for now)
- Use extra time for Phase 3 orchestration work
- Re-plan Phase 2 to focus on architecture detection improvements

---

### Risk 6: Toolchain Incompatibilities

**Severity:** MEDIUM  
**Probability:** LOW  
**Impact:** LOW (easy fix)

**Trigger:** GitNexus requires incompatible Python version, dependencies, or OS

**Symptoms:**
- GitNexus requires Python 3.11+ (Ortho uses 3.9)
- GitNexus has C++ dependencies (hard to install on Windows)
- GitNexus needs system libraries (not in container)

**Mitigation:**
- [ ] Check Python version requirement (before Week 8)
- [ ] Check system dependencies
- [ ] Test on target OS (Windows, Linux, Mac)
- [ ] Test in Docker container (if using containerization)

**Contingency:**
- Upgrade Python version (1 hour, low risk)
- Install system dependencies (documented process)
- Use virtual environment (isolate GitNexus deps)

---

### Risk 7: GitNexus Maintenance Status

**Severity:** LOW  
**Probability:** LOW  
**Impact:** MEDIUM (orphaned code)

**Trigger:** GitNexus becomes unmaintained (no commits in 6+ months)

**Symptoms:**
- Bugs reported but not fixed
- Security vulnerabilities not patched
- Community moves to alternative

**Mitigation:**
- [ ] Check commit history (active in last 3 months?)
- [ ] Check issue response time (maintainers respond to issues?)
- [ ] Check community size (how many stars, forks, users?)
- [ ] Evaluate alternatives (if GitNexus looks dormant)

**Contingency:**
- Fork GitNexus and maintain ourselves (high effort)
- Switch to alternative library (tree-sitter, Sourcetrail, etc.)
- Keep PythonAdapter and accept maintenance burden

---

### Risk 8: Symbol Confidence Scores

**Severity:** LOW  
**Probability:** MEDIUM  
**Impact:** MEDIUM (architecture detection less accurate)

**Trigger:** GitNexus confidence scores are different from Ortho's expectations

**Symptoms:**
- Architecture detector reports lower confidence
- Some edge cases get confidence 0.5 instead of 0.8
- False positives in call graph

**Mitigation:**
- [ ] Define confidence scoring clearly
- [ ] Map GitNexus confidence (0-1) to Ortho scale
- [ ] Test on known ambiguous cases
- [ ] Document edge cases where confidence is low

**Contingency:**
- Adjust confidence thresholds in architecture detector
- Accept lower confidence as trade-off for 2x speed
- Document limitations in user guide

---

### Risk 9: Multi-Language Mismatches

**Severity:** MEDIUM  
**Probability:** MEDIUM  
**Impact:** MEDIUM (Phase 2 Week 15-16 slip)

**Trigger:** GitNexus TypeScript/Go support is immature or buggy

**Symptoms:**
- TypeScript parser misses some symbols
- Go dependency parsing incomplete
- Multi-language architecture detection fails

**Mitigation:**
- [ ] Test GitNexus on real TypeScript repos (Week 8)
- [ ] Test GitNexus on real Go repos (Week 8)
- [ ] Document language support matrix
- [ ] Plan fallback to single-language (Python-only) if needed

**Contingency:**
- Accept limited TS/Go support in Phase 2
- Improve language support in Phase 3
- Keep Python as primary (most repos start with Python)

---

### Risk 10: Vendor Lock-in

**Severity:** MEDIUM  
**Probability:** LOW  
**Impact:** MEDIUM (hard to switch away)

**Trigger:** Ortho becomes deeply dependent on GitNexus, hard to replace

**Symptoms:**
- All repo intelligence hardcoded to GitNexus
- Can't switch back to PythonAdapter
- No alternative exists
- GitNexus changes pricing model (if commercial)

**Mitigation:**
- [ ] Implement strict adapter pattern (MANDATORY)
- [ ] Keep PythonAdapter runnable throughout Phase 2
- [ ] Make GitNexus swappable (config option, not hardcoded)
- [ ] Document how to implement custom adapters
- [ ] Test adapter swapability (ensure fallback works)

**Contingency:**
- Switch back to PythonAdapter (takes 5 minutes, config change)
- Implement alternative adapter (if needed)
- Fork GitNexus (last resort, high effort)

---

## Medium-Risk Findings

| Risk | Severity | Probability | Mitigation | Contingency |
|------|----------|-------------|-----------|-------------|
| **Python version conflict** | MEDIUM | LOW | Check before Week 8 | Upgrade Python (1 hr) |
| **Large repo performance** | MEDIUM | MEDIUM | Benchmark on 100k file repos | Optimize caching, add pagination |
| **Type annotation parsing** | LOW | MEDIUM | Document what GitNexus can parse | Accept reduced type info |
| **TS/JS version support** | MEDIUM | MEDIUM | Test on modern JS (ES2020+) | Document supported versions |
| **Monorepo support** | MEDIUM | LOW | Test on real monorepos | Implement manual splitting |
| **Circular dependency loops** | LOW | LOW | Test on known problematic repos | Handle gracefully in incremental indexer |

---

## Open Questions

### Question 1: Is GitNexus License OK?

**Status:** UNANSWERED (must verify Week 8)

**Impact:** If license is incompatible, cannot use GitNexus

**Investigation needed:**
- [ ] Clone GitNexus, check LICENSE file
- [ ] Verify license is MIT, Apache 2.0, or similar
- [ ] Check transitive dependencies (pip list)
- [ ] Run license scan tool (FOSSA, Black Duck)
- [ ] Get legal sign-off

**Resolution:** Document license findings in `gitnexus-license-check.md`

---

### Question 2: What is GitNexus Python Version Support?

**Status:** UNANSWERED

**Impact:** If GitNexus requires Python 3.11+ and Ortho uses 3.9, need to upgrade

**Investigation needed:**
- [ ] Check GitNexus pyproject.toml or setup.py
- [ ] Run `pip install gitnexus` on Ortho's Python version
- [ ] If fails, determine what version is needed
- [ ] Estimate impact of Python upgrade

**Resolution:** Document in `gitnexus-api-reference.md`

---

### Question 3: Does GitNexus Handle Type Annotations?

**Status:** UNANSWERED (probable yes)

**Impact:** If not, Ortho's architecture detection might have lower accuracy

**Investigation needed:**
- [ ] Test GitNexus on typed Python code
- [ ] Check if return types are extracted
- [ ] Check if parameter types are parsed
- [ ] Compare to PythonAdapter output

**Resolution:** Document in data model mapping

---

### Question 4: How Does GitNexus Handle Circular Dependencies?

**Status:** UNANSWERED

**Impact:** Incremental indexer needs to handle these correctly

**Investigation needed:**
- [ ] Test GitNexus on Python code with circular imports
- [ ] Verify it detects cycles (not hangs)
- [ ] Compare confidence scores

**Resolution:** Create test case in adapter tests

---

### Question 5: Is GitNexus Repository Class Thread-Safe?

**Status:** UNANSWERED

**Impact:** If not, concurrent API requests could cause issues

**Investigation needed:**
- [ ] Read GitNexus documentation
- [ ] Test concurrent access (if possible)
- [ ] Determine if need per-request instance or shared instance

**Resolution:** Document in adapter implementation

---

### Question 6: What is GitNexus Call Graph Algorithm?

**Status:** UNANSWERED

**Impact:** May explain confidence score differences

**Investigation needed:**
- [ ] Read GitNexus documentation
- [ ] Understand algorithm (DFS, static analysis, etc.)
- [ ] Compare to Ortho's AST-based approach

**Resolution:** Document in `gitnexus-architecture-summary.md` (should already be done)

---

### Question 7: Can GitNexus Analyze Installed vs. Source Packages?

**Status:** UNANSWERED

**Impact:** If only source packages, dependency analysis incomplete

**Investigation needed:**
- [ ] Test on repo with external dependencies
- [ ] Check if GitNexus can analyze installed packages
- [ ] Document limitations

**Resolution:** Test during Phase 0

---

### Question 8: How Does GitNexus Handle Monorepos?

**Status:** UNANSWERED

**Impact:** Large projects may have monorepo structure

**Investigation needed:**
- [ ] Test GitNexus on real monorepo (e.g., TurboRepo)
- [ ] Check if auto-detects workspaces
- [ ] Document workspace handling

**Resolution:** Include in integration tests (Phase 2, Task 5)

---

### Question 9: What Languages Does GitNexus Actually Support?

**Status:** PARTIALLY ANSWERED (README says 6+, needs verification)

**Impact:** Determines Phase 2 multi-language scope

**Investigation needed:**
- [ ] List all languages in GitNexus
- [ ] Test each language (create test files, verify parsing)
- [ ] Note which are "beta" vs. "stable"
- [ ] Plan Phase 2 scope based on what's proven stable

**Resolution:** Create language support matrix in Phase 0

---

### Question 10: What Happens if GitNexus Parsing Fails?

**Status:** UNANSWERED

**Impact:** Error handling critical for production robustness

**Investigation needed:**
- [ ] Test GitNexus on files with syntax errors
- [ ] Check exception types and messages
- [ ] Determine if partial parse is possible
- [ ] Plan error recovery in adapter

**Resolution:** Include in adapter tests

---

## Decision Blockers

**All of these must be resolved BEFORE Phase 2 can start:**

1. ✅ Architecture decision approved (DONE — Option D: Adapter Pattern)
2. ⏳ License verified (PENDING — Week 8, Phase 0)
3. ⏳ API stability confirmed (PENDING — Week 8, Phase 0)
4. ⏳ Baseline performance measured (PENDING — Week 8, Phase 0)
5. ⏳ Team sign-off on revised roadmap (PENDING — approval needed)

---

## Mitigation Strategies (General)

### Strategy 1: Adapter Pattern Isolation
- Everything beyond LanguageAdapter interface is pluggable
- If GitNexus doesn't work out, can revert to PythonAdapter
- Cost of switching: 5 minutes (config change)

### Strategy 2: Gradual Integration
- Phase 0: Verify before committing
- Phase 1 (Task 4): Implement alongside PythonAdapter
- Phase 2 (Tasks 5-6): Test in parallel, no breaking changes
- Phase 3 (Week 29+): Remove only after 3+ months production use

### Strategy 3: Monitoring & Alerting
- Track performance metrics (indexing time, memory)
- Alert on regressions (>20% slower)
- Easy rollback if issues detected

### Strategy 4: Version Pinning
- Lock GitNexus version (no auto-upgrades)
- Test each upgrade thoroughly
- Document breaking changes in changelog

### Strategy 5: Fallback Capability
- PythonAdapter remains runnable
- Can switch via config (no code changes)
- Zero downtime fallback

---

## Sign-Off Checklist

Before proceeding to Phase 0, verify:

- [ ] Lead Architect approves this risk assessment
- [ ] Team Lead agrees with mitigation strategies
- [ ] Legal reviews license concerns
- [ ] QA lead reviews testing strategy
- [ ] DevOps confirms monitoring capability

---

## Review Schedule

This document should be reviewed:
- **Week 8 (Phase 0):** After investigating open questions, update findings
- **Week 10:** After GitNexusAdapter implementation, update risk status
- **Week 14:** After production transition, assess new risks
- **Week 29:** Before archiving PythonAdapter, final risk review

---

## Conclusion

**Overall risk level: LOW-MEDIUM**

The adapter pattern isolates GitNexus risk. Most failures are non-catastrophic (can fallback or fix). Legal and technical due diligence in Week 8 eliminates highest-probability risks.

**Proceed with Phase 0 (Preparation). Risks are manageable.**

---

*Risk assessment prepared by LEAD SYSTEM ARCHITECT*  
*Open questions to be resolved during Phase 0*  
*Next: Team review and approval before Week 8 starts*
