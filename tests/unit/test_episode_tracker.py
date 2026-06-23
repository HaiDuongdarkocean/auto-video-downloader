import pytest

from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_http_adapter import MockHTTPAdapter
from src.core.tracking.episode_tracker import EpisodeTracker
from src.core.tracking.watch_list_manager import WatchListEntry
from src.core.video_extractor import VideoExtractor, VideoInfo


def _html_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "text/html"})


def _three_episode_html() -> str:
    return """
    <html><body>
      <ul>
        <li><a class="video" href="/series/ep1">Episode 1</a></li>
        <li><a class="video" href="/series/ep2">Episode 2</a></li>
        <li><a class="video" href="/series/ep3">Episode 3</a></li>
      </ul>
    </body></html>
    """


def _make_entry(url: str, selector: str, known_episodes=None) -> WatchListEntry:
    return WatchListEntry(
        watch_id="w1",
        url=url,
        selector=selector,
        schedule="0 * * * *",
        known_episodes=known_episodes if known_episodes is not None else [],
    )


def _make_extractor(html: str, url: str) -> VideoExtractor:
    http = MockHTTPAdapter()
    http.set_response(url, _html_response(url, html))
    return VideoExtractor(http)


class TestEpisodeTrackerCheckForUpdates:
    """Tests for EpisodeTracker.check_for_updates."""

    def test_no_new_episodes_returns_empty(self):
        url = "https://example.com/series"
        selector = "a.video"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, _three_episode_html()))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=[
            "https://example.com/series/ep1",
            "https://example.com/series/ep2",
            "https://example.com/series/ep3",
        ])

        new_episodes = tracker.check_for_updates(entry)

        assert new_episodes == []

    def test_all_new_when_known_empty(self):
        url = "https://example.com/series"
        selector = "a.video"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, _three_episode_html()))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=[])

        new_episodes = tracker.check_for_updates(entry)

        assert len(new_episodes) == 3
        urls = [e.url for e in new_episodes]
        assert "https://example.com/series/ep1" in urls
        assert "https://example.com/series/ep2" in urls
        assert "https://example.com/series/ep3" in urls

    def test_returns_only_new_episodes(self):
        url = "https://example.com/series"
        selector = "a.video"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, _three_episode_html()))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=["https://example.com/series/ep1"])

        new_episodes = tracker.check_for_updates(entry)

        assert len(new_episodes) == 2
        new_urls = [e.url for e in new_episodes]
        assert "https://example.com/series/ep1" not in new_urls
        assert "https://example.com/series/ep2" in new_urls
        assert "https://example.com/series/ep3" in new_urls

    def test_compares_by_url(self):
        url = "https://example.com/series"
        selector = "a.video"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, _three_episode_html()))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=["Episode 1", "Episode 2"])

        new_episodes = tracker.check_for_updates(entry)

        assert len(new_episodes) == 3

    def test_uses_extractor_with_watch_list_url_and_selector(self):
        url = "https://example.com/series"
        selector = "a.video"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, _three_episode_html()))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=[])

        tracker.check_for_updates(entry)

        assert len(http.get_calls) == 1
        assert http.get_calls[0]["url"] == url

    def test_empty_extraction_returns_empty(self):
        url = "https://example.com/series"
        selector = "a.video"
        html = "<html><body><p>nothing here</p></body></html>"
        http = MockHTTPAdapter()
        http.set_response(url, _html_response(url, html))
        extractor = VideoExtractor(http)
        tracker = EpisodeTracker(extractor)
        entry = _make_entry(url, selector, known_episodes=[])

        new_episodes = tracker.check_for_updates(entry)

        assert new_episodes == []
