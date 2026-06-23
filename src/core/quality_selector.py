import re
from typing import List, Tuple

from src.core.ports.http_port import HTTPPort


class QualitySelector:
    """Selects video quality from m3u8 master playlists."""

    def __init__(self, http: HTTPPort):
        self._http = http

    def get_available_qualities(self, m3u8_url: str) -> List[str]:
        """Fetch an m3u8 playlist and return available quality labels.

        Parses the master playlist for variant streams and extracts
        resolution-based labels (e.g. "1080p") falling back to
        bandwidth-based labels (e.g. "3000k") when no resolution is
        present. Qualities are sorted from highest to lowest.

        If the URL points to a media playlist (no variants) or an empty
        playlist, returns ["default"].

        Args:
            m3u8_url: URL of the m3u8 master or media playlist.

        Returns:
            List of quality labels sorted highest to lowest, or
            ["default"] when no variants are available.
        """
        response = self._http.get(m3u8_url)
        variants = self._parse_variants(response.text)
        if not variants:
            return ["default"]

        variants.sort(key=self._sort_key, reverse=True)
        return [self._label_for(variant) for variant in variants]

    def select_quality(self, qualities: List[str], preferred: str) -> str:
        """Select a quality from the available list.

        If the preferred quality is available it is returned. Otherwise
        the highest available quality is returned. If the list is empty,
        returns "default".

        Args:
            qualities: Available quality labels sorted highest to lowest.
            preferred: Desired quality label.

        Returns:
            The selected quality label.
        """
        if not qualities:
            return "default"
        if preferred in qualities:
            return preferred
        return qualities[0]

    @staticmethod
    def _parse_variants(text: str) -> List[Tuple[str, int]]:
        """Parse variant streams from a playlist.

        Returns a list of (label, sort_value) tuples where sort_value is
        the numeric height for resolution labels or the bandwidth for
        bandwidth labels.
        """
        variants: List[Tuple[str, int]] = []
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                inf = line
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                if not next_line or next_line.startswith("#"):
                    continue
                resolution_match = re.search(r"RESOLUTION=(\d+)x(\d+)", inf)
                bandwidth_match = re.search(r"BANDWIDTH=(\d+)", inf)
                if resolution_match:
                    height = int(resolution_match.group(2))
                    variants.append((f"{height}p", height))
                elif bandwidth_match:
                    bandwidth = int(bandwidth_match.group(1))
                    kbps = bandwidth // 1000
                    variants.append((f"{kbps}k", bandwidth))
        return variants

    @staticmethod
    def _label_for(variant: Tuple[str, int]) -> str:
        return variant[0]

    @staticmethod
    def _sort_key(variant: Tuple[str, int]) -> int:
        return variant[1]
