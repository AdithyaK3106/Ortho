# PLANNER Phase: Forensic Architecture Audit

**Investigator:** Lead Engineer  
**Date:** 2026-07-13  
**Scope:** Root-cause analysis of architecture detector failures  

---

## Executive Summary

The detector produces "unknown" for Click and Flask because **all five style scorers return scores ≤ 0.45**, triggering the unknown-style gate. Investigation reveals:

1. **Directory-vocabulary dominates scoring** — rare layer-name tokens mean weak baseline
2. **Scorers are asymmetric** — layered scorer fires on any 2-layer bands, flat scorer requires 70% depth-1 files
3. **Graph analysis is shallow** — only import direction, not topology, coupling, fan-in/fan-out
4. **Confidence calibration is correct** — 0.40 honestly reflects "we have no idea"
5. **Framework detection is absent** — Flask/Click distinctive patterns go unused

---

## Hypothesis Test Results

### Hypothesis A: Evidence Threshold Too High?

**Finding:** PARTIALLY TRUE

Evidence threshold is 0.45, and winners score 0.40. **But lowering threshold ≠ fix** — the scores themselves are weak because scorers have weak input signals (rare vocabulary, shallow graph analysis).

**Root cause:** The vocabulary detection (directory and file stem tokens) works, but Click/Flask lack explicit layer names in their directory structure. They organize by *functionality* and *visibility* (private/public), not by *architectural layers*.

Click structure:
```
src/click/
  globals.py        (layer 0 — infrastructure)
  exceptions.py     (layer 1 — domain)
  core.py          (layer 2 — core logic)
  testing.py       (layer 3 — testing utilities)
```

The detector sees `src/click/` (no layer vocabulary like "services", "models", "data") and assigns everything to one band. Ground truth human sees semantic layers (infrastructure→domain→core→testing) based on *imports* and *dependencies*, not *names*.

**Conclusion:** Threshold is appropriate; the scorers need richer input signals.

---

### Hypothesis B: Directory-Only Vocabulary

**Finding:** TRUE

Current vocabulary extraction:
```python
# arch_detector.py, line 106-114
for p in self.paths.values():
    parts = p.lower().split("/")
    for seg in parts[:-1]:
        self.dir_tokens[seg] += 1
    stem = parts[-1].rsplit(".", 1)[0]
    self.stem_tokens[stem] += 1
self.all_tokens = set(self.dir_tokens) | set(self.stem_tokens)
```

**Click tokens found:**
- `src`, `click` (every file has these)
- `examples`, `docs`, `tests`, `typing` (file types, not layer names)
- NO: `services`, `domain`, `data`, `models`, `layer`, `level`, `core`

**Flask tokens found:**
- `src`, `flask` (every file)
- `tests`, `docs` (file types)
- NO: `service`, `domain`, `data`, `model`

**The scorers expect names like:**
- `services` (service layer)
- `domain` (domain logic)
- `data` (data access)

But Flask/Click organize by *module functionality* (ctx, config, session, helpers, blueprints), not *layer abstractions*.

**Conclusion:** Directory-based vocabulary detection works, but it's optimized for explicitly-layered monoliths (Django-style). It doesn't recognize:
- Implicit layer boundaries (detected via imports)
- Framework-specific structures (Flask blueprint plugins, Click command hierarchy)
- Coupling-based layers (computed from graph, not names)

---

### Hypothesis C: Missing Graph Features

**Finding:** TRUE — Critical

Current graph analysis:
```python
# Only measures:
- dag_depth: max path length in import graph
- cycle_ratio: % of edges in cycles
- n_files: number of files
- shallow_ratio: % of files at depth ≤ 1
```

**Missing signals:**
1. **Fan-in distribution** — which files are imported by many others? (centrality)
2. **Fan-out patterns** — which files import many? (responsibility)
3. **Layer violation count** — how many reverse-imports? (acyclic-ness)
4. **Coupling metrics** — internal vs external coupling per module?
5. **Entry points** — public API surface identification?
6. **Package hierarchy** — how deep is module nesting?
7. **Framework fingerprints** — Flask routes, Click commands, Django models?

**Example: Flask call-graph has 3,829 edges. Current detector ignores all of them.**

Flask's actual architecture is hidden in the **call graph** (who calls whom), not visible in imports alone:
- Route handlers (@app.route) are entry points
- Request context manager (ctx.py) is core
- Helpers (helpers.py) are utility

But the detector sees imports only, missing the distinction.

**Conclusion:** Graph analysis is a 1D projection of a 3D problem. Call graph + import graph together reveal architecture; either alone is incomplete.

---

### Hypothesis D: Confidence Calibration

**Finding:** CORRECT

0.40 confidence is mathematically honest:
- All scorers return 0.40 or below
- Threshold is 0.45
- Therefore → unknown (uncertain)

This is **working as intended**. The detector correctly says "I don't have enough signal."

**However:** The current calibration has no way to distinguish between:
- "I'm genuinely unsure" (0.40)
- "I'm certain it's unknown" (0.40)

Both use the same score. Confidence should reflect the *strength of evidence*, not just whether we hit the threshold.

**Conclusion:** Calibration logic is sound; the issue is that scorers have insufficient input signals to reach > 0.45.

---

### Hypothesis E: Framework Detection Missing

**Finding:** TRUE

Flask is unmistakable:
- Has a `@app.route` decorator pattern (hundreds of uses)
- Central `app` object (Flask application instance)
- Middleware pattern (before_request, after_request hooks)
- Blueprint system (modular plugins)

Click is unmistakable:
- `@click.command()` decorators
- `@click.option()` parameter binding
- No traditional MVC — CLI framework, not web
- Flat file structure (single responsibility per module)

**But:** The detector has no framework fingerprinting. It treats Flask and Click like generic Python packages.

**Conclusion:** Adding framework detection would immediately improve accuracy. Flask = "layered (framework pattern)", Click = "flat (CLI framework)".

---

## Root Cause Summary

| Hypothesis | Result | Impact |
|---|---|---|
| A. Threshold too high | Partially true | Raises bar but doesn't solve core issue |
| B. Directory vocabulary only | TRUE | Misses implicit layer signals |
| C. Graph features missing | TRUE (Critical) | Ignores 95% of architecture signal |
| D. Calibration broken | False | Working correctly; honest about uncertainty |
| E. Framework detection absent | TRUE | Treats frameworks as generic packages |

**Primary Root Cause:** Detector relies on **explicit directory naming** (services, models, data) to detect architecture. When a repository uses **implicit structuring** (Flask: module names describe function, not layer; Click: single package, no layers), the detector has nothing to work with.

**Secondary Issues:** Graph analysis incomplete (call graph ignored), framework patterns unrecognized.

---

## Proposed Redesign Strategy

### Phase 1: Immediate Wins (Low Risk, High ROI)

1. **Add framework fingerprinting** (Flask, Click, Django, FastAPI, etc.)
2. **Incorporate call-graph analysis** (currently 100% ignored)
3. **Measure coupling metrics** (fan-in/fan-out per module)

### Phase 2: Calibration Improvements

4. **Per-evidence weighting** (directory vocab 20%, graph topology 60%, framework 20%)
5. **Multi-layer inference** (detect layers via dependency direction even without names)

### Phase 3: Graph-Based Architecture

6. **Subsystem clustering via coupling** (current Jaccard approach unchanged; improve signal quality)
7. **Entry-point detection** (public API surface identification)

### Phase 4: Validation & Iteration

8. **Expand ground truth** (8 repositories, manually validated)
9. **Measure accuracy per hypothesis** (what helped? what didn't?)
10. **Iterate with evidence, not guesses**

---

## Next Steps

1. **ARCHITECT:** Manually classify FastAPI, Django, Requests, LangChain
2. **ARCHITECT:** Design multi-evidence scorer
3. **BUILDER:** Implement framework detection + call-graph analysis
4. **VERIFIER:** Measure accuracy on expanded ground truth
5. **REVIEWER:** Gate each change; no hardcoding

