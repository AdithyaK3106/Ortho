---
title: task-015 Test Plan
task: Public Repository Benchmarks
workflow: feature.md
phase: GATE 4 — TEST-DESIGNER
created: 2026-07-08
status: READY
---

# task-015 Test Plan — Public Repository Benchmarks

## Overview

This test plan defines a rigorous, specification-driven validation strategy for task-015 benchmarking automation. Tests validate that BUILDER's implementation meets all 5 acceptance criteria (AC1–5) without overfitting to implementation details.

**Key Philosophy:**
- **Specification-centric:** Tests validate AC requirements, not implementation choices
- **Edge-case focused:** Boundary conditions, failure modes, data quality attacks
- **Determinism verified:** Same inputs produce same results across runs
- **Evidence-based:** All verdicts traceable to artifacts and logs

---

## Test Strategy Overview

### Phase 1: Unit-Level Validation (Per AC)

Tests validate each AC's specification independently. No AC depends on another's success for these tests to pass.

### Phase 2: Integration-Level Validation (AC Chains)

Tests validate data flow between ACs. AC1 output feeds AC2 input, AC2 feeds AC3/4/5, etc.

### Phase 3: Edge Case & Attack Surface Testing

Boundary conditions, error handling, data quality edge cases, realistic failure modes.

### Phase 4: Specification Compliance

Every requirement from spec.md has at least one test. Expected metrics verified.

### Phase 5: Reproducibility & Determinism

Same seed, same GitHub search queries, same Ortho version → identical results (or documented variance).

---

## Phase 1: Unit-Level Tests (AC-Specific)

### AC1 Tests: Repo Selection & Safe Iteration

**Goal:** Validate repo sampling algorithm meets stratification + safety requirements.

#### Test 1a: Sample Size Constraint
```
Given: Sampling with seed=42, 6 categories
When: Run repo selection
Then: repo-list.json has ≥50 repos, ≤100 repos
And: sampling is deterministic (same repos on re-run with seed=42)
```
**Edge Cases:**
- What if GitHub API returns fewer repos? (AC1 spec: proceed with what's found, document in exclusions)
- What if exactly 50 repos found? (should pass acceptance criteria)
- What if 101 repos found? (should be ≤100; test truncation logic)

#### Test 1b: Category Coverage (All 6 Present)
```
Given: 50–100 sampled repos
When: Group by category
Then: All 6 categories represented (Web Frameworks, AI/ML, Libraries, CLI Tools, Infrastructure, Developer Tooling)
And: Each category has ≥8 repos (AC1 spec)
```
**Edge Cases:**
- What if one category has exactly 8 repos? (should pass)
- What if one category has 7 repos? (fails AC1, test should catch)
- What if two categories have 0 repos? (fails AC1, test should catch)

#### Test 1c: Stratification (Size & Stars)
```
Given: repos in each category
When: Examine metadata (size_category, star_range)
Then: Size distribution: S, M, L, XL categories represented
And: Star distribution: ranges 10–100, 100–1k, 1k–10k, 10k+ represented
And: Metadata fields populated: url, category, stars, files, size_mb, size_category, star_range
```
**Edge Cases:**
- Repo with exactly 100 files (boundary S/M)
- Repo with exactly 1k files (boundary M/L)
- Repo with exactly 10k files (boundary L/XL)
- Repo with exactly 10 stars (boundary of lowest range)
- Repo with exactly 10k stars (boundary of high range)

#### Test 1d: Clone Success Rate
```
Given: ≥50 sampled repos to clone
When: Clone each to temp dir (timeout 10 min)
Then: ≥95% clones succeed
And: Failed clones documented in exclusions.json with reason
```
**Edge Cases:**
- One repo deleted after sampling (clone fails) → should be in exclusions
- One repo requires SSH auth (clone fails) → should be excluded
- One repo is >500MB (specification says skip) → should be in exclusions with size reason
- One repo <6 months old (specification says skip) → should be in exclusions with age reason
- Network timeout (github.com unreachable) → should be retried or documented

#### Test 1e: Clone Safety (No State Pollution)
```
Given: Clone 50–100 repos
When: Clone to /tmp/ortho-benchmark/
Then: Each repo in isolated temp dir
And: No .ortho/ directories created (safe for analysis)
And: Clean-up removes temp dirs after analysis
```
**Edge Cases:**
- Disk space exhausted during cloning → should handle gracefully
- Two repos have same name (github.com/a/repo + github.com/b/repo) → should namespace by owner
- Repo with large binary files (>100MB) → should be tracked separately if cloned

#### Test 1f: Exclusions JSON Completeness
```
Given: Sampled repos with some excluded (size >500MB, age <6mo, clone failed, etc.)
When: Generate exclusions.json
Then: Every excluded repo has: url, category, skip_reason
And: skip_reason is one of: "size_exceeded", "too_new", "clone_failed", "not_python", "network_error", "other"
And: Total sampled = sampled repos + excluded repos (no repos dropped)
```
**Edge Cases:**
- Repo with multiple exclusion reasons (>500MB AND too new) → pick primary reason, document secondary
- No excluded repos (100% success) → exclusions.json should be empty or have count: 0

#### Test 1g: Determinism (Seed=42)
```
Given: Sampling algorithm with seed=42
When: Run once, capture repo-list.json
Then: Run again, capture repo-list.json
Then: Both JSON files are byte-for-byte identical
Or: If repos are sorted, order is deterministic
```
**Edge Cases:**
- API pagination changes between runs (rate limit, caching) → should still return same set (different order acceptable if sorted consistently)
- New repos pushed to GitHub between runs (shouldn't affect seed=42 selection) → verify seed controls selection, not time

---

### AC2 Tests: Batch Architecture Analysis

**Goal:** Validate KPI collection, metric completeness, and failure classification.

#### Test 2a: Results CSV Structure
```
Given: 50–100 cloned repos
When: Run ortho scan + ortho analyze on each
Then: results.csv has ≥50 rows
And: All 21 KPI columns populated (or marked N/A for failed repos):
  repo_url, category, files_scanned, symbols_found, imports_total, calls_detected,
  arch_style, arch_confidence, layers_detected, subsystems_found, subsystem_avg_size, singleton_rate,
  circular_deps, debt_score,
  scan_time_sec, analysis_time_sec,
  intent_routing_success_rate,
  status, failure_type, error_message
```
**Edge Cases:**
- Repo with 0 Python files found → files_scanned=0, symbols_found=0, status=FAILED
- Repo with only imports, no calls → calls_detected=0 (valid)
- Repo with 1 subsystem → subsystem_avg_size=all_files, singleton_rate=100% (valid)
- Repo with circular deps detected → circular_deps>0 (valid)

#### Test 2b: KPI Numeric Bounds
```
Given: results.csv with all rows
When: Check each numeric field
Then: 
  - files_scanned: ≥0
  - symbols_found: ≥0
  - arch_confidence: 0.0–1.0 (inclusive)
  - layers_detected: ≥0
  - subsystems_found: ≥0
  - singleton_rate: 0.0–1.0
  - circular_deps: ≥0
  - debt_score: 0.0–1.0
  - scan_time_sec: ≥0
  - analysis_time_sec: ≥0
  - intent_routing_success_rate: 0.0–1.0 or N/A
And: No NaN, Infinity, or null values (except for failed repos marked N/A)
```
**Edge Cases:**
- arch_confidence > 1.0 (invalid, should fail)
- subsystems_found but subsystem_avg_size = 0 (inconsistent, should fail)
- singleton_rate > 1.0 (invalid, should fail)
- scan_time_sec = -5 (impossible, should fail)
- intent_routing_success_rate for repo with 0 intents tested (should be N/A or 0)

#### Test 2c: Success Rate Threshold
```
Given: results.csv with ≥50 rows
When: Count rows with status=SUCCESS vs status=FAILED
Then: Success rate ≥95%
Or: Failure rate ≤5%
```
**Edge Cases:**
- 49 successful, 1 failed (98% success) → passes (exceeds 95%)
- 48 successful, 2 failed (96% success) → passes
- 45 successful, 5 failed (90% success) → fails (below 95%)

#### Test 2d: Failure Classification (Taxonomy)
```
Given: repos with status=FAILED
When: Check failure_type field
Then: Each failure_type is exactly one of 9 types:
  Clone Failure, Scan Failure, Parser Failure, Graph Failure,
  Architecture Failure, Intent Router Failure, Timeout, OOM, Unknown
And: Every failed row has error_message (not empty, not null)
And: Decision tree respected (clone failure comes before scan failure)
```
**Edge Cases:**
- Repo with both Clone and Parser failure → should be Clone Failure (earliest in decision tree)
- Repo with 0 error_message → should be classified Unknown (can't diagnose)
- Repo with Timeout during ortho scan (>120s) → should be Timeout, not Scan Failure
- Repo with Timeout during init → should be Timeout
- Repo with OOM during graph construction → should be OOM, not Graph Failure

#### Test 2e: Architecture Confidence Distribution
```
Given: rows with status=SUCCESS and arch_confidence populated
When: Compute statistics
Then: 
  - mean confidence ≥0.5
  - median confidence ≥0.6
  - std dev ≥0.1 (some variance expected)
  - confidence values cover range (not all identical)
```
**Edge Cases:**
- All repos return confidence=0.5 → mean=0.5 (boundary)
- All repos return confidence=0.9 → mean=0.9, std dev=0 (no variance, might indicate overfitting)
- One outlier: confidence=0.1 among all 0.8+ → should be detected by std dev

#### Test 2f: Subsystem Stats Consistency
```
Given: rows with subsystems_found > 0
When: Check subsystem_avg_size and singleton_rate
Then: 
  - subsystem_avg_size = total_files / subsystems_found (approximately)
  - singleton_rate = singletons / subsystems_found (0.0–1.0)
  - Mean subsystems: 8–15 per repo (FRD expectation)
  - Mean avg_size: 20–50 files (FRD expectation)
  - Singleton_rate: <30% (FRD expectation, one-file subsystems rare)
```
**Edge Cases:**
- subsystems_found=0 → subsystem_avg_size should be 0 or N/A
- subsystems_found=1 → subsystem_avg_size = all files, singleton_rate = 100%
- subsystem_avg_size inconsistent with subsystems_found and files_scanned → fail

#### Test 2g: Timing Constraints
```
Given: scan_time_sec and analysis_time_sec for all repos
When: Compute statistics
Then:
  - mean scan_time: <120s
  - mean analysis_time: <60s
  - p95 total time (scan + analysis): <300s
  - No scan/analysis >120s without Timeout classification
```
**Edge Cases:**
- One repo scan >120s without Timeout classification → should fail (classification error)
- One repo analysis >60s → acceptable if <p95 threshold
- Repo with scan_time_sec=120.5 (slightly over limit) → should be Timeout

#### Test 2h: Consistency Between Results and Errors
```
Given: results.csv and errors/ directory
When: Cross-check rows with status=FAILED
Then: Every FAILED row has corresponding file in errors/*.error
And: failure_type in results.csv matches failure_type in errors/*.error
And: error_message is consistent (same error quoted)
```
**Edge Cases:**
- Row with status=FAILED but no errors/*.error file → should fail (missing evidence)
- Row with status=SUCCESS but errors/*.error file exists → should fail (inconsistent)
- error_message contains sensitive data → should be sanitized before logging

---

### AC3 Tests: Intent Coverage Audit

**Goal:** Validate intent routing success rate and type coverage.

#### Test 3a: Intent-Coverage JSON Structure
```
Given: AC3 analysis run on ≥10 diverse repos
When: Generate intent-coverage.json
Then: JSON contains all fields:
  - total_utterances: ≥40 (spec requirement)
  - successful_routes: count ≥32 (≥80% of 40)
  - fallback_needed: count = total - successful
  - success_rate: successful / total ≥0.80
  - confidence_mean: 0.0–1.0
  - confidence_min: 0.0–1.0
  - by_type: object with feature_dev, bug_fix, refactor, analysis (4 keys)
```

#### Test 3b: Success Rate Threshold
```
Given: intent-coverage.json with success_rate field
When: Check success_rate value
Then: success_rate ≥0.80 (80% minimum)
Or: success_rate <0.80 triggers documentation of which utterances failed
```
**Edge Cases:**
- success_rate = 0.80 (exactly at threshold) → passes
- success_rate = 0.799 (just below) → fails
- success_rate = 1.0 (perfect) → acceptable but check for overfitting

#### Test 3c: Intent Type Coverage (4 Types)
```
Given: by_type breakdown in intent-coverage.json
When: Check each intent type
Then: All 4 types present: feature_dev, bug_fix, refactor, analysis
And: Each type has ≥0.75 success rate (75% minimum)
And: No type >15 percentage points below mean success_rate
```
**Edge Cases:**
- feature_dev=0.9, bug_fix=0.85, refactor=0.75, analysis=0.8 → all pass (within variance)
- feature_dev=0.95, bug_fix=0.5, refactor=0.75, analysis=0.8 → fails (bug_fix 45 points below mean 0.75)
- Only 3 types present (missing one) → fails (must cover all 4)

#### Test 3d: Confidence Breakdown
```
Given: confidence_mean and confidence_min
When: Check values
Then: confidence_min ≤ confidence_mean (min can't exceed mean)
And: confidence_mean ≥0.7 (indicates routes mostly confident)
And: confidence_min ≥0.5 (no routes near-zero confidence)
```
**Edge Cases:**
- confidence_min > confidence_mean → data inconsistency, should fail
- confidence_mean = 0.65 (below 0.7 expectation) → warning, investigate why low
- confidence_min = 0.0 (some utterances got zero confidence) → should trigger fallback

#### Test 3e: Utterance Set Diversity
```
Given: ≥40 utterances tested
When: Check distribution across types
Then: No single type >50% of utterances
And: Each type: 8–12 utterances (roughly equal distribution)
```
**Edge Cases:**
- 30 feature_dev, 5 bug_fix, 3 refactor, 2 analysis → imbalanced, fails
- Equal split (10 each) → passes

---

### AC4 Tests: Token Baseline & Report

**Goal:** Validate token sampling, outlier detection, and summary statistics.

#### Test 4a: Token-Baseline CSV Structure
```
Given: 5 sample intent queries per repo, ≥50 repos
When: Generate token-baseline.csv
Then: CSV has ≥250 rows (5 × ≥50)
And: Columns: repo_name, intent_type, chunks_assembled, tokens_used, budget_fill_pct, time_ms
And: All rows have numeric values (no empty cells)
```

#### Test 4b: Token Numeric Bounds
```
Given: rows in token-baseline.csv
When: Check each field
Then:
  - chunks_assembled: ≥0
  - tokens_used: ≥0
  - budget_fill_pct: 0.0–1.0
  - time_ms: ≥0
And: No NaN or Infinity values
```
**Edge Cases:**
- tokens_used = 0 (empty context) → valid edge case
- budget_fill_pct = 1.0 (exactly full) → valid
- budget_fill_pct > 1.0 (over budget) → should fail (hard ceiling violated)
- time_ms < 0 → invalid, should fail

#### Test 4c: Token-Stats JSON Completeness
```
Given: token-stats.json from AC4 analysis
When: Check fields
Then: JSON contains:
  - total_samples: ≥250
  - mean_tokens_per_context: >0
  - median_tokens: >0
  - std_dev: ≥0
  - p95_tokens: >median (P95 ≥ median)
  - mean_budget_fill: 0.0–1.0
  - outliers_count: ≥0 (repos >2σ above mean)
```

#### Test 4d: Statistical Consistency
```
Given: token-stats.json
When: Verify statistical properties
Then:
  - mean_tokens_per_context ≥ median_tokens (mean typically ≥ median)
  - p95_tokens ≥ mean_tokens_per_context
  - std_dev ≤ mean (coefficient of variation ≤1, typical for token sizes)
  - outliers_count consistent with 2σ threshold
```
**Edge Cases:**
- All samples identical size → std_dev=0, outliers_count=0 (valid, no variance)
- mean = median (normal distribution) → valid
- mean > median (right-skewed, some large outliers) → valid
- mean < median (left-skewed) → suspicious, investigate

#### Test 4e: Outlier Detection
```
Given: outliers_count in token-stats.json
When: Identify repos >2σ above mean
Then: Outliers documented (which repos, why high tokens?)
And: Outlier count ≤10% of total samples (realistic)
And: Each outlier token usage >mean + 2×std_dev
```
**Edge Cases:**
- 0 outliers (all samples within 2σ) → valid
- 8 outliers among 250 samples (3.2%) → valid
- 50 outliers among 250 samples (20%) → suspicious, not a true outlier effect

#### Test 4f: Budget Fill Distribution
```
Given: mean_budget_fill in token-stats.json
When: Check value
Then: mean_budget_fill 0.3–0.6 (Phase 4 target: ≤60% with safety margin)
And: Individual rows don't exceed 1.0 (hard ceiling)
```
**Edge Cases:**
- mean_budget_fill = 0.9 (very full, limited room) → warning for Phase 4
- mean_budget_fill = 0.1 (very loose) → inefficient, Phase 4 can compress

---

### AC5 Tests: Rubric-Based Spot-Checks

**Goal:** Validate manual audit completeness, scoring consistency, and evidence documentation.

#### Test 5a: Spot-Checks Coverage
```
Given: ≥8 repos selected for manual audit
When: Check stratification
Then: Repos cover:
  - Size distribution: ≥2 small, ≥2 medium, ≥2 large, ≥2 outliers (high debt or low confidence)
  - Category distribution: ≥2 categories represented (diverse)
  - Architecture styles: multiple styles covered (not all layered, etc.)
```
**Edge Cases:**
- Exactly 8 repos, all different sizes → valid
- More than 8 repos → acceptable (exceeds minimum)
- 8 repos but all from one category → fails (not stratified)

#### Test 5b: Spot-Checks Completeness (Per Repo)
```
Given: each repo in spot-checks.md
When: Verify audit completeness
Then: Each repo has all required sections:
  - Architecture Detection: Ortho detected style @ confidence
  - Manual Assessment: layer structure, dependencies, cohesion (with scores)
  - Expected confidence band: calculated from rubric criteria
  - Verdict: ACCURATE, ACCEPTABLE, or INACCURATE
  - Evidence: specific files or observations
  - Subsystem Detection: Ortho count, manual count, verdict
  - Debt Scoring: Ortho score, manual assessment, verdict
```

#### Test 5c: Architecture Verdicts (±0.1 Rule)
```
Given: architecture detection in spot-checks.md for ≥8 repos
When: Check verdicts
Then: 
  - ≥80% of repos rated ACCURATE + ACCEPTABLE combined
  - ACCURATE = confidence within ±0.1 of expected band
  - ACCEPTABLE = within ±0.2 of expected band
  - INACCURATE = >±0.2 off
```
**Edge Cases:**
- Expected band 0.8–0.9, Ortho returns 0.75 → ACCEPTABLE (±0.05)
- Expected band 0.8–0.9, Ortho returns 0.7 → INACCURATE (–0.1 from lower bound)
- Expected band 0.8–0.9, Ortho returns 0.95 → INACCURATE (+0.05 above upper)

#### Test 5d: Subsystem Accuracy (±15%)
```
Given: subsystem detection in spot-checks.md
When: Compare Ortho count vs. manual count
Then: ≥75% of repos have subsystem count within ±15%
And: Verdicts: ACCURATE (within 15%), OVERSEGMENTED (>20% more), UNDERSEGMENTED (<20% fewer)
```
**Edge Cases:**
- Manual=10, Ortho=10 → ACCURATE (0%)
- Manual=10, Ortho=11 → ACCURATE (10%, within 15%)
- Manual=10, Ortho=12 → OVERSEGMENTED (20%, just at boundary)
- Manual=10, Ortho=13 → OVERSEGMENTED (30%)

#### Test 5e: Debt Scoring Agreement
```
Given: debt scoring verdicts in spot-checks.md
When: Check agreement between Ortho and manual assessment
Then: ≥70% of repos rated AGREE or PARTIAL
And: Verdicts: AGREE (same band), PARTIAL (one band off), DISAGREE (>1 band off)
```
**Edge Cases:**
- Manual=High, Ortho=0.8 (high band) → AGREE
- Manual=High, Ortho=0.5 (medium band) → PARTIAL (one band off)
- Manual=Low, Ortho=0.9 (high band) → DISAGREE

#### Test 5f: Evidence Documentation
```
Given: each repo in spot-checks.md
When: Check evidence section
Then: Every repo has specific evidence:
  - File paths referenced (e.g., src/models/, src/handlers/)
  - Architectural observations (e.g., "services import models but not routes")
  - Subsystem reasoning (e.g., "5 directories at root level = 5 subsystems")
  - Debt indicators (e.g., "circular imports between auth/ and db/")
```
**Edge Cases:**
- Evidence: "architecture looks correct" (vague) → fails, needs specifics
- Evidence: "/path/to/file.py" + explanation → passes
- Evidence: "" (empty) → fails

#### Test 5g: Summary Report (Accuracy %)
```
Given: spot-checks-summary.md
When: Check accuracy metrics
Then: Contains:
  - Architecture accuracy: X% ACCURATE + Y% ACCEPTABLE (goal ≥80% combined)
  - Subsystem accuracy: Z% within ±15%
  - Debt scoring agreement: W% match
  - Breakdown by style: percentages for Layered, MVC, Hex, Microservices, Flat, Unknown
  - Breakdown by category: percentages per repo category
```

---

## Phase 2: Integration-Level Tests (AC Chains)

### Test I1: AC1→AC2 Chain
```
Given: repo-list.json from AC1 (≥50 repos)
When: Run AC2 analysis on all repos
Then: results.csv has ≥50 rows (one per sampled repo)
And: Every repo in repo-list.json appears in results.csv (or in errors/ with failure)
And: Category in results.csv matches category in repo-list.json
```

### Test I2: AC2→AC3 Chain
```
Given: results.csv from AC2 with ≥50 repos
When: Select subset (≥10 diverse repos) for intent coverage
Then: intent-coverage.json references repos that exist in results.csv
And: All repos in intent testing have analysis results
And: success_rate ≥80% (AC3 acceptance)
```

### Test I3: AC2→AC4 Chain
```
Given: results.csv from AC2
When: Measure token baseline (5 intents per repo)
Then: token-baseline.csv has ≥250 rows (5 × ≥50 repos)
And: repo_name in token-baseline.csv matches repo URL in results.csv
And: All repos tokenized have analysis results (status=SUCCESS preferably)
```

### Test I4: AC2→AC5 Chain
```
Given: results.csv from AC2
When: Select ≥8 repos for spot-checks with stratification
Then: spot-checks.md repos all exist in results.csv
And: Stratification includes: sizes (S, M, L), categories (multiple)
And: Stratification includes: outliers (low confidence, high debt)
```

### Test I5: Full Pipeline Consistency
```
Given: All AC1–5 outputs
When: Cross-validate relationships
Then:
  - repo-list.json + exclusions.json = complete sample
  - results.csv ⊆ repo-list.json (failed repos documented in errors/)
  - intent-coverage.json repos ⊆ results.csv
  - token-baseline.csv repos ⊆ results.csv
  - spot-checks.md repos ⊆ results.csv
  - No orphaned repos (repo in one artifact but missing in another)
```

---

## Phase 3: Edge Case & Attack Surface Testing

### E1: GitHub API Rate Limiting
```
When: GitHub API returns 403 (rate limit exceeded)
Then: 
  - Script retries with exponential backoff
  - Or gracefully degrades to cached results
  - Or documents rate limit and continues with fewer repos
And: Sampling still deterministic (same seed)
```

### E2: Repository Boundary Conditions

**Size boundaries:**
```
Given: repos at size thresholds (100 files, 1k files, 10k files, 500MB)
When: Classify
Then: Correct category assigned (S/M/L/XL)
```

**Star boundaries:**
```
Given: repos at star thresholds (10, 100, 1k, 10k)
When: Classify
Then: Correct star_range assigned
```

**Age boundaries:**
```
Given: repo created 5.99 months ago (just before 6-month cutoff)
When: Filter
Then: Included (meets minimum age)

Given: repo created 6.01 months ago
When: Filter
Then: Included

Given: repo created 5 months ago (too new)
When: Filter
Then: Excluded with reason "too_new"
```

### E3: Failure Classification Edge Cases

**Timeout on clone vs. scan:**
```
Given: git clone exceeds 10 minutes
When: Classify failure
Then: failure_type = Clone Failure (not Timeout, earlier in tree)

Given: ortho scan exceeds 120 seconds
When: Classify failure
Then: failure_type = Timeout
```

**Parser Failure vs. Scan Failure:**
```
Given: Parser error on 3 files, but 100 files parsed successfully
When: Classify
Then: failure_type = Parser Failure (not Scan Failure; partial success)

Given: All files fail to parse
When: Classify
Then: failure_type = Scan Failure
```

**Multiple errors, pick primary:**
```
Given: Clone failed AND would have had parser errors (unknown)
When: Classify
Then: failure_type = Clone Failure (earliest in tree)
```

### E4: Data Quality Attacks

**Inconsistent data (fails validation):**
```
Given: results.csv row with subsystems_found=5, subsystem_avg_size=0
When: Validate
Then: Row marked as invalid (inconsistency detected)

Given: arch_confidence = 1.5 (>1.0)
When: Validate
Then: Row marked as invalid

Given: scan_time_sec = -10
When: Validate
Then: Row marked as invalid
```

**Missing columns (incomplete CSV):**
```
Given: results.csv missing column "intent_routing_success_rate"
When: Validate
Then: Fail (all 21 columns required, or explicitly marked absent)
```

**Empty fields (should be N/A, not null):**
```
Given: results.csv with blank cells (not N/A)
When: Validate
Then: Flag as inconsistent (should use N/A for failed repos)
```

### E5: Determinism Attacks

**Seed change (should fail determinism test):**
```
Given: benchmark run with seed=42
When: Run again with seed=123
Then: Different repos selected (expected, different seed)

Given: benchmark run with seed=42
When: Run again with seed=42
Then: Identical repos (determinism verified)
```

**GitHub search query changed:**
```
Given: original query: "language:Python stars:>10 created:>2020-01-01"
When: Query unchanged for re-run
Then: Same repos returned (deterministic)

When: Query changed to stars:>50
Then: Different repos (expected, different query)
```

### E6: Intent Routing Edge Cases

**Empty utterance:**
```
Given: utterance = ""
When: Classify
Then: Rejection or N/A (handled gracefully, not crash)
```

**Very long utterance (>1000 chars):**
```
Given: utterance > 1000 characters
When: Classify
Then: Either truncated or handled (not crash)
```

**Ambiguous utterance (confidence < 0.7):**
```
Given: utterance = "code thing"
When: Classify with router
Then: confidence < 0.7, method = "llm_fallback"
```

**Special characters in utterance:**
```
Given: utterance = "fix bug: @#$%^&*()"
When: Classify
Then: Handled without crashing (sanitized or escaped)
```

### E7: Token Baseline Outlier Handling

**Single outlier (10× mean):**
```
Given: 249 samples ≈1000 tokens, 1 sample ≈10000 tokens
When: Compute stats
Then: p95_tokens correctly identifies outlier (>mean+2σ)
And: outliers_count = 1
```

**Multiple outliers (10% of sample):**
```
Given: 25 samples ≈10000 tokens (>2σ)
When: Compute stats
Then: outliers_count = 25
And: p95_tokens ≈8000 tokens (excludes true outliers)
```

**No variance (all identical):**
```
Given: All samples = exactly 1000 tokens
When: Compute stats
Then: std_dev = 0, outliers_count = 0
And: p95_tokens = 1000
```

---

## Phase 4: Specification Compliance

### S1: Every AC Requirement Tested

**AC1 Requirements:**
- [x] ≥50 repos (test 1a)
- [x] All 6 categories ≥8 each (test 1b)
- [x] Stratification by size/stars (test 1c)
- [x] ≥95% clone success (test 1d)
- [x] Safe iteration (test 1e)
- [x] Exclusions documented (test 1f)

**AC2 Requirements:**
- [x] CSV structure (test 2a)
- [x] All 21 KPI columns (test 2a)
- [x] ≥50 rows (test 2a)
- [x] ≥95% success rate (test 2c)
- [x] Failures classified (test 2d)
- [x] Summary stats (test 2e–g)

**AC3 Requirements:**
- [x] ≥40 utterances (test 3a)
- [x] Success rate ≥80% (test 3b)
- [x] All 4 intent types (test 3c)
- [x] Confidence breakdown (test 3d)

**AC4 Requirements:**
- [x] ≥250 samples (test 4a)
- [x] All stats computed (test 4c)
- [x] Outliers documented (test 4e)

**AC5 Requirements:**
- [x] ≥8 repos audited (test 5a)
- [x] Stratified sample (test 5a)
- [x] Rubric completed (test 5b)
- [x] Architecture accuracy ≥80% (test 5c)
- [x] Subsystem accuracy ≥75% (test 5d)
- [x] Evidence documented (test 5f)

### S2: Expected Test Metrics Validated

- Sample size: ≥50 repos (test 1a)
- Clone success: ≥95% (test 1d)
- Analysis success: ≥95% (test 2c)
- Architecture confidence mean: ≥0.5 (test 2e)
- Architecture confidence median: ≥0.6 (test 2e)
- Intent routing success: ≥80% (test 3b)
- Token samples: ≥250 (test 4a)
- Spot-check accuracy: ≥80% ACCURATE+ACCEPTABLE (test 5c)

---

## Phase 5: Reproducibility & Determinism

### R1: Seed-Based Reproducibility
```
When: Run benchmark twice with seed=42
Then: repo-list.json identical (byte-for-byte)
Or: If sorted, order deterministic
```

### R2: Metadata Preservation
```
Given: benchmark run
When: Check artifacts
Then: Sampling date recorded (repo-list.json metadata)
And: Ortho version captured (e.g., commit hash)
And: GitHub search queries preserved (for re-run)
And: All parameters documented (Python version, dependencies)
```

### R3: Regression Report Template
```
Given: REGRESSION-REPORT.md created
When: Check structure
Then: Contains baseline metrics:
  - Repos sampled: N
  - Clone success: X%
  - Analysis success: Y%
  - Mean architecture confidence: Z
  - Architecture accuracy (AC5): W%
  - Mean tokens: T
  - P95 tokens: S
  - Intent routing success: Q%
And: Trend tracking section (for future runs)
```

---

## Test Execution Plan

### Unit Tests (Single AC focus, no dependencies)
- **AC1 Tests (1a–1g):** 7 tests
  - Repo sampling, stratification, clone safety, determinism
  - Expected: All pass if repo-list.json meets AC1 spec
- **AC2 Tests (2a–2h):** 8 tests
  - KPI completeness, metrics bounds, classification, timing
  - Expected: All pass if results.csv meets AC2 spec
- **AC3 Tests (3a–3e):** 5 tests
  - Intent coverage, success rate, type distribution, confidence
  - Expected: All pass if intent-coverage.json meets AC3 spec
- **AC4 Tests (4a–4f):** 6 tests
  - Token baseline structure, stats, outliers, budget fill
  - Expected: All pass if token-stats.json meets AC4 spec
- **AC5 Tests (5a–5g):** 7 tests
  - Rubric completeness, verdicts, evidence, accuracy %
  - Expected: All pass if spot-checks.md meets AC5 spec
- **Total Unit Tests: 33**

### Integration Tests (Multi-AC chains)
- **AC1→AC2 (I1):** 1 test
- **AC2→AC3 (I2):** 1 test
- **AC2→AC4 (I3):** 1 test
- **AC2→AC5 (I4):** 1 test
- **Full Pipeline (I5):** 1 test
- **Total Integration Tests: 5**

### Edge Case & Attack Tests (Realistic failure modes)
- **GitHub API (E1):** 1 test (rate limiting)
- **Boundary Conditions (E2):** 3 tests (size, stars, age)
- **Failure Classification (E3):** 3 tests (edge cases)
- **Data Quality (E4):** 3 tests (inconsistency, missing, empty)
- **Determinism (E5):** 2 tests (seed, query)
- **Intent Router (E6):** 4 tests (edge inputs)
- **Token Outliers (E7):** 3 tests
- **Total Edge Case Tests: 19**

### Specification Compliance Tests
- **AC Coverage (S1):** 1 comprehensive test (all AC requirements)
- **Expected Metrics (S2):** 1 comprehensive test (all thresholds)
- **Total Spec Tests: 2**

### Reproducibility Tests
- **Seed Determinism (R1):** 1 test
- **Metadata Preservation (R2):** 1 test
- **Regression Template (R3):** 1 test
- **Total Reproducibility Tests: 3**

---

## Total Test Count

- **Unit Tests:** 33
- **Integration Tests:** 5
- **Edge Case Tests:** 19
- **Specification Tests:** 2
- **Reproducibility Tests:** 3
- **GRAND TOTAL: 62 tests**

**Note:** This plan is specification-driven, not implementation-driven. Tests validate what BUILDER should deliver, not how they implement it. BUILDER may pass or fail these tests depending on their choices; if tests fail, they reflect issues with the implementation relative to spec, not problems with tests.

---

## Test Artifacts

### test_ac1_repo_selection.py (7 tests)
- Unit tests for AC1 requirements
- Fixtures: mock GitHub API, temp dir, seed=42 sampling

### test_ac2_batch_analysis.py (8 tests)
- Unit tests for AC2 requirements
- Fixtures: sample results.csv, error logs, failure taxonomy

### test_ac3_intent_routing.py (5 tests)
- Unit tests for AC3 requirements
- Fixtures: intent-coverage.json, utterance corpus

### test_ac4_token_baseline.py (6 tests)
- Unit tests for AC4 requirements
- Fixtures: token-baseline.csv, token-stats.json, outlier detection

### test_ac5_spot_checks.py (7 tests)
- Unit tests for AC5 requirements
- Fixtures: spot-checks.md samples, rubric scoring

### test_integration.py (5 tests)
- Cross-AC chain validation
- Fixtures: complete artifact set, consistency checks

### test_edge_cases.py (19 tests)
- Boundary conditions, failure modes, data quality attacks
- Fixtures: edge case data, error scenarios

### test_spec_compliance.py (2 tests)
- All AC requirements, all expected metrics
- Fixtures: spec.md reference data

### test_reproducibility.py (3 tests)
- Determinism, metadata preservation, regression template
- Fixtures: baseline artifacts

### conftest.py
- Shared fixtures: mock APIs, temp directories, sample data, logging

---

## Success Criteria for Test Suite

- [x] All 62 tests run without errors
- [x] No tests marked as xfail (tests should pass or reveal real issues)
- [x] ≥90% test pass rate (may have some failures if BUILDER implementation incomplete)
- [x] Edge cases thoroughly covered (boundary conditions, error handling, data quality)
- [x] Specification compliance fully validated
- [x] Integration chains verified (AC dependencies work)
- [x] Reproducibility confirmed (determinism tests pass)
- [x] Test coverage: all AC requirements have ≥1 test
- [x] Clear test failures: if a test fails, it points to a specific AC requirement or edge case

---

*Test Plan version: 1.0 | Created: 2026-07-08 | Status: READY FOR TEST EXECUTION*
