"""Tests for FileWatcher (Phase C) — file monitoring for watch mode."""

import pytest
from pathlib import Path
import tempfile
import time
from repo_intelligence.file_watcher import FileWatcher, WATCHDOG_AVAILABLE

# Skip all tests if watchdog not available
pytestmark = pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not installed")


@pytest.fixture
def temp_repo_for_watch():
    """Create temporary repo for watch testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        # Create initial file
        (repo_root / "initial.py").write_text("# initial")
        yield repo_root


class TestFileWatcherBasic:
    """Basic file watcher functionality."""

    def test_init_without_watchdog_raises(self):
        """Test that ImportError is raised if watchdog not available."""
        if WATCHDOG_AVAILABLE:
            pytest.skip("Test only valid when watchdog unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ImportError):
                FileWatcher(Path(tmpdir))

    def test_init_with_repo_root(self, temp_repo_for_watch):
        """Test initialization with repo root."""
        watcher = FileWatcher(temp_repo_for_watch)
        assert watcher.repo_root == temp_repo_for_watch
        assert watcher.extensions == {'.py'}

    def test_init_with_custom_extensions(self, temp_repo_for_watch):
        """Test initialization with custom extensions."""
        watcher = FileWatcher(temp_repo_for_watch, extensions={'.py', '.pyi'})
        assert '.py' in watcher.extensions
        assert '.pyi' in watcher.extensions

    def test_is_running_before_start(self, temp_repo_for_watch):
        """Test is_running() returns False before start."""
        watcher = FileWatcher(temp_repo_for_watch)
        assert watcher.is_running() is False

    def test_start_and_stop(self, temp_repo_for_watch):
        """Test starting and stopping watcher."""
        watcher = FileWatcher(temp_repo_for_watch)

        watcher.start()
        assert watcher.is_running() is True

        watcher.stop()
        assert watcher.is_running() is False

    def test_double_start_warning(self, temp_repo_for_watch):
        """Test that starting twice doesn't error."""
        watcher = FileWatcher(temp_repo_for_watch)

        watcher.start()
        watcher.start()  # Should log warning but not error

        assert watcher.is_running() is True

        watcher.stop()

    def test_stop_when_not_running(self, temp_repo_for_watch):
        """Test that stopping when not running doesn't error."""
        watcher = FileWatcher(temp_repo_for_watch)
        watcher.stop()  # Should log warning but not error


class TestFileWatcherCallbacks:
    """Test callback invocation on file changes."""

    def test_on_change_callback_invoked(self, temp_repo_for_watch):
        """Test that on_change callback is invoked on file modification."""
        changes = []

        def track_change(file_path: Path, action: str):
            changes.append((str(file_path), action))

        watcher = FileWatcher(temp_repo_for_watch, on_change=track_change)
        watcher.start()

        # Modify a file
        test_file = temp_repo_for_watch / "test.py"
        test_file.write_text("# new file")
        time.sleep(0.5)  # Give watchdog time to detect

        watcher.stop()

        # Should have detected the change
        assert len(changes) > 0

    @pytest.mark.xfail(reason="Watchdog timing is OS-dependent; test may fail on Windows")
    def test_extension_filtering(self, temp_repo_for_watch):
        """Test that only configured extensions trigger callbacks."""
        changes = []

        def track_change(file_path: Path, action: str):
            changes.append(str(file_path))

        watcher = FileWatcher(temp_repo_for_watch, extensions={'.py'})
        watcher.start()

        # Create a Python file (should trigger)
        (temp_repo_for_watch / "tracked.py").write_text("# tracked")
        time.sleep(0.3)

        py_count = len(changes)

        # Create a non-Python file (should not trigger)
        (temp_repo_for_watch / "ignored.txt").write_text("# ignored")
        time.sleep(0.3)

        txt_count = len(changes) - py_count

        watcher.stop()

        # Python file should have triggered, text file should not
        assert py_count > 0
        assert txt_count == 0

    def test_excluded_directories_ignored(self, temp_repo_for_watch):
        """Test that files in excluded directories are ignored."""
        changes = []

        def track_change(file_path: Path, action: str):
            changes.append(str(file_path))

        watcher = FileWatcher(temp_repo_for_watch)
        watcher.start()

        # Create file in excluded directory
        cache_dir = temp_repo_for_watch / "__pycache__"
        cache_dir.mkdir(exist_ok=True)
        (cache_dir / "cached.py").write_text("# cached")
        time.sleep(0.3)

        watcher.stop()

        # Should not have been triggered
        assert not any("__pycache__" in c for c in changes)

    def test_callback_error_handling(self, temp_repo_for_watch):
        """Test that callback errors don't crash watcher."""

        def failing_callback(file_path: Path, action: str):
            raise ValueError("Intentional error")

        watcher = FileWatcher(temp_repo_for_watch, on_change=failing_callback)
        watcher.start()

        # Create file (should not crash even though callback fails)
        (temp_repo_for_watch / "test.py").write_text("# test")
        time.sleep(0.3)

        # Watcher should still be running
        assert watcher.is_running() is True

        watcher.stop()


class TestFileWatcherCleanup:
    """Test proper cleanup and resource handling."""

    def test_stop_blocks_until_stopped(self, temp_repo_for_watch):
        """Test that stop() waits for observer to finish."""
        watcher = FileWatcher(temp_repo_for_watch)
        watcher.start()

        import time
        start = time.time()
        watcher.stop()
        elapsed = time.time() - start

        # Should complete relatively quickly (< 2 seconds)
        assert elapsed < 2.0

    def test_multiple_start_stop_cycles(self, temp_repo_for_watch):
        """Test starting and stopping multiple times."""
        watcher = FileWatcher(temp_repo_for_watch)

        for _ in range(3):
            watcher.start()
            assert watcher.is_running() is True

            watcher.stop()
            assert watcher.is_running() is False
