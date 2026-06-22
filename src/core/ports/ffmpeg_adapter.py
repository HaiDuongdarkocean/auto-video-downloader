import subprocess
from typing import List, Optional, Callable

from src.core.ports.ffmpeg_port import FFmpegPort


class FFmpegAdapter(FFmpegPort):
    """Production adapter for FFmpeg using subprocess."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self._ffmpeg_path = ffmpeg_path

    def check_available(self) -> bool:
        try:
            result = subprocess.run(
                [self._ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    def get_path(self) -> str:
        return self._ffmpeg_path

    def run_command(
        self, args: List[str], progress_callback: Optional[Callable[[float], None]] = None
    ) -> subprocess.CompletedProcess:
        cmd = [self._ffmpeg_path] + args
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg command failed: {process.stderr}")
        if progress_callback:
            progress_callback(100.0)
        return process
