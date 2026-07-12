# Benchmark Results

- **Total:** 10 (10 SUCCESS, 0 other)

## Summary

| Suite | Dataset | Status | Metrics |
|---|---|---|---|
| repository | click | SUCCESS | callgraph_f1=0.3483, callgraph_precision=0.2109, callgraph_recall=1.0, imports_f1=0.25, imports_precision=0.1429, imports_recall=1.0, parse_success_rate=1.0, repository_coverage=1.0, symbols_f1=0.3805, symbols_precision=0.235, symbols_recall=1.0 |
| repository | flask | SUCCESS | callgraph_f1=0.2417, callgraph_precision=0.1374, callgraph_recall=1.0, imports_f1=0.225, imports_precision=0.1268, imports_recall=1.0, parse_success_rate=1.0, repository_coverage=1.0, symbols_f1=0.1485, symbols_precision=0.0802, symbols_recall=1.0 |
| architecture | click | SUCCESS | architecture_confidence=0.75, architecture_style_accuracy=0.0, dependency_direction_accuracy=0.6667, layer_f1=0.2667, layer_precision=0.2667, layer_recall=0.2667, subsystem_matched=5, subsystem_mean_jaccard=0.0429, subsystem_unmatched=0 |
| architecture | flask | SUCCESS | architecture_confidence=0.5, architecture_style_accuracy=0.0, dependency_direction_accuracy=1.0, layer_f1=0.1765, layer_precision=0.1765, layer_recall=0.1765, subsystem_matched=5, subsystem_mean_jaccard=0.041, subsystem_unmatched=0 |
| impact | click | SUCCESS | blast_radius_mean_relative_error=5.5, entries_evaluated=2, impact_f1=0.0, impact_precision=0.0, impact_recall=0.0, risk_score_correlation=0.0 |
| impact | flask | SUCCESS | blast_radius_mean_relative_error=6.4524, entries_evaluated=3, impact_f1=0.3389, impact_precision=0.6842, impact_recall=0.5476, risk_score_correlation=-0.866 |
| efficiency | click | SUCCESS | context_budget_fill_pct=8.0, context_chunks_included=2, context_chunks_total=2, context_compression_ratio=0.5352, context_tokens_used=640, peak_memory_mb=0.4 |
| efficiency | flask | SUCCESS | context_budget_fill_pct=7.7, context_chunks_included=2, context_chunks_total=2, context_compression_ratio=0.5357, context_tokens_used=616, peak_memory_mb=0.2 |
| retrieval | click | SUCCESS | mrr=0.0, ndcg_at_10=0.0, precision_at_10=0.0, precision_at_5=0.0, questions_evaluated=6, recall_at_10=0.0, recall_at_5=0.0 |
| retrieval | flask | SUCCESS | mrr=0.0, ndcg_at_10=0.0, precision_at_10=0.0, precision_at_5=0.0, questions_evaluated=6, recall_at_10=0.0, recall_at_5=0.0 |

## repository / click

**Status:** SUCCESS

**Metrics:**

- callgraph_f1: 0.3483
- callgraph_precision: 0.2109
- callgraph_recall: 1.0
- imports_f1: 0.25
- imports_precision: 0.1429
- imports_recall: 1.0
- parse_success_rate: 1.0
- repository_coverage: 1.0
- symbols_f1: 0.3805
- symbols_precision: 0.235
- symbols_recall: 1.0

**Timings (s):**

- scan_repository: 1.291

**Detail:**

```json
{
  "symbols": {
    "precision": 0.235,
    "recall": 1.0,
    "f1": 0.3805,
    "correct": 328,
    "missed": 0,
    "extra": 1068
  },
  "imports": {
    "precision": 0.1429,
    "recall": 1.0,
    "f1": 0.25,
    "correct": 12,
    "missed": 0,
    "extra": 72
  },
  "callgraph": {
    "precision": 0.2109,
    "recall": 1.0,
    "f1": 0.3483,
    "correct": 844,
    "missed": 0,
    "extra": 3158
  },
  "parse_errors": []
}
```

## repository / flask

**Status:** SUCCESS

**Metrics:**

- callgraph_f1: 0.2417
- callgraph_precision: 0.1374
- callgraph_recall: 1.0
- imports_f1: 0.225
- imports_precision: 0.1268
- imports_recall: 1.0
- parse_success_rate: 1.0
- repository_coverage: 1.0
- symbols_f1: 0.1485
- symbols_precision: 0.0802
- symbols_recall: 1.0

**Timings (s):**

- scan_repository: 0.789

**Detail:**

```json
{
  "symbols": {
    "precision": 0.0802,
    "recall": 1.0,
    "f1": 0.1485,
    "correct": 100,
    "missed": 0,
    "extra": 1147
  },
  "imports": {
    "precision": 0.1268,
    "recall": 1.0,
    "f1": 0.225,
    "correct": 9,
    "missed": 0,
    "extra": 62
  },
  "callgraph": {
    "precision": 0.1374,
    "recall": 1.0,
    "f1": 0.2417,
    "correct": 399,
    "missed": 0,
    "extra": 2504
  },
  "parse_errors": []
}
```

## architecture / click

**Status:** SUCCESS

**Metrics:**

- architecture_confidence: 0.75
- architecture_style_accuracy: 0.0
- dependency_direction_accuracy: 0.6667
- layer_f1: 0.2667
- layer_precision: 0.2667
- layer_recall: 0.2667
- subsystem_matched: 5
- subsystem_mean_jaccard: 0.0429
- subsystem_unmatched: 0

**Timings (s):**

- detect_architecture: 0.835

**Detail:**

```json
{
  "ground_truth_style": "flat",
  "predicted_style": "layered",
  "predicted_alternative": null,
  "layer_scores": {
    "precision": 0.2667,
    "recall": 0.2667,
    "f1": 0.2667,
    "correct": 4,
    "missed": 11,
    "extra": 11
  },
  "subsystem_scores": {
    "mean_jaccard": 0.0429,
    "matched": 5,
    "unmatched": 0,
    "pairs": [
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0429
      },
      {
        "expected_size": 4,
        "predicted_index": 1,
        "jaccard": 0.0571
      },
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0429
      },
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0429
      },
      {
        "expected_size": 2,
        "predicted_index": 1,
        "jaccard": 0.0286
      }
    ]
  },
  "evidence": [
    "Detected style: layered",
    "Confidence: 0.75",
    "Layer vocabulary present in structure: presentation, business",
    "Import graph forms 3-level dependency chain",
    "Low import-cycle ratio (0.0%)",
    "Competing scores: layered=0.75, microservices=0.20, mvc=0.00, hexagonal=0.00, flat=0.00"
  ]
}
```

## architecture / flask

**Status:** SUCCESS

**Metrics:**

- architecture_confidence: 0.5
- architecture_style_accuracy: 0.0
- dependency_direction_accuracy: 1.0
- layer_f1: 0.1765
- layer_precision: 0.1765
- layer_recall: 0.1765
- subsystem_matched: 5
- subsystem_mean_jaccard: 0.041
- subsystem_unmatched: 0

**Timings (s):**

- detect_architecture: 0.023

**Detail:**

```json
{
  "ground_truth_style": "layered",
  "predicted_style": "ambiguous",
  "predicted_alternative": "layered",
  "layer_scores": {
    "precision": 0.1765,
    "recall": 0.1765,
    "f1": 0.1765,
    "correct": 3,
    "missed": 14,
    "extra": 14
  },
  "subsystem_scores": {
    "mean_jaccard": 0.041,
    "matched": 5,
    "unmatched": 0,
    "pairs": [
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0385
      },
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0385
      },
      {
        "expected_size": 3,
        "predicted_index": 1,
        "jaccard": 0.0385
      },
      {
        "expected_size": 5,
        "predicted_index": 1,
        "jaccard": 0.0641
      },
      {
        "expected_size": 2,
        "predicted_index": 1,
        "jaccard": 0.0256
      }
    ]
  },
  "evidence": [
    "Detected style: ambiguous",
    "Confidence: 0.50",
    "Multiple architectural patterns are equally plausible. Strongest candidate: layered (0.50).",
    "Competing scores: layered=0.50, microservices=0.35, mvc=0.20, flat=0.12, hexagonal=0.00"
  ]
}
```

## impact / click

**Status:** SUCCESS

**Metrics:**

- blast_radius_mean_relative_error: 5.5
- entries_evaluated: 2
- impact_f1: 0.0
- impact_precision: 0.0
- impact_recall: 0.0
- risk_score_correlation: 0.0

**Timings (s):**

- analyze_impact_total: 0.014

**Detail:**

```json
{
  "per_entry": [
    {
      "changed_file": "src/click/_termui_impl.py",
      "precision": 0.0,
      "recall": 0.0,
      "f1": 0.0,
      "predicted_blast_radius": 6,
      "actual_blast_radius": 1,
      "blast_radius_rel_error": 5.0,
      "risk_score": 0.3150684931506849
    },
    {
      "changed_file": "src/click/decorators.py",
      "precision": 0.0,
      "recall": 0.0,
      "f1": 0.0,
      "predicted_blast_radius": 7,
      "actual_blast_radius": 1,
      "blast_radius_rel_error": 6.0,
      "risk_score": 0.13013698630136986
    }
  ]
}
```

## impact / flask

**Status:** SUCCESS

**Metrics:**

- blast_radius_mean_relative_error: 6.4524
- entries_evaluated: 3
- impact_f1: 0.3389
- impact_precision: 0.6842
- impact_recall: 0.5476
- risk_score_correlation: -0.866

**Timings (s):**

- analyze_impact_total: 0.02

**Detail:**

```json
{
  "per_entry": [
    {
      "changed_file": "src/flask/ctx.py",
      "precision": 1.0,
      "recall": 0.5,
      "f1": 0.6667,
      "predicted_blast_radius": 1,
      "actual_blast_radius": 2,
      "blast_radius_rel_error": 0.5,
      "risk_score": 0.10625
    },
    {
      "changed_file": "src/flask/ctx.py",
      "precision": 1.0,
      "recall": 0.1429,
      "f1": 0.25,
      "predicted_blast_radius": 1,
      "actual_blast_radius": 7,
      "blast_radius_rel_error": 0.8571,
      "risk_score": 0.10625
    },
    {
      "changed_file": "src/flask/helpers.py",
      "precision": 0.0526,
      "recall": 1.0,
      "f1": 0.1,
      "predicted_blast_radius": 19,
      "actual_blast_radius": 1,
      "blast_radius_rel_error": 18.0,
      "risk_score": 0.20625
    }
  ]
}
```

## efficiency / click

**Status:** SUCCESS

**Metrics:**

- context_budget_fill_pct: 8.0
- context_chunks_included: 2
- context_chunks_total: 2
- context_compression_ratio: 0.5352
- context_tokens_used: 640
- peak_memory_mb: 0.4

**Timings (s):**

- assemble_context: 0.009
- context_latency_ms: 4.9
- detect_architecture: 0.059
- ingest_analysis_artifacts: 0.108
- scan_repository: 0.021
- total: 0.197

**Detail:**

```json
{
  "budget_total": 8000,
  "query": "architecture overview subsystems dependency health technical debt"
}
```

## efficiency / flask

**Status:** SUCCESS

**Metrics:**

- context_budget_fill_pct: 7.7
- context_chunks_included: 2
- context_chunks_total: 2
- context_compression_ratio: 0.5357
- context_tokens_used: 616
- peak_memory_mb: 0.2

**Timings (s):**

- assemble_context: 0.01
- context_latency_ms: 5.61
- detect_architecture: 0.062
- ingest_analysis_artifacts: 0.111
- scan_repository: 0.01
- total: 0.193

**Detail:**

```json
{
  "budget_total": 8000,
  "query": "architecture overview subsystems dependency health technical debt"
}
```

## retrieval / click

**Status:** SUCCESS

**Metrics:**

- mrr: 0.0
- ndcg_at_10: 0.0
- precision_at_10: 0.0
- precision_at_5: 0.0
- questions_evaluated: 6
- recall_at_10: 0.0
- recall_at_5: 0.0

**Timings (s):**

- retrieve_total: 0.035

**Detail:**

```json
{
  "per_question": [
    {
      "question": "what class represents a click CLI command",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "what class represents a command-line option",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how do I print output to the terminal in click",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how does click ask the user for confirmation",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "what holds the execution state for a running click command",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how does click group multiple commands into a collection",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    }
  ]
}
```

## retrieval / flask

**Status:** SUCCESS

**Metrics:**

- mrr: 0.0
- ndcg_at_10: 0.0
- precision_at_10: 0.0
- precision_at_5: 0.0
- questions_evaluated: 6
- recall_at_10: 0.0
- recall_at_5: 0.0

**Timings (s):**

- retrieve_total: 0.033

**Detail:**

```json
{
  "per_question": [
    {
      "question": "how does flask store per-request configuration values",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how do I flash a message to the user",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how does flask register a blueprint",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how does flask generate a url for a view function",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "what is the current app context proxy",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    },
    {
      "question": "how does flask push and pop the application context",
      "recall_at_5": 0.0,
      "precision_at_5": 0.0,
      "recall_at_10": 0.0,
      "precision_at_10": 0.0,
      "mrr": 0.0,
      "ndcg_at_10": 0.0
    }
  ]
}
```

