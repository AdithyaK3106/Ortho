"""Technical debt scorer: computes multi-dimensional debt scores per module."""

from .types import DebtScore, CallEdge, ImportEdge, Symbol, GitFileMetadata


class DebtScorer:
    """Computes multi-dimensional technical debt scores per module (stateless)."""

    # Phase 1 default weights
    DEFAULT_WEIGHTS = {
        "coupling": 0.30,
        "churn": 0.20,
        "complexity": 0.20,
        "test_coverage": 0.20,
        "other": 0.10,
    }

    # Phase 1 default thresholds
    CHURN_THRESHOLD = 20  # commits in 30 days = high churn
    COMPLEXITY_THRESHOLD = 8  # AST depth threshold

    def score_module(
        self,
        file_id: str,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        git_metadata: dict[str, GitFileMetadata],
    ) -> DebtScore:
        """
        Compute debt score for a single module (stateless).

        Args:
            file_id: ID of the file to score
            call_graph: List of CallEdge objects
            import_graph: List of ImportEdge objects
            symbols: List of Symbol objects
            git_metadata: Dict mapping file paths to GitFileMetadata

        Returns:
            DebtScore with all dimensions and evidence
        """
        # Coupling score: (fan_in + fan_out) / (2 * num_files)
        coupling_score = self._compute_coupling_score(file_id, import_graph)

        # Churn score: min(1.0, commits_30d / 20)
        churn_score = self._compute_churn_score(file_id, git_metadata)

        # Complexity score: min(1.0, avg_ast_depth / 8)
        complexity_score = self._compute_complexity_score(file_id, symbols)

        # Test coverage score: 0.0 if tests exist, 1.0 if not
        test_coverage_score = self._compute_test_coverage_score(file_id)

        # Total score: weighted average
        total_score = (
            self.DEFAULT_WEIGHTS["coupling"] * coupling_score
            + self.DEFAULT_WEIGHTS["churn"] * churn_score
            + self.DEFAULT_WEIGHTS["complexity"] * complexity_score
            + self.DEFAULT_WEIGHTS["test_coverage"] * test_coverage_score
            + self.DEFAULT_WEIGHTS["other"] * 0.0  # Reserved for future
        )
        total_score = min(1.0, max(0.0, total_score))

        # Build evidence
        evidence = []
        if coupling_score > 0.7:
            evidence.append(f"High coupling ({coupling_score:.2f}): central module with many dependencies")
        if churn_score > 0.7:
            evidence.append(f"High churn ({churn_score:.2f}): frequently modified")
        if complexity_score > 0.7:
            evidence.append(f"High complexity ({complexity_score:.2f}): deeply nested code")
        if test_coverage_score > 0.5:
            evidence.append(f"Low test coverage ({test_coverage_score:.2f}): no tests detected")

        return DebtScore(
            module_id=file_id,
            total_score=total_score,
            coupling_score=coupling_score,
            churn_score=churn_score,
            complexity_score=complexity_score,
            test_coverage_score=test_coverage_score,
            evidence=evidence,
        )

    def score_all_modules(
        self,
        call_graph: list[CallEdge],
        import_graph: list[ImportEdge],
        symbols: list[Symbol],
        git_metadata: dict[str, GitFileMetadata],
    ) -> list[DebtScore]:
        """
        Compute debt scores for all modules (stateless).

        Args:
            call_graph: List of CallEdge objects
            import_graph: List of ImportEdge objects
            symbols: List of Symbol objects
            git_metadata: Dict mapping file paths to GitFileMetadata

        Returns:
            List of DebtScore, sorted by total_score descending
        """
        # Collect unique file IDs
        file_ids = set()
        for sym in symbols:
            file_ids.add(sym.file_id)

        # Score each module
        scores = []
        for file_id in file_ids:
            score = self.score_module(
                file_id,
                call_graph,
                import_graph,
                symbols,
                git_metadata,
            )
            scores.append(score)

        # Sort by total_score descending
        return sorted(scores, key=lambda s: s.total_score, reverse=True)

    @staticmethod
    def _compute_coupling_score(
        file_id: str,
        import_graph: list[ImportEdge],
    ) -> float:
        """Compute coupling score: (fan_in + fan_out) / 2."""
        fan_in = sum(1 for edge in import_graph if edge.imported_file_id == file_id)
        fan_out = sum(1 for edge in import_graph if edge.importer_file_id == file_id)
        num_files = 1  # Denominator is just this file
        coupling = (fan_in + fan_out) / (2 * num_files) if num_files > 0 else 0.0
        return min(1.0, coupling)

    @staticmethod
    def _compute_churn_score(
        file_id: str,
        git_metadata: dict[str, GitFileMetadata],
    ) -> float:
        """Compute churn score: min(1.0, commits_30d / 20)."""
        # Find metadata for this file
        for path, metadata in git_metadata.items():
            if file_id in path or path.endswith(file_id.split("/")[-1]):
                commits = metadata.commits_30d
                churn = min(1.0, commits / DebtScorer.CHURN_THRESHOLD)
                return churn
        return 0.0  # No git metadata, assume stable

    @staticmethod
    def _compute_complexity_score(
        file_id: str,
        symbols: list[Symbol],
    ) -> float:
        """Compute complexity score: min(1.0, avg_ast_depth / 8)."""
        # Filter symbols for this file
        file_symbols = [s for s in symbols if s.file_id == file_id]
        if not file_symbols:
            return 0.0

        # Estimate depth from line ranges (proxy for nesting)
        total_depth = 0
        for sym in file_symbols:
            lines = max(1, sym.end_line - sym.start_line)
            # Rough heuristic: deeper = more lines
            depth = min(8, max(1, lines // 20))  # Normalize to ~8
            total_depth += depth

        avg_depth = total_depth / len(file_symbols) if file_symbols else 1
        complexity = min(1.0, avg_depth / DebtScorer.COMPLEXITY_THRESHOLD)
        return complexity

    @staticmethod
    def _compute_test_coverage_score(file_id: str) -> float:
        """Compute test coverage score: 0.0 if tests exist, 1.0 if not."""
        # Heuristic: check if file_id ends with _test or if there's a test_*.py for it
        if "test" in file_id.lower():
            return 0.0  # It's a test file itself

        # Check if corresponding test file exists (would need external check in real impl)
        # For now, return neutral (0.5)
        return 0.5
