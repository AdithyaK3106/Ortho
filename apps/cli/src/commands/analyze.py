import json
from pathlib import Path
from typing import Optional


class AnalyzeCommand:
    """ortho analyze — Full architecture report."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root

    def run(self, impact_file: Optional[str] = None) -> dict:
        """
        Run architecture analysis.
        
        Returns:
            dict with architecture model, layers, subsystems
        """
        from arch_intelligence import (
            ArchitectureDetector,
            LayerDetector,
            SubsystemDetector,
            ArchitectureModelStore,
        )
        from shared.storage import OrthoDatabase

        # Load repo data
        db = OrthoDatabase(self.repo_root)
        
        # Placeholder: would load actual call/import graphs from database
        call_graph = []
        import_graph = []
        symbols = []
        files = []

        # Run detection
        arch_detector = ArchitectureDetector()
        result = arch_detector.detect(call_graph, import_graph, symbols, files)

        # Extract layers and subsystems
        layer_detector = LayerDetector()
        layers = layer_detector.extract_layers(import_graph, files)

        subsystem_detector = SubsystemDetector()
        subsystems = subsystem_detector.detect_subsystems(call_graph, symbols, files)

        # Build model
        from arch_intelligence import ArchitectureModel
        model = ArchitectureModel(
            repo_id="repo",
            style=result.style,
            style_confidence=result.confidence,
            layers=layers,
            subsystems=subsystems,
            evidence=result.evidence,
        )

        # Save model
        store = ArchitectureModelStore(db)
        model_id = store.save(model)

        return {
            "style": result.style.value,
            "confidence": result.confidence,
            "evidence": result.evidence,
            "layers": len(layers),
            "subsystems": len(subsystems),
            "model_id": model_id,
        }


def analyze(repo_root: str, impact_file: Optional[str] = None) -> dict:
    """Entry point for ortho analyze command."""
    cmd = AnalyzeCommand(Path(repo_root))
    return cmd.run(impact_file)
