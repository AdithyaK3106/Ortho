# Rollback Plan: Phase 4 Components 4–6

**Trigger Conditions:**
- Any component fails GATE 4 (test coverage review)
- Integration tests fail to pass
- Critical bugs found during verification

**Rollback Procedure:**

```bash
# 1. Remove all new files
rm -f packages/token-optimizer/src/token_optimizer/compressor.py
rm -f packages/token-optimizer/src/token_optimizer/arch_retrieval.py
rm -f packages/token-optimizer/src/token_optimizer/model_adapter.py
rm -f packages/token-optimizer/tests/test_compressor.py
rm -f packages/token-optimizer/tests/test_arch_retrieval.py
rm -f packages/token-optimizer/tests/test_model_adapter.py

# 2. Revert __init__.py (remove imports for components 4-6)
git checkout HEAD -- packages/token-optimizer/src/token_optimizer/__init__.py

# 3. Revert PHASE_4_BUILD_PLAN.md (remove ✅ markers for components 4-6)
git checkout HEAD -- PHASE_4_BUILD_PLAN.md

# 4. Reset git history to last good commit (after component 3)
# Find the commit: "docs: mark component 3 complete (graph expander)"
git log --oneline | grep "component 3"
# Then: git reset --hard <commit-hash>
```

**Verification Checklist:**

After rollback, verify:
- [ ] `ls packages/token-optimizer/src/token_optimizer/` — no compressor.py, arch_retrieval.py, model_adapter.py
- [ ] `ls packages/token-optimizer/tests/` — no test_compressor.py, test_arch_retrieval.py, test_model_adapter.py
- [ ] `python -c "from token_optimizer import compress_over_budget"` — ImportError (expected)
- [ ] `pytest packages/token-optimizer/tests/test_deduplicator.py -v` — all pass
- [ ] `pytest packages/token-optimizer/tests/test_reranker.py -v` — all pass
- [ ] `pytest packages/token-optimizer/tests/test_graph_expander.py -v` — all pass
- [ ] `git log --oneline | head -5` — shows commit "docs: mark component 3 complete"
- [ ] `cat PHASE_4_BUILD_PLAN.md | grep -c "✅ DONE"` — shows 3 (components 1-3 only)

**Rollback Completion Confirmation:**

When all verification steps pass:
1. Document reason in `.ases/tasks/phase-4-components-4-6/rollback-report.md`
2. Update CLAUDE.md task status: BLOCKED (with specific issue)
3. Create new task for re-attempt (if applicable)

**Time Estimate:** 10 minutes (automated)
**Data Loss Risk:** None (all changes in uncommitted branch or recent commits)
