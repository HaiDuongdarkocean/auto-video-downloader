import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class WatchListEntry:
    """A single watch list entry.

    Attributes:
        watch_id: Unique identifier for the watch list entry.
        url: URL of the page to watch.
        selector: CSS selector used to locate episodes.
        schedule: Cron expression describing the check schedule.
        auto_download: Whether to download new episodes automatically.
        notify: Whether to notify on new episodes.
        last_check: ISO-formatted timestamp of the last check.
        known_episodes: List of known episode identifiers/URLs.
    """

    watch_id: str
    url: str
    selector: str
    schedule: str
    auto_download: bool = False
    notify: bool = True
    last_check: str = ""
    known_episodes: List[str] = field(default_factory=list)


class WatchListManager:
    """Manages watch lists persisted in a JSON file.

    Watch lists are stored as a mapping of watch_id to an entry dict.
    Loading is lazy: the file is read on first access if the in-memory
    cache is empty.
    """

    def __init__(self, watch_list_path: str = "watch_list.json"):
        self._watch_list_path = watch_list_path
        self._watch_lists: Dict[str, Dict] = {}

    def load(self) -> Dict:
        """Load watch lists from the JSON file.

        Returns an empty dict if the file does not exist.

        Returns:
            Watch list dictionary keyed by watch_id.
        """
        if os.path.exists(self._watch_list_path):
            with open(self._watch_list_path, "r", encoding="utf-8") as f:
                self._watch_lists = json.load(f)
        else:
            self._watch_lists = {}
        return self._watch_lists

    def save(self, history: Dict) -> None:
        """Save watch lists to the JSON file.

        Args:
            history: Watch list dictionary to persist.
        """
        self._watch_lists = history
        with open(self._watch_list_path, "w", encoding="utf-8") as f:
            json.dump(self._watch_lists, f, indent=2, ensure_ascii=False)

    def add_watch_list(
        self,
        url: str,
        selector: str,
        schedule: str,
        auto_download: bool = False,
        notify: bool = True,
    ) -> str:
        """Create a new watch list entry.

        Args:
            url: URL of the page to watch.
            selector: CSS selector used to locate episodes.
            schedule: Cron expression describing the check schedule.
            auto_download: Whether to download new episodes automatically.
            notify: Whether to notify on new episodes.

        Returns:
            The generated watch_id.
        """
        if not self._watch_lists:
            self.load()
        watch_id = uuid.uuid4().hex
        self._watch_lists[watch_id] = {
            "url": url,
            "selector": selector,
            "schedule": schedule,
            "auto_download": auto_download,
            "notify": notify,
            "last_check": "",
            "known_episodes": [],
        }
        self.save(self._watch_lists)
        return watch_id

    def remove_watch_list(self, watch_id: str) -> bool:
        """Remove a watch list entry by id.

        Args:
            watch_id: Identifier of the entry to remove.

        Returns:
            True if the entry existed and was removed, False otherwise.
        """
        if not self._watch_lists:
            self.load()
        if watch_id not in self._watch_lists:
            return False
        del self._watch_lists[watch_id]
        self.save(self._watch_lists)
        return True

    def get_watch_list(self, watch_id: str) -> Optional[WatchListEntry]:
        """Get a single watch list entry by id.

        Args:
            watch_id: Identifier of the entry to look up.

        Returns:
            WatchListEntry if present, None otherwise.
        """
        if not self._watch_lists:
            self.load()
        entry = self._watch_lists.get(watch_id)
        if entry is None:
            return None
        return self._to_entry(watch_id, entry)

    def get_all_watch_lists(self) -> List[WatchListEntry]:
        """Return all watch list entries.

        Returns:
            List of WatchListEntry, one per stored entry.
        """
        if not self._watch_lists:
            self.load()
        return [
            self._to_entry(watch_id, entry)
            for watch_id, entry in self._watch_lists.items()
        ]

    def update_watch_list(self, watch_id: str, **kwargs) -> bool:
        """Update fields of a watch list entry.

        Args:
            watch_id: Identifier of the entry to update.
            **kwargs: Fields to update (schedule, auto_download, notify,
                last_check, known_episodes).

        Returns:
            True if the entry existed and was updated, False otherwise.
        """
        if not self._watch_lists:
            self.load()
        if watch_id not in self._watch_lists:
            return False
        entry = self._watch_lists[watch_id]
        for key, value in kwargs.items():
            if key in entry:
                entry[key] = value
        self.save(self._watch_lists)
        return True

    @staticmethod
    def _to_entry(watch_id: str, entry: Dict) -> WatchListEntry:
        return WatchListEntry(
            watch_id=watch_id,
            url=entry.get("url", ""),
            selector=entry.get("selector", ""),
            schedule=entry.get("schedule", ""),
            auto_download=entry.get("auto_download", False),
            notify=entry.get("notify", True),
            last_check=entry.get("last_check", ""),
            known_episodes=list(entry.get("known_episodes", [])),
        )
