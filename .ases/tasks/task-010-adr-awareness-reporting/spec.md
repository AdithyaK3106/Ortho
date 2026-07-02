---
name: task-010-spec
type: specification
phase: Phase 2, Week 13-14
task_id: task-010-adr-awareness-reporting
---

# Task-010 Specification: ADR Awareness + Reporting

## Overview

Implement the last two Pillar 3 features (FRD line 843-854):
1. **ADR awareness** — cross-reference ADRs against actual code, flag drift
2. **Reuse discovery** — find structurally similar code via AST comparison

And fix `ortho analyze --impact` which currently loads empty graphs (dead stub), blocking the
FRD Phase 2 exit criterion at line 1905.

## Known Gap Inherited From Prior Tasks (Document, Do Not Silently Fix)

`Symbol` (`packages/repo-intelligence/src/repo_intelligence/symbol_extractor.py:13-21`) and
`ImportEdge` (`packages/repo-intelligence/src/repo_intelligence/import_graph.py:12-19`) carry no
`file_id`/`file_path` field — they're returned per-file by their respective extractors, and the
caller is expected to track which file a given extraction batch belongs to. Task-009's
`ImpactAnalyzer` spec assumed a `changed_file_id` join key exists on these types; it does not
natively. This task works around it (join by file path supplied by the CLI caller, since
`ortho analyze --impact <file>` already takes a file argument) rather than modifying the shared
types, to avoid an out-of-scope breaking change across repo-intelligence, arch-intelligence, and
impact-analysis. If a future task needs symbol-to-file joins at the data-model level, that's a
separate ADR-worthy decision, not a task-010 side effect.

## Component 1: ADRTracker

### Purpose
Answer: "Do our ADRs still match reality?"

### Class: `ADRTracker`

```python
class ADRTracker:
    """Cross-references ADRs against the current repo tree (stateless)."""

    def check_adrs(
        self,
        adr_dir: Path,
        repo_root: Path,
    ) -> list[ADRStatus]:
        """
        For every ADR-*.md file in adr_dir:
          1. Parse status line (Status: DRAFT|PROPOSED|ACCEPTED|SUPERSEDED)
          2. Extract referenced code paths (see "ADR Path Extraction Contract" below)
          3. Check each referenced path exists relative to repo_root
          4. Classify: OK (all refs exist, >=1 ref found), STALE (>=1 ref missing),
             UNLINKED (zero code refs found in the ADR text at all)

        Returns one ADRStatus per ADR file, sorted by adr_id.

        Edge cases:
        - ADR dir doesn't exist -> return []
        - ADR file has no Status: line -> status = "UNKNOWN"
        - Referenced path is a glob/pattern (e.g. "packages/*/tests/") -> skip existence check,
          not counted as a broken ref (documented limitation, see Known Limitations)
        """
        ...
```

### ADR Path Extraction Contract

This contract is fully specified so that two independent implementations parsing the same ADR
file produce identical `referenced_paths` and `missing_paths` results.

**Extraction precedence** (higher-precedence sources are extracted first; a path found by more
than one rule is recorded once — see Duplicate Handling):

1. **Explicit `File:` lines** — a line matching `^\s*(?:-\s*)?File:\s*` followed by a
   backtick-quoted or bare path, up to end of line
2. **Explicit `Code:` lines** — same pattern, keyword `Code:` instead of `File:`
3. **Markdown links to repository paths** — `[text](path)` where `path` does not start with
   `http://`, `https://`, or `#` (in-page anchors are not code references)
4. **Inline backtick-quoted paths** — any `` `...` `` span whose content contains at least one
   `/` or a file extension matching `\.[a-zA-Z0-9]{1,5}$`, found anywhere else in the document
   body (this is the fallback catch-all; rules 1–3 exist so an ADR author can be explicit about
   intent, rule 4 catches everything else)

A candidate string is a "path reference" only if it matches this shape after trimming: contains
no whitespace, and either contains `/` or ends in a recognized file extension. Bare identifiers
like `` `ArchitectureModel` `` or `` `save()` `` are not path references and are excluded at
every precedence level.

**Path normalization** (applied to every extracted candidate before classification):

- Trim leading/trailing whitespace
- Normalize path separators to `/` (handles ADRs written with `\` on Windows-authored docs)
- Strip a leading `./` if present
- Paths are treated as relative to `repo_root`; a leading `/` is stripped (never treated as
  filesystem-root-absolute) — ADRs reference repo-relative paths only
- Case-sensitivity follows the host filesystem (no forced case-folding) — this is a known
  cross-platform limitation, not a bug: an ADR authored referencing `Auth.py` will report STALE
  on a case-sensitive filesystem if the real file is `auth.py`

**Duplicate handling:**

- The same normalized path referenced multiple times within one ADR is deduplicated —
  `referenced_paths` contains each unique path once, regardless of how many times or by which
  precedence rule it was mentioned
- Existence checks run once per unique normalized path, after deduplication, after all four
  extraction rules have run over the full document
- No conflict resolution is needed between precedence rules for existence checking, since
  precedence only matters for extraction provenance, not for the (deduplicated) final path set

**Unsupported references** (recognized but explicitly excluded from `referenced_paths`, never
counted toward `missing_paths`, never affect classification):

- **Glob patterns** — any candidate containing `*`, `?`, or `[...]` wildcard syntax
  (e.g. `packages/*/tests/`)
- **URLs** — `http://`, `https://`, `ftp://` prefixed strings
- **External repository references** — strings shaped like `owner/repo` GitHub shorthand or
  containing `github.com`, `gitlab.com` — not resolvable against `repo_root`
- **Prose-only references** — text mentioning a component by name without a path-shaped token
  (e.g. "see the database module") — undetectable by design, documented in Known Limitations
- **Malformed paths** — candidates that, after normalization, contain null bytes or are empty —
  silently dropped, not reported as errors

### Data Type: `ADRStatus`

```python
@dataclass
class ADRStatus:
    adr_id: str                  # e.g. "ADR-005"
    title: str
    status: str                  # DRAFT | PROPOSED | ACCEPTED | SUPERSEDED | UNKNOWN
    referenced_paths: list[str]  # paths found in the ADR text
    missing_paths: list[str]     # referenced_paths that don't exist on disk
    classification: str          # OK | STALE | UNLINKED | UNKNOWN
    evidence: list[str]
```

### Tests (14+ total)

**Unit tests (9+):**
- `test_adr_parse_status_accepted` — `**Status:** ACCEPTED` parsed correctly
- `test_adr_parse_status_missing` — no Status line -> UNKNOWN
- `test_adr_extract_backtick_paths` — extracts path-shaped backtick spans from prose (rule 4)
- `test_adr_extract_file_line_precedence` — a path in a `File:` line (rule 1) and the same path
  also appearing inline elsewhere (rule 4) is recorded once, not duplicated
- `test_adr_extract_markdown_link` — `[text](packages/foo/bar.py)` extracted, `[text](#anchor)`
  and `[text](https://example.com)` are not
- `test_adr_classify_ok` — all referenced paths exist -> OK
- `test_adr_classify_stale` — one missing path -> STALE, listed in missing_paths
- `test_adr_classify_unlinked` — zero code refs found -> UNLINKED
- `test_adr_glob_and_url_skipped` — glob patterns and URLs excluded from referenced_paths and
  missing_paths entirely (not just skipped for existence checking)

**Integration tests (4+):**
- `test_adr_directory_with_n_adrs` — a fixture directory with a known number of well-formed ADR
  files returns exactly that many `ADRStatus` results, each correctly classified
- `test_adr_empty_dir` — nonexistent adr_dir -> []
- `test_adr_deterministic_repeat_run` — same fixture directory, run twice, byte-identical result
  ordering and content both times
- `test_adr_deterministic_across_extraction_order` — an ADR containing the same path reachable
  via two different precedence rules produces the same `referenced_paths` regardless of which
  rule is evaluated first internally (verifies dedup is order-independent)

**Edge cases (1+):**
- `test_adr_malformed_markdown` — file with no headers/status at all doesn't crash, returns UNKNOWN

---

## Component 2: ReuseDetector

### Purpose
Answer: "Where is similar logic duplicated?"

### Class: `ReuseDetector`

```python
class ReuseDetector:
    """Finds structurally similar symbols via AST comparison (stateless)."""

    def find_similar(
        self,
        symbols_by_file: dict[str, list[Symbol]],
        sources_by_file: dict[str, str],
        threshold: float = 0.7,
    ) -> list[ReuseCluster]:
        """
        Compare function/method bodies pairwise within type+size buckets
        (bucket by Symbol.type and body line-count band to avoid O(n^2) over
        the full symbol set), score structural similarity, cluster matches
        above threshold.

        Similarity = normalized tree edit distance over tree-sitter AST node
        *types* (not identifier names/literals) between two symbol bodies.

        Args:
            symbols_by_file: file path -> extracted Symbols for that file
            sources_by_file: file path -> raw source text (for re-parsing bodies)
            threshold: minimum similarity [0.0-1.0] to form a cluster.
                0.7 is the Phase 2 default (see "Threshold Configuration Policy" below) — callers
                (CLI, future API consumers) may override it per invocation. The similarity
                computation itself does not change based on threshold; threshold only selects
                which already-computed scores are reported as clusters.

        Returns:
            List of ReuseCluster, sorted by similarity desc

        Edge cases:
        - Symbol with no body extractable -> skipped
        - Fewer than 2 symbols total -> []
        - Two symbols in the same file, same name (overload-like) -> still compared
        """
        ...
```

### Threshold Configuration Policy

`threshold=0.7` is a **default configuration value for Phase 2**, not an architectural constant:

- The similarity *algorithm* (AST-type-sequence + edit distance, see below) is fixed and
  deterministic regardless of threshold — threshold is purely a post-hoc filter on computed scores
- Callers may configure the threshold through the CLI (`--threshold`) or by calling
  `find_similar()` directly with a different value; both paths use the same algorithm
- Future phases may recalibrate the default (e.g. based on false-positive rate observed across
  more repositories) without any change to how similarity is computed — recalibrating the default
  is a configuration change, not a re-architecture
- This task does not implement persisted/per-repo threshold configuration (e.g. a config file
  entry) — the default is a Python parameter default and a CLI flag default. Persisted
  configuration, if wanted later, is out of scope here.

### Data Type: `ReuseCluster`

```python
@dataclass
class ReuseCluster:
    symbol_ids: list[str]        # qualified_name per matched symbol
    file_ids: list[str]          # file paths, parallel to symbol_ids
    similarity: float            # 0.0-1.0
    evidence: list[str]          # e.g. "Both functions: 1 if-branch, 2 calls, 1 return"

    def __post_init__(self):
        assert 0.0 <= self.similarity <= 1.0
        assert len(self.symbol_ids) == len(self.file_ids)
        assert len(self.symbol_ids) >= 2
```

### Similarity Algorithm (ADR-010)

```
1. Parse each symbol's source range into a tree-sitter subtree (already available via
   SymbolExtractor's parser, re-sliced to the symbol's line range)
2. Flatten subtree to a sequence of node *type* labels (drop identifier names, literal
   values, comments) - this is what makes it structural, not textual
3. similarity = 1 - (levenshtein(seq_a, seq_b) / max(len(seq_a), len(seq_b)))
4. Bucket candidates by (Symbol.type, line_count // 5) before pairwise comparison to
   keep this near-linear in practice instead of O(n^2) over the whole repo
```

Rationale for AST-type-sequence + edit distance over embeddings: stays local-first (FRD
principle — no ML dependency), deterministic, explainable via evidence strings, consistent with
task-008/009's "stateless, deterministic, evidence-backed" pattern.

### Tests (14+ total)

**Unit tests (8+):**
- `test_reuse_identical_functions_different_names` — same structure, different identifiers -> similarity 1.0
- `test_reuse_unrelated_functions` — similarity below threshold, not clustered
- `test_reuse_threshold_boundary` — similarity exactly at threshold -> included (>=)
- `test_reuse_empty_input` — no symbols -> []
- `test_reuse_single_symbol` — one symbol total -> []
- `test_reuse_same_file_duplicates` — two similar functions in one file -> clustered
- `test_reuse_bucketing_skips_size_mismatch` — wildly different line counts not compared (perf guard)
- `test_reuse_cluster_evidence_present` — every ReuseCluster has non-empty evidence

**Property-based tests (10+ cases via hypothesis):**
- `test_reuse_similarity_bounds` — similarity always in [0.0, 1.0]
- `test_reuse_deterministic` — same symbols/sources -> same clusters, same order
- `test_reuse_symmetry` — similarity(a, b) == similarity(b, a)
- (+ 7 more: varying symbol counts, random AST shapes, threshold sweeps)

**Integration tests (2+):**
- `test_reuse_finds_known_duplicate_pair` — given a fixture pair of symbols constructed to be
  structurally identical apart from naming, `find_similar()` reports them as a cluster at the
  default threshold (validates the end-to-end pipeline against a controlled, repo-independent
  fixture rather than incidental repo content)
- `test_reuse_symbol_set_scales` — a symbol set at the size documented in the Benchmark Environment
  below completes within the documented time ceiling (see Benchmark Environment; not a fixed
  wall-clock assertion — see Note on Timing Assertions)

### Benchmark Environment

Performance figures for `ReuseDetector` are engineering quality metrics for regression tracking,
not binary acceptance criteria. A benchmark run must document:

- **Symbol count:** approximate number of symbols in the input (order of magnitude — hundreds vs
  thousands matters more than the exact count)
- **Repository size:** approximate file count and total Python LOC of the benchmarked codebase
- **Execution mode:** cold (first run, no OS filesystem cache warmup) vs warm (repeated run) —
  report both if they differ meaningfully
- **Hardware assumption:** typical developer workstation (no specific CPU/RAM spec required;
  note if run in CI vs local, since CI runners are often slower)
- **OS assumption:** noted if timing differs meaningfully between platforms (tree-sitter parsing
  is generally OS-independent; filesystem walk speed can vary)
- **Sample count:** whether the reported timing is a single observation or an average of multiple
  runs — single-run observations must be labeled as such, not presented as stable averages

**Note on Timing Assertions:** `test_reuse_symbol_set_scales` asserts against a documented ceiling
(e.g. "completes in under N seconds"), not an exact benchmark value — the ceiling should be set
generously above the observed benchmark (see Validation Baseline below) to avoid flaking on slower
hardware/CI, while still catching a genuine algorithmic regression (e.g. accidentally losing the
bucketing optimization and falling back to full O(n²)).

Actual measured values from a specific run belong in implementation-notes.md and the Validation
Baseline (spec.md), not hardcoded as pass/fail thresholds in test assertions.

---

## Component 3: CLI Integration

### New/Fixed Commands

```bash
ortho analyze --adr-check
  -> ADRTracker.check_adrs(Path(".ases/architecture/adrs"), repo_root)
  -> Print: adr_id | status | classification | missing_paths

ortho analyze --reuse [--threshold 0.7]
  -> Load symbols+sources for all Python files via SymbolExtractor
  -> ReuseDetector.find_similar(symbols_by_file, sources_by_file, threshold)
  -> Print: cluster similarity | symbol_ids | file_ids

ortho analyze --impact <file>
  -> FIX: replace empty-list stub in AnalyzeCommand.run (analyze.py:31-34) with real
     graph loads from OrthoDatabase, then call task-009's ImpactAnalyzer.analyze(...)
  -> This is the only change to existing AnalyzeCommand code in this task
```

### Tests (6+ total)

- `test_cli_adr_check_command` — runs `ortho analyze --adr-check` against a repository containing
  ADRs, produces a well-formed report (valid for zero-or-more ADRs, per ADRTracker contract)
- `test_cli_reuse_command` — runs `ortho analyze --reuse` against a repository containing
  structurally similar symbols (fixture), produces a well-formed report
- `test_cli_reuse_threshold_option` — `--threshold` changes which computed similarity scores are
  included in the report (higher threshold -> subset of clusters at lower threshold, same fixture)
- `test_cli_impact_fixed_not_stub` — `ortho analyze --impact <file>` on a fixture/indexed
  repository where the target file has a known dependent returns that dependent in
  `direct_dependents` (regression guard: the old stub always returned an empty report regardless
  of input — this test fails against the old behavior and passes against the fix)
- `test_cli_impact_missing_file` — nonexistent file -> empty report, no crash
- `test_cli_json_format_all_new_commands` — `--format json` valid JSON for adr-check and reuse

---

## Expected Test Metrics Summary

| Category | Count | Note |
|----------|-------|------|
| Unit tests | 17+ | ADRTracker + ReuseDetector isolated, fixture-based |
| Integration tests | 6+ | Fixture ADR sets, fixture symbol pairs, repeatable across repos |
| Property-based (hypothesis) | 10+ | Reuse similarity bounds/determinism/symmetry |
| CLI tests | 6+ | End-to-end command validation incl. --impact fix regression guard |
| Edge cases | 1+ | Malformed ADR markdown |
| **Total** | **40+** | |
| **Coverage target** | **≥85%** | Per component |
| **Pass rate** | **100%** | No known xfail unless discovered during build (documented before GATE 4) |

Test design favors deterministic fixtures (constructed ADR files, constructed symbol pairs) over
assertions tied to this repository's current contents, so the suite remains valid as the repo
evolves. Where a test also happens to run against this repo's real files (e.g. as a smoke test),
that is incidental coverage, not the basis for pass/fail — see Validation Baseline above.

## Validation Baseline (Reference Benchmark Environment)

These are **informational observations** from running the planned components against this repo's
actual state at planning time. They exist to support regression tracking during development and
GATE 5 spot-checks — they are **not release gates** and are **not** part of the Acceptance
Criteria in plan.md. They will evolve as the repository changes; a future run producing different
numbers is not a failure by itself.

**Repository:** `ortho` (this repo), local working tree
**Benchmark date:** 2026-07-02

**ADRTracker baseline:**
- ADR directory: `.ases/architecture/adrs/`
- Observed ADR file count matching `ADR-*.md`: 5 (ADR-001 through ADR-005; `INDEX.md` is
  intentionally excluded by the glob, not an ADR)
- All 5 observed as `Status: ACCEPTED` in current content
- Expected classification at benchmark time: all 5 -> OK (each ADR's referenced paths, once
  implemented and run, are expected to resolve — to be confirmed during BUILDER/VERIFIER, not
  assumed here)

**ReuseDetector baseline:**
- Reference codebase: `packages/arch-intelligence/` + `packages/impact-analysis/`
  (~4,227 combined lines of Python across both packages at benchmark time)
- Rationale for choosing this pair: both packages independently implement the "stateless
  dataclass with `__post_init__` bounds validation" pattern established in task-008/009 — a
  structurally plausible source of at least one reuse cluster, useful as a smoke-test fixture
  during development
- Expected observation: at least one cluster at the 0.7 default threshold — to be confirmed
  during BUILDER/VERIFIER, not guaranteed by this document

**CLI baseline:**
- `ortho analyze --adr-check` expected to produce 5 report rows against this repo's ADR directory
- `ortho analyze --impact <file>` expected to return non-empty `direct_dependents` for any file
  in this repo currently imported by 2+ other files (several such files exist in
  `packages/repo-intelligence/src/repo_intelligence/`, per existing call/import graph builders)

**Benchmark execution notes:**
- Symbol count order of magnitude for `packages/arch-intelligence` + `packages/impact-analysis`:
  low hundreds (exact count depends on `SymbolExtractor` granularity — functions, classes, and
  methods all count as separate symbols)
- Execution mode: not yet measured (no implementation exists at planning time) — BUILDER/VERIFIER
  will record cold vs warm timing once `ReuseDetector` exists
- Hardware/OS: developer workstation, Windows, no specific spec assumed or required
- Sample count: N/A at planning time — first measurement will be a single-run observation, to be
  labeled as such in implementation-notes.md

## Known Limitations (To Mark as xfail if Testing Confirms)

1. **ADR path extraction is heuristic:** limited to the four rules in the ADR Path Extraction
   Contract (File:/Code: lines, markdown links, backtick-quoted path-shaped spans). An ADR that
   references code in unstructured prose (e.g. "see the database module") won't be detected.
   Biases toward under-reporting (fewer false STALE flags) per plan.md risk mitigation.
2. **Glob patterns, URLs, and external repo references are excluded entirely:** per the
   Unsupported References section of the extraction contract, these never appear in
   `referenced_paths` or `missing_paths` — not a false STALE, but also not verified.
3. **Reuse similarity is structural only:** two functions with identical shape but opposite logic
   (e.g. `if x > 0` vs `if x < 0`) score as fully similar since literals/operators inside condition
   nodes aren't distinguished at the node-type level chosen for determinism/speed. Documented
   ceiling; upgrade path is comparing a richer node label (type + operator) if false positives
   prove common in practice.
4. **No file_id on Symbol/ImportEdge (see Known Gap section above):** worked around via
   caller-supplied file path, not fixed at the type level.
5. **Performance:** ReuseDetector pairwise comparison, even bucketed, may be slow beyond a few
   thousand symbols. Document actual real-repo timing in implementation-notes.md.

## Rollback (If Implementation Fails)

1. **Branch-level:** `git reset --hard HEAD~[N]`
2. **Published (main):** `git revert [commit]` + document in ADR
3. **Clean up:** `rm -rf .ases/tasks/task-010-* .ases/evidence/task-010/`
4. **Restart:** Replan with updated requirements

---

*Specification created by PLANNER, 2026-07-02*
*Awaiting GATE 1 approval*
