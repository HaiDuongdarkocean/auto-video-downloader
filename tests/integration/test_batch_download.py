"""Integration tests for batch download with thread pool coordination.

Verifies that the DownloadCoordinator correctly manages concurrent downloads,
aggregates progress, handles per-video failures, and supports cancellation —
all with real thread pool execution against mock FFmpeg.
"""

import os
import tempfile
import threading

import pytest

from src.core.download.download_coordinator import DownloadCoordinator
from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.ports.ffmpeg_port import FFmpegPort
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter
from src.core.video_extractor import VideoInfo


class TestBatchDownloadCoordination:
    """Batch download integration with real ThreadPoolExecutor."""

    def _make_videos(self, n: int) -> list:
        return [
            VideoInfo(
                url=f"https://example.com/ep{i}",
                title=f"Episode {i}",
                m3u8_link=f"https://cdn.example.com/ep{i}.m3u8",
            )
            for i in range(1, n + 1)
        ]

    def test_batch_all_succeed(self):
        ffmpeg = MockFFmpegAdapter()
        coordinator = DownloadCoordinator(
            M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=tempfile.mkdtemp()
        )
        videos = self._make_videos(5)
        progress_values = []
        results = coordinator.download_videos(videos, max_concurrent=3, progress_callback=progress_values.append)

        assert len(results) == 5
        assert all(r.success for r in results)
        assert progress_values[-1] == 100.0
        assert progress_values == sorted(progress_values)

    def test_batch_preserves_input_order(self):
        ffmpeg = MockFFmpegAdapter()
        coordinator = DownloadCoordinator(
            M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=tempfile.mkdtemp()
        )
        videos = self._make_videos(4)
        results = coordinator.download_videos(videos, max_concurrent=3)

        assert [r.video_url for r in results] == [v.url for v in videos]

    def test_batch_partial_failure_does_not_crash(self):
        class _SelectiveFFmpeg(FFmpegPort):
            def __init__(self):
                self.commands_run = []
                self._call_count = 0

            def check_available(self):
                return True

            def get_path(self):
                return "selective"

            def run_command(self, args, progress_callback=None):
                self._call_count += 1
                self.commands_run.append(args)
                if self._call_count == 1:
                    raise RuntimeError("Simulated failure on first command")
                if progress_callback:
                    progress_callback(100.0)
                import subprocess
                return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        ffmpeg = _SelectiveFFmpeg()
        coordinator = DownloadCoordinator(
            M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=tempfile.mkdtemp()
        )
        videos = self._make_videos(3)
        results = coordinator.download_videos(videos, max_concurrent=1)

        assert len(results) == 3
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]
        assert len(successes) >= 1
        assert len(failures) >= 1
        assert all(f.error for f in failures)

    def test_batch_cancellation_skips_remaining(self):
        ffmpeg = MockFFmpegAdapter()
        coordinator = DownloadCoordinator(
            M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=tempfile.mkdtemp()
        )
        videos = self._make_videos(5)
        cancel_event = threading.Event()
        progress_count = 0

        def on_progress(pct):
            nonlocal progress_count
            progress_count += 1
            if progress_count == 2:
                cancel_event.set()

        results = coordinator.download_videos(
            videos, max_concurrent=1, progress_callback=on_progress, cancel_event=cancel_event
        )

        cancelled = [r for r in results if r.error == "cancelled"]
        succeeded = [r for r in results if r.success]
        assert len(succeeded) >= 2
        assert len(cancelled) >= 1

    def test_batch_empty_list_returns_empty(self):
        ffmpeg = MockFFmpegAdapter()
        coordinator = DownloadCoordinator(
            M3U8Downloader(ffmpeg), VideoConverter(ffmpeg), base_dir=tempfile.mkdtemp()
        )
        progress_values = []
        results = coordinator.download_videos([], progress_callback=progress_values.append)
        assert results == []
        assert progress_values == [100.0]
