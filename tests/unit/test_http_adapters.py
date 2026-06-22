from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_http_adapter import MockHTTPAdapter


class TestMockHTTPAdapter:
    """Tests for MockHTTPAdapter."""

    def test_get_returns_default_response(self):
        adapter = MockHTTPAdapter()
        response = adapter.get("https://example.com")
        assert response.status_code == 200
        assert response.url == "https://example.com"
        assert response.text == ""

    def test_get_returns_preset_response(self):
        adapter = MockHTTPAdapter()
        expected = HTTPResponse(
            status_code=200,
            text="<html>test</html>",
            url="https://example.com",
            headers={"Content-Type": "text/html"},
        )
        adapter.set_response("https://example.com", expected)
        response = adapter.get("https://example.com")
        assert response.status_code == 200
        assert response.text == "<html>test</html>"
        assert response.headers["Content-Type"] == "text/html"

    def test_get_records_call(self):
        adapter = MockHTTPAdapter()
        adapter.get("https://example.com", timeout=10)
        assert len(adapter.get_calls) == 1
        assert adapter.get_calls[0]["url"] == "https://example.com"
        assert adapter.get_calls[0]["timeout"] == 10

    def test_post_returns_default_response(self):
        adapter = MockHTTPAdapter()
        response = adapter.post("https://example.com", data={"key": "value"})
        assert response.status_code == 200
        assert response.url == "https://example.com"

    def test_post_records_call(self):
        adapter = MockHTTPAdapter()
        adapter.post("https://example.com", data={"key": "value"}, timeout=15)
        assert len(adapter.post_calls) == 1
        assert adapter.post_calls[0]["data"] == {"key": "value"}
        assert adapter.post_calls[0]["timeout"] == 15
