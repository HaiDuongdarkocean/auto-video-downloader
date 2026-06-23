import os
import tempfile

from src.core.download.video_converter import VideoConverter
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter


class TestVideoConverter:
    """Tests for VideoConverter."""

    def test_convert_calls_run_command_with_input_and_output(self):
        ffmpeg = MockFFmpegAdapter()
        converter = VideoConverter(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "video.ts")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("data")
            output_path = os.path.join(tmp, "video.mp4")
            converter.convert(input_path, output_path)
            assert len(ffmpeg.commands_run) == 1
            args = ffmpeg.commands_run[0]
            assert input_path in args
            assert output_path in args

    def test_convert_returns_output_path(self):
        ffmpeg = MockFFmpegAdapter()
        converter = VideoConverter(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "video.ts")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("data")
            output_path = os.path.join(tmp, "video.mp4")
            result = converter.convert(input_path, output_path)
            assert result == output_path

    def test_convert_deletes_input_temp_file_after_success(self):
        ffmpeg = MockFFmpegAdapter()
        converter = VideoConverter(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "video.ts")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("data")
            output_path = os.path.join(tmp, "video.mp4")
            converter.convert(input_path, output_path)
            assert not os.path.exists(input_path)

    def test_convert_forwards_progress_callback(self):
        ffmpeg = MockFFmpegAdapter()
        converter = VideoConverter(ffmpeg)
        progress_values = []
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "video.ts")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("data")
            output_path = os.path.join(tmp, "video.mp4")
            converter.convert(
                input_path,
                output_path,
                progress_callback=progress_values.append,
            )
        assert progress_values == [100.0]

    def test_convert_uses_overwrite_flag(self):
        ffmpeg = MockFFmpegAdapter()
        converter = VideoConverter(ffmpeg)
        with tempfile.TemporaryDirectory() as tmp:
            input_path = os.path.join(tmp, "video.ts")
            with open(input_path, "w", encoding="utf-8") as f:
                f.write("data")
            output_path = os.path.join(tmp, "video.mp4")
            converter.convert(input_path, output_path)
            assert "-y" in ffmpeg.commands_run[0]
