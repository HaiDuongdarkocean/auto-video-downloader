from typing import Dict, Optional

from src.core.ports.http_port import HTTPPort, HTTPResponse


class MockHTTPAdapter(HTTPPort):
    """Mock adapter for HTTP used in testing."""

    def __init__(self):
        self._responses: Dict[str, HTTPResponse] = {}
        self.get_calls: list = []
        self.post_calls: list = []

    def set_response(self, url: str, response: HTTPResponse):
        """Pre-set a response for a given URL."""
        self._responses[url] = response

    def get(self, url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        self.get_calls.append({"url": url, "timeout": timeout, "headers": headers})
        if url in self._responses:
            return self._responses[url]
        return HTTPResponse(status_code=200, text="", url=url, headers={})

    def post(self, url: str, data: Dict, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        self.post_calls.append({"url": url, "data": data, "timeout": timeout, "headers": headers})
        if url in self._responses:
            return self._responses[url]
        return HTTPResponse(status_code=200, text="", url=url, headers={})
