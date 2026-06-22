import subprocess

from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter
from src.core.ports.ffmpeg_adapter import FFmpegAdapter


class TestMockFFmpegAdapter:
    """Tests for MockFFmpegAdapter."""

    def test_check_available_default_true(self):
        adapter = MockFFmpegAdapter()
        assert adapter.check_available() is True

    def test_check_available_false(self):
        adapter = MockFFmpegAdapter(available=False)
        assert adapter.check_available() is False

    def test_get_path(self):
        adapter = MockFFmpegAdapter()
        assert adapter.get_path() == "mock_ffmpeg"

    def test_run_command_records_args(self):
        adapter = MockFFmpegAdapter()
        args = ["-i", "input.ts", "output.mp4"]
        result = adapter.run_command(args)
        assert adapter.commands_run == [args]
        assert result.returncode == 0

    def test_run_command_with_progress_callback(self):
        adapter = MockFFmpegAdapter()
        progress_values = []
        adapter.run_command(["-version"], progress_callback=progress_values.append)
        assert progress_values == [100.0]


class TestFFmpegAdapter:
    """Tests for FFmpegAdapter (production, only tests interface compliance)."""

    def test_get_path_default(self):
        adapter = FFmpegAdapter()
        assert adapter.get_path() == "ffmpeg"

    def test_get_path_custom(self):
        adapter = FFmpegAdapter(ffmpeg_path="/usr/local/bin/ffmpeg")
        assert adapter.get_path() == "/usr/local/bin/ffmpeg"
