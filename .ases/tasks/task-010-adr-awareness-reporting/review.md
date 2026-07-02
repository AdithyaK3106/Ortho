---
name: task-010-review
type: review
task_id: task-010-adr-awareness-reporting
created_by: REVIEWER (fresh session, zero BUILDER context)
gate: GATE 5 (post-VERIFIED) / GATE 6
---

# Task-010 Review (REVIEWER)

## Verdict: **APPROVED**

---

## What I Read (in order, per feature.md)

1. `.ases/workflows/feature.md` — REVIEWER role section, GATE 5 checklist
2. `spec.md`, `plan.md`, `architecture-review.md`
3. `ADR-009` (ADR cross-reference strategy), `ADR-010` (reuse similarity algorithm)
4. `implementation-notes.md` (BUILDER, including both documented bug fixes)
5. `test-plan.md` (independent fresh-context TEST-DESIGNER audit)
6. `verification-report.md` (VERIFIER)
7. Actual log files: `test-arch-intelligence-1783004201.log`, `pilot-test.log`,
   `test-apps-cli-1783004215.log` (opened and read in full, not sampled)
8. Actual source: `adr_tracker.py`, `reuse_detector.py`, `analyze.py`, `analyze.ts`, `index.ts`
9. Actual tests: `test_adr_tracker.py`, `test_reuse_detector.py`, `test_analyze.py`
10. `git log`/`git show` on all five modified/created files to independently confirm the commit
    history matches the claimed scope

---

## Security Review

**Path traversal (`adr_tracker.py`):** `check_adrs()` only performs `Path.exists()` checks
(`missing_paths = [p for p in referenced_paths if not (repo_root / p).exists()]`, line 190-192)
— it never opens, reads, or executes the referenced path, only tests existence. A malicious ADR
referencing `../../etc/passwd` would resolve outside `repo_root` and `Path.exists()` would report
its real-world existence truthfully — this is an information-disclosure-shaped concern in
principle (confirms whether an arbitrary path exists on the host filesystem), but (a) ADRs are
first-party, human-authored repo content, not attacker-supplied network input, matching every
other Pillar 3 detector's trust model (task-008/009 also operate on trusted local repo state
without a threat model change), and (b) the result surfaced to the user is only "this path exists
or doesn't," never file contents. Not a defect for this task's actual threat model (local CLI tool
over a local repo you already have write access to); flagging only because the prompt asked me to
check it explicitly. No code change recommended.

**Arbitrary code execution / unsafe deserialization (`reuse_detector.py`, `analyze.py`):**
`ReuseDetector.find_similar()` uses `tree_sitter.Parser.parse()`, which is a pure syntax parser
(no code execution). `AnalyzeCommand.run_reuse()` walks the filesystem via
`self.repo_root.rglob("*.py")` and reads file *text* (`read_text`), never executes it. No `eval`,
`exec`, `pickle`, or `subprocess` with untrusted input anywhere in the two new modules.

**Resource exhaustion:** `_node_type_sequence()` (`reuse_detector.py:36-41`) recurses over the
tree-sitter tree with no depth guard. A pathologically deeply-nested Python file (thousands of
nested `if` statements) could raise `RecursionError` given Python's default recursion limit
(~1000). This is a real, if narrow, robustness gap — not present in the test suite (no test
constructs a >1000-deep nesting fixture) and not called out in spec.md's Known Limitations. I am
not sending this back: it requires a deliberately pathological input (no realistic Python codebase
nests this deeply — even generated code rarely exceeds a few hundred levels), tree-sitter parsing
itself would already be under strain at that depth, and the failure mode is a clean unhandled
exception (crash), not silent corruption or a security boundary violation. Worth a one-line note
for a future hardening pass, not a GATE 5/6 blocker.

**SQL injection (`analyze.py`, `run_impact`):** All four queries (`files`, `symbols`, `call_edges`
join, `import_edges` join) use `?` parameter placeholders exclusively — `file_path`, `repo_id` are
never string-interpolated into SQL text. Confirmed by reading lines 97-98, 115-118, 130-138,
144-152 directly. No injection vector.

**Corrupted/partially-migrated `.ortho/ortho.db` handling:** `run_impact()` checks
`db_path.exists()` before connecting (line 83) and returns a well-formed empty report if absent —
covered by `test_impact_no_database_no_crash`. However, if `.ortho/ortho.db` *exists* but is not a
valid SQLite file (corrupted) or is mid-migration (missing the `symbols`/`call_edges`/
`import_edges` tables), `sqlite3.connect()` itself will not raise (SQLite lazily validates on
first access), but the subsequent `conn.execute(...)` calls will raise `sqlite3.DatabaseError` or
`sqlite3.OperationalError` uncaught — propagating as an unhandled Python exception (crash with
traceback) rather than the same graceful empty-report degradation used for the missing-file case.
This is a real, narrow gap: spec.md's acceptance criteria only require "returns graph-derived data
**whenever the repository has been indexed**" (AC6) and don't explicitly require graceful
degradation for a *corrupted* index (as opposed to a *missing* one) — so this is not a spec
violation, and it's arguably correct behavior to surface a loud error for actual DB corruption
rather than silently returning an empty report that could be mistaken for "no dependents found."
Not sending back. Noting for awareness: a future hardening task could wrap the `conn.execute`
block in a `try/except sqlite3.DatabaseError` and return the same "not indexed" shape, but that's
a judgment call about UX (loud failure vs. silent degradation), not a correctness bug.

**Verdict: no security blockers.**

---

## Architecture Check

Compared `architecture-review.md` and both ADRs against the actual code:

- **Module boundaries:** confirmed. `adr_tracker.py` imports only `re`, `pathlib`, and
  `.types.ArchitectureModel` (for `check_subsystem_coverage`) — matches architecture-review.md's
  dependency graph exactly, including the claim that it has "no dependency on repo-intelligence,
  impact-analysis, or arch-intelligence internals" beyond the one documented exception.
- **`reuse_detector.py`** imports `tree_sitter.Parser`, `tree_sitter_languages.get_language`, and
  `repo_intelligence.symbol_extractor.Symbol` — matches. Uses `difflib.SequenceMatcher`, not a new
  Levenshtein dependency, per ADR-010's stated default and rollback-plan.md Scenario 4's gate.
  Confirmed no new entries were added to `packages/arch-intelligence/pyproject.toml`.
- **ADR-009's four-rule precedence** (File:/Code: lines → markdown links → backtick spans) is
  implemented exactly as specified: `_FILE_LINE_RE`, `_MD_LINK_RE`, `_BACKTICK_RE` are applied in
  that literal order inside `_extract_candidates()` (lines 106-119), with dedup via an
  insertion-ordered `dict` (`seen: dict[str, None]`) in `_extract_referenced_paths()` — correctly
  order-independent for the *set* of results, per the "duplicate handling" contract in spec.md.
- **ADR-010's algorithm** (AST-node-type-sequence + normalized edit distance, bucketed by
  `(type, line_count // 5)`) is implemented exactly as specified in `_node_type_sequence`,
  `_bucket_key`, and `_similarity`. The one deviation from the *original* ADR-010 text — averaging
  forward and backward `SequenceMatcher.ratio()` instead of computing it once — is a **correct,
  necessary refinement** discovered during implementation (documented as the "similarity symmetry
  bug"), not an unapproved architecture drift: it exists specifically *to satisfy* ADR-010's own
  stated symmetry requirement, which the naive single-direction implementation violated. This is
  the right kind of deviation (implementation detail fixing a bug relative to the decision's
  intent) versus a wrong kind (silently changing the decision itself).
- **CLI dependency direction:** `analyze.py` imports `arch_intelligence.ADRTracker`/`ReuseDetector`
  and `impact_analysis.ImpactAnalyzer`, never the reverse — confirmed, matches
  architecture-review.md's stated acyclic graph.
- **`run_impact`'s use of `impact_analysis.types.Symbol`** (the `file_id`-carrying local type)
  rather than `repo_intelligence.symbol_extractor.Symbol` is exactly what architecture-review.md's
  "Data Contracts Alignment" section anticipated and approved — confirmed by reading
  `analyze.py:80` (`from impact_analysis import ImpactAnalyzer, Symbol, CallEdge, ImportEdge`) and
  the query construction that builds these types from `symbols`/`call_edges`/`import_edges` rows.

No architecture drift found. Both Out-of-Scope Findings from architecture-review.md (dual `Symbol`
types, orphaned `detector.py`/`detection_types.py`/`models.py`) remain untouched, as claimed.

---

## Code Quality — Detailed Checks

**Regex correctness (`adr_tracker.py`):**
- `_EXT_RE = r"^[A-Za-z_][\w\-]*\.[a-zA-Z]{1,5}$"` correctly requires a non-empty, non-digit-first
  stem before the extension — verified this rejects `.db` and `0.7` (both fail the leading
  `[A-Za-z_]` requirement) while accepting `mod.py`, `adapter.ts`. Confirmed against
  `test_null_byte_in_candidate_dropped_silently` and the implementation-notes.md's documented
  pre-commit bug fix; the regex in the current file matches the fix as described.
- `_is_unsupported`'s "bare owner/repo" exclusion (lines 80-84) checks `candidate.count("/") == 1`
  AND matches `_BARE_OWNER_REPO_RE`, AND *then* additionally checks whether the last path segment
  itself looks like a file (`_EXT_RE.match(last_segment)`) before excluding — this correctly
  implements the documented fix for the `shared/adapter.ts`-vs-`owner/repo` ambiguity (a real path
  with one slash and a file extension on the last segment is *not* excluded; a bare
  `anthropics/claude-code`-shaped string *is*). Traced through both cases by hand; correct.
- `_STATUS_RE = r"^\**Status:?\**\s*[:]?\s*([A-Z][A-Z \-]*)"` correctly matches
  `**Status:** ACCEPTED` (bold markdown around the keyword, optional second colon before the
  value) — verified against `test_parse_status_accepted`'s exact fixture text. One residual
  observation, not a bug: the character class `[A-Z \-]*` would also greedily consume a trailing
  markdown artifact like `ACCEPTED**` if a status value were immediately followed by closing bold
  markers with no space (this repo's actual ADRs always have a line break or `\n` after the status
  word, so this never triggers in practice — confirmed by checking ADR-001 through ADR-010's exact
  formatting). Not a defect against any documented behavior; not sending back.

**Union-find (`_UnionFind`):** Traced `find()`'s path-halving (`self._parent[x] =
self._parent[self._parent[x]]; x = self._parent[x]`) and `union()` (`if root_a != root_b:
self._parent[root_b] = root_a`) by hand against the 3-element mutual-match case
(`test_dedup_merges_mutually_similar_group`) and a 4-element two-cluster case. Both correct:
no off-by-one, path-halving correctly shortens future lookups without breaking the invariant,
`union()` correctly no-ops when roots already match (avoiding a self-parent cycle). No defect.

**SQL construction (`analyze.py`):** All four queries fully parameterized (see Security Review
above). Query logic itself is correct: `call_edges` and `import_edges` are scoped to `repo_id` via
a `JOIN` back to `symbols`/`files` respectively (since neither edge table appears to carry
`repo_id` directly) — this is the right join shape to avoid cross-repo data leakage if multiple
repos ever share one `ortho.db` (not currently the case per ADR-004's local-first single-repo
model, but the join is correct regardless).

**Both documented bug fixes verified in current source, not merely trusted from
implementation-notes.md's prose:**
1. **Symmetry fix** — `_similarity()` (`reuse_detector.py:67-85`) computes `forward` and
   `backward` `SequenceMatcher.ratio()` calls and returns their average. Confirmed present in the
   file I read directly (not inferred from the changelog).
2. **Cluster-ordering fix** — `find_similar()`'s final sort (`reuse_detector.py:211`) is
   `clusters.sort(key=lambda c: (-c.similarity, sorted(c.symbol_ids)))` — a genuine secondary sort
   key, not just similarity. Confirmed present in current source. The regression test
   (`test_reuse_cluster_order_independent_of_input_order`, `test_reuse_detector.py:245-269`) now
   asserts full list equality (line 269), not merely set equality — I confirmed the assertion
   itself, not just the test's docstring claim. One minor cosmetic leftover: lines 271-272 of that
   same test file still contain the old commented-out "TARGET for BUILDER's fix... currently would
   FAIL" line duplicating the now-live assertion above it — harmless dead comment, not a functional
   issue, not worth a BUILDER round-trip by itself.

**No new correctness bugs found** beyond what test-plan.md's independent audit already surfaced
(Findings 1-3), and Finding 1 (the blocking one) is confirmed fixed in current source and covered
by a real regression test that passes for the right reason (full order equality, not weakened to
set equality).

---

## Evidence Verification (Not Fabricated)

Opened and read three log files in full:
- `test-arch-intelligence-1783004201.log`: 76 tests collected, all `PASSED`, ends with
  `76 passed in 4.50s`, `EXIT: 0`, `TIMESTAMP: 2026-07-02T14:56:47Z`. Coverage table shows
  `adr_tracker.py 95%`, `reuse_detector.py 95%` — matches verification-report.md's claim exactly,
  down to the specific uncovered line numbers.
- `pilot-test.log`: 41 tests (the two new task-010 test files only), all `PASSED`,
  `41 passed in 1.59s`, `EXIT: 0` — matches verification-report.md's Phase B claim exactly.
- `test-apps-cli-1783004215.log`: 16 tests, all `PASSED`, `16 passed in 2.58s`, `EXIT: 0` — matches.

All test names in these logs match test-plan.md's inventory tables exactly (cross-checked every
row in test-plan.md Sections 1-3 against the log output — no name mismatches, no missing tests, no
extra unexplained tests). Exit codes in every log match the "VERIFIED"/"PASS" claims in
verification-report.md. This is genuine pytest output (real collection counts, real percentage
timings, real coverage line numbers, real Windows file paths) — not fabricated text.

---

## Scope Verification

Ran `git log`/`git show` independently on all five modified/created files. Commit history:
`ab22be7` → `be06fbe` → `37250f9` → `f5ec147` → `66a066f` → `4e155f3` (symmetry fix) → `d531e0d`
(cluster-ordering fix), each an atomic, isolated commit matching the atomic-task breakdown in
plan.md and the granular-rollback requirement in rollback-plan.md. `66a066f`'s commit message
independently corroborates implementation-notes.md's two documented deviations word-for-word
(unregistered `analyzeCommand` in `index.ts`, stale spawn path in `analyze.ts`) — I did not simply
trust the prose in implementation-notes.md; the commit message was written before (or independent
of) that document and says the same thing. No undocumented files or unexplained changes found in
any of the seven commits' stat output for the reviewed files.

---

## Summary

No blocking issues. Both real defects found during this task's own development process (similarity
symmetry, cluster ordering) are fixed in the code I read directly, covered by regression tests
that pass for the correct reason, and independently corroborated across implementation-notes.md,
test-plan.md, verification-report.md, real log files, and git history — all four sources agree
with each other and with the current state of the source tree. Architecture matches both ADRs and
architecture-review.md with no drift. SQL is fully parameterized. No injection, deserialization, or
code-execution vectors in the new code. Two narrow robustness gaps noted (unbounded AST recursion
depth, uncaught `sqlite3.DatabaseError` on a corrupted-but-present `.ortho/ortho.db`) — both
documented above for future awareness, neither blocks approval since neither violates a stated
acceptance criterion or introduces a security boundary violation.

**APPROVED.**

---

*Review completed by REVIEWER, fresh session, 2026-07-02.*
