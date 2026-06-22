from dataclasses import dataclass, field
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.core.ports.http_port import HTTPPort


@dataclass
class VideoInfo:
    """Metadata for a discovered video.

    Attributes:
        url: Absolute URL of the video page.
        title: Human-readable video title.
        m3u8_link: Direct m3u8 stream URL if available on the listing page,
            otherwise empty (to be resolved later from the video page).
    """

    url: str
    title: str
    m3u8_link: str = ""


class VideoExtractor:
    """Extract video links from web pages using a CSS selector.

    A deep module: the caller provides a URL and a CSS selector and receives a
    list of VideoInfo. HTML fetching, parsing, URL resolution, and pagination
    are handled internally.
    """

    def __init__(self, http_port: HTTPPort, timeout: int = 30):
        self._http = http_port
        self._timeout = timeout

    def extract_video_links(
        self,
        url: str,
        selector: str,
        next_selector: Optional[str] = None,
        max_pages: int = 1,
    ) -> List[VideoInfo]:
        """Extract video links from a page (and optionally following pagination).

        Args:
            url: URL of the listing page to scrape.
            selector: CSS selector matching video link elements.
            next_selector: Optional CSS selector for the "next page" link.
                When provided, pagination is followed up to max_pages.
            max_pages: Maximum number of pages to visit. Defaults to 1 (no
                pagination).

        Returns:
            List of VideoInfo, one per matched element with an href, in document
            order across all visited pages.

        Raises:
            RuntimeError: If an HTTP request fails or returns a non-2xx status.
        """
        results: List[VideoInfo] = []
        current_url = url
        pages_visited = 0

        while current_url and pages_visited < max_pages:
            html = self._fetch_html(current_url)
            soup = BeautifulSoup(html, "html.parser")

            for element in soup.select(selector):
                info = self._element_to_info(element, current_url)
                if info is not None:
                    results.append(info)

            pages_visited += 1

            if next_selector is None or pages_visited >= max_pages:
                break

            next_link = soup.select_one(next_selector)
            if next_link is None:
                break
            next_href = next_link.get("href")
            if not next_href:
                break
            current_url = urljoin(current_url, next_href)

        return results

    def _fetch_html(self, url: str) -> str:
        response = self._http.get(url, timeout=self._timeout)
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"Failed to fetch {url}: HTTP {response.status_code}")
        return response.text

    def _element_to_info(self, element, base_url: str) -> Optional[VideoInfo]:
        href = element.get("href")
        if not href:
            return None
        absolute_url = urljoin(base_url, href)
        title = (element.get_text(strip=True) or element.get("title") or "").strip()
        m3u8_link = element.get("data-m3u8") or element.get("data-src") or ""
        return VideoInfo(url=absolute_url, title=title, m3u8_link=m3u8_link)
