# tiny_repo fixture -- hand-verified known contents

5 Python files, used by `validation/test_adapter_contract.py` for a REAL
correctness check against `adapter.scan_repository()` (not just a shape
check). If BUILDER's adapter or the underlying repo_intelligence extractors
change qualified-name conventions, this file is the source of truth for what
"correct" means here -- update deliberately, not to make a failing test pass.

## Files (5)
- `pkg/__init__.py` -- empty
- `pkg/core.py` -- defines `helper` (function), `Widget` (class, methods `__init__`, `render`)
- `pkg/util.py` -- imports `pkg.core.Widget`; defines `make_widget` (function); calls `Widget(...)` and `w.render()`
- `pkg/isolated.py` -- defines `standalone` (function). NO imports in or out, NO calls to/from any other file in the repo. Used as the boundary-condition fixture for isolated-file tests.
- `main.py` -- imports `pkg.util.make_widget`; defines `run` (function); calls `make_widget(...)`

## Known symbols (qualified names, dotted-module convention)
- `pkg.core.helper`
- `pkg.core.Widget`
- `pkg.core.Widget.__init__`
- `pkg.core.Widget.render`
- `pkg.util.make_widget`
- `pkg.isolated.standalone`
- `main.run`

(Exact qualified-name string format is extractor-dependent -- test asserts
the SET of symbol short-names/counts, not brittle exact-string qualified
names, since the qualified-name delimiter convention is an implementation
detail of `repo_intelligence.symbol_extractor`, not part of this spec.)

## Known imports (importer -> imported)
- `pkg/util.py` -> `pkg/core.py` (via `from pkg.core import Widget`)
- `main.py` -> `pkg/util.py` (via `from pkg.util import make_widget`)
- `pkg/isolated.py` -> (none)
- `pkg/core.py` -> (none)

## Known call edges (caller -> callee, same-file or cross-file)
- `pkg.util.make_widget` -> `pkg.core.Widget.__init__` (constructing `Widget(name)`)
- `pkg.util.make_widget` -> `pkg.core.Widget.render` (calling `w.render()`)
- `pkg.core.Widget.render` -> `pkg.core.helper`
- `main.run` -> `pkg.util.make_widget`
- `pkg.isolated.standalone` -> (none; isolated)

## Isolated file
`pkg/isolated.py` has zero incoming edges (nothing imports it, nothing calls
`standalone`) and zero outgoing edges (imports nothing, calls nothing). This
is the fixture used to test `analyze_impact`/`assemble_context` do not crash
on a changed_file with no blast radius.
