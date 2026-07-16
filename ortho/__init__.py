"""Root `ortho` metapackage.

Exists only so poetry-core's build backend has a real module to locate --
this project has no source of its own beyond this file. All real code
lives in the 13 workspace packages under packages/ and shared/, each
installed separately and editable (see install.sh/.bat/.ps1). `pip install
-e .` installs this file plus the shared third-party dependencies every
workspace package needs (numpy, pydantic, tree-sitter, etc.), declared in
[tool.poetry.dependencies] below.
"""
