import subprocess
from typing import List, Optional, Callable

from src.core.ports.ffmpeg_port import FFmpegPort


class MockFFmpegAdapter(FFmpegPort):
    """Mock adapter for FFmpeg used in testing."""

    def __init__(self, available: bool = True):
        self._available = available
        self._path = "mock_ffmpeg"
        self.commands_run: List[List[str]] = []

    def check_available(self) -> bool:
        return self._available

    def get_path(self) -> str:
        return self._path

    def run_command(
        self, args: List[str], progress_callback: Optional[Callable[[float], None]] = None
    ) -> subprocess.CompletedProcess:
        self.commands_run.append(args)
        if progress_callback:
            progress_callback(100.0)
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="mock output", stderr=""
        )
