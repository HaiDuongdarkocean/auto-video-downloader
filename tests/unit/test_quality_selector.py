import pytest

from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_http_adapter import MockHTTPAdapter
from src.core.quality_selector import QualitySelector


def _m3u8_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "application/vnd.apple.mpegurl"})


MASTER_PLAYLIST = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
720p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480
480p.m3u8
"""

MEDIA_PLAYLIST = """#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
segment0.ts
#EXT-X-ENDLIST
"""


class TestGetAvailableQualities:
    """Tests for QualitySelector.get_available_qualities."""

    def test_get_qualities_from_master_playlist(self):
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/master.m3u8", _m3u8_response("https://cdn.example.com/master.m3u8", MASTER_PLAYLIST))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/master.m3u8")

        assert len(qualities) == 3

    def test_get_qualities_returns_highest_first(self):
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/master.m3u8", _m3u8_response("https://cdn.example.com/master.m3u8", MASTER_PLAYLIST))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/master.m3u8")

        assert qualities == ["1080p", "720p", "480p"]

    def test_get_qualities_media_playlist_returns_default(self):
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/media.m3u8", _m3u8_response("https://cdn.example.com/media.m3u8", MEDIA_PLAYLIST))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/media.m3u8")

        assert qualities == ["default"]

    def test_get_qualities_empty_playlist_returns_default(self):
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/empty.m3u8", _m3u8_response("https://cdn.example.com/empty.m3u8", "#EXTM3U\n"))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/empty.m3u8")

        assert qualities == ["default"]

    def test_get_qualities_extracts_resolution_labels(self):
        playlist = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
720p.m3u8
"""
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/master.m3u8", _m3u8_response("https://cdn.example.com/master.m3u8", playlist))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/master.m3u8")

        assert qualities == ["1080p", "720p"]

    def test_get_qualities_falls_back_to_bandwidth_when_no_resolution(self):
        playlist = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=3000000
high.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000000
low.m3u8
"""
        http = MockHTTPAdapter()
        http.set_response("https://cdn.example.com/master.m3u8", _m3u8_response("https://cdn.example.com/master.m3u8", playlist))
        selector = QualitySelector(http)

        qualities = selector.get_available_qualities("https://cdn.example.com/master.m3u8")

        assert qualities == ["3000k", "1000k"]


class TestSelectQuality:
    """Tests for QualitySelector.select_quality."""

    def test_select_quality_preferred_available(self):
        http = MockHTTPAdapter()
        selector = QualitySelector(http)

        assert selector.select_quality(["1080p", "720p"], "720p") == "720p"

    def test_select_quality_preferred_not_available_returns_highest(self):
        http = MockHTTPAdapter()
        selector = QualitySelector(http)

        assert selector.select_quality(["720p", "480p"], "1080p") == "720p"

    def test_select_quality_empty_returns_default(self):
        http = MockHTTPAdapter()
        selector = QualitySelector(http)

        assert selector.select_quality([], "1080p") == "default"
