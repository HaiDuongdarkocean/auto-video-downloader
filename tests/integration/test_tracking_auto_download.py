"""Integration tests for the tracking + auto-download flow.

Verifies that the tracking infrastructure composes correctly: watch list
management, episode detection, and auto-download of new episodes — all using
mock adapters for external dependencies.
"""

import os
import tempfile

import pytest

from src.core.download.download_coordinator import DownloadCoordinator
from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.history_manager import HistoryManager
from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter
from src.core.ports.mock_http_adapter import MockHTTPAdapter
from src.core.ports.mock_scheduler_adapter import MockSchedulerAdapter
from src.core.tracking.episode_tracker import EpisodeTracker
from src.core.tracking.scheduler_manager import SchedulerManager
from src.core.tracking.watch_list_manager import WatchListManager
from src.core.video_extractor import VideoExtractor


def _html_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "text/html"})


class TestTrackingAutoDownloadFlow:
    """End-to-end: add watch list, detect new episodes, auto-download them."""

    def test_add_watch_list_then_detect_new_episodes(self):
        html = """
        <html><body>
          <a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>
          <a class="video" href="/ep2" data-m3u8="https://cdn.example.com/ep2.m3u8">Episode 2</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series", _html_response("https://example.com/series", html))

        with tempfile.TemporaryDirectory() as base_dir:
            watch_list_path = os.path.join(base_dir, "watch_list.json")
            wlm = WatchListManager(watch_list_path)
            watch_id = wlm.add_watch_list(
                "https://example.com/series", "a.video", "0 * * * *", auto_download=True, notify=True
            )
            entry = wlm.get_watch_list(watch_id)
            assert entry.url == "https://example.com/series"

            extractor = VideoExtractor(http)
            tracker = EpisodeTracker(extractor)
            new_episodes = tracker.check_for_updates(entry)
            assert len(new_episodes) == 2

            wlm.update_watch_list(
                watch_id,
                known_episodes=[ep.url for ep in new_episodes],
                last_check="2026-06-22T12:00:00",
            )
            entry_updated = wlm.get_watch_list(watch_id)
            assert len(entry_updated.known_episodes) == 2

            second_check = tracker.check_for_updates(entry_updated)
            assert second_check == []

    def test_auto_download_new_episodes(self):
        html = """
        <html><body>
          <a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>
          <a class="video" href="/ep2" data-m3u8="https://cdn.example.com/ep2.m3u8">Episode 2</a>
          <a class="video" href="/ep3" data-m3u8="https://cdn.example.com/ep3.m3u8">Episode 3</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series", _html_response("https://example.com/series", html))

        with tempfile.TemporaryDirectory() as base_dir:
            wlm = WatchListManager(os.path.join(base_dir, "watch_list.json"))
            watch_id = wlm.add_watch_list(
                "https://example.com/series", "a.video", "0 * * * *", auto_download=True
            )
            wlm.update_watch_list(watch_id, known_episodes=["https://example.com/ep1"])
            entry = wlm.get_watch_list(watch_id)

            extractor = VideoExtractor(http)
            tracker = EpisodeTracker(extractor)
            new_episodes = tracker.check_for_updates(entry)
            assert len(new_episodes) == 2

            ffmpeg = MockFFmpegAdapter()
            coordinator = DownloadCoordinator(
                M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=base_dir
            )
            history = HistoryManager(os.path.join(base_dir, "history.json"))

            results = coordinator.download_videos(new_episodes, max_concurrent=2)
            assert all(r.success for r in results)

            for r in results:
                history.mark_downloaded(
                    r.video_url,
                    {"title": "Episode", "path": r.output_path, "quality": "1080p"},
                )

            for ep in new_episodes:
                assert history.is_downloaded(ep.url)

            wlm.update_watch_list(
                watch_id,
                known_episodes=[ep.url for ep in new_episodes] + ["https://example.com/ep1"],
            )

    def test_scheduler_lifecycle_with_watch_list(self):
        with tempfile.TemporaryDirectory() as base_dir:
            wlm = WatchListManager(os.path.join(base_dir, "watch_list.json"))
            scheduler = SchedulerManager(MockSchedulerAdapter())

            scheduler.start_scheduler()
            assert scheduler.is_running()

            watch_id = wlm.add_watch_list(
                "https://example.com/series", "a.video", "0 * * * *", auto_download=True
            )
            scheduler.add_job(watch_id, "0 * * * *", lambda: None)

            entry = wlm.get_watch_list(watch_id)
            assert entry is not None

            scheduler.remove_job(watch_id)
            scheduler.stop_scheduler()
            assert not scheduler.is_running()

    def test_notify_only_does_not_download(self):
        html = '<a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series", _html_response("https://example.com/series", html))

        with tempfile.TemporaryDirectory() as base_dir:
            wlm = WatchListManager(os.path.join(base_dir, "watch_list.json"))
            watch_id = wlm.add_watch_list(
                "https://example.com/series", "a.video", "0 * * * *",
                auto_download=False, notify=True,
            )
            entry = wlm.get_watch_list(watch_id)

            extractor = VideoExtractor(http)
            tracker = EpisodeTracker(extractor)
            new_episodes = tracker.check_for_updates(entry)
            assert len(new_episodes) == 1

            history = HistoryManager(os.path.join(base_dir, "history.json"))
            assert not history.is_downloaded(new_episodes[0].url)
