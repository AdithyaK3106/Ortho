---
title: task-015 Specification
task: Public Repository Benchmarks
workflow: feature.md
status: READY-FOR-ARCHITECT
---

# task-015 Specification

## Acceptance Criteria (AC)

### AC1: Repo Selection & Safe Iteration

**What:** Sample 50–100 public Python repositories stratified by category and size; prepare for analysis.

**Repository Categories (6 explicit categories):**
1. **Web Frameworks** — Flask, FastAPI, Django, Pyramid, Tornado (Python web servers)
2. **AI/ML** — TensorFlow, PyTorch, scikit-learn, Hugging Face, transformers (machine learning libraries)
3. **Libraries** — General-purpose libraries (requests, pandas, numpy, sqlalchemy, etc.)
4. **CLI Tools** — Command-line applications (Click-based, argparse, Typer, etc.)
5. **Infrastructure** — DevOps, infrastructure-as-code (Ansible, Terraform Python, CloudFormation parsers, etc.)
6. **Developer Tooling** — Build tools, linters, test frameworks, documentation generators (pytest, black, sphinx, etc.)

**How:**
- Use `requests` + GitHub Search API (no auth needed for 60 req/hr; cache results)
- For each category, run category-specific search query
  - Example: `language:Python stars:>10 created:>2020-01-01 "flask" OR "django" OR "fastapi"` (Web Frameworks)
- Stratified sampling across categories:
  - Target: ≥8 repos per category (6 categories × 8 = 48, up to 100 total)
  - Within each category:
    - Size: distribute across S (1–100 files), M (100–1k files), L (1k–10k files), XL (10k–100k files)
    - Stars: distribute across 10–100 stars, 100–1k, 1k–10k, 10k+
- Store metadata in `.ases/evidence/repo-list.json`:
  ```json
  [
    {
      "url": "https://github.com/org/name",
      "category": "Web Frameworks",
      "stars": 5000,
      "files": 342,
      "size_mb": 45,
      "sampled": true,
      "size_category": "medium",
      "star_range": "1k-10k"
    },
    ...
  ]
  ```
- Clone to temp dir with timeout (10 min per repo)
- Skip if: clone fails, size >500MB, not Python, too new (<6 months)
- Document exclusions in `.ases/evidence/exclusions.json` with category and skip reason

**Acceptance:** 
- `.ases/evidence/repo-list.json` contains ≥50 repos
- All 6 categories represented (≥8 repos each)
- Size and star stratification documented
- ≥95% clones successful (≤5 repos excluded)

---

### AC2: Batch Architecture Analysis

**What:** Run full scanning + analysis pipeline on each repo; collect KPIs and classify any failures.

**KPI Schema** (all metrics stored in `.ases/evidence/results.csv`):
```csv
repo_url,category,files_scanned,symbols_found,imports_total,calls_detected,
arch_style,arch_confidence,layers_detected,subsystems_found,subsystem_avg_size,subsystem_singleton_count,singleton_rate,
circular_deps,debt_score,
scan_time_sec,analysis_time_sec,
intent_routing_success_rate,
status,failure_type,error_message,
```

**How:**
1. For each repo in sample:
   ```bash
   cd /tmp/ortho-benchmark/$REPO_NAME
   timeout 60 ortho init --project-name test
   timeout 120 ortho scan 2>&1 | tee scan.log
   timeout 60 ortho analyze --adr-check --reuse 2>&1 | tee analyze.log
   ```
2. Parse output and extract KPIs; time each phase (scan_time_sec, analysis_time_sec)
3. For intent routing (AC3 subset): run 3 sample utterances per repo, calculate success rate
4. Subsystem singleton rate: count subsystems with 1 file / total subsystems
5. On error: classify using **Failure Taxonomy** (see below)
   - Log to `.ases/evidence/errors/$REPO_NAME.error` with failure_type and error_message
   - Mark status as FAILED or INCOMPLETE

**Failure Taxonomy** (reference: `.ases/tasks/task-015-repo-benchmarks/failure-taxonomy-TEMPLATE.md`; fixed classification):
- **Clone Failure** — Git clone timed out or failed (network, auth, repo issue)
- **Scan Failure** — `ortho scan` exited non-zero (dependency issue, corrupted repo)
- **Parser Failure** — AST parsing failed on Python files (syntax error, rare dialect)
- **Graph Failure** — Call/import graph construction failed (malformed imports, circular logic)
- **Architecture Failure** — Architecture detection crashed or returned invalid style
- **Intent Router Failure** — Semantic router failed to classify utterances
- **Timeout** — Any operation exceeded time limit (scan >120s, analyze >60s, etc.)
- **OOM** — Out of memory error detected
- **Unknown** — Error occurred but taxonomy doesn't match

**Acceptance:** 
- `.ases/evidence/results.csv` has ≥50 rows (≥95% success rate)
- All KPI columns populated (or N/A for repos with failures)
- Failure types classified; each error has failure_type + error_message
- Summary stats computed (mean, median, std dev per KPI)

---

### AC3: Intent Coverage Audit

**What:** Validate that Ortho's semantic-router can classify user intents on real repo workflows.

**How:**
1. Collect 40 workflow utterances from FRD Section 11 + task-012 corpus:
   - Feature dev: "add rate limiting", "implement caching", "create new endpoint"
   - Bug fix: "fix null pointer", "users getting 500 errors", "login broken"
   - Refactor: "extract repository pattern", "reduce coupling", "split monolith"
   - Analysis: "blast radius of X", "show architecture", "technical debt summary"
2. For each of ≥10 repos (diverse sizes):
   ```bash
   # Simulate IntentRouter on each repo's codebase context
   # (no LLM call; measure router confidence only)
   python -c "from packages.orchestration import IntentRouter; 
     router = IntentRouter(); 
     result = router.classify_intent('add rate limiting')
     print(f'{result.type},{result.confidence},{result.method}')"
   ```
3. Aggregate: % of utterances with confidence ≥0.7 (route success) vs. fallback needed
4. Store in `.ases/evidence/intent-coverage.json`:
   ```json
   {
     "total_utterances": 40,
     "successful_routes": 34,
     "fallback_needed": 6,
     "success_rate": 0.85,
     "confidence_mean": 0.78,
     "confidence_min": 0.62,
     "by_type": {"feature_dev": 0.9, "bug_fix": 0.85, "refactor": 0.75, "analysis": 0.8}
   }
   ```

**Acceptance:** Intent coverage report produced; success rate ≥80%; breakdowns by intent type clear.

---

### AC4: Token Baseline & Report

**What:** Measure context assembly costs; establish baseline for Phase 4 optimization targets.

**How:**
1. For each repo in AC2 results, measure token usage:
   - Run a synthetic `assemble_context()` call on 5 sample intent queries per repo
   - Capture: num_chunks, total_tokens, mean_chunk_tokens, budget_fill_pct
   - Store in `.ases/evidence/token-baseline.csv`:
     ```csv
     repo_name,intent_type,chunks_assembled,tokens_used,budget_fill_pct,time_ms
     ```
2. Compute aggregate statistics:
   - Mean context size: X tokens (median, std dev)
   - Mean budget fill: Y% (median range)
   - Outliers (>3σ above mean): flag for inspection
3. Store in `.ases/evidence/token-stats.json`:
   ```json
   {
     "total_samples": 250,
     "mean_tokens_per_context": 1200,
     "median_tokens": 950,
     "std_dev": 420,
     "p95_tokens": 2100,
     "mean_budget_fill": 0.45,
     "outliers_count": 8
   }
   ```

**Acceptance:** Token baseline computed; stats file has all required fields; outliers documented.

---

### AC5: Rubric-Based Spot-Checks

**What:** Audit 5–10 repos using a documented scoring rubric; compare Ortho's analysis against rubric criteria.

**Architecture Scoring Rubric** (reference: `.ases/tasks/task-015-repo-benchmarks/architecture-scoring-rubric-TEMPLATE.md`):

For each architecture style, define clear scoring criteria:

```markdown
## Layered Architecture Rubric

**Definition:** Code organized into horizontal layers (data, business, presentation). Clear dependencies flow downward.

**Scoring Criteria (Evidence-Based):**
- **Clear Layer Structure (Yes/No):** 
  - Look for: directories like `models/`, `services/`, `handlers/`, `schemas/`, or equivalent package names
  - Evidence: file tree shows 3+ distinct layers
- **Dependency Direction (Correct/Reversed/Mixed):**
  - Check imports: does presentation import from services? (correct)
  - Does services import from presentation? (reversed)
- **Layer Cohesion (High/Medium/Low):**
  - Are all files in a layer functionally related?
  - Medium: 80%+ files fit layer purpose
- **Confidence Score Assessment (0.0–1.0):**
  - If all 3 criteria Met → expected confidence 0.8–1.0
  - If 2/3 criteria Met → expected confidence 0.6–0.8
  - If 1/3 criteria Met → expected confidence 0.4–0.6
  - If 0/3 criteria Met → expected UNKNOWN (confidence < 0.45)

**Rubric Scoring:**
- Ortho confidence within ±0.1 of expected → **ACCURATE**
- Ortho confidence ±0.1–0.2 off → **ACCEPTABLE** (minor miscalibration)
- Ortho confidence >±0.2 off → **INACCURATE** (needs investigation)
```

Repeat for: MVC, Hexagonal, Microservices, Flat, Unknown.

**How:**
1. Select ≥8 repos from AC2 results:
   - Stratified: ≥2 small, ≥2 medium, ≥2 large, ≥2 outliers (high debt, low confidence, failure-adjacent)
   - Stratified by category: include multiple categories
2. For each repo, manually examine code structure and fill rubric assessment:
   ```markdown
   ## Repo: [URL] | Category: [Category]
   
   ### Architecture Detection
   - **Ortho detected:** [style] @ [confidence]
   - **Manual assessment using rubric:**
     - Clear layer structure: [Yes/No]
     - Dependency direction: [Correct/Reversed/Mixed]
     - Layer cohesion: [High/Medium/Low]
     - Expected confidence band: [0.0–0.45 (UNKNOWN)|0.45–0.65|0.65–0.85|0.85–1.0]
   - **Verdict:** [ACCURATE|ACCEPTABLE|INACCURATE]
   - **Evidence:** [specific file examples or architectural observations]
   
   ### Subsystem Detection
   - **Ortho found:** M subsystems, avg size X files, singleton rate Y%
   - **Manual expectation:** ~N subsystems (reasoning)
   - **Verdict:** [ACCURATE (within 15%)|OVERSEGMENTED (>20% more than expected)|UNDERSEGMENTED (>20% fewer)]
   - **Quality:** subsystems are [logically cohesive|noisy|missing key boundaries]
   
   ### Debt Scoring
   - **Ortho score:** Y
   - **Manual quick assessment:** [High|Medium|Low] debt (reasoning: circular deps, long files, etc.)
   - **Agreement:** [Yes|Partial|No]
   ```
3. Compile summary in `.ases/evidence/spot-checks-summary.md`:
   - Architecture accuracy: X% ACCURATE + Y% ACCEPTABLE (goal: ≥80% ACCURATE + ACCEPTABLE combined)
   - Subsystem accuracy: Z% within expected range
   - Debt scoring agreement: W% match
   - Notable patterns (e.g., "Microservices detected ≥90% accurately; Flat architecture 60% accurate")

**Acceptance:** 
- Rubric completed for ≥8 repos with category stratification
- All repos have explicit verdict (ACCURATE/ACCEPTABLE/INACCURATE)
- Summary has accuracy % by style + category
- Evidence preserved: specific file paths, architectural observations

---

## Expected Test Metrics & KPIs

### AC1 (Repo Selection)
- Sampling algorithm: deterministic (fixed seed=42)
- Sample size: ≥50 repos (target 100)
- Category coverage: all 6 categories represented (≥8 repos each)
- Clone success rate: ≥95%
- Metadata completeness: 100% (all fields populated for selected repos)

### AC2 (Batch Architecture Analysis)
- **Completion Rate:** ≥95% repos analyzed without fatal error
- **KPI Completeness:** all rows have values for: arch_style, arch_confidence, layers_detected, subsystems_found, subsystem_avg_size, singleton_rate, scan_time_sec, analysis_time_sec
- **Failure Classification:** all errors assigned to one of 9 failure types
- **Time Per Repo:** mean scan <120s, mean analysis <60s, p95 total <300s
- **Architecture Confidence:** mean confidence ≥0.5, median confidence ≥0.6
- **Subsystem Stats:** mean subsystems 8–15, mean avg_size 20–50 files, singleton_rate <30%

### AC3 (Intent Coverage)
- Utterance set: ≥40 distinct intents across 4 types (feature_dev, bug_fix, refactor, analysis)
- Router success rate: ≥80% (confidence ≥0.7)
- Coverage by type: each intent type ≥75% success rate
- Success rate variance: no type >15 percentage points below mean

### AC4 (Token Baseline)
- Sample size: ≥250 context assemblies (5 per repo × ≥50 repos)
- Completeness: all rows have tokens, budget_fill_pct, time_ms
- Token statistics: mean, median, std dev, p95 all computed
- Outlier detection: identify repos >2σ above mean (document reasons)

### AC5 (Rubric-Based Spot-Checks)
- Repos audited: ≥8 with category stratification
- Rubric completeness: 100% (all 3 dimensions: architecture, subsystem, debt for each repo)
- Architecture accuracy: ≥80% rated ACCURATE or ACCEPTABLE
- Subsystem accuracy: ≥75% within 20% of expected count
- Debt scoring agreement: ≥70% match
- Evidence: each repo has specific file examples or observations

---

## Known Limitations

- **No LLM in scope:** Only validating Phases 1–3. Phase 4 (prompt assembly, compression, ranker) not tested.
- **Manual audit subjective:** Rubric is structured, but "correct" architecture calls remain a judgment call.
- **GitHub bias:** Sample is public GitHub repos. Private codebases, closed-source, non-GitHub sources excluded.
- **One-time snapshot:** Benchmarks capture one moment in time. Reproducible with same seed, but not continuous.

---

## Success Definition

- [x] ≥50 public Python repos sampled and analyzed
- [x] Metrics CSV complete (repos × 16 columns)
- [x] Intent coverage ≥80% (router success)
- [x] Token baseline computed (mean, median, p95, outliers)
- [x] Spot-check rubric applied to ≥8 repos with evidence
- [x] Summary report: BENCHMARKS-REPORT.md (findings + recommendations)

---

## Rollback (If Needed)

No production code changes. Benchmarks are pure analysis.
- Delete `.ases/tasks/task-015-repo-benchmarks/`
- Delete `.ases/evidence/task-015/` (all results)
- No git cleanup needed.

---

## Determinism & Reproducibility

- Sampling seed: `random.seed(42)` in benchmark script
- GitHub search query fixed: same language/stars/date filters
- Ortho version: frozen at task-014 commit (no new code)
- Environment: Python 3.10+, dependencies from task-014 pyproject.toml

Same inputs → same 100 repos → same metrics (slight variation in seconds only).

---

## Evidence Contract

For each AC, store artifact in `.ases/evidence/task-015/`:

| AC | Artifact | Format | Owner | Purpose |
|----|----------|--------|-------|---------|
| AC1 | repo-list.json | JSON array | BUILDER | Sampled repos with metadata (category, size, stars) |
| AC1 | exclusions.json | JSON | BUILDER | Skipped repos + reasons (category + reason for each) |
| AC2 | results.csv | CSV | BUILDER | KPI metrics per repo (schema defined in AC2) |
| AC2 | results/*.log | Text | BUILDER | Ortho scan/analyze output per repo |
| AC2 | errors/*.error | Text | BUILDER | Failure details classified by failure_type |
| — | failure-taxonomy-TEMPLATE.md | Markdown | Reference | 9 failure types with decision tree (Clone, Scan, Parser, Graph, Architecture, Intent Router, Timeout, OOM, Unknown) |
| AC3 | intent-coverage.json | JSON | BUILDER | Coverage stats by intent type + overall success rate |
| AC4 | token-baseline.csv | CSV | BUILDER | Token samples (repo, intent_type, chunks, tokens, budget_fill_pct, time_ms) |
| AC4 | token-stats.json | JSON | BUILDER | Aggregate stats (mean, median, std dev, p95, outliers) |
| AC5 | architecture-scoring-rubric-TEMPLATE.md | Markdown | Reference | Rubric for each style + scoring criteria (Layered, MVC, Hexagonal, Microservices, Flat, Unknown) |
| AC5 | spot-checks.md | Markdown | BUILDER | Detailed rubric assessments for ≥8 repos |
| AC5 | spot-checks-summary.md | Markdown | BUILDER | Aggregate accuracy % by style, category, dimension |
| — | BENCHMARKS-REPORT.md | Markdown | TEST-DESIGNER | Summary findings + KPI highlights + phase 4 targets |
| — | REGRESSION-REPORT.md | Markdown | TEST-DESIGNER | Baseline metrics table + trend tracking template for future runs |
| — | regression-report-TEMPLATE.md | Markdown | Reference | Regression baseline template (reference for REGRESSION-REPORT.md structure) |

---

## Phase 4 Integration

**Regression Report Baseline** (REGRESSION-REPORT.md template):

This benchmark becomes the baseline for measuring future improvements. Future benchmark runs will compare against these metrics:

| KPI | Value | Unit | Source |
|-----|-------|------|--------|
| Repos sampled | N | count | AC1 |
| Clone success rate | X% | % | AC1 |
| Analysis success rate | Y% | % | AC2 |
| Mean architecture confidence | Z | 0.0–1.0 | AC2 |
| Architecture accuracy (from AC5) | W% | % | AC5 |
| Subsystem accuracy (within 20%) | V% | % | AC5 |
| Debt scoring agreement | U% | % | AC5 |
| Mean tokens per context | T | tokens | AC4 |
| P95 tokens per context | S | tokens | AC4 |
| Mean budget fill | R% | % | AC4 |
| Intent routing success rate | Q% | % | AC3 |
| Mean scan time | P | sec | AC2 |
| Mean analysis time | O | sec | AC2 |
| Failure rate by type | [breakdown] | % | AC2 |

Token baseline (AC4) feeds directly into Phase 4 optimization targets:
- Current mean: T tokens/context → Phase 4 goal: 0.8T (20% reduction)
- P95: S tokens → target: 0.9S (outliers compress)
- Budget fill: R% → target: ≤60% (safety margin preserved)

Architecture accuracy (AC5) validates Phase 2 architecture module:
- If ≥80% ACCURATE+ACCEPTABLE by style → proceed to Phase 4 (no changes needed)
- If <80% for specific style → Phase 2 module targeted for improvement before Phase 4

**Trend Tracking (Future Runs):**
Track these metrics across subsequent benchmark runs:
- Architecture accuracy per style (layered, mvc, hex, microservices, flat, unknown)
- Subsystem detection quality (over/under-segmentation)
- Intent routing success by type (feature_dev, bug_fix, refactor, analysis)
- Runtime improvements (scan time, analysis time, total time)
- Token usage changes (mean, p95, outlier count)
- Crash/failure rate by type

---

*Spec version: 1.0 | Created: 2026-07-08*
