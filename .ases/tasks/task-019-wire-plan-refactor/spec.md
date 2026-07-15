# Spec — task-019-wire-plan-refactor

## API Contract (unchanged signatures)
```python
def plan(self, intent: str, **kwargs: Any) -> CliReport: ...
def refactor(self, path: str | None = None, **kwargs: Any) -> CliReport: ...
```
No new public methods, no new constructor args on `CliCommands`.

## New internal adapters (cli_commands package)

### `FeaturePlannerArchModelAdapter` (new file: `feature_plan_adapter.py`)
```python
class FeaturePlannerArchModelAdapter:
    def __init__(self, arch_model: ArchitectureModel) -> None: ...
    def get_style(self) -> str:
        """Returns arch_model.style.value (e.g. 'unknown', 'layered')."""
```

### `CodeRepositoryAdapter` (new file: `refactor_adapter.py`)
```python
class CodeRepositoryAdapter:
    def __init__(self, scan: ScanResult) -> None: ...

    def get_tight_couplings(self) -> list[tuple[str, str]]:
        """2-node cycles from DependencyHealthAnalyzer.find_cycles(),
        deduplicated (A,B) == (B,A), returned as module-name pairs."""

    def get_circular_deps(self) -> list[list[str]]:
        """Cycles of length > 2 from find_cycles(), as module-name chains."""

    def get_bloated_modules(self) -> list[tuple[str, int, int]]:
        """(module, lines, functions) for every module where
        lines > 300 or functions > 20, via CodeMetricsAdapter."""

    def get_duplications(self) -> list[tuple[str, str, float]]:
        """Always []. No code-similarity detector exists in this
        codebase (see plan.md 'Out of Scope'). Documented gap, not
        fabricated data."""

    def get_high_churn_modules(self) -> list[str]:
        """Always []. No git-history integration wired into
        cli-commands scan path. Documented gap, not fabricated data."""
```

Internally resolves `repo_intelligence.import_graph.ImportEdge` (module-name
target) to `impact_analysis.types.ImportEdge` (file-id target) using the
same module-name -> file-id resolution as
`repo_scanner._build_layer_import_edges` (exact match, then
`.endswith(f".{module}")` fallback for relative-import suffixes).

## Behavior — plan()

| Input | Output |
|---|---|
| Non-empty intent, valid repo scan | `success=True`, content lists >=3 `ImplementationPath` entries (name, effort, risk, rationale) from `FeaturePlanner.plan_feature()` |
| `""` | `success=False`, content `"Cannot plan for an empty intent."`, no scan performed |
| `kwargs["scan_path"]` provided | scans that path instead of cwd (mirrors `decide()`'s existing `scan_path` kwarg) |
| Scan path does not exist | `success=False`, `FileNotFoundError` message surfaced |

## Behavior — refactor()

| Input | Output |
|---|---|
| `path=None` or valid dir | `success=True`, content lists `RefactoringIssue` entries (type, location, severity, recommendation, effort, confidence) from `RefactoringAdvisor.find_issues()`, or `"No refactoring issues found."` if empty |
| `path` does not exist | `success=False`, `FileNotFoundError` message surfaced |
| Scan succeeds but repo has no cycles/bloat | `success=True`, empty-findings message (not an error — a clean repo is a valid real outcome) |

## Non-Goals (explicit, matches plan.md)
- `get_duplications()`/`get_high_churn_modules()` returning non-empty data.
- Architecture-style classification.

## Real-Repo Verification Target
`repos/click` — chosen because it is already used for task-017/018
verification, is a real non-trivial Python codebase, and its known
structure (single-package, some genuinely large modules like `core.py`)
gives predictable bloat signal for anti-overfitting bounded assertions
(e.g. "at least 1 bloated module found", not "exactly module X at exactly
Y lines").
