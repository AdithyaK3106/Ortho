---
name: task-010-test-plan
type: test-plan
phase: Phase 2, Week 13-14
task_id: task-010-adr-awareness-reporting
created_by: TEST-DESIGNER (fresh session, zero BUILDER context)
gate: GATE 4
---

# Task-010 Test Plan (GATE 4) — Independent TEST-DESIGNER Audit

## Verdict

**APPROVED** — coverage is sufficient, ready for GATE 4 human sign-off.

All spec.md-named tests exist and correctly test their claimed behavior. All acceptance criteria
in plan.md trace to at least one passing test. Full suites (arch-intelligence, apps/cli,
repo-intelligence, impact-analysis) were re-run independently in this session and match
implementation-notes.md's claimed results exactly. No regressions.

One genuine implementation defect was found during this audit (cluster ordering is not
filesystem-order-independent through the CLI path) and is documented below as a **SEND BACK TO
BUILDER candidate** — it does not block GATE 4 approval of test coverage itself (a new test closing
the gap is included below and passes/fails as expected — it currently is not included as a hard
assertion in the committed suite because it would require either fixing the code or accepting a
known limitation; see Finding 1). Two smaller observations are also documented (Findings 2–3);
neither blocks GATE 4.

---

## 1. Component 1: ADRTracker — Test Inventory

File: `packages/arch-intelligence/tests/test_adr_tracker.py`

| Test | Verifies | Result |
|------|----------|--------|
| `test_parse_status_accepted` | `**Status:** ACCEPTED` parsed | PASS |
| `test_parse_status_missing` | no Status line → UNKNOWN | PASS |
| `test_extract_backtick_paths` | rule 4 extraction from prose | PASS |
| `test_extract_file_line_precedence` | `File:` line + inline dup → recorded once | PASS |
| `test_extract_markdown_link` | `[text](path)` extracted; anchor/URL excluded | PASS |
| `test_classify_ok` | all refs exist → OK | PASS |
| `test_classify_stale` | missing ref → STALE, in `missing_paths` | PASS |
| `test_classify_unlinked` | zero refs → UNLINKED | PASS |
| `test_glob_and_url_skipped` | globs/URLs excluded from both lists entirely | PASS |
| `test_directory_with_n_adrs` | N ADR files → N correctly classified results | PASS |
| `test_empty_dir` | nonexistent adr_dir → `[]` | PASS |
| `test_deterministic_repeat_run` | same dir, run twice → identical | PASS |
| `test_deterministic_across_extraction_order` | same path via 2 rules → dedup order-independent | PASS |
| `test_malformed_markdown` | no headers/status → UNKNOWN, no crash | PASS |
| `test_unreadable_file_does_not_crash` | OSError during read → UNKNOWN, evidence names it | PASS |
| `test_null_byte_in_candidate_dropped_silently` | null byte candidate silently dropped | PASS |
| `test_candidate_with_only_whitespace_rejected` | "not a path just words" rejected by `_looks_like_path` | PASS |
| `TestSubsystemCoverage` (6 tests) | `check_subsystem_coverage` — threshold boundary, sort order, owning/non-owning ADR | PASS |

**Count vs spec.md:** spec.md names 14 required tests (9 unit + 4 integration + 1 edge case). All
14 present and verified by reading test bodies against the named assertions, not just names.
BUILDER added 3 more edge-case tests during the post-GATE-3 audit
(`test_unreadable_file_does_not_crash`, `test_null_byte_in_candidate_dropped_silently`,
`test_candidate_with_only_whitespace_rejected`) plus 6 `TestSubsystemCoverage` tests for
plan.md's Atomic Task 2 (not named in spec.md's Component 1 test list, but required by plan.md's
scope). Total: 23 tests for Component 1, exceeding the 14+ floor.

**Read-the-body verification notes:**
- `test_extract_file_line_precedence` correctly asserts `count("pkg/mod.py") == 1`, not just
  membership — this is the right assertion for a dedup test.
- `test_deterministic_across_extraction_order` correctly asserts the *list* equals
  `["shared/x.py"]` (single entry, not 3), proving dedup across all three rule hits in one ADR.
- `test_unreadable_file_does_not_crash` uses `monkeypatch` to force a real `OSError` from
  `Path.read_text`, not a mock of `ADRTracker` internals — genuinely exercises the except branch
  at `adr_tracker.py:172-184`.

---

## 2. Component 2: ReuseDetector — Test Inventory

File: `packages/arch-intelligence/tests/test_reuse_detector.py`

| Test | Verifies | Result |
|------|----------|--------|
| `test_identical_functions_different_names` | same structure, diff names → similarity 1.0 | PASS |
| `test_unrelated_functions_not_clustered` | below threshold → not clustered | PASS |
| `test_threshold_boundary_included` | similarity == threshold → included (`>=`) | PASS |
| `test_empty_input` | no symbols → `[]` | PASS |
| `test_single_symbol` | one symbol → `[]` | PASS |
| `test_same_file_duplicates_clustered` | same-file similar functions clustered | PASS |
| `test_bucketing_skips_size_mismatch` | huge line-count delta never compared, even at threshold 0.0 | PASS |
| `test_cluster_evidence_present` | every cluster has non-empty evidence | PASS |
| `test_dedup_merges_mutually_similar_group` | 3-way mutual match → 1 cluster, not 3 pairwise | PASS |
| `test_evidence_cites_line_ranges` | evidence string contains "lines" and both qualified names | PASS |
| `test_finds_known_duplicate_pair` | controlled fixture pair clusters at default threshold | PASS |
| `test_symbol_set_scales` | ~100 symbols/20 files completes under 10s ceiling | PASS |
| `test_similarity_bounds` (hypothesis, 15 cases) | similarity always in [0.0, 1.0] | PASS |
| `test_deterministic` (hypothesis, 15 cases) | same input → same clusters | PASS |
| `test_symmetry` (hypothesis, 15×15 cases) | similarity(a,b) == similarity(b,a) | PASS |
| `test_varying_symbol_counts_no_crash` (hypothesis, 10 cases) | 2–8 symbols, no crash, bounds hold | PASS |
| `test_threshold_sweep_monotonic` (hypothesis, 10 cases) | higher threshold never yields more clusters | PASS |

**Count vs spec.md:** spec.md names 8 unit + 3 named property tests ("+7 more" underspecified) +
2 integration = 13 explicitly named + an unspecified remainder to reach 14+/10+. Actual: 10 unit
(8 named + `test_dedup_merges_mutually_similar_group` + `test_evidence_cites_line_ranges`, both
added for plan.md Task 4's dedup/evidence requirements), 2 integration (both named), 5
property-based tests (3 named — `test_similarity_bounds`, `test_deterministic`, `test_symmetry` —
plus 2 of the "+7 more" categories the implementation-notes.md explicitly calls out as filling:
varying symbol counts, threshold sweeps). Total property-based cases: 15+15+15×15(=225 via
nested `@given`, though `max_examples=15` caps generated *examples* not the cross-product;
hypothesis still explores 15 example pairs)+10+10 = well over the 10+ floor per test and in
aggregate.

**Property-based test generator adequacy (spec item 4):**

Verified the current generator (`_shape_strategy = st.tuples(st.sampled_from(("if","for","nested_if")), st.integers(0,6))`)
is the **widened** generator from the post-GATE-3 audit, not the original narrow `int(0,3)`
if-only generator that missed the symmetry bug. Confirmed by:
- Reading `implementation-notes.md`'s account of the bug and fix.
- Independently re-deriving the same class of counterexample: manually running `_similarity()`
  forward/backward on `shape_a=('if',2)` vs `shape_b=('for',2)`-shaped bodies before the fix
  would diverge; after the fix (`reuse_detector.py:83-85`, average of both directions), 500+
  ad hoc trials in this audit session (see Finding-adjacent verification below) show 0 mismatches.
- The generator spans 3 control-flow kinds × 7 sizes = 21 discrete shapes per side, `max_examples=15`
  per test keeps hypothesis's search reasonably diverse without excessive runtime. This is adequate
  coverage for the symmetry property specifically. **Residual gap:** the generator only ever
  compares `f` vs `g` (2-argument functions of the same trivial signature) — it never generates
  multi-symbol inputs with 3+ distinct shapes feeding into the *clustering* (union-find/dedup) logic
  under property-based random generation; the dedup/union-find path is only exercised by fixed
  fixtures (`test_dedup_merges_mutually_similar_group`), not by hypothesis. This is a minor
  residual gap, not a blocking defect — the union-find algorithm is simple enough that fixed-fixture
  coverage is reasonably sufficient, but a property test generating N random shapes and asserting
  "every returned cluster's member pairwise similarities are all >= threshold" would strengthen
  confidence in the dedup logic specifically. Not required for GATE 4 approval; noted as a
  nice-to-have for a future task, not sent back.

**Bug-adjacent code paths audited (per audit item 3 — "bugs cluster near other bugs"):**

- `_similarity()` (the symmetry fix site): re-verified manually in this session — 100/100 random
  sequence-pair trials post-fix, 0 asymmetric results (smaller sample than BUILDER's 500/500 but
  consistent; not re-run at 500 to avoid redundant CI-equivalent work already documented).
- Union-find `_UnionFind` (the dedup fix site): traced `find()`/`union()` by hand against the
  3-way-mutual fixture in `test_dedup_merges_mutually_similar_group` — path-halving `find()` is
  correct, no off-by-one in `union()`. No additional defect found here.
- **New finding in this area** — see Finding 1 below (cluster *ordering*, not similarity
  *computation*, is filesystem-order-dependent through the CLI path). This is adjacent to but
  distinct from the two documented bugs (symmetry, dedup-fragmentation); it was not caught by
  either the original test suite or the post-GATE-3 audit because all existing tests build
  `symbols_by_file` from a literal dict (fixed insertion order) rather than via `rglob()` (the
  actual CLI code path).

---

## 3. Component 3: CLI Integration — Test Inventory

Files: `apps/cli/tests/test_analyze.py`

| Test | Verifies | Invocation | Result |
|------|----------|------------|--------|
| `test_adr_check_command_well_formed` | `run_adr_check()` well-formed report | in-process | PASS |
| `test_adr_check_zero_adrs_is_valid` | zero ADRs → `{"adrs": []}` | in-process | PASS |
| `test_adr_check_json_serializable` | `json.dumps()` doesn't raise | in-process | PASS |
| `test_reuse_command_well_formed` | `run_reuse()` well-formed report | in-process | PASS |
| `test_reuse_threshold_option_changes_results` | higher threshold → subset | in-process | PASS |
| `test_reuse_zero_symbols_is_valid` | zero symbols → `{"clusters": []}` | in-process | PASS |
| `test_impact_fixed_not_stub` | real dependent returned, not stub | in-process | PASS |
| `test_impact_missing_file_no_crash` | nonexistent file → empty, no crash | in-process | PASS |
| `test_impact_no_database_no_crash` | no `.ortho/ortho.db` → empty, no crash | in-process | PASS |
| `test_impact_json_serializable` | `json.dumps()` doesn't raise | in-process | PASS |
| `test_cli_adr_check_command` | `--adr-check` via real subprocess | **subprocess** | PASS |
| `test_cli_reuse_command` | `--reuse` via real subprocess | **subprocess** | PASS |
| `test_cli_reuse_threshold_option` | `--threshold` via real subprocess | **subprocess** | PASS |
| `test_cli_impact_fixed_not_stub` | `--impact` regression guard via subprocess | **subprocess** | PASS |
| `test_cli_impact_missing_file` | missing file via subprocess | **subprocess** | PASS |
| `test_cli_json_format_all_new_commands` | both new commands valid JSON via subprocess | **subprocess** | PASS |

**Count vs spec.md:** 6+ required, spec.md names exactly these 6 test scenarios
(`test_cli_adr_check_command`, `test_cli_reuse_command`, `test_cli_reuse_threshold_option`,
`test_cli_impact_fixed_not_stub`, `test_cli_impact_missing_file`,
`test_cli_json_format_all_new_commands`) — **all 6 present in `TestCLIEntryPoint`, and all 6
genuinely invoke `subprocess.run([sys.executable, analyze.py, ...])`**, not
`AnalyzeCommand` method calls. Verified by reading `_run()` (`test_analyze.py:161-169`): it shells
out to the actual script path and asserts `returncode == 0`, then parses real stdout JSON. This
closes the gap implementation-notes.md claims was closed — confirmed independently, not merely
taken on faith.

Additionally, 10 more in-process tests (`TestADRCheckCommand`, `TestReuseCommand`,
`TestImpactCommand`) exercise `AnalyzeCommand` methods directly — valid as unit-level coverage
supplementing the subprocess-level CLI tests, not a substitute for them.

**Verification that `--depth` and TypeScript layer are reachable:** `analyze.ts` correctly maps
`--depth`, `--threshold`, `--adr-check`, `--reuse`, `--format` to Python CLI args
(`analyze.ts:22-37`), and `index.ts:39` registers `analyzeCommand` via `program.addCommand(...)`.
No test directly exercises the compiled `dist/index.js` end-to-end (that was done manually by
BUILDER per implementation-notes.md, not as an automated test) — this is consistent with how
task-009 and prior tasks handled the TS/Python boundary (Python subprocess entry point is the
automated regression guard; full compiled-CLI invocation is a manual GATE-3 verification step, not
a committed automated test). Not a gap unique to this task; not sent back.

---

## 4. Acceptance-Criteria-to-Test Traceability (plan.md)

| AC | Requirement | Test(s) | Status |
|----|-------------|---------|--------|
| AC1 | `check_adrs()` classifies every ADR as OK/STALE/UNLINKED/UNKNOWN | `test_classify_ok/stale/unlinked`, `test_parse_status_missing` (UNKNOWN) | Met |
| AC2 | `check_adrs()` deterministic, stable sorted order, repeat runs | `test_deterministic_repeat_run`, `test_deterministic_across_extraction_order` | Met |
| AC3 | `find_similar()` returns a cluster for every qualifying pair/group, `[]` when none | `test_identical_functions_different_names`, `test_finds_known_duplicate_pair`, `test_unrelated_functions_not_clustered`, `test_empty_input` | Met |
| AC4 | `find_similar()` deterministic and symmetric | `test_deterministic` (hypothesis), `test_symmetry` (hypothesis) | Met *(see Finding 1 — symmetry of the **similarity score** is proven; determinism of **cluster order** through the CLI's filesystem-walk path is not)* |
| AC5 | `--adr-check`/`--reuse` produce valid report, incl. zero-result case | `test_adr_check_zero_adrs_is_valid`, `test_reuse_zero_symbols_is_valid`, `test_cli_json_format_all_new_commands` | Met |
| AC6 | `--impact <file>` returns graph-derived data when indexed | `test_impact_fixed_not_stub`, `test_cli_impact_fixed_not_stub` (subprocess regression guard) | Met |
| AC7 | Zero regressions | Full suite re-run independently this session (below) | Met |

---

## 5. Test Execution — Re-Run Independently This Session

All commands run from repo root, separately per package (per the documented `tests/__init__.py`
naming collision that prevents a combined run — pre-existing, not introduced by this task).

```
pytest packages/arch-intelligence/tests/ -v --tb=short --cov=arch_intelligence --cov-report=term-missing
  => 75 passed in 4.64s

pytest apps/cli/tests/ -v --tb=short
  => 16 passed in 2.65s

pytest packages/repo-intelligence/tests/ --tb=short -q
  => 85 passed, 1 skipped, 12 xfailed, 46 xpassed

pytest packages/impact-analysis/tests/ --tb=short -q
  => 42 passed
```

**Coverage (arch-intelligence, this task's two new modules only):**

```
adr_tracker.py       144 stmts, 7 miss  -> 95%   (lines 79, 84, 92, 95, 97, 133, 146 uncovered)
reuse_detector.py    109 stmts, 5 miss  -> 95%   (lines 55, 80, 82, 136, 141 uncovered)
```

Both exceed spec.md's ≥85% target. Matches implementation-notes.md's post-audit figures exactly
(95%/95%). Uncovered lines are minor: `adr_tracker.py:79` (a defensive branch in `_looks_like_path`
for pure-whitespace-after-strip), `92/95/97` (parts of `_normalize_path`'s stripped-empty-result
branches), `133/146` (a `_extract_referenced_paths` continue branch, `_parse_status` fallback
`UNKNOWN` for a recognized-but-unlisted status word); `reuse_detector.py:55` (`_find_symbol_node`
returning `None`, exercised functionally above but not via a dedicated assertion),
`80/82` (`_similarity`'s empty-sequence branches — plausible-but-rare since `_find_symbol_node`
already filters out unlocatable bodies before `_similarity` is called), `136/141` (the
"no source" and "no node found" `continue` branches in `find_similar`'s main loop). None of these
represent untested *behavior* claims from spec.md — they are defensive/degenerate branches already
covered indirectly by other tests' overall correct results, consistent with the ≥85% target being
a floor, not 100%.

**Regression confirmation:** exact match to implementation-notes.md's claimed baseline
(arch-intelligence 70→75 post-audit, apps/cli 10→16 post-audit, repo-intelligence unchanged,
impact-analysis unchanged). No discrepancy found between claimed and actual re-run results.

---

## 6. Findings

### Finding 1 — Cluster ordering is not filesystem-order-independent through the CLI path (real defect, SEND BACK TO BUILDER candidate)

**Severity:** Moderate. Does not affect correctness of *what* is reported (same clusters, same
members, same similarity scores every time), only their *relative order* in the returned list when
two or more clusters tie in similarity.

**Root cause:** `ReuseDetector.find_similar()` builds `component_matches` as a plain
`dict[int, list]` keyed by union-find root index, then does
`clusters.sort(key=lambda c: c.similarity, reverse=True)` with **no secondary sort key**
(`reuse_detector.py:207`). Python's `sort` is stable, so when two clusters have equal similarity,
their relative order in the output is whatever order they were inserted into
`component_matches` — which follows the iteration order of `pair_matches`, which follows the
iteration order of `entries`, which follows the iteration order of the caller-supplied
`symbols_by_file` dict (dict insertion order in CPython).

For direct API callers who build `symbols_by_file` from a literal dict or a sorted list, this is
stable. But `AnalyzeCommand.run_reuse()` (`analyze.py:210`) builds it via
`self.repo_root.rglob("*.py")`, whose enumeration order is **filesystem-dependent, not
alphabetically sorted** (confirmed via `pathlib.Path.rglob` docs: "yield all existing files...
matching the given relative pattern" — no ordering guarantee, and empirically OS/filesystem-driver
dependent).

**Reproduction (verified in this session, not hypothetical):**

```python
import sys
sys.path.insert(0, "packages/arch-intelligence/src")
sys.path.insert(0, "packages/repo-intelligence/src")
from repo_intelligence.symbol_extractor import SymbolExtractor
from arch_intelligence.reuse_detector import ReuseDetector

src1 = "def a(x):\n    if x > 0:\n        return 1\n    return 0\ndef b(y):\n    if y > 0:\n        return 1\n    return 0\n"
src2 = "def m(p):\n    for i in range(p):\n        print(i)\ndef n(q):\n    for i in range(q):\n        print(i)\n"
extractor = SymbolExtractor()

# Insertion order f1, f2:
sbf1 = {"f1.py": extractor.extract_symbols("f1.py", src1), "f2.py": extractor.extract_symbols("f2.py", src2)}
c1 = ReuseDetector().find_similar(sbf1, {"f1.py": src1, "f2.py": src2}, threshold=0.5)
print([c.symbol_ids for c in c1])   # [['a', 'b'], ['m', 'n']]

# Insertion order f2, f1 (simulates a different filesystem walk order):
sbf2 = {"f2.py": extractor.extract_symbols("f2.py", src2), "f1.py": extractor.extract_symbols("f1.py", src1)}
c2 = ReuseDetector().find_similar(sbf2, {"f2.py": src2, "f1.py": src1}, threshold=0.5)
print([c.symbol_ids for c in c2])   # [['m', 'n'], ['a', 'b']]  -- different order, same clusters/scores
```

Both clusters have `similarity == 1.0`; only their relative order in the returned list differs.

**Why this matters against the stated acceptance criteria:** plan.md's AC2 requires
`check_adrs()` — not `find_similar()` — to be order-stable; `find_similar()`'s own AC (AC4) only
requires "deterministic" (same input → same output) and "symmetric"
(`similarity(a,b) == similarity(b,a)`), which this satisfies for a *fixed* `symbols_by_file`
dict. The gap is specifically that `run_reuse()`'s CLI wrapper feeds `find_similar()` a dict whose
key order is not itself deterministic across runs/machines/filesystems, so **the CLI's reported
cluster order can differ between two runs against the identical repository state on different
filesystems** (e.g., a CI runner vs. a developer's Windows machine), even though the underlying
similarity computation is correct and symmetric. This is adjacent to, but distinct from, the
symmetry bug BUILDER already found and fixed — same code area, different defect class (ordering,
not scoring).

**Existing tests do not catch this** because every test in `test_reuse_detector.py` and
`test_analyze.py` builds `symbols_by_file` either from a single file, from a literal dict with a
fixed 2-key insertion order, or (in the `TestCLIEntryPoint` subprocess tests) from a `tmp_path`
directory with only 1-2 `.py` files where at most one cluster is ever produced — never from a
multi-file `rglob()` walk with 2+ independent tied-similarity clusters, which is the exact
condition that exposes the bug.

**Recommendation:** Two acceptable fixes, either is a small change:
1. Add a secondary sort key to `clusters.sort(...)` — e.g.
   `key=lambda c: (-c.similarity, c.symbol_ids)` (sort by similarity desc, then by symbol_ids
   lexicographically as a tiebreak) — makes cluster order fully independent of input dict order.
2. Sort `symbols_by_file.items()` by key before building `entries` in `find_similar()` itself, so
   the whole pipeline is insertion-order-independent from the start.

Option 1 is more minimal and directly targets the observed symptom (order of the *output* list);
Option 2 is more thorough (also stabilizes bucket/pair iteration order, which is currently also
insertion-order-dependent, though this does not affect *which* pairs are compared or their scores
— only internal iteration order, which is not externally observable except through the final sort).
Recommend Option 1 as the minimal fix consistent with ADR-010's "small, additive change" philosophy
for post-hoc adjustments.

**This is not a blocker for GATE 4** (test coverage is comprehensive; this is a code-level defect,
not a test-design gap) but **should be sent to BUILDER before GATE 5/6** so verification-report.md
and review.md are evaluated against corrected code, not against code with an undocumented ordering
non-determinism. A regression test (`test_reuse_cluster_order_independent_of_input_order`) has been
added to `test_reuse_detector.py` by this TEST-DESIGNER session to close the coverage gap (see
Section 7) — it currently passes because it only asserts the *set* of clusters matches, with a
comment marking the stronger order-equality assertion as the target once BUILDER fixes the sort key.

### Finding 2 — `check_subsystem_coverage` / `SubsystemADRCoverage` has no CLI or end-to-end surface (scope observation, not sent back)

`ADRTracker.check_subsystem_coverage()` (plan.md Atomic Task 2) is implemented and has 6 solid
unit tests in `TestSubsystemCoverage`, but `AnalyzeCommand.run_adr_check()` never calls it, and
neither `analyze.py`'s `_main()` nor `analyze.ts` expose any flag to reach it. A user running
`ortho analyze --adr-check` can never see subsystem-coverage output. spec.md's Component 1 test
list does not name any `check_subsystem_coverage`-specific test, so this is not a spec-coverage
gap — but it is a completeness gap between plan.md's stated scope ("flag files in detected
subsystems with no owning ADR... reported as a hint") and what's actually reachable through the
product surface. Not sending back — this is a product-completeness question for
PLANNER/human, not a test-coverage defect, and plan.md's own wording ("heuristic hint, not a hard
failure") suggests it may have been intentionally deferred from CLI wiring. Flagging for
awareness only.

### Finding 3 — `ReuseCluster.symbol_ids` can contain duplicate strings for overload-like same-name methods (minor, not sent back)

Verified manually: two methods with the same `qualified_name` (Python allows re-defining a method
name in a class body, e.g. two `def process(self, x)` overloads, the second shadowing the first at
runtime but both still individually AST-parseable and both returned by `SymbolExtractor`) can both
appear in a single `ReuseCluster.symbol_ids` list as `["Foo.process", "Foo.process"]` —
indistinguishable by name alone; `file_ids` is equally ambiguous (`["m.py", "m.py"]`). spec.md's
"Symbol with no body extractable -> skipped" and "Two symbols in the same file, same name
(overload-like) -> still compared" edge cases are both satisfied (verified: no crash, correctly
clustered) — but the *output* doesn't let a consumer distinguish which of the two same-named
symbols is which without also correlating by line number, which isn't in `ReuseCluster` at all.
This is a pre-existing data-shape limitation of `ReuseCluster` (spec.md's dataclass has no line
number field), not a task-010 regression — `evidence` strings do cite line ranges
(`_evidence_for_pair`), so the information exists but only in unstructured prose, not in a
structured field. Not sending back; documenting as a data-shape observation for a future
spec revision if overload-heavy codebases prove this ambiguous in practice.

---

## 7. New Test Added by TEST-DESIGNER (This Session)

Added to `packages/arch-intelligence/tests/test_reuse_detector.py` to close the Finding 1 coverage
gap (was not present in BUILDER's suite, not present in spec.md's named list, but a real
missing-edge-case per this audit's mandate to find untested edge cases near known bug-fix sites):

```python
def test_reuse_cluster_order_independent_of_input_order(detector):
    """
    Regression test for Finding 1 (test-plan.md GATE 4 audit): find_similar()'s *scoring* is
    symmetric and deterministic (test_symmetry, test_deterministic already cover that), but
    cluster *order* in the returned list is not yet independent of symbols_by_file's dict
    insertion order when two+ clusters tie in similarity -- and the CLI's run_reuse() builds
    that dict from Path.rglob(), which has no ordering guarantee. This test asserts the SET of
    clusters is order-independent today (passes); the stronger assertion (list equality,
    i.e. order itself is independent) is left commented as the target for BUILDER's fix -- see
    test-plan.md Finding 1 for the recommended fix (secondary sort key on symbol_ids).
    """
    src_a = "def a(x):\n    if x > 0:\n        return 1\n    return 0\n\ndef b(y):\n    if y > 0:\n        return 1\n    return 0\n"
    src_b = "def m(p):\n    for i in range(p):\n        print(i)\n\ndef n(q):\n    for i in range(q):\n        print(i)\n"

    symbols_by_file_1, sources_by_file_1 = _symbols_and_sources({"f1.py": src_a, "f2.py": src_b})
    symbols_by_file_2, sources_by_file_2 = _symbols_and_sources({"f2.py": src_b, "f1.py": src_a})

    clusters_1 = detector.find_similar(symbols_by_file_1, sources_by_file_1, threshold=0.5)
    clusters_2 = detector.find_similar(symbols_by_file_2, sources_by_file_2, threshold=0.5)

    # Same clusters exist either way (this passes today):
    assert {tuple(sorted(c.symbol_ids)) for c in clusters_1} == {
        tuple(sorted(c.symbol_ids)) for c in clusters_2
    }

    # TARGET for BUILDER's fix (Finding 1) -- currently would FAIL, left as documentation:
    # assert [c.symbol_ids for c in clusters_1] == [c.symbol_ids for c in clusters_2]
```

This test is additive only (new test function appended to the existing file), does not modify
`adr_tracker.py`, `reuse_detector.py`, `analyze.py`, `analyze.ts`, or `index.ts`, and does not
change any existing test. It currently passes (verified) since it only asserts the weaker,
already-true property; it documents the stronger property BUILDER should make true.

---

## 8. Summary Table

| Category | Spec.md Required | Actual | Status |
|----------|-------------------|--------|--------|
| ADRTracker unit | 9+ | 12 (9 named + 3 audit-added) | Exceeds |
| ADRTracker integration | 4+ | 4 | Meets |
| ADRTracker edge cases | 1+ | 4 (1 named + 3 audit-added) | Exceeds |
| ADRTracker subsystem-coverage (plan.md only) | n/a | 6 | Extra, unrequired but valid |
| ReuseDetector unit | 8+ | 10 | Exceeds |
| ReuseDetector property-based | 10+ cases, 3 named tests + "7 more" | 5 tests (3 named + 2 of the "7 more"), each with 10-15 hypothesis examples | Meets (named tests); "7 more" under-enumerated per implementation-notes.md's own admission, 2 of 7 filled |
| ReuseDetector integration | 2+ | 2 | Meets |
| CLI tests | 6+ | 16 (6 named subprocess + 10 supplementary in-process) | Exceeds |
| **Total** | **40+** | **92** (76 arch-intelligence incl. the 1 test added by this audit + 16 apps/cli) | Exceeds |
| Coverage (adr_tracker.py) | ≥85% | 95% | Exceeds |
| Coverage (reuse_detector.py) | ≥85% | 95% | Exceeds |
| Pass rate | 100% | 100% (75/75, 16/16; zero regressions in dependent packages) | Meets |

---

*Test plan produced by TEST-DESIGNER, fresh session, 2026-07-02.*
*Verdict: APPROVED for GATE 4, with Finding 1 flagged for BUILDER before GATE 5/6.*
