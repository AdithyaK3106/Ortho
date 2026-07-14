TASK:           task-018-layer-boundaries-noise
TIMESTAMP:      2026-07-15

## Contract Summary

Total public APIs examined: 1 class (unchanged constructor), 1 method (unchanged signature), 1 new module-level helper function
Matched (spec = arch = impl = tests): 2
Missing (in spec, absent from implementation): 0
Unexpected (in implementation or tests, absent from spec): 0

## Constructor Comparison

| Class | Specification | Architecture Review | Builder Implementation | Tests Expect | Match? |
|---|---|---|---|---|---|
| LayerDetector | no constructor change — stateless (spec.md, contract_in/out section) | same (architecture-review.md: "public signature unchanged") | no `__init__` override, stateless (layer_detector.py:21-28) | `LayerDetector()` — zero args (test_layer_detector_exclusions.py:63,74,80,97,110,122,136) | ✅ |

## Method Comparison

| Method | Specification Signature | Builder Signature | Test Call Pattern | Return Type Match | Match? |
|---|---|---|---|---|---|
| LayerDetector.extract_layers | `extract_layers(self, import_graph: list, files: list) -> list[Layer]` — unchanged (spec.md contract_in/out) | `extract_layers(self, import_graph: list, files: list) -> list[Layer]` (layer_detector.py:30), identical signature, added internal filter step only | `.extract_layers(edges, files)` — 2 positional args (test file, multiple call sites) | ✅ (list[Layer], verified via `layers[0].file_ids`/`.number` attribute access in tests) | ✅ |
| `_is_excluded` (new module-level helper, not spec'd as a class method) | Implied by spec.md's "Notes for BUILDER": filter logic checking path segments against an exclusion set | `_is_excluded(rel_path: str) -> bool` (layer_detector.py:16-18) | `_is_excluded("tests/test_core.py")` — single positional str arg, boolean assertion (test file, 11 call sites) | ✅ | ✅ |

## Dataclass Comparison

No dataclasses changed. `Layer` (types.py) is explicitly in `files_forbid` and untouched — confirmed via `git diff` showing zero changes to `types.py`.

## Verdict

**VERDICT: Contract Valid**

The one behavior change (filtering non-production files before layer
assignment) is implemented as an internal addition with zero change to any
public signature. Tests instantiate `LayerDetector()` with no arguments and
call `.extract_layers()` with the same two positional arguments as
pre-existing tests (`test_layer_detector.py`, unmodified) — no
stateful-vs-stateless mismatch, no argument-count mismatch, matching the
exact failure pattern this gate exists to catch (task-008 precedent). The
new `_is_excluded` helper's signature in tests matches its implementation
exactly (single string argument, boolean return).

## Recommendation

Proceed to VERIFIER.
