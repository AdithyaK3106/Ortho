"""Architecture model persistence."""

import json
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Optional
from .types import ArchitectureModel


class ArchitectureModelStore:
    """SQLite persistence for architecture models."""

    def __init__(self, db_path: str = ".ortho/ortho.db"):
        """Initialize with database path (default: local ortho db)."""
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        # Connections are always closed (Windows locks the db file otherwise)
        return sqlite3.connect(self.db_path)

    def _init_schema(self):
        """Create architecture_models table if not exists."""
        with closing(self._connect()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS architecture_models (
                    id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    style TEXT NOT NULL,
                    style_confidence REAL NOT NULL,
                    evidence TEXT NOT NULL,
                    model_json TEXT NOT NULL,
                    detected_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def save(self, model: ArchitectureModel) -> str:
        """Save architecture model. Returns model_id."""
        import uuid

        model_id = str(uuid.uuid4())
        detected_at = model.detected_at or datetime.utcnow().isoformat()

        evidence_json = json.dumps(model.evidence or [])
        model_json = self._serialize_model(model)

        with closing(self._connect()) as conn:
            conn.execute("""
                INSERT INTO architecture_models
                (id, repo_id, style, style_confidence, evidence, model_json, detected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                model_id,
                model.repo_id,
                model.style.value,
                model.style_confidence,
                evidence_json,
                model_json,
                detected_at,
            ))
            conn.commit()
        return model_id

    def load(self, model_id: str) -> Optional[ArchitectureModel]:
        """Load a specific model by ID."""
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT model_json FROM architecture_models WHERE id = ?", (model_id,)
            ).fetchone()
        if row:
            return self._deserialize_model(row[0])
        return None

    def load_latest(self, repo_id: str) -> Optional[ArchitectureModel]:
        """Load most recent model for repo."""
        with closing(self._connect()) as conn:
            row = conn.execute("""
                SELECT model_json FROM architecture_models
                WHERE repo_id = ?
                ORDER BY detected_at DESC
                LIMIT 1
            """, (repo_id,)).fetchone()
        if row:
            return self._deserialize_model(row[0])
        return None

    def load_all_versions(self, repo_id: str) -> list[ArchitectureModel]:
        """Load all versions for repo."""
        with closing(self._connect()) as conn:
            rows = conn.execute("""
                SELECT model_json FROM architecture_models
                WHERE repo_id = ?
                ORDER BY detected_at DESC
            """, (repo_id,)).fetchall()
        return [self._deserialize_model(row[0]) for row in rows]

    def delete(self, model_id: str):
        """Delete a model by ID."""
        with closing(self._connect()) as conn:
            conn.execute("DELETE FROM architecture_models WHERE id = ?", (model_id,))
            conn.commit()

    def _serialize_model(self, model: ArchitectureModel) -> str:
        """Serialize ArchitectureModel to JSON."""
        data = {
            "repo_id": model.repo_id,
            "style": model.style.value,
            "style_confidence": model.style_confidence,
            "layers": [
                {
                    "id": l.id,
                    "number": l.number,
                    "name": l.name,
                    "file_ids": l.file_ids,
                    "depends_on": l.depends_on,
                    "confidence": l.confidence,
                    "evidence": l.evidence,
                }
                for l in model.layers
            ],
            "subsystems": [
                {
                    "id": s.id,
                    "name": s.name,
                    "file_ids": s.file_ids,
                    "coupling_score": s.coupling_score,
                    "layer_id": s.layer_id,
                }
                for s in model.subsystems
            ],
            "detected_at": model.detected_at,
            "evidence": model.evidence,
        }
        return json.dumps(data)

    def _deserialize_model(self, json_str: str) -> ArchitectureModel:
        """Deserialize JSON to ArchitectureModel."""
        from .types import Layer, Subsystem, ArchStyle

        data = json.loads(json_str)

        layers = [
            Layer(
                id=l["id"],
                number=l["number"],
                name=l["name"],
                file_ids=l.get("file_ids", []),
                depends_on=l.get("depends_on", []),
                confidence=l.get("confidence", 1.0),
                evidence=l.get("evidence", []),
            )
            for l in data.get("layers", [])
        ]

        subsystems = [
            Subsystem(
                id=s["id"],
                name=s["name"],
                file_ids=s.get("file_ids", []),
                coupling_score=s.get("coupling_score", 0.0),
                layer_id=s.get("layer_id"),
            )
            for s in data.get("subsystems", [])
        ]

        return ArchitectureModel(
            repo_id=data["repo_id"],
            style=ArchStyle(data["style"]),
            style_confidence=data["style_confidence"],
            layers=layers,
            subsystems=subsystems,
            detected_at=data.get("detected_at", ""),
            evidence=data.get("evidence", []),
        )
