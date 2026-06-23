import os
from typing import Callable, Optional

from src.core.ports.ffmpeg_port import FFmpegPort


class M3U8Downloader:
    """Download an m3u8 stream to a temporary .ts file using FFmpeg.

    Resume behavior: if a temp file already exists at ``output_path + ".ts"``,
    the download is skipped and the existing temp file path is returned. This
    assumes a previous (possibly interrupted) run produced a usable file; the
    caller may delete the temp file to force a fresh download.
    """

    def __init__(self, ffmpeg_port: FFmpegPort):
        self._ffmpeg = ffmpeg_port

    def download(
        self,
        m3u8_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> str:
        """Download an m3u8 stream to a .ts temp file.

        Args:
            m3u8_url: URL of the m3u8 playlist.
            output_path: Base output path (without extension). The temp file
                is written to ``output_path + ".ts"``.
            progress_callback: Optional callback receiving progress percentage.

        Returns:
            Path to the temp .ts file.
        """
        temp_path = output_path + ".ts"
        if os.path.exists(temp_path):
            return temp_path
        args = [
            "-y",
            "-i",
            m3u8_url,
            "-c",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            temp_path,
        ]
        self._ffmpeg.run_command(args, progress_callback=progress_callback)
        return temp_path
