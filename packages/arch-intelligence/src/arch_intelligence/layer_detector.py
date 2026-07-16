"""Layer detection via real persistence/framework signatures.

Redesigned 2026-07-16 (see docs/archive/FALSE_POSITIVE_AUDIT_2026-07-16.md):
the previous version assigned layer 0 to any module with zero internal
imports (a purely topological fact -- config.py, typing.py, and other
ordinary leaf modules all landed there) and then named that layer via
directory-keyword match. That produced a 100% false-positive rate on every
real repo it fired on in the audit's 9-repo sample: "imports a leaf module"
is not evidence of a layer-boundary violation.

This version only assigns a module to "Data" or "Presentation" when there
is real, checkable evidence for it: the module actually imports a known
persistence/ORM/DB-client library (Data) or a known web/API/CLI framework
(Presentation). A module with no such evidence is left unclassified and
excluded from layer-boundary checking entirely, rather than defaulted into
a layer it may have nothing to do with.
"""

from typing import Optional
from .types import Layer

# Path segments (exact match, case-insensitive) identifying non-production
# code. Files under any of these directories are excluded from layer
# assignment entirely — they are not part of the architecture being
# evaluated, and including them causes test/example files that import
# production code to be misclassified as architectural layer violations.
_EXCLUDED_SEGMENTS = frozenset({
    "tests", "test", "examples", "example", "__tests__", "vendor", "node_modules",
})

# Real, checkable signatures: does this module actually import a library
# that does persistence/IO, or actually import a web/API/CLI framework?
# Top-level module name only (e.g. "sqlalchemy", not "sqlalchemy.orm").
_DATA_SIGNATURES = frozenset({
    "sqlalchemy", "psycopg2", "psycopg", "pymongo", "motor", "redis",
    "sqlite3", "peewee", "pony", "asyncpg", "aiomysql", "aiosqlite",
    "pymysql", "mysqlclient", "cassandra", "elasticsearch", "boto3",
    "dynamodb", "django_orm", "tortoise", "sqlmodel", "alembic",
})
_PRESENTATION_SIGNATURES = frozenset({
    "flask", "fastapi", "django", "starlette", "aiohttp", "tornado",
    "sanic", "bottle", "pyramid", "falcon", "litestar", "quart",
    "click", "typer", "grpc", "graphene", "strawberry",
})

_LAYER_DATA = 0
_LAYER_PRESENTATION = 1


def _is_excluded(rel_path: str) -> bool:
    segments = rel_path.replace("\\", "/").split("/")
    return any(segment.lower() in _EXCLUDED_SEGMENTS for segment in segments)


class LayerDetector:
    """Extracts architectural layers from real persistence/framework signatures."""

    def extract_layers(
        self,
        import_graph: list,
        files: list,
        external_imports_by_file: Optional[dict] = None,
    ) -> list[Layer]:
        """
        Classify modules into Data/Presentation layers using real evidence
        (imports of known persistence or web/API/CLI libraries), not import
        topology. Modules with no such evidence are left out of every
        layer -- unclassified, not defaulted to layer 0 -- so
        layer_boundaries only fires on modules it has real grounds to
        judge.

        `external_imports_by_file` maps file id -> set of top-level
        external module names that file imports (e.g. {"sqlalchemy"}).
        Defaults to {} for callers that don't have this data yet (keeps
        the old call signature working, just with no layers detected).
        """
        external_imports_by_file = external_imports_by_file or {}
        files = [f for f in files if not _is_excluded(f.rel_path)]
        if not files:
            return []

        data_files: list[str] = []
        presentation_files: list[str] = []
        for f in files:
            modules = {m.lower() for m in external_imports_by_file.get(f.id, set())}
            data_hits = sorted(modules & _DATA_SIGNATURES)
            presentation_hits = sorted(modules & _PRESENTATION_SIGNATURES)
            # A module that imports both a DB client and a web framework
            # (e.g. a Flask app file that also opens sqlite3) has no single
            # clear layer identity -- skip rather than guess.
            if data_hits and not presentation_hits:
                data_files.append(f.id)
            elif presentation_hits and not data_hits:
                presentation_files.append(f.id)

        layers: list[Layer] = []
        if data_files:
            layers.append(Layer(
                id=f"layer_{_LAYER_DATA}",
                number=_LAYER_DATA,
                name="Data",
                file_ids=data_files,
                depends_on=[],
                confidence=1.0,
                evidence=[f"imports a known persistence/DB library ({len(data_files)} file(s))"],
            ))
        if presentation_files:
            layers.append(Layer(
                id=f"layer_{_LAYER_PRESENTATION}",
                number=_LAYER_PRESENTATION,
                name="Presentation",
                file_ids=presentation_files,
                depends_on=[_LAYER_DATA] if data_files else [],
                confidence=1.0,
                evidence=[f"imports a known web/API/CLI framework ({len(presentation_files)} file(s))"],
            ))
        return layers
