import json
import os
import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DownloadRecord:
    """A single download history entry.

    Attributes:
        video_url: Absolute URL of the downloaded video page.
        timestamp: ISO-formatted timestamp of the download.
        title: Human-readable video title.
        path: Local filesystem path of the downloaded file.
        quality: Requested/achieved quality (e.g. "1080p").
    """

    video_url: str
    timestamp: str
    title: str
    path: str
    quality: str


class HistoryManager:
    """Manages download history persisted in a JSON file.

    History is stored as a mapping of video_url to a metadata dict
    containing timestamp, title, path, and quality. Loading is lazy:
    the file is read on first access if the in-memory cache is empty.
    """

    def __init__(self, history_path: str = "history.json"):
        self._history_path = history_path
        self._history: Dict[str, Dict] = {}

    def load(self) -> Dict:
        """Load history from the JSON file.

        Returns an empty dict if the file does not exist.

        Returns:
            History dictionary keyed by video URL.
        """
        if os.path.exists(self._history_path):
            with open(self._history_path, "r", encoding="utf-8") as f:
                self._history = json.load(f)
        else:
            self._history = {}
        return self._history

    def save(self, history: Dict) -> None:
        """Save history to the JSON file.

        Args:
            history: History dictionary to persist.
        """
        self._history = history
        with open(self._history_path, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, ensure_ascii=False)

    def is_downloaded(self, video_url: str) -> bool:
        """Check whether a video URL has been recorded as downloaded.

        Args:
            video_url: Video URL to check.

        Returns:
            True if the URL is present in history, False otherwise.
        """
        if not self._history:
            self.load()
        return video_url in self._history

    def mark_downloaded(self, video_url: str, metadata: Dict) -> None:
        """Add or update a download history entry.

        Args:
            video_url: Video URL being recorded.
            metadata: Dict containing title, path, and quality. A
                timestamp is automatically added in ISO format.
        """
        if not self._history:
            self.load()
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "title": metadata.get("title", ""),
            "path": metadata.get("path", ""),
            "quality": metadata.get("quality", ""),
        }
        self._history[video_url] = entry
        self.save(self._history)

    def get_history(self) -> List[DownloadRecord]:
        """Return all history records as a list of DownloadRecord.

        Returns:
            List of DownloadRecord, one per stored entry.
        """
        if not self._history:
            self.load()
        return [
            DownloadRecord(
                video_url=url,
                timestamp=entry.get("timestamp", ""),
                title=entry.get("title", ""),
                path=entry.get("path", ""),
                quality=entry.get("quality", ""),
            )
            for url, entry in self._history.items()
        ]

    def get_record(self, video_url: str) -> Optional[DownloadRecord]:
        """Get a single download record by video URL.

        Args:
            video_url: Video URL to look up.

        Returns:
            DownloadRecord if present, None otherwise.
        """
        if not self._history:
            self.load()
        entry = self._history.get(video_url)
        if entry is None:
            return None
        return DownloadRecord(
            video_url=video_url,
            timestamp=entry.get("timestamp", ""),
            title=entry.get("title", ""),
            path=entry.get("path", ""),
            quality=entry.get("quality", ""),
        )

    def remove(self, video_url: str) -> bool:
        """Remove a download record by video URL.

        Args:
            video_url: Video URL to remove.

        Returns:
            True if the record existed and was removed, False otherwise.
        """
        if not self._history:
            self.load()
        if video_url not in self._history:
            return False
        del self._history[video_url]
        self.save(self._history)
        return True

    def clear(self) -> None:
        """Remove all download history."""
        if not self._history:
            self.load()
        self._history = {}
        self.save(self._history)
