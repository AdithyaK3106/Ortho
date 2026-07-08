---
title: Failure Taxonomy — Reference
task: task-015
created: 2026-07-08
status: TEMPLATE
---

# Failure Taxonomy

This document defines the fixed classification scheme for failures encountered during AC2 batch analysis. Every error logged during benchmarking must be assigned exactly one failure type.

**Purpose:** Understand which part of Ortho's pipeline fails most often, identify systematic issues, and plan targeted improvements.

---

## Failure Types (9 Total)

### 1. Clone Failure

**Definition:** Repository failed to clone from GitHub or was not accessible.

**Common Causes:**
- Network timeout (github.com unreachable)
- Repository deleted or made private
- Git clone timed out (>10 min wait)
- SSH key or authentication issue
- Disk full or I/O error

**How to Identify:**
- `git clone` command exits non-zero
- Error message contains: "fatal: unable to access", "timeout", "not found", "Permission denied"

**Example Error Messages:**
```
fatal: unable to access 'https://github.com/user/repo.git/': Could not resolve host
fatal: repository not found
fatal: the remote end hung up unexpectedly
```

**Logging Template:**
```
failure_type: Clone Failure
repo_url: https://github.com/org/repo
reason: Git clone timed out after 10 minutes
error_message: [verbatim git error]
```

---

### 2. Scan Failure

**Definition:** `ortho scan` command executed but exited with non-zero status or hung.

**Common Causes:**
- Corrupted Python syntax in repo (can't parse some files)
- Missing dependencies (imports fail)
- Repository too large for scan to complete
- `ortho scan` hung or timed out (>120 sec)
- Out of order execution (forgot `ortho init`)

**How to Identify:**
- `ortho scan` exits non-zero
- Scan logs show parse errors on multiple files
- Command runs >120s and times out

**Example Error Messages:**
```
SyntaxError: invalid syntax in /path/to/file.py
ModuleNotFoundError: No module named 'X'
Traceback (most recent call last): ... timeout
```

**Logging Template:**
```
failure_type: Scan Failure
repo_url: https://github.com/org/repo
reason: Scan timed out after 120 seconds
error_message: [verbatim ortho scan error]
```

---

### 3. Parser Failure

**Definition:** Python AST parser failed on specific files (subset of Scan Failure, split for diagnostics).

**Common Causes:**
- Python syntax errors (invalid code that somehow got committed)
- Rare Python dialects (future imports, walrus operators in old Python versions)
- Encoding issues (non-UTF-8 files)
- Files not actually Python (misnamed .py files)

**How to Identify:**
- Error message explicitly says "SyntaxError", "ParseError", or AST parsing failed
- Error points to specific file paths
- Other files parsed successfully (not a Scan Failure)

**Example Error Messages:**
```
SyntaxError: invalid syntax at line 42 of src/bad_file.py
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xFF in encoding
```

**Logging Template:**
```
failure_type: Parser Failure
repo_url: https://github.com/org/repo
reason: AST parsing failed on 3 files
error_message: SyntaxError in src/models.py line 42: invalid syntax
files_affected: [src/models.py, src/bad_syntax.py, ...]
```

---

### 4. Graph Failure

**Definition:** Call graph or import graph construction failed.

**Common Causes:**
- Circular import detection algorithm failed
- Call graph builder crashed on complex call patterns
- Import graph has unresolvable cycles (logic error in builder)
- Memory error while building large graph

**How to Identify:**
- Error occurs during graph construction phase
- Error message mentions "graph", "cycle", "edge", or "node"
- Files parsed successfully, but graph building fails

**Example Error Messages:**
```
RecursionError: maximum recursion depth exceeded while building call graph
ValueError: Cycle detected in import graph
MemoryError: Unable to construct graph for large repository
```

**Logging Template:**
```
failure_type: Graph Failure
repo_url: https://github.com/org/repo
reason: Call graph construction failed on circular imports
error_message: [verbatim error from graph builder]
```

---

### 5. Architecture Failure

**Definition:** Architecture detection crashed or returned invalid/malformed result.

**Common Causes:**
- Architecture detector crashed (unhandled exception)
- Confidence calculation failed (div by zero, invalid stats)
- Return value is missing required fields
- Detector returned invalid style name (not one of 5 valid styles)

**How to Identify:**
- Error occurs in `ortho analyze` architecture phase
- Error message mentions "architecture", "detector", "confidence", or "style"
- Graphs built successfully, but analysis failed

**Example Error Messages:**
```
ZeroDivisionError: division by zero in confidence calculation
ValueError: Unknown architecture style 'invalid_style'
KeyError: Missing 'confidence' field in architecture result
```

**Logging Template:**
```
failure_type: Architecture Failure
repo_url: https://github.com/org/repo
reason: Architecture detector crashed
error_message: ZeroDivisionError in confidence aggregation
```

---

### 6. Intent Router Failure

**Definition:** Semantic router failed to classify intent utterances.

**Common Causes:**
- Router model not loaded or corrupted
- Embedding encoder failed
- Route similarity calculation crashed
- Router configuration invalid

**How to Identify:**
- Error occurs during intent classification (AC3 phase)
- Error message mentions "router", "intent", "embedding", or "route"
- Other analysis phases succeeded

**Example Error Messages:**
```
RuntimeError: HuggingFace encoder failed to load model
ValueError: No routes defined in router
KeyError: Intent type not found in route definitions
```

**Logging Template:**
```
failure_type: Intent Router Failure
repo_url: https://github.com/org/repo
reason: Semantic router failed during intent classification
error_message: [verbatim router error]
```

---

### 7. Timeout

**Definition:** Any Ortho operation exceeded its time limit.

**Common Causes:**
- Repository too large (scanning takes >120s)
- Analysis too complex (>60s for analyze)
- Network latency (cloning takes >10 min)
- System resource contention (slow disk, limited RAM)

**How to Identify:**
- Command explicitly times out (reaches timeout threshold)
- Error message says "timeout" or "timed out"
- No error from the operation itself, just timeout signal

**Example Error Messages:**
```
Timeout: ortho scan exceeded 120 seconds
TimeoutError: Operation did not complete within 60s
```

**Logging Template:**
```
failure_type: Timeout
repo_url: https://github.com/org/repo
operation: ortho scan
limit_seconds: 120
reason: Repository too large for scan
```

---

### 8. OOM (Out of Memory)

**Definition:** Process ran out of available memory.

**Common Causes:**
- Repository has very large files (>100MB single file)
- Graph construction uses excessive memory
- System limits too tight for this repo
- Memory leak in Ortho

**How to Identify:**
- Error message explicitly says "MemoryError" or "OutOfMemory"
- System shows OOM killer event
- Process dies with no error message (OOM kill)

**Example Error Messages:**
```
MemoryError: Unable to allocate X GB for graph storage
Process terminated by OOM killer (exit code 137)
```

**Logging Template:**
```
failure_type: OOM
repo_url: https://github.com/org/repo
operation: ortho scan
available_memory: 2GB
error_message: [verbatim memory error]
```

---

### 9. Unknown

**Definition:** An error occurred that doesn't fit any of the above categories.

**When to Use:**
- Error message is unclear or unrecognizable
- Multiple errors occur (report as Unknown, then investigate)
- Logging system itself failed
- Human reviewer can't categorize despite examination

**How to Identify:**
- None of the 1–8 categories match
- Error message is cryptic or incomplete

**Example Error Messages:**
```
Unhandled exception in subprocess
Exit code 99 (unknown meaning)
[No error message captured]
```

**Logging Template:**
```
failure_type: Unknown
repo_url: https://github.com/org/repo
error_message: [verbatim output]
investigation_notes: [what to check next]
```

---

## Classification Decision Tree

Use this flowchart to assign a failure type:

```
Did the repo clone successfully?
├─ No → Clone Failure
└─ Yes → Did 'ortho scan' succeed?
    ├─ No → Was it a parser error?
    │   ├─ Yes → Parser Failure
    │   └─ No → Did it run >120s?
    │       ├─ Yes → Timeout
    │       └─ No → Scan Failure
    └─ Yes → Did graph construction succeed?
        ├─ No → Graph Failure
        └─ Yes → Did architecture detection succeed?
            ├─ No → Architecture Failure
            └─ Yes → Did intent routing succeed?
                ├─ No → Intent Router Failure
                └─ Yes → [No failure] ✓
```

---

## Metrics to Track

For each benchmark run, report:

| Failure Type | Count | % of Total | Example Repos |
|--------------|-------|-----------|---|
| Clone Failure | N | X% | [3 examples] |
| Scan Failure | N | X% | [3 examples] |
| Parser Failure | N | X% | [3 examples] |
| Graph Failure | N | X% | [3 examples] |
| Architecture Failure | N | X% | [3 examples] |
| Intent Router Failure | N | X% | [3 examples] |
| Timeout | N | X% | [3 examples] |
| OOM | N | X% | [3 examples] |
| Unknown | N | X% | [3 examples] |
| **Total Failures** | N | X% | — |
| **Success** | N | Y% | — |

---

## Logging Format

Every error in `.ases/evidence/task-015/errors/*.error` must follow this format:

```
repo_url: https://github.com/org/repo
category: [repo category]
failure_type: [one of 9 types]
operation: [scan|analyze|init|clone]
timestamp: [ISO 8601]
error_message: [verbatim output]
logs_location: .ases/evidence/results/[repo_name].log
remediation: [if applicable]
```

---

## Using This Taxonomy in AC2

When AC2 batch analysis encounters an error:

1. **Capture** the full error output
2. **Classify** using the decision tree above
3. **Log** to `.ases/evidence/errors/$REPO_NAME.error` with failure_type
4. **Increment** the count for that failure type
5. **Continue** to next repo (do not stop on single failures)

At the end, report failure breakdown in BENCHMARKS-REPORT.md:
- "X% Clone Failure (Y repos), Z% Scan Failure (W repos), etc."
- Highlight most common failures
- Suggest fixes for Phase 4 or future tasks

---

*Taxonomy version: 1.0 | Created: 2026-07-08 | Used in AC2 batch analysis*
