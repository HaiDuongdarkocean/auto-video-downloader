import os
import tempfile
import threading

from src.core.download.download_coordinator import DownloadCoordinator, DownloadResult
from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.ports.ffmpeg_port import FFmpegPort
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter
from src.core.video_extractor import VideoInfo


class _FailingFFmpeg(FFmpegPort):
    """FFmpeg port that always fails run_command."""

    def __init__(self):
        self.commands_run = []

    def check_available(self) -> bool:
        return True

    def get_path(self) -> str:
        return "failing_ffmpeg"

    def run_command(self, args, progress_callback=None):
        import subprocess
        self.commands_run.append(args)
        raise RuntimeError("ffmpeg failed")


class _SelectiveFFmpeg(FFmpegPort):
    """FFmpeg port that fails for specific m3u8 urls."""

    def __init__(self, fail_urls):
        self._fail_urls = set(fail_urls)
        self.commands_run = []

    def check_available(self) -> bool:
        return True

    def get_path(self) -> str:
        return "selective_ffmpeg"

    def run_command(self, args, progress_callback=None):
        import subprocess
        self.commands_run.append(args)
        if any(u in args for u in self._fail_urls):
            raise RuntimeError("ffmpeg failed for " + str(args))
        if progress_callback:
            progress_callback(100.0)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")


class TestDownloadCoordinator:
    """Tests for DownloadCoordinator."""

    def _make_coordinator(self, ffmpeg, base_dir):
        downloader = M3U8Downloader(ffmpeg)
        converter = VideoConverter(ffmpeg)
        return DownloadCoordinator(downloader, converter, base_dir=base_dir)

    def test_downloads_single_video_end_to_end(self):
        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [VideoInfo(url="http://example.com/page", title="My Video",
                                m3u8_link="http://example.com/stream.m3u8")]
            results = coord.download_videos(videos)
            assert len(results) == 1
            assert results[0].success is True
            assert results[0].video_url == "http://example.com/page"
            assert results[0].error is None
            assert results[0].output_path.endswith(".mp4")

    def test_batch_downloads_multiple_videos(self):
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

    def test_respects_max_concurrent(self):
        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [
                VideoInfo(url="http://example.com/p%d" % i, title="V%d" % i,
                          m3u8_link="http://example.com/s%d.m3u8" % i)
                for i in range(5)
            ]
            results = coord.download_videos(videos, max_concurrent=2)
            assert len(results) == 5
            assert all(r.success for r in results)

    def test_aggregates_progress_ending_at_100(self):
        ffmpeg = MockFFmpegAdapter()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [
                VideoInfo(url="http://example.com/p%d" % i, title="V%d" % i,
                          m3u8_link="http://example.com/s%d.m3u8" % i)
                for i in range(4)
            ]
            progress_values = []
            coord.download_videos(videos, progress_callback=progress_values.append)
            assert progress_values[-1] == 100.0
            assert all(progress_values[i] <= progress_values[i + 1]
                       for i in range(len(progress_values) - 1))

    def test_handles_per_video_failure_gracefully(self):
        ffmpeg = _SelectiveFFmpeg(fail_urls=["http://example.com/s2.m3u8"])
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
            by_url = {r.video_url: r for r in results}
            assert by_url["http://example.com/p1"].success is True
            assert by_url["http://example.com/p2"].success is False
            assert by_url["http://example.com/p3"].success is True
            assert by_url["http://example.com/p2"].error is not None

    def test_returns_download_result_list_with_success_error_info(self):
        ffmpeg = _FailingFFmpeg()
        with tempfile.TemporaryDirectory() as tmp:
            coord = self._make_coordinator(ffmpeg, tmp)
            videos = [VideoInfo(url="http://example.com/p1", title="V1",
                                m3u8_link="http://example.com/s1.m3u8")]
            results = coord.download_videos(videos)
            assert isinstance(results, list)
            assert all(isinstance(r, DownloadResult) for r in results)
            assert results[0].success is False
            assert results[0].error is not None
            assert "ffmpeg failed" in results[0].error
