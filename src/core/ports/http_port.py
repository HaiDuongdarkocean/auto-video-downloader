from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class HTTPResponse:
    """HTTP response data."""
    status_code: int
    text: str
    url: str
    headers: Dict[str, str]


class HTTPPort(ABC):
    """Port interface for HTTP operations."""

    @abstractmethod
    def get(self, url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> HTTPResponse:
        """Perform an HTTP GET request.

        Args:
            url: The URL to fetch.
            timeout: Request timeout in seconds.
            headers: Optional request headers.

        Returns:
            HTTPResponse with status code, text, url, and headers.

        Raises:
            ConnectionError: If the request fails.
            TimeoutError: If the request times out.
        """
        pass

    @abstractmethod
    def post(
        self, url: str, data: Dict, timeout: int = 30, headers: Optional[Dict[str, str]] = None
    ) -> HTTPResponse:
        """Perform an HTTP POST request.

        Args:
            url: The URL to post to.
            data: Dictionary of data to send.
            timeout: Request timeout in seconds.
            headers: Optional request headers.

        Returns:
            HTTPResponse with status code, text, url, and headers.

        Raises:
            ConnectionError: If the request fails.
            TimeoutError: If the request times out.
        """
        pass
