"""Architecture model persistence."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

# Add shared storage to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "shared" / "storage" / "src"))

from database import OrthoDatabase

if TYPE_CHECKING:
    from shared.types import ArchitectureModel


class ArchitectureModelStore:
    """Persist and retrieve architecture models."""

    def __init__(self, db: OrthoDatabase, repo_id: str):
        self.db = db
        self.repo_id = repo_id

    def save(self, model: "ArchitectureModel") -> str:
        """
        Insert/update architecture model.
        Returns model_id.
        """
        model_id = self._compute_id(model)
        conn = self.db.connection()

        # Serialize model to JSON
        model_json = json.dumps(self._to_dict(model))
        evidence_json = json.dumps(model.style_evidence if hasattr(model, "style_evidence") else [])

        # Upsert
        conn.execute(
            """
            INSERT OR REPLACE INTO architecture_models
            (id, repo_id, style, style_confidence, evidence, model_json, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_id,
                self.repo_id,
                model.style,
                model.style_confidence,
                evidence_json,
                model_json,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        return model_id

    def load(self, model_id: str) -> "ArchitectureModel | None":
        """Retrieve architecture model by ID."""
        conn = self.db.connection()

        row = conn.execute(
            "SELECT model_json FROM architecture_models WHERE id = ? AND repo_id = ?",
            (model_id, self.repo_id),
        ).fetchone()

        conn.close()

        if not row:
            return None

        model_dict = json.loads(row[0])
        return self._from_dict(model_dict)

    def load_latest(self) -> "ArchitectureModel | None":
        """Retrieve most recent architecture model for repo."""
        conn = self.db.connection()

        row = conn.execute(
            """
            SELECT model_json FROM architecture_models
            WHERE repo_id = ?
            ORDER BY detected_at DESC
            LIMIT 1
            """,
            (self.repo_id,),
        ).fetchone()

        conn.close()

        if not row:
            return None

        model_dict = json.loads(row[0])
        return self._from_dict(model_dict)

    def _compute_id(self, model: "ArchitectureModel") -> str:
        """Generate stable ID for model."""
        import hashlib

        key = f"{self.repo_id}:{model.style}".encode()
        return hashlib.sha256(key).hexdigest()[:16]

    def _to_dict(self, model: "ArchitectureModel") -> dict:
        """Convert model to JSON-serializable dict."""
        return {
            "repo_id": model.repo_id,
            "style": model.style,
            "style_confidence": model.style_confidence,
            "layers": [
                {
                    "id": layer.id,
                    "name": layer.name,
                    "file_ids": layer.file_ids,
                    "depends_on": layer.depends_on,
                    "confidence": layer.confidence,
                }
                for layer in model.layers
            ],
            "subsystems": [
                {
                    "id": subsys.id,
                    "name": subsys.name,
                    "file_ids": subsys.file_ids,
                    "layer_id": subsys.layer_id,
                    "coupling_score": subsys.coupling_score,
                }
                for subsys in model.subsystems
            ],
            "service_boundaries": model.service_boundaries if hasattr(model, "service_boundaries") else [],
        }

    def _from_dict(self, model_dict: dict) -> "ArchitectureModel":
        """Reconstruct model from dict."""
        # Import here to avoid circular
        from shared.types import ArchitectureModel as SharedArchModel
        from .layer_detector import Layer
        from .subsystem_detector import Subsystem

        layers = [
            Layer(
                id=l["id"],
                name=l["name"],
                file_ids=l["file_ids"],
                depends_on=l["depends_on"],
                confidence=l["confidence"],
            )
            for l in model_dict.get("layers", [])
        ]

        subsystems = [
            Subsystem(
                id=s["id"],
                name=s["name"],
                file_ids=s["file_ids"],
                layer_id=s.get("layer_id"),
                coupling_score=s["coupling_score"],
            )
            for s in model_dict.get("subsystems", [])
        ]

        return SharedArchModel(
            repo_id=model_dict["repo_id"],
            style=model_dict["style"],
            style_confidence=model_dict["style_confidence"],
            layers=layers,
            subsystems=subsystems,
            service_boundaries=model_dict.get("service_boundaries", []),
            detected_at=datetime.now(timezone.utc),
        )
