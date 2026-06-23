import json
import os
import tempfile

from src.core.history_manager import HistoryManager, DownloadRecord


class TestHistoryManager:
    """Tests for HistoryManager."""

    def test_mark_then_is_downloaded_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            assert manager.is_downloaded("http://example.com/v1") is True

    def test_is_downloaded_false_for_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            assert manager.is_downloaded("http://example.com/unknown") is False

    def test_mark_downloaded_stores_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            record = manager.get_record("http://example.com/v1")
            assert record is not None
            assert record.title == "Video 1"
            assert record.path == "/downloads/v1.mp4"
            assert record.quality == "1080p"
            assert record.video_url == "http://example.com/v1"

    def test_mark_downloaded_auto_adds_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            record = manager.get_record("http://example.com/v1")
            assert record is not None
            assert isinstance(record.timestamp, str)
            assert len(record.timestamp) > 0

    def test_mark_downloaded_overwrites_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1 Updated", "path": "/downloads/v1_new.mp4", "quality": "720p"},
            )
            record = manager.get_record("http://example.com/v1")
            assert record is not None
            assert record.title == "Video 1 Updated"
            assert record.path == "/downloads/v1_new.mp4"
            assert record.quality == "720p"

    def test_get_history_returns_all_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            for i in range(3):
                manager.mark_downloaded(
                    f"http://example.com/v{i}",
                    {"title": f"Video {i}", "path": f"/downloads/v{i}.mp4", "quality": "1080p"},
                )
            records = manager.get_history()
            assert len(records) == 3
            urls = {r.video_url for r in records}
            assert urls == {
                "http://example.com/v0",
                "http://example.com/v1",
                "http://example.com/v2",
            }

    def test_get_history_empty_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            records = manager.get_history()
            assert records == []

    def test_get_record_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            record = manager.get_record("http://example.com/v1")
            assert isinstance(record, DownloadRecord)
            assert record.video_url == "http://example.com/v1"
            assert record.title == "Video 1"

    def test_get_record_missing_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            record = manager.get_record("http://example.com/missing")
            assert record is None

    def test_remove_existing_returns_true_and_removes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            assert manager.remove("http://example.com/v1") is True
            assert manager.is_downloaded("http://example.com/v1") is False
            assert manager.get_record("http://example.com/v1") is None

    def test_remove_missing_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            assert manager.remove("http://example.com/missing") is False

    def test_clear_empties_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            manager.mark_downloaded(
                "http://example.com/v2",
                {"title": "Video 2", "path": "/downloads/v2.mp4", "quality": "1080p"},
            )
            manager.clear()
            assert manager.get_history() == []
            assert manager.is_downloaded("http://example.com/v1") is False

    def test_persistence_across_instances(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            manager.mark_downloaded(
                "http://example.com/v1",
                {"title": "Video 1", "path": "/downloads/v1.mp4", "quality": "1080p"},
            )
            manager2 = HistoryManager(path)
            assert manager2.is_downloaded("http://example.com/v1") is True
            record = manager2.get_record("http://example.com/v1")
            assert record is not None
            assert record.title == "Video 1"

    def test_load_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            history = manager.load()
            assert history == {}

    def test_save_writes_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "history.json")
            manager = HistoryManager(path)
            history = {
                "http://example.com/v1": {
                    "timestamp": "2026-01-01T00:00:00",
                    "title": "Video 1",
                    "path": "/downloads/v1.mp4",
                    "quality": "1080p",
                }
            }
            manager.save(history)
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            assert "http://example.com/v1" in content
            assert content["http://example.com/v1"]["title"] == "Video 1"
