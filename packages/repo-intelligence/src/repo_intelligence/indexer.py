"""Main indexer that orchestrates file discovery and symbol/import/call extraction."""

from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass, field
import logging

from repo_intelligence.file_discoverer import FileDiscoverer
from repo_intelligence.symbol_extractor import SymbolExtractor
from repo_intelligence.import_graph import ImportGraphBuilder
from repo_intelligence.call_graph import CallGraphBuilder
from repo_intelligence.file_watcher import FileWatcher


logger = logging.getLogger(__name__)


@dataclass
class IndexResult:
    """Result of repository indexing."""
    total_files: int = 0
    files_scanned: int = 0
    files_with_errors: int = 0
    total_symbols: int = 0
    total_imports: int = 0
    total_calls: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Return percentage of files successfully scanned."""
        if self.total_files == 0:
            return 0.0
        return (self.files_scanned / self.total_files) * 100

    @property
    def error_count(self) -> int:
        """Return number of errors encountered."""
        return len(self.errors)


class Indexer:
    """Orchestrates file discovery and extraction for repository indexing."""

    def __init__(
        self,
        repo_root: Path,
        exclude_patterns: set[str] | None = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Initialize indexer.

        Args:
            repo_root: Repository root directory
            exclude_patterns: Optional set of additional exclusion patterns
            progress_callback: Optional callback(files_done, total_files) for progress tracking
        """
        self.repo_root = Path(repo_root)
        self.discoverer = FileDiscoverer(repo_root, exclude_patterns)
        self.symbol_extractor = SymbolExtractor()
        self.import_builder = ImportGraphBuilder()
        self.call_builder = CallGraphBuilder()
        self.progress_callback = progress_callback
        self.error_threshold = 0.9  # Accept up to 10% error rate

    def index_repository(self) -> IndexResult:
        """
        Full repository scan and indexing.

        Returns:
            IndexResult with scan statistics and errors

        Process:
            1. Discover all Python files
            2. For each file:
               - Read source
               - Extract symbols
               - Extract imports
               - Extract calls
               - Track results
            3. Report summary
        """
        result = IndexResult()

        # Discover files
        python_files = self.discoverer.find_python_files()
        result.total_files = len(python_files)

        if result.total_files == 0:
            logger.warning(f"No Python files found in {self.repo_root}")
            return result

        logger.info(f"Discovered {result.total_files} Python files")

        # Index each file
        for idx, file_path in enumerate(python_files):
            if self.progress_callback:
                self.progress_callback(idx, result.total_files)

            try:
                self._index_file(file_path, result)
                result.files_scanned += 1
            except Exception as e:
                error_msg = f"{file_path.relative_to(self.repo_root)}: {str(e)}"
                result.errors.append(error_msg)
                result.files_with_errors += 1
                logger.warning(f"Error indexing {error_msg}")

        if self.progress_callback:
            self.progress_callback(result.total_files, result.total_files)

        # Log summary
        logger.info(
            f"Index complete: {result.files_scanned}/{result.total_files} files, "
            f"{result.total_symbols} symbols, {result.total_imports} imports, "
            f"{result.total_calls} calls, {result.error_count} errors "
            f"({result.success_rate:.1f}% success)"
        )

        return result

    def index_files(self, file_paths: List[Path]) -> IndexResult:
        """
        Index a specific list of files.

        Args:
            file_paths: List of absolute paths to index

        Returns:
            IndexResult with scan statistics
        """
        result = IndexResult()
        result.total_files = len(file_paths)

        for idx, file_path in enumerate(file_paths):
            if self.progress_callback:
                self.progress_callback(idx, result.total_files)

            try:
                self._index_file(file_path, result)
                result.files_scanned += 1
            except Exception as e:
                error_msg = f"{file_path}: {str(e)}"
                result.errors.append(error_msg)
                result.files_with_errors += 1
                logger.warning(f"Error indexing {error_msg}")

        if self.progress_callback:
            self.progress_callback(result.total_files, result.total_files)

        return result

    def _index_file(self, file_path: Path, result: IndexResult) -> None:
        """
        Index a single file: extract symbols, imports, calls.

        Args:
            file_path: Absolute path to Python file
            result: IndexResult to update with counts

        Raises:
            Exception: If file cannot be read or parsed (caught by caller)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.suffix == '.py':
            raise ValueError(f"Not a Python file: {file_path}")

        # Read source
        try:
            source = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as e:
            raise ValueError(f"Cannot decode file: {e}")

        # Extract symbols
        symbols = self.symbol_extractor.extract_symbols(file_path, source)
        result.total_symbols += len(symbols)

        # Extract imports
        imports = self.import_builder.extract_imports(file_path, source)
        result.total_imports += len(imports)

        # Extract calls (requires symbols for context)
        calls = self.call_builder.extract_calls(file_path, source, symbols)
        result.total_calls += len(calls)

    def can_accept_error_rate(self, result: IndexResult) -> bool:
        """
        Check if error rate is acceptable.

        Args:
            result: IndexResult from indexing

        Returns:
            True if success rate >= error_threshold, False otherwise
        """
        return result.success_rate >= (self.error_threshold * 100)

    def watch(self) -> None:
        """
        Enter watch mode: monitor for file changes and re-index.

        Watches for Python file changes (added, modified, deleted) and re-indexes
        changed files only. Blocks until interrupted (Ctrl+C).

        Process:
            1. Start file watcher
            2. On file change, re-index changed file only
            3. Report results
            4. Stop on KeyboardInterrupt or error
        """
        try:
            watcher = FileWatcher(self.repo_root, on_change=self._on_file_change)
            watcher.start()

            logger.info("Watch mode started. Press Ctrl+C to stop.")

            # Block indefinitely until interrupted
            import time
            try:
                while watcher.is_running():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                logger.info("Watch mode interrupted by user")

            watcher.stop()

        except ImportError as e:
            logger.error(f"Cannot start watch mode: {e}")
            raise

    def _on_file_change(self, file_path: Path, action: str) -> None:
        """
        Callback when a file changes in watch mode.

        Args:
            file_path: Path to changed file
            action: 'added', 'modified', or 'deleted'
        """
        try:
            if action == 'deleted':
                logger.info(f"Deleted: {file_path.name}")
                return

            if file_path.suffix != '.py':
                return

            logger.info(f"Changed ({action}): {file_path.relative_to(self.repo_root)}")

            # Re-index just this file
            result = self.index_files([file_path])

            if result.error_count > 0:
                for error in result.errors:
                    logger.warning(error)
            else:
                logger.info(
                    f"✓ {result.total_symbols} symbols, "
                    f"{result.total_imports} imports, "
                    f"{result.total_calls} calls"
                )

        except Exception as e:
            logger.error(f"Error processing change: {e}")
