import json
import sqlite3
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

    def run_impact(self, file_path: str, depth: int = 3) -> dict:
        """
        Change impact analysis for a real file, loaded from the indexed database.

        Replaces the previous stub that unconditionally returned an empty report
        regardless of input (task-010 fix — see spec.md's Known Gap and
        architecture-review.md's storage-layer verification).
        """
        from impact_analysis import ImpactAnalyzer, Symbol, CallEdge, ImportEdge

        db_path = self.repo_root / ".ortho" / "ortho.db"
        if not db_path.exists():
            return {
                "changed_file_id": file_path,
                "direct_dependents": [],
                "transitive_dependents": [],
                "risk_score": 0.0,
                "analysis_confidence": 0.0,
                "blast_radius": 0,
                "evidence": ["Repository not indexed (.ortho/ortho.db not found); run `ortho scan` first"],
            }

        conn = sqlite3.connect(str(db_path))
        try:
            conn.row_factory = sqlite3.Row
            file_row = conn.execute(
                "SELECT id, repo_id FROM files WHERE rel_path = ?", (file_path,)
            ).fetchone()

            if file_row is None:
                return {
                    "changed_file_id": file_path,
                    "direct_dependents": [],
                    "transitive_dependents": [],
                    "risk_score": 0.0,
                    "analysis_confidence": 0.0,
                    "blast_radius": 0,
                    "evidence": [f"File not found in index: {file_path}"],
                }

            file_id = file_row["id"]
            repo_id = file_row["repo_id"]

            symbol_rows = conn.execute(
                "SELECT id, name, file_id, start_line, end_line FROM symbols WHERE repo_id = ?",
                (repo_id,),
            ).fetchall()
            symbols = [
                Symbol(
                    id=row["id"],
                    name=row["name"],
                    file_id=row["file_id"],
                    start_line=row["start_line"] or 0,
                    end_line=row["end_line"] or 0,
                )
                for row in symbol_rows
            ]

            call_rows = conn.execute(
                """
                SELECT ce.caller_id, ce.callee_id, ce.confidence
                FROM call_edges ce
                JOIN symbols s ON s.id = ce.caller_id
                WHERE s.repo_id = ?
                """,
                (repo_id,),
            ).fetchall()
            call_graph = [
                CallEdge(caller_id=row["caller_id"], callee_id=row["callee_id"], confidence=row["confidence"])
                for row in call_rows
            ]

            import_rows = conn.execute(
                """
                SELECT importer_file_id, imported_file_id, imported_module, is_external
                FROM import_edges ie
                JOIN files f ON f.id = ie.importer_file_id
                WHERE f.repo_id = ?
                """,
                (repo_id,),
            ).fetchall()
            import_graph = [
                ImportEdge(
                    importer_file_id=row["importer_file_id"],
                    imported_file_id=row["imported_file_id"],
                    imported_module=row["imported_module"],
                    is_external=bool(row["is_external"]),
                )
                for row in import_rows
            ]
        finally:
            conn.close()

        analyzer = ImpactAnalyzer()
        report = analyzer.analyze(call_graph, import_graph, file_id, symbols=symbols, depth=depth)

        return {
            "changed_file_id": file_path,
            "direct_dependents": report.direct_dependents,
            "transitive_dependents": report.transitive_dependents,
            "risk_score": report.risk_score,
            "analysis_confidence": report.analysis_confidence,
            "blast_radius": report.blast_radius,
            "evidence": report.evidence,
        }

    def run_adr_check(self) -> dict:
        """ortho analyze --adr-check — cross-reference ADRs against the repo tree."""
        from arch_intelligence import ADRTracker

        adr_dir = self.repo_root / ".ases" / "architecture" / "adrs"
        tracker = ADRTracker()
        results = tracker.check_adrs(adr_dir, self.repo_root)

        return {
            "adrs": [
                {
                    "adr_id": r.adr_id,
                    "title": r.title,
                    "status": r.status,
                    "classification": r.classification,
                    "referenced_paths": r.referenced_paths,
                    "missing_paths": r.missing_paths,
                    "evidence": r.evidence,
                }
                for r in results
            ]
        }

    def run_reuse(self, threshold: float = 0.7) -> dict:
        """ortho analyze --reuse — find structurally similar symbols across the repo."""
        from repo_intelligence.symbol_extractor import SymbolExtractor
        from arch_intelligence import ReuseDetector

        extractor = SymbolExtractor()
        symbols_by_file: dict = {}
        sources_by_file: dict = {}

        for py_file in self.repo_root.rglob("*.py"):
            if "__pycache__" in py_file.parts or ".ortho" in py_file.parts:
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            rel_path = str(py_file.relative_to(self.repo_root))
            symbols_by_file[rel_path] = extractor.extract_symbols(rel_path, source)
            sources_by_file[rel_path] = source

        detector = ReuseDetector()
        clusters = detector.find_similar(symbols_by_file, sources_by_file, threshold=threshold)

        return {
            "clusters": [
                {
                    "symbol_ids": c.symbol_ids,
                    "file_ids": c.file_ids,
                    "similarity": c.similarity,
                    "evidence": c.evidence,
                }
                for c in clusters
            ]
        }


def analyze(repo_root: str, impact_file: Optional[str] = None) -> dict:
    """Entry point for ortho analyze command."""
    cmd = AnalyzeCommand(Path(repo_root))
    if impact_file:
        return cmd.run_impact(impact_file)
    return cmd.run()


def _main() -> None:
    """CLI entry point, invoked as a script by apps/cli/src/commands/analyze.ts."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="ortho analyze")
    parser.add_argument("--repo-root", default=".", help="Repository root path")
    parser.add_argument("--impact", help="File path for change impact analysis")
    parser.add_argument("--depth", type=int, default=3, help="Impact traversal depth")
    parser.add_argument("--adr-check", action="store_true", help="Cross-reference ADRs against code")
    parser.add_argument("--reuse", action="store_true", help="Find structurally similar symbols")
    parser.add_argument("--threshold", type=float, default=0.7, help="Reuse similarity threshold")
    args = parser.parse_args()

    cmd = AnalyzeCommand(Path(args.repo_root))

    if args.impact:
        result = cmd.run_impact(args.impact, depth=args.depth)
    elif args.adr_check:
        result = cmd.run_adr_check()
    elif args.reuse:
        result = cmd.run_reuse(threshold=args.threshold)
    else:
        result = cmd.run()

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    _main()
