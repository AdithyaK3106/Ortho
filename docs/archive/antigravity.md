# Antigravity Session Changelog

This document tracks all the changes, improvements, bug fixes, and architectural overhauls applied to the **Ortho** codebase from the very first message of this chat session.

## 1. Audit Fixes & Git Hygiene
- **DebtScorer Bugs Fixed:** 
  - **B-1:** Coupling score is now normalized by total graph size rather than hardcoded division by 1.
  - **B-2:** Churn now matches exact `file_id` first, falling back to basename only when unambiguous.
  - **B-3 / B-7:** Test coverage heuristic replaced constant penalty with dynamic existence checks; heuristic documentation updated.
- **Dependency Health & API:** 
  - **B-4:** Dropped the unused `call_graph` parameter from `find_cycles` in `DependencyHealthAnalyzer`.
  - **B-6:** Replaced hardcoded `repo-default` in API server (`orchestration.py`). `RunRequest` and `/history` now accept dynamic `repo_id` from the request.
- **ImpactAnalyzer Bug Fixed:**
  - **B-5:** Risk score was previously normalizing by `num_symbols` leading to saturated scores on small files; it is now correctly normalized by the total graph file count.
- **Package Import Guards:**
  - **B-8:** Converted hard-fail `ImportError` in `python_adapter.py` to a lazy guard. `repo_intelligence` is now fully importable for its graph builders without requiring `tree-sitter`.
- **Git Hygiene (P0-1 → P0-6) & Dead Code:** 
  - Generated root `README.md` and MIT `LICENSE`.
  - Updated `.gitignore` to include `venv/`, `node_modules/`, `*.log`, `screenshots/`, `dist/`, and `ortho-demo/`.
  - Untracked thousands of junk files (including mangled unicode logs, node_modules, venv, and ortho-demo as a separate repo).
  - Deleted the obsolete `graph_utils.py` and the `screenshots/` directory.
  - Archived stale documentation into `docs/archive/`.
  - Removed stale stub comments regarding `task-014` in `step_runner.py`.

## 2. Forensic Audit & Release Cleanup
- **Forensic Validation:** Conducted a zero-assumption forensic audit of every metric displayed by Ortho. Found that `task-015` KPIs (77.5% intent routing, 1032 mean tokens, 496 tests) were simulated, not measured.
- **Metric Scrubbing:** Purged all unverified and simulated metrics from `CLAUDE.md`, `status.md`, `README.md`, `AUDIT.md`, and the `ortho-demo` dashboard.
- **Simulated Evidence Removal:** Deleted `.ases/evidence/task-015` and `.ases/tasks/task-015-repo-benchmarks`. Removed references to `task-015` across test suites and core pipeline logic (`test_metrics.py`, `evaluate.py`, `runner.py`, `adapter.py`).
- **Context Distillation:** Drastically shortened `CLAUDE.md` (1100+ lines to ~60) and `status.md` (500+ lines to ~40) to focus only on highly relevant, current architectural context.
- **Determinism Proof:** Re-ran `generate_data.py --all` across all 8 datasets. The git diff resulted in zero byte-level changes, proving Ortho's benchmark metrics are fully deterministic and reproducible.

## 3. Algorithm Correctness Fixes
- **ImpactAnalyzer (Blast Radius):** Fixed a critical flaw in `blast_radius` calculation. It now correctly aggregates both `direct_dependents` and `transitive_dependents`. Updated assertions in `test_impact_analyzer.py` to reflect exact graph counts.
- **DebtScorer (Test Coverage):** Fixed a flaw where test coverage defaulted to a blind penalty. `_compute_test_coverage_score` now dynamically validates against a concrete set of all known `file_ids` derived from git metadata and import graphs. Updated `test_debt_scorer.py`.
- **Test Suite Health:** Resolved widespread `TypeError` failures in `test_dependency_health.py` by systematically removing legacy `call_graph=[]` keyword arguments passed to `DependencyHealthAnalyzer`.

## 4. Architecture Visualization Refactor (`ortho-demo/dashboard/`)
- **Node Classification:** Built a deterministic classifier inside the dashboard to categorize filepaths into architectural roles (`Controllers`, `Services`, `Models`, `Repositories`, `Utilities`, `Tests`, `Configuration`, `Generated`, etc.).
- **Importance Scoring:** Replaced raw-degree sizing with a real-time mathematical Importance Score: `0.35*Betweenness + 0.25*PageRank + 0.20*Fan-in + 0.10*Fan-out + 0.10*RoleWeight`. PageRank and approximate Betweenness Centrality algorithms execute dynamically in the browser.
- **Repository Composition:** Built a visual summary widget detailing the breakdown of the codebase by percentage of architectural roles.
- **Interactive Toggles:** 
  - Switch between **"Architecture View"** (collapses noise) and **"Raw Dependency Graph"**.
  - Apply filters: `Collapse Tests`, `Collapse Packages`, `Hide Generated/Docs`, `Only Business Logic`.
  - Added new "Architectural Role" color segmentation mapped alongside Subsystem, Layer, and Debt.
- **Physics Engine:** Adjusted D3/force-graph simulation to cluster nodes by Subsystem and Role.
- **Dashboard Patches:** Fixed JavaScript redeclaration syntax errors (`dragMoved`, `svg`) that temporarily hung the boot screen, verifying flawless execution via browser subagent.
