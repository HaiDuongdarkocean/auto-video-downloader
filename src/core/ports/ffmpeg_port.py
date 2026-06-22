from abc import ABC, abstractmethod
from typing import List, Optional, Callable
import subprocess


class FFmpegPort(ABC):
    """Port interface for FFmpeg operations."""

    @abstractmethod
    def check_available(self) -> bool:
        """Check if FFmpeg is available on the system."""
        pass

    @abstractmethod
    def get_path(self) -> str:
        """Get the FFmpeg executable path."""
        pass

    @abstractmethod
    def run_command(
        self, args: List[str], progress_callback: Optional[Callable[[float], None]] = None
    ) -> subprocess.CompletedProcess:
        """Run an FFmpeg command with optional progress callback.

        Args:
            args: List of FFmpeg command arguments.
            progress_callback: Optional callback receiving progress percentage (0-100).

        Returns:
            CompletedProcess result from subprocess.

        Raises:
            RuntimeError: If FFmpeg command fails.
        """
        pass
