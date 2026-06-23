import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QLineEdit, QMenuBar, QProgressBar, QPushButton

from src.gui.main_window import MainWindow


class TestMainWindow:
    """Smoke tests for the MainWindow GUI foundation."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def test_window_title_is_set(self):
        window = MainWindow()
        try:
            assert window.windowTitle() == "Video Downloader"
        finally:
            window.close()

    def test_has_url_input(self):
        window = MainWindow()
        try:
            url_input = window.findChild(QLineEdit, "url_input")
            assert url_input is not None
            assert url_input.placeholderText() == "Enter website URL..."
        finally:
            window.close()

    def test_has_selector_input(self):
        window = MainWindow()
        try:
            selector_input = window.findChild(QLineEdit, "selector_input")
            assert selector_input is not None
            assert selector_input.placeholderText() == "Enter CSS selector..."
        finally:
            window.close()

    def test_has_extract_button(self):
        window = MainWindow()
        try:
            button = window.findChild(QPushButton, "extract_button")
            assert button is not None
            assert button.text() == "Extract videos"
        finally:
            window.close()

    def test_has_progress_bar(self):
        window = MainWindow()
        try:
            bar = window.findChild(QProgressBar, "progress_bar")
            assert bar is not None
            assert bar.value() == 0
        finally:
            window.close()

    def test_has_menubar(self):
        window = MainWindow()
        try:
            menubar = window.findChild(QMenuBar)
            assert menubar is not None
            actions = [a.text() for a in menubar.actions()]
            assert any("File" in a for a in actions)
            assert any("Settings" in a for a in actions)
            assert any("Tracking" in a for a in actions)
            assert any("Help" in a for a in actions)
        finally:
            window.close()
