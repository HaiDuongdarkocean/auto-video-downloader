import os
import tempfile

from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter


class TestM3U8Downloader:
    """Tests for M3U8Downloader."""

    def test_download_calls_run_command_with_url_and_temp_path(self):
        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "video")
            downloader.download("http://example.com/stream.m3u8", output_path)
            assert len(ffmpeg.commands_run) == 1
            args = ffmpeg.commands_run[0]
            assert "http://example.com/stream.m3u8" in args
            assert any(str(a).endswith(".ts") for a in args)

    def test_download_returns_temp_file_path(self):
        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "video")
            result = downloader.download("http://example.com/stream.m3u8", output_path)
            assert result == output_path + ".ts"

    def test_download_forwards_progress_callback(self):
        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        progress_values = []
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "video")
            downloader.download(
                "http://example.com/stream.m3u8",
                output_path,
                progress_callback=progress_values.append,
            )
        assert progress_values == [100.0]

    def test_download_uses_overwrite_flag(self):
        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "video")
            downloader.download("http://example.com/stream.m3u8", output_path)
            assert "-y" in ffmpeg.commands_run[0]

    def test_download_skips_when_temp_file_exists(self):
        ffmpeg = MockFFmpegAdapter()
        downloader = M3U8Downloader(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            output_path = os.path.join(tmp, "video")
            temp_path = output_path + ".ts"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write("existing")
            result = downloader.download("http://example.com/stream.m3u8", output_path)
            assert result == temp_path
            assert ffmpeg.commands_run == []
