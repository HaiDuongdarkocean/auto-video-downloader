import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.video_extractor import VideoInfo
from src.utils.logger import get_logger
from src.utils.path_helper import create_output_path

_logger = get_logger("download_coordinator")


@dataclass
class DownloadResult:
    """Result of a single video download attempt.

    Attributes:
        video_url: Source URL of the video page.
        success: True if download and conversion completed.
        output_path: Path to the final mp4 file on success, else empty.
        error: Error message on failure, else None.
    """

    video_url: str
    success: bool
    output_path: str
    error: Optional[str]


class DownloadCoordinator:
    """Coordinate batch downloads of multiple videos concurrently.

    Each video is downloaded to a .ts temp file via M3U8Downloader and then
    converted to mp4 via VideoConverter. Failures are isolated per video so
    one error does not abort the batch. Overall progress is reported as the
    fraction of completed videos (0-100).
    """

    def __init__(
        self,
        downloader: M3U8Downloader,
        converter: VideoConverter,
        base_dir: str = "./downloads",
    ):
        self._downloader = downloader
        self._converter = converter
        self._base_dir = base_dir

    def download_videos(
        self,
        videos: List[VideoInfo],
        max_concurrent: int = 3,
        progress_callback: Optional[Callable[[float], None]] = None,
        cancel_event: Optional[threading.Event] = None,
    ) -> List[DownloadResult]:
        """Download and convert a batch of videos concurrently.

        Args:
            videos: List of videos to download.
            max_concurrent: Maximum number of concurrent downloads.
            progress_callback: Optional callback receiving overall progress
                percentage (0-100) as videos complete.
            cancel_event: Optional threading.Event that, when set, causes
                remaining videos to be skipped and marked as cancelled.

        Returns:
            List of DownloadResult, one per input video, in input order.
        """
        total = len(videos)
        if total == 0:
            if progress_callback:
                progress_callback(100.0)
            return []
        results: List[Optional[DownloadResult]] = [None] * total
        completed = 0
        lock = threading.Lock()

        def process(index: int, video: VideoInfo) -> None:
            nonlocal completed
            if cancel_event is not None and cancel_event.is_set():
                with lock:
                    results[index] = DownloadResult(
                        video_url=video.url,
                        success=False,
                        output_path="",
                        error="cancelled",
                    )
                    completed += 1
                    if progress_callback:
                        progress_callback(completed / total * 100.0)
                return
            result = self._download_one(video)
            with lock:
                results[index] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed / total * 100.0)

        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [
                executor.submit(process, i, v) for i, v in enumerate(videos)
            ]
            for future in as_completed(futures):
                future.result()
        return [r for r in results if r is not None]

    def _download_one(self, video: VideoInfo) -> DownloadResult:
        try:
            folder = create_output_path(
                video.url, video.title, base_dir=self._base_dir
            )
            base = os.path.join(folder, os.path.basename(folder))
            temp_path = self._downloader.download(video.m3u8_link, base)
            output_path = self._converter.convert(temp_path, base + ".mp4")
            return DownloadResult(
                video_url=video.url,
                success=True,
                output_path=output_path,
                error=None,
            )
        except Exception as exc:
            _logger.error(
                "Download failed for %s (%s): %s",
                video.url,
                video.title,
                exc,
                exc_info=True,
            )
            return DownloadResult(
                video_url=video.url,
                success=False,
                output_path="",
                error=str(exc),
            )
