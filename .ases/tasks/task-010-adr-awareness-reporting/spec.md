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
          2. Extract referenced code paths (backtick-quoted paths containing '/' or '.')
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

### Tests (12+ total)

**Unit tests (7+):**
- `test_adr_parse_status_accepted` — `**Status:** ACCEPTED` parsed correctly
- `test_adr_parse_status_missing` — no Status line -> UNKNOWN
- `test_adr_extract_backtick_paths` — extracts `shared/types/src/adapter.ts` style refs from prose
- `test_adr_classify_ok` — all referenced paths exist -> OK
- `test_adr_classify_stale` — one missing path -> STALE, listed in missing_paths
- `test_adr_classify_unlinked` — zero code refs found -> UNLINKED
- `test_adr_glob_pattern_skipped` — `packages/*/tests/` not flagged as missing

**Integration tests (4+):**
- `test_adr_real_repo_all_5_adrs` — run against this repo's actual `.ases/architecture/adrs/`,
  verify 5 ADRStatus results returned (ADR-001 through ADR-005)
- `test_adr_empty_dir` — nonexistent adr_dir -> []
- `test_adr_deterministic` — same input, same output (no ordering flakiness)

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
            threshold: minimum similarity [0.0-1.0] to form a cluster

        Returns:
            List of ReuseCluster, sorted by similarity desc

        Edge cases:
        - Symbol with no body extractable -> skipped
        - Fewer than 2 symbols total -> []
        - Two symbols in the same file, same name (overload-like) -> still compared
        """
        ...
```

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
- `test_reuse_real_repo` — run on `packages/arch-intelligence` + `packages/impact-analysis`
  (both have parallel dataclass `__post_init__` validation patterns — expected to cluster)
- `test_reuse_large_symbol_set` — 200+ symbols, completes in reasonable time (documented ceiling)

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

- `test_cli_adr_check_command` — runs `ortho analyze --adr-check` against this repo, non-empty output
- `test_cli_reuse_command` — runs `ortho analyze --reuse`, non-empty output on this repo
- `test_cli_reuse_threshold_option` — `--threshold` changes cluster count
- `test_cli_impact_fixed_not_stub` — `ortho analyze --impact <known-imported-file>` returns
  direct_dependents non-empty (regression guard against the old empty-list stub)
- `test_cli_impact_missing_file` — nonexistent file -> empty report, no crash
- `test_cli_json_format_all_new_commands` — `--format json` valid JSON for adr-check and reuse

---

## Expected Test Metrics Summary

| Category | Count | Note |
|----------|-------|------|
| Unit tests | 15+ | ADRTracker + ReuseDetector isolated |
| Integration tests | 6+ | Real ADRs, real repo symbols |
| Property-based (hypothesis) | 10+ | Reuse similarity bounds/determinism/symmetry |
| CLI tests | 6+ | End-to-end command validation incl. --impact fix regression guard |
| Edge cases | 1+ | Malformed ADR markdown |
| **Total** | **38+** | |
| **Coverage target** | **≥85%** | Per component |
| **Pass rate** | **100%** | No known xfail unless discovered during build (documented before GATE 4) |

## Known Limitations (To Mark as xfail if Testing Confirms)

1. **ADR path extraction is heuristic:** backtick-quoted, path-shaped strings only. An ADR that
   references code in prose without backticks (e.g. "see the database module") won't be detected.
   Biases toward under-reporting (fewer false STALE flags) per plan.md risk mitigation.
2. **Glob-pattern references skipped:** `packages/*/tests/` style refs aren't existence-checked,
   just excluded from missing_paths. Not a false STALE, but also not verified.
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
