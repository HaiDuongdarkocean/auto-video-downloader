from typing import List

from src.core.tracking.watch_list_manager import WatchListEntry
from src.core.video_extractor import VideoExtractor, VideoInfo


class EpisodeTracker:
    """Detects new episodes for a tracked series.

    Wraps a VideoExtractor to fetch the current episode list for a watch list
    entry and compares the result against the entry's known_episodes. Only
    episodes whose URL is not already known are returned. The watch list entry
    is never mutated; the caller is responsible for persisting updates via
    WatchListManager.update_watch_list.
    """

    def __init__(self, video_extractor: VideoExtractor):
        self._video_extractor = video_extractor

    def check_for_updates(self, watch_list_entry: WatchListEntry) -> List[VideoInfo]:
        """Check a watch list entry for new episodes.

        Args:
            watch_list_entry: The watch list entry describing the page to
                watch and the episodes already known.

        Returns:
            List of VideoInfo for episodes whose URL is not present in
            watch_list_entry.known_episodes. Returns an empty list when no
            new episodes are found.
        """
        extracted = self._video_extractor.extract_video_links(
            watch_list_entry.url, watch_list_entry.selector
        )
        known = set(watch_list_entry.known_episodes)
        return [info for info in extracted if info.url not in known]
