from typing import Dict, Optional

import requests

from src.core.ports.http_port import HTTPPort, HTTPResponse


class RequestsAdapter(HTTPPort):
    """Production adapter for HTTP using requests library."""

    def get(self, url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        try:
            response = requests.get(url, timeout=timeout, headers=headers or {})
            return HTTPResponse(
                status_code=response.status_code,
                text=response.text,
                url=response.url,
                headers=dict(response.headers),
            )
        except requests.Timeout:
            raise TimeoutError(f"Request to {url} timed out after {timeout}s")
        except requests.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")

    def post(self, url: str, data: Dict, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        try:
            response = requests.post(url, data=data, timeout=timeout, headers=headers or {})
            return HTTPResponse(
                status_code=response.status_code,
                text=response.text,
                url=response.url,
                headers=dict(response.headers),
            )
        except requests.Timeout:
            raise TimeoutError(f"Request to {url} timed out after {timeout}s")
        except requests.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {e}")
