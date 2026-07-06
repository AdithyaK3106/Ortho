"""Persist scan results to .ortho/ortho.db.

Single writer of the scan tables (files, symbols, call_edges, import_edges) per ADR-011.
Detectors and analyzers are read-only consumers. Persistence strategy:

- Minted, deterministic symbol IDs: sha256("{repo_id}:{rel_path}:{qualified_name}")[:16],
  re-minted with ":{lineno}" appended to the hash input on intra-file collision.
- Per-file wipe-and-rewrite inside one transaction (idempotent re-scans, atomic per file).
- Unresolvable references are dropped and counted, never guessed.
"""

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from storage import OrthoDatabase


def mint_repo_id(repo_root: Path) -> str:
    """Stable repo ID derived from the resolved root path."""
    return hashlib.sha256(str(Path(repo_root).resolve()).encode()).hexdigest()[:16]


def _mint(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]


@dataclass
class PersistResult:
    """Per-file persistence counts."""

    symbols_written: int
    imports_written: int
    calls_written: int
    calls_dropped_unresolved: int


class IndexStore:
    """All database writes for repository scan results."""

    def __init__(self, db: OrthoDatabase, repo_id: str, repo_root: Path):
        self.db = db
        self.repo_id = repo_id
        self.repo_root = Path(repo_root)

    def ensure_repository(self, name: str, primary_language: str = "python") -> None:
        """INSERT OR IGNORE the repositories row; refresh indexed_at."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self.db.connection()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO repositories (id, root_path, name, primary_language, indexed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (self.repo_id, str(self.repo_root.resolve()), name, primary_language, now),
            )
            conn.execute(
                "UPDATE repositories SET indexed_at = ? WHERE id = ?", (now, self.repo_id)
            )
            conn.commit()
        finally:
            conn.close()

    def persist_file(
        self,
        rel_path: str,
        symbols: List,
        imports: List,
        calls: List,
    ) -> PersistResult:
        """Wipe-and-rewrite all rows for one file in a single transaction.

        Idempotent: persisting the same inputs twice yields identical rows.
        Call edges resolve against this file's symbols plus symbols already
        persisted for this repo; unresolved edges are dropped and counted.
        # ponytail: cross-file calls to files later in (sorted) scan order drop;
        # upgrade path is a buffered repo-wide second pass if edge recall matters.
        """
        rel_path = rel_path.replace("\\", "/")
        file_id = _mint(self.repo_id, rel_path)
        now = datetime.now(timezone.utc).isoformat()

        conn = self.db.connection()
        try:
            # Minted IDs for this file's symbols; deterministic collision re-mint.
            minted: dict[str, str] = {}
            symbol_rows = []
            for sym in symbols:
                sym_id = _mint(self.repo_id, rel_path, sym.qualified_name)
                if sym.qualified_name in minted:
                    sym_id = _mint(self.repo_id, rel_path, sym.qualified_name, str(sym.lineno))
                else:
                    minted[sym.qualified_name] = sym_id
                visibility = "private" if sym.name.startswith("_") else "public"
                symbol_rows.append(
                    (
                        sym_id,
                        self.repo_id,
                        file_id,
                        sym.name,
                        sym.qualified_name,
                        sym.type,  # already within the DB CHECK set (function/class/method)
                        visibility,
                        sym.lineno,
                        sym.lineno,  # extractor emits no end spans (spec: known limitation)
                        sym.docstring,
                        None,
                    )
                )

            # Repo-wide qualified-name map from already-persisted symbols (unique names only —
            # ambiguous matches are never guessed).
            repo_map: dict[str, Optional[str]] = {}
            for qname, sym_id in conn.execute(
                "SELECT qualified_name, id FROM symbols WHERE repo_id = ? AND file_id != ?",
                (self.repo_id, file_id),
            ):
                repo_map[qname] = None if qname in repo_map else sym_id

            def resolve(name: Optional[str]) -> Optional[str]:
                if not name:
                    return None
                if name in minted:
                    return minted[name]
                return repo_map.get(name) or None

            call_rows = []
            dropped = 0
            for edge in calls:
                caller_id = resolve(edge.caller_name)
                callee_name = edge.callee_name
                callee_id = resolve(callee_name)
                if callee_id is None and callee_name.startswith("self."):
                    # self.foo() inside Class.method -> Class.foo
                    prefix = edge.caller_name.rsplit(".", 1)[0] if "." in edge.caller_name else ""
                    if prefix:
                        callee_id = resolve(f"{prefix}.{callee_name[len('self.'):]}")
                if caller_id is None or callee_id is None:
                    dropped += 1
                    continue
                call_rows.append((caller_id, callee_id, edge.lineno, edge.confidence))

            import_rows = [
                (file_id, None, imp.target_module, 1, None) for imp in imports
            ]

            conn.execute("BEGIN")
            # Wipe: edges keyed to this file first (FK direction), then symbols, then file.
            conn.execute(
                "DELETE FROM call_edges WHERE caller_id IN (SELECT id FROM symbols WHERE file_id = ?)",
                (file_id,),
            )
            conn.execute(
                "DELETE FROM call_edges WHERE callee_id IN (SELECT id FROM symbols WHERE file_id = ?)",
                (file_id,),
            )
            conn.execute("DELETE FROM import_edges WHERE importer_file_id = ?", (file_id,))
            conn.execute("DELETE FROM symbols WHERE file_id = ?", (file_id,))
            # Plain check-then-write: the minted id and UNIQUE(repo_id, rel_path)
            # collide on the same row, which makes upsert conflict targets ambiguous,
            # and INSERT OR REPLACE would break other files' import-edge FKs.
            if conn.execute("SELECT 1 FROM files WHERE id = ?", (file_id,)).fetchone():
                conn.execute(
                    "UPDATE files SET last_modified = ? WHERE id = ?", (now, file_id)
                )
            else:
                conn.execute(
                    """
                    INSERT INTO files (id, repo_id, rel_path, language, last_modified)
                    VALUES (?, ?, ?, 'python', ?)
                    """,
                    (file_id, self.repo_id, rel_path, now),
                )
            conn.executemany(
                """
                INSERT INTO symbols
                (id, repo_id, file_id, name, qualified_name, kind, visibility,
                 start_line, end_line, docstring, signature)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                symbol_rows,
            )
            conn.executemany(
                """
                INSERT INTO import_edges
                (importer_file_id, imported_file_id, imported_module, is_external, symbols_imported)
                VALUES (?, ?, ?, ?, ?)
                """,
                import_rows,
            )
            conn.executemany(
                """
                INSERT INTO call_edges (caller_id, callee_id, call_site_line, confidence)
                VALUES (?, ?, ?, ?)
                """,
                call_rows,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        return PersistResult(
            symbols_written=len(symbol_rows),
            imports_written=len(import_rows),
            calls_written=len(call_rows),
            calls_dropped_unresolved=dropped,
        )

    def resolve_import_targets(self) -> None:
        """Second pass: map imported_module dotted paths to repo files.

        Runs after all files are persisted, so resolution never depends on scan
        order. "pkg.mod" resolves to pkg/mod.py or pkg/mod/__init__.py; leading
        dots in relative imports resolve against the importer's directory.
        Unresolved imports stay is_external=1 — never guessed.
        """
        conn = self.db.connection()
        try:
            files = {
                rel: fid
                for fid, rel in conn.execute(
                    "SELECT id, rel_path FROM files WHERE repo_id = ?", (self.repo_id,)
                )
            }
            rows = conn.execute(
                """
                SELECT ie.id, ie.imported_module, f.rel_path
                FROM import_edges ie
                JOIN files f ON f.id = ie.importer_file_id
                WHERE f.repo_id = ?
                """,
                (self.repo_id,),
            ).fetchall()

            updates = []
            for edge_id, module, importer_rel in rows:
                target = self._module_to_file_id(module, importer_rel, files)
                if target is not None:
                    updates.append((target, edge_id))
            conn.executemany(
                "UPDATE import_edges SET imported_file_id = ?, is_external = 0 WHERE id = ?",
                updates,
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _module_to_file_id(
        module: str, importer_rel: str, files: dict[str, str]
    ) -> Optional[str]:
        """Dotted module path -> files.id, or None if it isn't a repo file."""
        if not module:
            return None
        if module.startswith("."):
            dots = len(module) - len(module.lstrip("."))
            remainder = module.lstrip(".")
            base_parts = importer_rel.split("/")[:-1]  # importer's package dir
            up = dots - 1
            if up > len(base_parts):
                return None
            parts = base_parts[: len(base_parts) - up] + (
                remainder.split(".") if remainder else []
            )
        else:
            parts = module.split(".")
        if not parts or not all(parts):
            return None
        stem = "/".join(parts)
        return files.get(f"{stem}.py") or files.get(f"{stem}/__init__.py")
