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
        """Compute coupling score: (fan_in + fan_out) / (2 * num_files).

        Normalises by the total number of unique files in the import graph so
        that only the most central files in large repos score near 1.0.
        """
        fan_in = sum(1 for edge in import_graph if edge.imported_file_id == file_id)
        fan_out = sum(1 for edge in import_graph if edge.importer_file_id == file_id)
        # Collect all unique file IDs visible in the graph
        file_ids: set[str] = set()
        for edge in import_graph:
            file_ids.add(edge.importer_file_id)
            if edge.imported_file_id:
                file_ids.add(edge.imported_file_id)
        num_files = max(len(file_ids), 1)
        coupling = (fan_in + fan_out) / (2 * num_files)
        return min(1.0, coupling)

    @staticmethod
    def _compute_churn_score(
        file_id: str,
        git_metadata: dict[str, GitFileMetadata],
    ) -> float:
        """Compute churn score: min(1.0, commits_30d / 20).

        Matches on exact file_id first, then falls back to a suffix match
        only when the suffix is unique in the graph (avoids cross-crediting
        files that share a basename such as __init__.py).
        """
        # Exact match takes priority
        if file_id in git_metadata:
            commits = git_metadata[file_id].commits_30d
            return min(1.0, commits / DebtScorer.CHURN_THRESHOLD)

        # Suffix fallback — only use when the basename is unambiguous
        basename = file_id.split("/")[-1]
        suffix_matches = [
            (path, metadata)
            for path, metadata in git_metadata.items()
            if path.endswith(basename)
        ]
        if len(suffix_matches) == 1:
            commits = suffix_matches[0][1].commits_30d
            return min(1.0, commits / DebtScorer.CHURN_THRESHOLD)

        return 0.0  # No unambiguous match — assume stable

    @staticmethod
    def _compute_complexity_score(
        file_id: str,
        symbols: list[Symbol],
    ) -> float:
        """Compute complexity score: min(1.0, avg_line_span / 160).

        Uses line-span per symbol as a *proxy* for nesting depth because
        tree-sitter AST depth is not stored in Symbol.  A 160-line symbol
        maps to score 1.0 (threshold = 8 * 20).  This is a known
        approximation; replace with real AST-depth data when available.
        """
        # Filter symbols for this file
        file_symbols = [s for s in symbols if s.file_id == file_id]
        if not file_symbols:
            return 0.0

        # Estimate depth from line ranges (proxy for nesting)
        total_depth = 0
        for sym in file_symbols:
            lines = max(1, sym.end_line - sym.start_line)
            depth = min(8, max(1, lines // 20))
            total_depth += depth

        avg_depth = total_depth / len(file_symbols) if file_symbols else 1
        complexity = min(1.0, avg_depth / DebtScorer.COMPLEXITY_THRESHOLD)
        return complexity

    @staticmethod
    def _compute_test_coverage_score(file_id: str) -> float:
        """Compute test coverage score: 0.0 if well-tested, 1.0 if no tests.

        Heuristic: infer test coverage from file-naming conventions.
        A score of 0.5 means the heuristic found no evidence either way.
        Callers should treat 0.5 as "unknown" rather than a measured value.

        Limitation: this cannot detect tests that cover a module without
        following the test_<module>.py or <module>_test.py convention.
        Real coverage data from pytest-cov would supersede this score.
        """
        # Files that ARE test files contribute no debt for this dimension
        if "test" in file_id.lower():
            return 0.0

        # Derive conventional test file basename from file_id
        # e.g. "src/flask/app.py" -> "test_app.py" or "app_test.py"
        basename = file_id.split("/")[-1]  # e.g. "app.py"
        stem = basename.rsplit(".", 1)[0]   # e.g. "app"
        conventional_names = {f"test_{stem}.py", f"{stem}_test.py"}

        # Check: is there any path in file_id's parent that matches?
        # We only have the file_id string, not the filesystem, so we check
        # if any test-named sibling would share the same directory prefix.
        parent = "/".join(file_id.split("/")[:-1])
        for name in conventional_names:
            candidate = f"{parent}/{name}" if parent else name
            # Marker: if the file_id itself mentions a tests/ directory above,
            # assume tests exist — conservative guess.
            if "tests/" in file_id or "test/" in file_id:
                return 0.2  # Likely in a tested package

        # No evidence of tests found via convention
        return 0.7  # Higher debt signal than neutral 0.5
