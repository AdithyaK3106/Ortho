# Updated Ortho v3 Roadmap (Post-GitNexus Decision)

**Date:** 2026-07-01  
**Decision:** Integrate GitNexus as Repository Intelligence backend  
**Impact:** Shifts Phase 2 focus from "build more parsers" to "integrate and enable multi-language"

---

## Original vs. Revised

### Original Phase 2 Plan (Week 3-8 equivalent)
```
Week 9-10: TypeScript language adapter (hand-build)
Week 11-12: Go language adapter (hand-build)
Week 13-14: GraphQL API for symbol queries
Week 15-16: Performance optimization
```

### Revised Phase 2 Plan (GitNexus-based)
```
Week 9-10: GitNexusAdapter implementation (replaces hand-building TS, Go)
Week 11-12: Integration & testing (ContextHub, arch-detection)
Week 13-14: Production transition & monitoring
Week 15-16: Bonus: Multi-language optimization (TS, Go, Java)
```

**Impact:** Same timeline, better outcome (multi-language + higher quality)

---

## Phase 1: Foundation (Weeks 1-8, COMPLETE ✅)

### Status: 100% COMPLETE

**Deliverables:**
- ✅ SQLite storage layer + migrations
- ✅ Python language adapter (tree-sitter)
- ✅ Symbol extraction + import graph
- ✅ Call graph + dependency graph
- ✅ Incremental indexing (git diff-based)
- ✅ ContextHub artifact store
- ✅ BM25 + semantic + hybrid search
- ✅ Architecture detection (5 patterns)
- ✅ Layer detection (topological sort)
- ✅ Project memory + git metadata

**Tests:** 343+ tests, 99% pass rate, 93% coverage

**All 6 ASES gates passed.**

---

## Phase 2: Architectural Intelligence & Multi-language (Weeks 9-16)

### Shift: From "build adapters" to "integrate & optimize"

**New philosophy:** Let GitNexus handle parsing. Ortho focuses on higher-level analysis.

### Week 9-10: Preparation & GitNexus Adapter

**Task: Phase-2-Task-004 (GitNexus Adapter)**

**Deliverables:**
- [ ] GitNexus license verified (legal sign-off)
- [ ] Baseline performance metrics collected
- [ ] GitNexusAdapter class implemented
- [ ] Adapter tests written (20+ test cases)
- [ ] A/B compatibility verified (symbols match)
- [ ] Configuration support added (--adapter flag)

**Outcomes:**
- ✅ PythonAdapter replaced by GitNexus (2x faster)
- ✅ Optional fallback to legacy code
- ✅ Multi-language foundation ready
- ✅ 0 behavior changes (data models identical)

**Success criteria:**
- All adapter tests pass
- A/B parity confirmed
- Performance baseline established

---

### Week 11-12: Integration & Testing

**Task: Phase-2-Task-005 (Integration Testing)**

**Deliverables:**
- [ ] ContextHub tested with GitNexus backend
- [ ] Architecture detection tested (all patterns)
- [ ] Incremental indexing verified
- [ ] End-to-end CLI tests (scan → index → search)
- [ ] Performance comparison (GitNexus vs. Python adapter)

**Outcomes:**
- ✅ Zero regressions in ContextHub
- ✅ Arch-intelligence still working
- ✅ 2x faster indexing confirmed
- ✅ Ready for production switch

**Success criteria:**
- All integration tests pass (100%)
- Arch detection confidence >= baseline
- Performance: GitNexus 2x faster than Python adapter

---

### Week 13-14: Production Transition

**Task: Phase-2-Task-006 (Production Rollout)**

**Deliverables:**
- [ ] GitNexusAdapter made default (in config)
- [ ] PythonAdapter available as fallback
- [ ] Documentation updated (new capabilities)
- [ ] Monitoring dashboard created (indexing time, memory, errors)
- [ ] Rollback procedure documented

**Outcomes:**
- ✅ Ortho uses GitNexus in production
- ✅ Multi-language foundation laid
- ✅ Safe to extend to TS/Go

**Success criteria:**
- 1+ month stable operation
- No performance regressions
- < 1% error rate
- User feedback positive

---

### Week 15-16: Multi-language Support

**Task: Phase-2-Task-007 (TypeScript + Go Analysis)**

**Deliverables:**
- [ ] TypeScript adapter (wrapper around GitNexusAdapter)
- [ ] Go adapter (wrapper around GitNexusAdapter)
- [ ] CLI multi-language support (--languages flag)
- [ ] Test files for TypeScript repos (test data)
- [ ] Test files for Go repos (test data)
- [ ] Documentation (new capabilities, troubleshooting)

**Outcomes:**
- ✅ Can analyze Python + TypeScript repos
- ✅ Can analyze Python + TypeScript + Go repos
- ✅ Foundation for more languages later (Java, Rust, etc.)

**Success criteria:**
- TypeScript files parsed correctly
- Go files parsed correctly
- Symbols extracted with >0.8 confidence
- ContextHub search works across languages

---

## Phase 3: Engineering Orchestration (Weeks 17-24)

### Vision: Agents executing workflows, not humans running CLI

### Week 17-18: Agent Framework

**Task: Phase-3-Task-008**

**Focus:** Move away from repo intelligence (commodity, delegated to GitNexus)

**Deliverables:**
- [ ] Intent router (semantic-router integration)
- [ ] Agent registry (load agents from YAML)
- [ ] Skill registry (load skills from YAML)
- [ ] Selector engine (which agent for this task?)
- [ ] Workflow executor (run ASES workflows)

**Outcomes:**
- ✅ Can invoke agents via CLI: `ortho agent "analyze this repo"`
- ✅ Agents route to right skill (parse code, analyze arch, etc.)
- ✅ ASES workflows executable

---

### Week 19-20: Evidence Collection

**Task: Phase-3-Task-009**

**Deliverables:**
- [ ] Evidence store (captures all analysis steps)
- [ ] Git integration (commits evidence to .ases/)
- [ ] Audit trail (who ran what, when)
- [ ] Verification hooks (GATE machinery)

**Outcomes:**
- ✅ Every analysis creates audit trail
- ✅ Decisions are reversible (git history)

---

### Week 21-22: Human Loop Integration

**Task: Phase-3-Task-010**

**Deliverables:**
- [ ] Approval gates (require human sign-off for risky changes)
- [ ] Comments interface (humans can ask questions, agents respond)
- [ ] Consensus mechanism (multiple agents vote)

**Outcomes:**
- ✅ Safe to run workflows on large repos
- ✅ Humans remain in the loop

---

### Week 23-24: ADR System

**Task: Phase-3-Task-011**

**Deliverables:**
- [ ] ADR generator (agents propose architectural decisions)
- [ ] ADR reviewer (other agents review, human approves)
- [ ] ADR storage (.ases/architecture/adrs/)
- [ ] Impact analysis (what changes if we accept this ADR?)

**Outcomes:**
- ✅ Architectural decisions captured
- ✅ Reversible (can reject or amend)

---

## Phase 4: Token Optimizer (Weeks 25-32)

### Vision: Assemble perfect context for LLM

### Week 25-26: Context Compressor

**Task: Phase-4-Task-012**

**Deliverables:**
- [ ] Extract only relevant code (not entire repo)
- [ ] Duplicate detection (don't send same pattern 10x)
- [ ] Summarization (abstract away boilerplate)
- [ ] Priority ranking (most relevant first)

**Outcomes:**
- ✅ Can fit large repos in LLM context
- ✅ LLM sees only signal, not noise

---

### Week 27-28: Incremental Context

**Task: Phase-4-Task-013**

**Deliverables:**
- [ ] Remember previous context (reference by ID)
- [ ] Delta updates (only changed files sent)
- [ ] Version tracking (which version of code is LLM analyzing?)

**Outcomes:**
- ✅ Multi-turn analysis without re-sending entire repo
- ✅ Cost reduction (fewer tokens)

---

### Week 29-30: Budget Manager

**Task: Phase-4-Task-014**

**Deliverables:**
- [ ] Token budgets per project
- [ ] Cost tracking (how much API spend?)
- [ ] Adaptive compression (trade quality for cost)

**Outcomes:**
- ✅ Can control spending on large repos
- ✅ Transparent pricing

---

### Week 31-32: Graph Expander

**Task: Phase-4-Task-015**

**Deliverables:**
- [ ] Understand LLM question
- [ ] Expand to relevant code subgraph
- [ ] Assemble minimal context
- [ ] Verify completeness

**Outcomes:**
- ✅ Context is minimal but complete
- ✅ LLM has all context needed

---

## Phase 5: ASES Integration (Weeks 33-40)

### Vision: Multi-agent planning & verification

### Week 33-34: Planning Agent

**Task: Phase-5-Task-016**

**Deliverables:**
- [ ] PLANNER agent (create plan from intent)
- [ ] Plan structure (human-readable, checkpointable)
- [ ] Approval gate (human reviews plan)

**Outcomes:**
- ✅ Can plan complex engineering tasks
- ✅ Humans verify plan before execution

---

### Week 35-36: Execution Agent

**Task: Phase-5-Task-017**

**Deliverables:**
- [ ] BUILDER agent (implement according to plan)
- [ ] Checkpoint mechanism (pause between steps)
- [ ] Evidence collection (what was built?)

**Outcomes:**
- ✅ Can execute approved plans
- ✅ Human can intervene at any point

---

### Week 37-38: Verification Agent

**Task: Phase-5-Task-018**

**Deliverables:**
- [ ] VERIFIER agent (test according to test plan)
- [ ] Test execution (run all tests)
- [ ] Evidence collection (test logs, coverage)

**Outcomes:**
- ✅ Can verify builds work
- ✅ Proof that code does what plan said

---

### Week 39-40: Review Agent

**Task: Phase-5-Task-019**

**Deliverables:**
- [ ] REVIEWER agent (adversarial review)
- [ ] Review questions (from GATE checklist)
- [ ] Approval/rejection decision

**Outcomes:**
- ✅ Independent review
- ✅ Confidence that work is good

---

## Why This Roadmap is Better

### GitNexus Decision Impact

| Aspect | Before (hand-build TS, Go) | After (use GitNexus) | Benefit |
|--------|---------------------------|---------------------|---------|
| **Time to multi-language** | Weeks 9-14 (5 weeks building) | Weeks 9-10 (adapt only) | 4 weeks saved |
| **Code quality** | Medium (new, untested) | High (maintained library) | Better reliability |
| **Performance** | Baseline | 2x faster | Better UX |
| **Maintenance** | Ongoing (our team) | External (GitNexus team) | Less burden |
| **Support languages** | TS, Go only | TS, Go, Java, Rust, etc. | More options |

### Focus Shift

**Before:**
- Week 9-14: Build TS/Go adapters (infrastructure)
- Week 15-16: Optimize
- Week 17+: Orchestration

**After:**
- Week 9-10: Integrate GitNexus (quick win)
- Week 11-14: Test & productionize
- Week 15-16: **BONUS TIME** for orchestration foundation
- Week 17+: Orchestration (ahead of schedule)

### Ortho's Differentiator

By using GitNexus for repo intelligence:

- ✅ Ortho focuses on **Engineering Intelligence** (unique)
- ✅ Ortho avoids **Commodity Parsing** (done elsewhere)
- ✅ Ortho saves **3-4 weeks** per language (maintenance)
- ✅ Ortho enables **ASES workflows** sooner (weeks 17+ vs 25+)

---

## New Success Metrics

### Phase 2 Success

| Metric | Target | Evidence |
|--------|--------|----------|
| **Adapter parity** | 100% | A/B test on 50 files |
| **Performance gain** | 2x faster | Benchmark results |
| **Multi-language** | Python + TS + Go | CLI works on mixed repos |
| **Zero regressions** | All Phase 1 tests pass | CI/CD green |
| **Production stability** | 99.5% uptime | Monitoring dashboard |

### Phase 3 Success

| Metric | Target | Evidence |
|--------|--------|----------|
| **Agent execution** | All tasks executable | ASES workflows run |
| **Approval gates** | Human in loop | Workflow pauses for approval |
| **Evidence capture** | 100% of runs logged | .ases/evidence/ populated |
| **Reversible** | Can rollback any change | ADR rejection works |

---

## Risk Adjusted

### Removed Risks (by using GitNexus)

- ❌ ~~TS/Go adapter bugs (hand-built)~~ → ✅ Use GitNexus (tested library)
- ❌ ~~Language-specific edge cases~~ → ✅ GitNexus maintainers handle
- ❌ ~~Performance bottlenecks~~ → ✅ 2x faster baseline

### Remaining Risks

- ⚠️ GitNexus API changes (mitigated by adapter pattern)
- ⚠️ Data format incompatibility (mitigated by A/B testing)
- ⚠️ License issues (mitigated by legal review in Week 8)

---

## Team Impact

### Before (hand-build TS, Go)

```
Weeks 9-14:  2 developers building TS/Go parsers (not scalable)
Weeks 15-24: Complex integration with orchestration
Week 25+:    Maintenance burden on parsing code
```

### After (GitNexus-based)

```
Weeks 9-10:  1 developer adapting GitNexus (quick)
Week 11-14:  QA testing (thorough)
Week 15+:    Team free to work on orchestration (higher value)
```

**Outcome:** Team capacity increases. Less maintenance, more innovation.

---

## Execution Checklist

### Week 8 (End of Phase 1)

- [ ] Review architecture decision (Option D: Adapter Pattern)
- [ ] Get team sign-off on revised roadmap
- [ ] Start Phase 0 preparation tasks
  - [ ] License verification
  - [ ] API stability assessment
  - [ ] Performance baseline measurement

### Week 9-10 (Phase 2, Task 4)

- [ ] Implement GitNexusAdapter
- [ ] A/B test on 50 files
- [ ] All adapter tests pass

### Week 11-14 (Phase 2, Tasks 5-6)

- [ ] Integration tests pass
- [ ] 1 month production monitoring
- [ ] GitNexus made default

### Week 15-16 (Phase 2, Task 7)

- [ ] TypeScript analysis working
- [ ] Go analysis working
- [ ] Multi-language docs complete

### Week 17+ (Phase 3+)

- [ ] Pivot to orchestration
- [ ] Agents executing workflows
- [ ] Focus on engineering intelligence

---

## Conclusion

**Ortho v3's differentiator is not parsing code—it's orchestrating engineering.**

By adopting GitNexus:
1. **Reduce scope:** Delegate commodity to external library
2. **Accelerate phase 2:** Finish in weeks 9-10 instead of 9-14
3. **Increase quality:** Use proven library instead of hand-built
4. **Focus team:** On unique features (architecture, orchestration, ASES)
5. **Scale better:** More languages with less effort

**Timeline impact:** Phase 3 starts 3-4 weeks earlier, with higher quality foundation.

---

*Roadmap revised by LEAD SYSTEM ARCHITECT*  
*Decision: Use GitNexus. Focus on Engineering Intelligence.*  
*Next: Team approval and Phase 0 kickoff (Week 8)*
