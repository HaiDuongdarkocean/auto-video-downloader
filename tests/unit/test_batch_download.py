import os
import tempfile
import threading

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import patch

from PyQt6.QtWidgets import QApplication, QListWidget, QProgressBar, QPushButton

from src.core.download.download_coordinator import DownloadCoordinator, DownloadResult
from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.history_manager import HistoryManager
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter
from src.core.video_extractor import VideoInfo
from src.gui.main_window import MainWindow


class FakeBatchCoordinator:
    """Test double simulating batch download with per-video progress."""

    def __init__(self, results=None):
        self._results = results if results is not None else []
        self.calls = []

    def download_videos(self, videos, max_concurrent=3, progress_callback=None, cancel_event=None):
        self.calls.append(
            {
                "videos": list(videos),
                "max_concurrent": max_concurrent,
                "cancel_event": cancel_event,
            }
        )
        total = len(videos)
        for i in range(total):
            if progress_callback is not None:
                progress_callback((i + 1) / total * 100.0)
        return list(self._results)


class _FakeConfig:
    """Minimal ConfigManager-like object returning preset values."""

    def __init__(self, concurrent_downloads=3):
        self._data = {"concurrent_downloads": concurrent_downloads}

    def get(self, key, default=None):
        return self._data.get(key, default)


class TestCoordinatorCancellation:
    """Tests for DownloadCoordinator cancellation support."""

    def _make_coordinator(self, ffmpeg, base_dir):
        downloader = M3U8Downloader(ffmpeg)
        converter = VideoConverter(ffmpeg)
        return DownloadCoordinator(downloader, converter, base_dir=base_dir)

    def test_coordinator_cancel_skips_remaining(self):
        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [
                VideoInfo(url="http://example.com/p1", title="V1",
                          m3u8_link="http://example.com/s1.m3u8"),
                VideoInfo(url="http://example.com/p2", title="V2",
                          m3u8_link="http://example.com/s2.m3u8"),
                VideoInfo(url="http://example.com/p3", title="V3",
                          m3u8_link="http://example.com/s3.m3u8"),
            ]
            cancel_event = threading.Event()
            completed = {"count": 0}

            def cb(pct):
                completed["count"] += 1
                if completed["count"] >= 2:
                    cancel_event.set()

            results = coord.download_videos(
                videos,
                max_concurrent=1,
                progress_callback=cb,
                cancel_event=cancel_event,
            )
            assert len(results) == 3
            assert results[0].success is True
            assert results[1].success is True
            assert results[2].success is False
            assert results[2].error == "cancelled"

    def test_coordinator_without_cancel_works_as_before(self):
        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [
                VideoInfo(url="http://example.com/p1", title="V1",
                          m3u8_link="http://example.com/s1.m3u8"),
                VideoInfo(url="http://example.com/p2", title="V2",
                          m3u8_link="http://example.com/s2.m3u8"),
                VideoInfo(url="http://example.com/p3", title="V3",
                          m3u8_link="http://example.com/s3.m3u8"),
            ]
            results = coord.download_videos(videos)
            assert len(results) == 3
            assert all(r.success for r in results)


class TestGuiBatchDownload:
    """Tests for GUI batch download enhancements."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def _make_window(self, coordinator=None, config=None):
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        tmp.close()
        os.remove(tmp.name)
        history = HistoryManager(history_path=tmp.name)
        if config is None:
            config = _FakeConfig()
        return MainWindow(
            download_coordinator=coordinator,
            history_manager=history,
            config_manager=config,
        )

    def _three_videos(self):
        return [
            VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1"),
            VideoInfo(url="https://v/2", title="V2", m3u8_link="m3u8/2"),
            VideoInfo(url="https://v/3", title="V3", m3u8_link="m3u8/3"),
        ]

    def test_batch_download_populates_status_list(self):
        coordinator = FakeBatchCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", True, "/out/2.mp4", None),
                DownloadResult("https://v/3", True, "/out/3.mp4", None),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = self._three_videos()
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            status_list = window.findChild(QListWidget, "download_status_list")
            assert status_list.count() == 3
        finally:
            window.close()

    def test_batch_download_overall_progress_reaches_100(self):
        coordinator = FakeBatchCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", True, "/out/2.mp4", None),
                DownloadResult("https://v/3", True, "/out/3.mp4", None),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = self._three_videos()
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            bar = window.findChild(QProgressBar, "progress_bar")
            assert bar.value() == 100
        finally:
            window.close()

    def test_cancel_button_stops_download(self):
        coordinator = FakeBatchCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", True, "/out/2.mp4", None),
                DownloadResult("https://v/3", True, "/out/3.mp4", None),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = self._three_videos()
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            cancel_button = window.findChild(QPushButton, "cancel_button")
            cancel_button.click()
            assert window._cancel_event is not None
            assert window._cancel_event.is_set()
        finally:
            window.close()

    def test_batch_download_shows_per_video_status(self):
        coordinator = FakeBatchCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", False, "", "boom"),
                DownloadResult("https://v/3", True, "/out/3.mp4", None),
            ]
        )
        window = self._make_window(coordinator=coordinator)
        try:
            window._selected_videos = self._three_videos()
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            status_list = window.findChild(QListWidget, "download_status_list")
            texts = [status_list.item(i).text() for i in range(status_list.count())]
            assert "[complete]" in texts[0]
            assert "[failed]" in texts[1]
            assert "boom" in texts[1]
            assert "[complete]" in texts[2]
        finally:
            window.close()

    def test_batch_uses_max_concurrent_from_config(self):
        coordinator = FakeBatchCoordinator(
            results=[
                DownloadResult("https://v/1", True, "/out/1.mp4", None),
                DownloadResult("https://v/2", True, "/out/2.mp4", None),
            ]
        )
        config = _FakeConfig(concurrent_downloads=2)
        window = self._make_window(coordinator=coordinator, config=config)
        try:
            window._selected_videos = [
                VideoInfo(url="https://v/1", title="V1", m3u8_link="m3u8/1"),
                VideoInfo(url="https://v/2", title="V2", m3u8_link="m3u8/2"),
            ]
            with patch("src.gui.main_window.QMessageBox.information"):
                window.download_selected_videos()
            assert len(coordinator.calls) == 1
            assert coordinator.calls[0]["max_concurrent"] == 2
        finally:
            window.close()
