import os
import tempfile

from src.core.tracking.watch_list_manager import WatchListManager, WatchListEntry


class TestWatchListManager:
    """Tests for WatchListManager."""

    def test_add_watch_list_returns_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            assert isinstance(watch_id, str)
            assert len(watch_id) > 0

    def test_add_watch_list_stores_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            entry = manager.get_watch_list(watch_id)
            assert entry is not None
            assert entry.url == "http://example.com/series"
            assert entry.selector == ".episode-list"
            assert entry.schedule == "0 * * * *"

    def test_get_watch_list_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            entry = manager.get_watch_list(watch_id)
            assert isinstance(entry, WatchListEntry)
            assert entry.watch_id == watch_id

    def test_get_watch_list_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            assert manager.get_watch_list("nonexistent") is None

    def test_get_all_watch_lists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            manager.add_watch_list("http://example.com/a", ".a", "0 * * * *")
            manager.add_watch_list("http://example.com/b", ".b", "0 * * * *")
            entries = manager.get_all_watch_lists()
            assert len(entries) == 2
            urls = {e.url for e in entries}
            assert urls == {"http://example.com/a", "http://example.com/b"}

    def test_get_all_empty_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            assert manager.get_all_watch_lists() == []

    def test_remove_existing_returns_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            assert manager.remove_watch_list(watch_id) is True
            assert manager.get_watch_list(watch_id) is None

    def test_remove_missing_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            assert manager.remove_watch_list("nonexistent") is False

    def test_update_watch_list_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            assert (
                manager.update_watch_list(
                    watch_id, schedule="30 * * * *", auto_download=True
                )
                is True
            )
            entry = manager.get_watch_list(watch_id)
            assert entry.schedule == "30 * * * *"
            assert entry.auto_download is True

    def test_update_watch_list_missing_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            assert manager.update_watch_list("nonexistent", schedule="* * * * *") is False

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            manager2 = WatchListManager(path)
            entry = manager2.get_watch_list(watch_id)
            assert entry is not None
            assert entry.url == "http://example.com/series"

    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            assert manager.load() == {}

    def test_default_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "watch_list.json")
            manager = WatchListManager(path)
            watch_id = manager.add_watch_list(
                "http://example.com/series",
                ".episode-list",
                "0 * * * *",
            )
            entry = manager.get_watch_list(watch_id)
            assert entry.auto_download is False
            assert entry.notify is True
            assert entry.known_episodes == []
