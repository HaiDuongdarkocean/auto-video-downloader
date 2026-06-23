import os
from typing import Callable, Optional

from src.core.ports.ffmpeg_port import FFmpegPort


class VideoConverter:
    """Convert a downloaded temp file to mp4 using FFmpeg.

    The input temp file is deleted after a successful conversion. If the
    conversion fails, the input file is left in place for debugging.
    """

    def __init__(self, ffmpeg_port: FFmpegPort):
        self._ffmpeg = ffmpeg_port

    def convert(
        self,
        input_path: str,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Convert an input file to mp4.

        Args:
            input_path: Path to the source file (e.g. a .ts temp file).
            output_path: Path to the target mp4 file.
            progress_callback: Optional callback receiving progress percentage.

        Returns:
            Path to the output mp4 file.
        """
        args = [
            "-y",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_path,
        ]
        self._ffmpeg.run_command(args, progress_callback=progress_callback)
        if os.path.exists(input_path):
            os.remove(input_path)
        return output_path
