import os
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import patch

from PyQt6.QtWidgets import QApplication, QProgressBar

from src.core.download.download_coordinator import DownloadResult
from src.core.history_manager import HistoryManager
from src.core.video_extractor import VideoInfo
from src.gui.main_window import MainWindow


class FakeDownloadCoordinator:
    """Test double for DownloadCoordinator that records calls and returns preset results."""

    def __init__(self, results=None):
        self._results = results if results is not None else []
        self.calls = []

    def download_videos(self, videos, max_concurrent=3, progress_callback=None, cancel_event=None):
        self.calls.append(
            {"videos": list(videos), "max_concurrent": max_concurrent}
        )
        if progress_callback is not None:
            progress_callback(100.0)
        return list(self._results)


class TestDownloadIntegration:
    """Tests for MainWindow download wiring."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def _make_window(self, coordinator=None, history=None):
        if history is None:
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            tmp.close()
            os.remove(tmp.name)
            history = HistoryManager(history_path=tmp.name)
        config = _FakeConfig()
        return MainWindow(
            download_coordinator=coordinator,
            history_manager=history,
            config_manager=config,
        )

    def test_download_selected_videos_calls_coordinator(self):
        coordinator = FakeDownloadCoordinator(
            results=[DownloadResult("https://v/1", True, "/out/1.mp4", None)]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = [
                VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1")
            ]
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            assert len(coordinator.calls) == 1
            assert coordinator.calls[0]["max_concurrent"] == 3
            assert len(coordinator.calls[0]["videos"]) == 1
        finally:
            window.close()

    def test_download_skips_duplicates(self):
        coordinator = FakeDownloadCoordinator(
            results=[DownloadResult("https://v/2", True, "/out/2.mp4", None)]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            dup = VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1")
            new = VideoInfo(url="https://v/2", title="V2", m3u8_link="m3u8/2")
            window._history_manager.mark_downloaded(
                "https://v/1", {"title": "V1", "path": "/out/1.mp4", "quality": "default"}
            )
            window._selected_videos = [dup, new]
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            assert len(coordinator.calls) == 1
            passed = coordinator.calls[0]["videos"]
            assert [v.url for v in passed] == ["https://v/2"]
        finally:
            window.close()

    def test_download_marks_successful_as_downloaded(self):
        coordinator = FakeDownloadCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", True, "/out/2.mp4", None),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = [
                VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1"),
                VideoInfo(url="https://v/2", title="V2", m3u8_link="m3u8/2"),
            ]
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            assert window._history_manager.is_downloaded("https://v/1")
            assert window._history_manager.is_downloaded("https://v/2")
        finally:
            window.close()

    def test_download_progress_updates_bar(self):
        window = self._make_window()
        try:
            window._on_download_progress(50.0)
            bar = window.findChild(QProgressBar, "progress_bar")
            assert bar.value() == 50
        finally:
            window.close()

    def test_download_all_duplicates_shows_info(self):
        coordinator = FakeDownloadCoordinator()
        window = self._make_window(coordinator=coordinator)
        try:
            v = VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1")
            window._history_manager.mark_downloaded(
                "https://v/1", {"title": "V1", "path": "/out/1.mp4", "quality": "default"}
            )
            window._selected_videos = [v]
            with patch("src.gui.main_window.QMessageBox.information") as info_mock:
                window.download_selected_videos()
            assert info_mock.called
            assert len(coordinator.calls) == 0
        finally:
            window.close()

    def test_download_handles_failures(self):
        coordinator = FakeDownloadCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", False, "", "boom"),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = [
                VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1"),
                VideoInfo(url="https://v/2", title="V2", m3u8_link="m3u8/2"),
            ]
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            assert window._history_manager.is_downloaded("https://v/1")
            assert not window._history_manager.is_downloaded("https://v/2")
        finally:
            window.close()


class _FakeConfig:
    """Minimal ConfigManager-like object returning preset values."""

    def __init__(self):
        self._data = {"concurrent_downloads": 3}

    def get(self, key, default=None):
        return self._data.get(key, default)
