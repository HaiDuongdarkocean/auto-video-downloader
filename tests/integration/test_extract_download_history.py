"""Integration tests for the extract -> download -> history update flow.

These tests exercise the real core modules end-to-end using mock adapters
for external dependencies (HTTP, FFmpeg). They verify that the modules
compose correctly across boundaries.
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
from src.core.video_extractor import VideoExtractor


def _html_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "text/html"})


class TestExtractDownloadHistoryFlow:
    """End-to-end: extract video links, download, mark in history."""

    def test_extract_then_download_then_history(self):
        html = """
        <html><body>
          <a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>
          <a class="video" href="/ep2" data-m3u8="https://cdn.example.com/ep2.m3u8">Episode 2</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series", _html_response("https://example.com/series", html))
        extractor = VideoExtractor(http)

        videos = extractor.extract_video_links("https://example.com/series", "a.video")
        assert len(videos) == 2

        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        converter = VideoConverter(ffmpeg)

        with tempfile.TemporaryDirectory() as base_dir:
            coordinator = DownloadCoordinator(downloader, converter, base_dir=base_dir)
            history_path = os.path.join(base_dir, "history.json")
            history = HistoryManager(history_path)

            progress_values = []
            results = coordinator.download_videos(
                videos, max_concurrent=2, progress_callback=progress_values.append
            )

            assert len(results) == 2
            assert all(r.success for r in results)

            for result in results:
                history.mark_downloaded(
                    result.video_url,
                    {"title": "Episode", "path": result.output_path, "quality": "1080p"},
                )

            for video in videos:
                assert history.is_downloaded(video.url)

            records = history.get_history()
            assert len(records) == 2
            assert progress_values[-1] == 100.0

    def test_duplicate_download_skipped_by_history(self):
        html = '<a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)
        videos = extractor.extract_video_links("https://example.com", "a.video")
        assert len(videos) == 1

        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as base_dir:
            coordinator = DownloadCoordinator(
                M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=base_dir
            )
            history = HistoryManager(os.path.join(base_dir, "history.json"))

            results = coordinator.download_videos(videos, max_concurrent=1)
            for r in results:
                history.mark_downloaded(r.video_url, {"title": videos[0].title, "path": r.output_path, "quality": "1080p"})

            assert history.is_downloaded(videos[0].url)

            new_videos = [v for v in videos if not history.is_downloaded(v.url)]
            assert new_videos == []

    def test_persistence_across_sessions(self):
        html = '<a class="video" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Episode 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)
        videos = extractor.extract_video_links("https://example.com", "a.video")

        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as base_dir:
            history_path = os.path.join(base_dir, "history.json")
            coordinator = DownloadCoordinator(
                M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=base_dir
            )

            results = coordinator.download_videos(videos, max_concurrent=1)
            history1 = HistoryManager(history_path)
            history1.mark_downloaded(
                results[0].video_url,
                {"title": videos[0].title, "path": results[0].output_path, "quality": "1080p"},
            )

            history2 = HistoryManager(history_path)
            assert history2.is_downloaded(videos[0].url)
            record = history2.get_record(videos[0].url)
            assert record is not None
            assert record.title == "Episode 1"
