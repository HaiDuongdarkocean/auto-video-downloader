import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import patch

from PyQt6.QtWidgets import QApplication, QLineEdit

from src.core.ports.http_port import HTTPResponse
from src.core.ports.mock_http_adapter import MockHTTPAdapter
from src.core.video_extractor import VideoExtractor, VideoInfo
from src.gui.main_window import MainWindow


def _html_response(url: str, body: str) -> HTTPResponse:
    return HTTPResponse(status_code=200, text=body, url=url, headers={"Content-Type": "text/html"})


class _NoopCoordinator:
    """Coordinator double that completes instantly without downloading."""

    def download_videos(self, videos, max_concurrent=3, progress_callback=None):
        if progress_callback is not None:
            progress_callback(100.0)
        return []


class TestExtractIntegration:
    """Tests for MainWindow extract wiring."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def _make_window(self, http: MockHTTPAdapter, coordinator=None) -> MainWindow:
        extractor = VideoExtractor(http)
        return MainWindow(extractor=extractor, download_coordinator=coordinator)

    def test_extract_with_empty_url_shows_warning(self):
        http = MockHTTPAdapter()
        window = self._make_window(http)
        try:
            url_input = window.findChild(QLineEdit, "url_input")
            selector_input = window.findChild(QLineEdit, "selector_input")
            url_input.setText("")
            selector_input.setText("a.video")
            with patch("src.gui.main_window.QMessageBox.warning") as warning_mock:
                results = window.extract_videos()
            assert results == []
            assert warning_mock.called
            assert window.get_selected_videos() == []
        finally:
            window.close()

    def test_extract_with_empty_selector_shows_warning(self):
        http = MockHTTPAdapter()
        window = self._make_window(http)
        try:
            url_input = window.findChild(QLineEdit, "url_input")
            selector_input = window.findChild(QLineEdit, "selector_input")
            url_input.setText("https://example.com")
            selector_input.setText("")
            with patch("src.gui.main_window.QMessageBox.warning") as warning_mock:
                results = window.extract_videos()
            assert results == []
            assert warning_mock.called
        finally:
            window.close()

    def test_extract_populates_selected_videos(self):
        html = """
        <html><body>
          <a class="video" href="/series/ep1">Episode 1</a>
          <a class="video" href="/series/ep2">Episode 2</a>
        </body></html>
        """
        http = MockHTTPAdapter()
        http.set_response(
            "https://example.com/series",
            _html_response("https://example.com/series", html),
        )
        window = self._make_window(http, coordinator=_NoopCoordinator())
        try:
            url_input = window.findChild(QLineEdit, "url_input")
            selector_input = window.findChild(QLineEdit, "selector_input")
            url_input.setText("https://example.com/series")
            selector_input.setText("a.video")

            results = window.extract_videos()
            assert len(results) == 2
            assert results[0].title == "Episode 1"
            assert results[1].title == "Episode 2"

            fake_selected = [results[0]]
            with patch("src.gui.main_window.DownloadDialog") as dialog_mock, patch(
                "src.gui.main_window.QMessageBox.information"
            ):
                instance = dialog_mock.return_value
                instance.exec.return_value = 1
                instance.get_selected_videos.return_value = fake_selected
                window._on_extract_clicked()

            assert window.get_selected_videos() == fake_selected
        finally:
            window.close()

    def test_extract_empty_results_shows_information(self):
        http = MockHTTPAdapter()
        http.set_response(
            "https://example.com",
            _html_response("https://example.com", "<html><body></body></html>"),
        )
        window = self._make_window(http)
        try:
            url_input = window.findChild(QLineEdit, "url_input")
            selector_input = window.findChild(QLineEdit, "selector_input")
            url_input.setText("https://example.com")
            selector_input.setText("a.video")
            with patch("src.gui.main_window.QMessageBox.information") as info_mock, patch(
                "src.gui.main_window.DownloadDialog"
            ) as dialog_mock:
                window._on_extract_clicked()
            assert info_mock.called
            assert not dialog_mock.called
            assert window.get_selected_videos() == []
        finally:
            window.close()
