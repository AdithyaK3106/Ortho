---
title: Regression Report — Benchmark Baseline
task: task-015
created: 2026-07-08
status: TEMPLATE
---

# Regression Report — task-015 Baseline

This document captures the baseline metrics for the task-015 benchmark. Future benchmark runs will compare against these values to detect regressions or improvements.

**Baseline Date:** [YYYY-MM-DD from first benchmark run]  
**Ortho Commit:** [git commit hash]  
**Repos Sampled:** [N]  
**Categories Represented:** [list]

---

## KPI Baseline Table

| KPI | Value | Unit | Source AC | Notes |
|-----|-------|------|-----------|-------|
| **Sampling & Infrastructure** | | | | |
| Repos sampled | [N] | count | AC1 | Total distinct repos analyzed |
| Clone success rate | [X]% | % | AC1 | Repos successfully cloned / total attempted |
| Categories sampled | [6] | count | AC1 | All 6 categories represented |
| Average repo size | [S] | MB | AC1 | Median size of sampled repos |
| **Analysis Success** | | | | |
| Analysis success rate | [Y]% | % | AC2 | Repos completed full pipeline |
| Scan + analyze complete | [Z]% | % | AC2 | No timeouts or crashes |
| Failure rate by type | [See breakdown] | % | AC2 | Count of each failure type |
| **Architecture Detection** | | | | |
| Mean architecture confidence | [C] | 0.0–1.0 | AC2 | Average confidence score across all repos |
| Median architecture confidence | [M] | 0.0–1.0 | AC2 | Median confidence (50th percentile) |
| Confidence std dev | [σ] | — | AC2 | Standard deviation (spread) |
| Confidence min | [MIN] | 0.0–1.0 | AC2 | Minimum detected confidence |
| Confidence max | [MAX] | 0.0–1.0 | AC2 | Maximum detected confidence |
| **Architecture Accuracy (from Manual Audit)** | | | | |
| Architecture ACCURATE % | [A]% | % | AC5 | Ortho confidence within ±0.1 of expected |
| Architecture ACCEPTABLE % | [B]% | % | AC5 | Ortho confidence within ±0.2 of expected |
| Architecture INACCURATE % | [C]% | % | AC5 | Ortho confidence >±0.2 off |
| Layered accuracy | [%] | % | AC5 | Accuracy for Layered style specifically |
| MVC accuracy | [%] | % | AC5 | Accuracy for MVC style specifically |
| Hexagonal accuracy | [%] | % | AC5 | Accuracy for Hexagonal style specifically |
| Microservices accuracy | [%] | % | AC5 | Accuracy for Microservices style specifically |
| Flat accuracy | [%] | % | AC5 | Accuracy for Flat style specifically |
| Unknown accuracy | [%] | % | AC5 | Accuracy for UNKNOWN classification |
| **Subsystem Detection** | | | | |
| Mean subsystems per repo | [M] | count | AC2 | Average subsystems found |
| Median subsystems per repo | [Med] | count | AC2 | Median subsystems (50th percentile) |
| Mean subsystem size | [S] | files | AC2 | Average files per subsystem |
| Subsystem singleton rate | [P]% | % | AC2 | % of subsystems with only 1 file |
| Subsystem accuracy (within ±15%) | [Q]% | % | AC5 | % of repos within expected ±15% subsystem count |
| Subsystem oversegmented % | [R]% | % | AC5 | % of repos with too many subsystems |
| Subsystem undersegmented % | [S]% | % | AC5 | % of repos with too few subsystems |
| **Debt Scoring** | | | | |
| Mean debt score | [D] | 0.0–1.0 | AC2 | Average debt score |
| Median debt score | [Med] | 0.0–1.0 | AC2 | Median debt score |
| Debt score std dev | [σ] | — | AC2 | Standard deviation |
| Debt scoring agreement % | [E]% | % | AC5 | % repos where Ortho score matches manual assessment |
| Debt scoring partial agreement % | [F]% | % | AC5 | % repos off by one difficulty level |
| **Intent Routing** | | | | |
| Intent coverage success rate | [G]% | % | AC3 | % of utterances classified ≥0.7 confidence |
| Feature dev intent success % | [%] | % | AC3 | Success rate for feature_dev intent type |
| Bug fix intent success % | [%] | % | AC3 | Success rate for bug_fix intent type |
| Refactor intent success % | [%] | % | AC3 | Success rate for refactor intent type |
| Analysis intent success % | [%] | % | AC3 | Success rate for analysis intent type |
| Mean router confidence | [H] | 0.0–1.0 | AC3 | Average confidence of routed intents |
| **Runtime Performance** | | | | |
| Mean scan time | [T1] | sec | AC2 | Average time to run `ortho scan` |
| Median scan time | [T1_med] | sec | AC2 | Median scan time |
| Scan time p95 | [T1_p95] | sec | AC2 | 95th percentile scan time |
| Scan time max | [T1_max] | sec | AC2 | Maximum scan time (slowest repo) |
| Mean analysis time | [T2] | sec | AC2 | Average time to run `ortho analyze` |
| Median analysis time | [T2_med] | sec | AC2 | Median analysis time |
| Analysis time p95 | [T2_p95] | sec | AC2 | 95th percentile analysis time |
| Analysis time max | [T2_max] | sec | AC2 | Maximum analysis time (slowest repo) |
| Mean total time (scan + analyze) | [T_total] | sec | AC2 | Average end-to-end time per repo |
| **Token Usage** | | | | |
| Mean tokens per context | [Tok_mean] | tokens | AC4 | Average context assembly size |
| Median tokens per context | [Tok_med] | tokens | AC4 | Median context size |
| Token std dev | [Tok_σ] | tokens | AC4 | Standard deviation of context size |
| Token p95 | [Tok_p95] | tokens | AC4 | 95th percentile (outliers start here) |
| Token max | [Tok_max] | tokens | AC4 | Maximum context size |
| Mean budget fill % | [Fill_mean]% | % | AC4 | Average % of budget used per context |
| Median budget fill % | [Fill_med]% | % | AC4 | Median budget fill |
| Budget fill p95 % | [Fill_p95]% | % | AC4 | 95th percentile budget fill |
| Outlier repos (>2σ) | [N] | count | AC4 | Repos with unusually large contexts |
| **Failure Analysis** | | | | |
| Clone Failure rate | [%] | % | AC2 | % of repos with Clone Failure |
| Scan Failure rate | [%] | % | AC2 | % of repos with Scan Failure |
| Parser Failure rate | [%] | % | AC2 | % of repos with Parser Failure |
| Graph Failure rate | [%] | % | AC2 | % of repos with Graph Failure |
| Architecture Failure rate | [%] | % | AC2 | % of repos with Architecture Failure |
| Intent Router Failure rate | [%] | % | AC2 | % of repos with Intent Router Failure |
| Timeout rate | [%] | % | AC2 | % of repos with Timeout |
| OOM rate | [%] | % | AC2 | % of repos with Out of Memory |
| Unknown Failure rate | [%] | % | AC2 | % of repos with Unknown error |

---

## Failure Breakdown

| Failure Type | Count | % of Total | Example Repos |
|--------------|-------|-----------|---|
| Clone Failure | [N] | [%] | [up to 3 examples] |
| Scan Failure | [N] | [%] | [up to 3 examples] |
| Parser Failure | [N] | [%] | [up to 3 examples] |
| Graph Failure | [N] | [%] | [up to 3 examples] |
| Architecture Failure | [N] | [%] | [up to 3 examples] |
| Intent Router Failure | [N] | [%] | [up to 3 examples] |
| Timeout | [N] | [%] | [up to 3 examples] |
| OOM | [N] | [%] | [up to 3 examples] |
| Unknown | [N] | [%] | [up to 3 examples] |
| **TOTAL FAILURES** | [N] | [%] | — |
| **SUCCESS** | [N] | [%] | — |

---

## Architecture Accuracy by Style

| Style | Repos Analyzed | ACCURATE % | ACCEPTABLE % | INACCURATE % | Mean Confidence |
|-------|---|---|---|---|---|
| Layered | [N] | [%] | [%] | [%] | [C] |
| MVC | [N] | [%] | [%] | [%] | [C] |
| Hexagonal | [N] | [%] | [%] | [%] | [C] |
| Microservices | [N] | [%] | [%] | [%] | [C] |
| Flat | [N] | [%] | [%] | [%] | [C] |
| Unknown | [N] | [%] | [%] | [%] | [C] |
| **TOTAL** | [N] | [%] | [%] | [%] | [C] |

---

## Repository Category Breakdown

| Category | Repos | Avg Confidence | Success Rate | Mean Subsystems | Debt Score Mean |
|----------|-------|---|---|---|---|
| Web Frameworks | [N] | [C] | [%] | [S] | [D] |
| AI/ML | [N] | [C] | [%] | [S] | [D] |
| Libraries | [N] | [C] | [%] | [S] | [D] |
| CLI Tools | [N] | [C] | [%] | [S] | [D] |
| Infrastructure | [N] | [C] | [%] | [S] | [D] |
| Developer Tooling | [N] | [C] | [%] | [S] | [D] |
| **TOTAL** | [N] | [C] | [%] | [S] | [D] |

---

## Trend Tracking Template (For Future Benchmarks)

When running a new benchmark, compare against this baseline using this format:

| KPI | Baseline | Current | Change | Status |
|-----|----------|---------|--------|--------|
| Architecture accuracy (ACCURATE+ACCEPTABLE) | [%] | [%] | [+/- %] | [↑ Improved / ↓ Regressed / → Stable] |
| Mean architecture confidence | [C] | [C] | [+/- C] | [↑ / ↓ / →] |
| Subsystem accuracy (within ±15%) | [%] | [%] | [+/- %] | [↑ / ↓ / →] |
| Intent routing success rate | [%] | [%] | [+/- %] | [↑ / ↓ / →] |
| Mean scan time | [T] sec | [T] sec | [+/- T] sec | [↑ Slower / ↓ Faster / → Same] |
| Mean analysis time | [T] sec | [T] sec | [+/- T] sec | [↑ / ↓ / →] |
| Mean tokens per context | [Tok] | [Tok] | [+/- Tok] | [↑ More / ↓ Less / →] |
| Failure rate | [%] | [%] | [+/- %] | [↑ Worse / ↓ Better / →] |
| Debt scoring agreement | [%] | [%] | [+/- %] | [↑ / ↓ / →] |

---

## Regression Alert Thresholds

Flag a regression (needs investigation) if any of these change by >5% or as specified:

| KPI | Threshold | Alert When |
|-----|-----------|-----------|
| Architecture accuracy (ACCURATE+ACCEPTABLE) | 5% | Drops below baseline - 5% |
| Intent routing success rate | 5% | Drops below baseline - 5% |
| Failure rate | 5% | Rises above baseline + 5% |
| Mean scan time | 10% | Increases >10% |
| Mean analysis time | 10% | Increases >10% |
| Mean tokens per context | 10% | Increases >10% (violates Phase 4 goal) |

---

## Recommendations for Future Phases

Based on this baseline, note any findings:

1. **Phase 2 Improvements (Architecture Detection):**
   - Accuracy: [Status: Meets expectation / Needs work]
   - Most problematic style: [Style with lowest accuracy]
   - Recommendation: [improve X module, add Y test cases, etc.]

2. **Phase 4 Token Optimization Targets:**
   - Current mean tokens: [Tok_mean]
   - Phase 4 goal (20% reduction): [0.8 × Tok_mean]
   - P95 target (10% reduction): [0.9 × Tok_p95]
   - Estimated savings: [0.2 × total_tokens_across_sample]

3. **Infrastructure Improvements:**
   - Failure patterns: [most common failures]
   - Timeout patterns: [which repos timeout most]
   - Recommendations: [increase timeout limits, optimize parsing, etc.]

---

## Reproducibility

To reproduce this baseline:

```bash
git checkout [commit_hash]
python -c "import random; random.seed(42)"  # Deterministic sampling
python benchmark_script.py --sample-size 100 --categories all
# Results in .ases/evidence/task-015/
```

---

*Regression Report version: 1.0 | Created: 2026-07-08 | Baseline established: [YYYY-MM-DD]*
