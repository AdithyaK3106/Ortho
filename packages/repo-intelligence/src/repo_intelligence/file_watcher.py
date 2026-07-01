"""File system watcher for live re-indexing during development."""

from pathlib import Path
from typing import Callable, Set, Optional
import logging

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False


logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches file system for changes and triggers re-indexing."""

    def __init__(
        self,
        repo_root: Path,
        on_change: Optional[Callable[[Path, str], None]] = None,
        extensions: Optional[Set[str]] = None,
    ) -> None:
        """
        Initialize file watcher.

        Args:
            repo_root: Repository root to watch
            on_change: Callback(file_path, action) when files change. Actions: 'added', 'modified', 'deleted'
            extensions: File extensions to watch (default: {'.py'})

        Raises:
            ImportError: If watchdog library not available
        """
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog library required for file watching. "
                "Install with: pip install watchdog"
            )

        self.repo_root = Path(repo_root)
        self.on_change = on_change
        self.extensions = extensions or {'.py'}
        self.observer: Optional[Observer] = None
        self._event_handler: Optional['_RepoEventHandler'] = None

    def start(self) -> None:
        """
        Start watching the repository for changes.

        Watches repo_root recursively for file modifications, creations, deletions.
        Filters to configured extensions and calls on_change callback.
        """
        if self.observer is not None:
            logger.warning("FileWatcher already started")
            return

        self._event_handler = _RepoEventHandler(
            repo_root=self.repo_root,
            extensions=self.extensions,
            on_change=self.on_change,
        )

        self.observer = Observer()
        self.observer.schedule(self._event_handler, str(self.repo_root), recursive=True)
        self.observer.start()
        logger.info(f"FileWatcher started: watching {self.repo_root}")

    def stop(self) -> None:
        """
        Stop watching for changes and cleanup.

        Blocks until observer thread stops (timeout: 10 seconds).
        """
        if self.observer is None:
            logger.warning("FileWatcher not started")
            return

        logger.info("Stopping FileWatcher...")
        self.observer.stop()
        self.observer.join(timeout=10)
        self.observer = None
        logger.info("FileWatcher stopped")

    def is_running(self) -> bool:
        """
        Check if watcher is currently running.

        Returns:
            True if observer thread is alive
        """
        return self.observer is not None and self.observer.is_alive()


class _RepoEventHandler(FileSystemEventHandler):
    """Internal event handler for watchdog."""

    def __init__(
        self,
        repo_root: Path,
        extensions: Set[str],
        on_change: Optional[Callable[[Path, str], None]],
    ) -> None:
        """Initialize event handler."""
        self.repo_root = Path(repo_root)
        self.extensions = extensions
        self.on_change = on_change

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification."""
        if not event.is_directory:
            self._check_and_trigger(event.src_path, 'modified')

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation."""
        if not event.is_directory:
            self._check_and_trigger(event.src_path, 'added')

    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion."""
        if not event.is_directory:
            self._check_and_trigger(event.src_path, 'deleted')

    def _check_and_trigger(self, file_path: str, action: str) -> None:
        """
        Check if file matches filters and trigger callback.

        Args:
            file_path: Path to file
            action: Action type ('added', 'modified', 'deleted')
        """
        path = Path(file_path)

        # Filter by extension
        if path.suffix not in self.extensions:
            return

        # Filter out excluded directories
        excluded = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.ortho'}
        if any(part in excluded for part in path.parts):
            return

        # Trigger callback
        if self.on_change:
            try:
                self.on_change(path, action)
            except Exception as e:
                logger.error(f"Error in on_change callback: {e}")
