import pytest

from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_http_adapter import MockHTTPAdapter
from src.core.video_extractor import VideoExtractor, VideoInfo


def _html_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "text/html"})


class TestVideoInfo:
    """Tests for VideoInfo data structure."""

    def test_has_url_title_m3u8_link(self):
        info = VideoInfo(url="https://example.com/v1", title="Ep 1", m3u8_link="https://m.example.com/v1.m3u8")
        assert info.url == "https://example.com/v1"
        assert info.title == "Ep 1"
        assert info.m3u8_link == "https://m.example.com/v1.m3u8"

    def test_m3u8_link_defaults_to_empty(self):
        info = VideoInfo(url="https://example.com/v1", title="Ep 1")
        assert info.m3u8_link == ""


class TestExtractVideoLinks:
    """Tests for VideoExtractor.extract_video_links."""

    def test_extracts_matching_elements(self):
        html = """
        <html><body>
          <ul>
            <li><a class="video" href="/series/ep1">Episode 1</a></li>
            <li><a class="video" href="/series/ep2">Episode 2</a></li>
            <li><a class="other" href="/other">Other</a></li>
          </ul>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series", _html_response("https://example.com/series", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com/series", "a.video")

        assert len(results) == 2
        assert results[0].title == "Episode 1"
        assert results[0].url == "https://example.com/series/ep1"
        assert results[1].title == "Episode 2"
        assert results[1].url == "https://example.com/series/ep2"

    def test_returns_empty_list_when_no_matches(self):
        html = "<html><body><p>nothing</p></body></html>"
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.video")
        assert results == []

    def test_resolves_relative_urls(self):
        html = '<html><body><a class="v" href="ep3.html">Ep 3</a></body></html>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com/series/list", _html_response("https://example.com/series/list", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com/series/list", "a.v")
        assert results[0].url == "https://example.com/series/ep3.html"

    def test_extracts_m3u8_from_data_attribute(self):
        html = '<a class="v" href="/ep1" data-m3u8="https://cdn.example.com/ep1.m3u8">Ep 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.v")
        assert results[0].m3u8_link == "https://cdn.example.com/ep1.m3u8"

    def test_m3u8_link_empty_when_no_data_attribute(self):
        html = '<a class="v" href="/ep1">Ep 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.v")
        assert results[0].m3u8_link == ""

    def test_uses_title_attribute_when_text_empty(self):
        html = '<a class="v" href="/ep1" title="Episode One"></a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.v")
        assert results[0].title == "Episode One"

    def test_skips_elements_without_href(self):
        html = '<a class="v">No link</a><a class="v" href="/ep1">Ep 1</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", html))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.v")
        assert len(results) == 1
        assert results[0].title == "Ep 1"

    def test_raises_on_http_error(self):
        http = MockHTTPAdapter()
        http.set_response(
            "https://example.com",
            HTTPResponse(status_code=500, text="", url="https://example.com", headers={}),
        )
        extractor = VideoExtractor(http)

        with pytest.raises(RuntimeError):
            extractor.extract_video_links("https://example.com", "a.v")


class TestPagination:
    """Tests for pagination handling."""

    def test_follows_next_selector(self):
        page1 = """
        <html><body>
          <a class="v" href="/ep1">Ep 1</a>
          <a class="next" href="/page2">Next</a>
        </body></html>
        """
        page2 = """
        <html><body>
          <a class="v" href="/ep2">Ep 2</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com/page1", _html_response("https://example.com/page1", page1))
        http.set_response("https://example.com/page2", _html_response("https://example.com/page2", page2))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links(
            "https://example.com/page1", "a.v", next_selector="a.next", max_pages=5
        )
        titles = [r.title for r in results]
        assert titles == ["Ep 1", "Ep 2"]

    def test_stops_when_no_next_link(self):
        page1 = """
        <html><body>
          <a class="v" href="/ep1">Ep 1</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", page1))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links(
            "https://example.com", "a.v", next_selector="a.next", max_pages=5
        )
        assert len(results) == 1

    def test_respects_max_pages_limit(self):
        page1 = '<a class="v" href="/ep1">Ep 1</a><a class="next" href="/page2">Next</a>'
        page2 = '<a class="v" href="/ep2">Ep 2</a><a class="next" href="/page3">Next</a>'
        page3 = '<a class="v" href="/ep3">Ep 3</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com/p1", _html_response("https://example.com/p1", page1))
        http.set_response("https://example.com/page2", _html_response("https://example.com/page2", page2))
        http.set_response("https://example.com/page3", _html_response("https://example.com/page3", page3))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links(
            "https://example.com/p1", "a.v", next_selector="a.next", max_pages=2
        )
        titles = [r.title for r in results]
        assert titles == ["Ep 1", "Ep 2"]

    def test_no_pagination_by_default(self):
        page1 = '<a class="v" href="/ep1">Ep 1</a><a class="next" href="/page2">Next</a>'
        page2 = '<a class="v" href="/ep2">Ep 2</a>'
        http = MockHTTPAdapter()
        http.set_response("https://example.com", _html_response("https://example.com", page1))
        http.set_response("https://example.com/page2", _html_response("https://example.com/page2", page2))
        extractor = VideoExtractor(http)

        results = extractor.extract_video_links("https://example.com", "a.v")
        assert len(results) == 1
        assert results[0].title == "Ep 1"
