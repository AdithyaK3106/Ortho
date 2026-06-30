#!/usr/bin/env python3
"""Test all task-003 module imports."""

import sys
sys.path.insert(0, 'packages/repo-intelligence/src')

results = []

try:
    from call_graph import CallGraphBuilder, CallEdge, CallGraphError
    results.append("PASS: CallGraphBuilder, CallEdge, CallGraphError")
except Exception as e:
    results.append(f"FAIL: CallGraphBuilder - {e}")

try:
    from dependency_graph import DependencyGraphBuilder, DependencyEdge
    results.append("PASS: DependencyGraphBuilder, DependencyEdge")
except Exception as e:
    results.append(f"FAIL: DependencyGraphBuilder - {e}")

try:
    from module_detector import ModuleDetector, Module
    results.append("PASS: ModuleDetector, Module")
except Exception as e:
    results.append(f"FAIL: ModuleDetector - {e}")

try:
    from incremental_indexer import IncrementalIndexer, IndexDelta, NotAGitRepoError
    results.append("PASS: IncrementalIndexer, IndexDelta, NotAGitRepoError")
except Exception as e:
    results.append(f"FAIL: IncrementalIndexer - {e}")

for result in results:
    print(result)

# Check for failures
failures = [r for r in results if r.startswith("FAIL")]
if failures:
    print(f"\n{len(failures)} import failures")
    sys.exit(1)
else:
    print(f"\nAll {len(results)} modules imported successfully")
    sys.exit(0)
