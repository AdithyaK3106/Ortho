"""Isolated module: no imports in, no imports out, no calls to/from other files.

Deliberately used to test the boundary condition of a file with ZERO
incoming/outgoing edges (spec.md's analyze_impact / assemble_context on an
isolated file must not crash).
"""


def standalone():
    return 42
