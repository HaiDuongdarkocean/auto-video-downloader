"""Main window for the video downloader GUI."""

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.config_manager import ConfigManager
from src.core.download.download_coordinator import DownloadCoordinator
from src.core.download.m3u8_downloader import M3U8Downloader
from src.core.download.video_converter import VideoConverter
from src.core.history_manager import HistoryManager
from src.core.ports.ffmpeg_adapter import FFmpegAdapter
from src.core.ports.requests_adapter import RequestsAdapter
from src.core.video_extractor import VideoExtractor, VideoInfo
from src.gui.download_dialog import DownloadDialog


DARK_THEME_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Sans Serif';
    font-size: 13px;
}
QFrame#Card {
    background-color: #313244;
    border-radius: 12px;
    padding: 16px;
}
QLabel {
    color: #cdd6f4;
    background: transparent;
}
QLabel#Title {
    font-size: 18px;
    font-weight: 600;
    color: #cba6f7;
}
QLineEdit {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 10px;
    color: #cdd6f4;
    selection-background-color: #cba6f7;
}
QLineEdit:focus {
    border: 1px solid #cba6f7;
}
QPushButton {
    background-color: #cba6f7;
    color: #1e1e2e;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton:pressed {
    background-color: #89b4fa;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QProgressBar {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    text-align: center;
    color: #cdd6f4;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #cba6f7;
    border-radius: 5px;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
}
QMenuBar::item:selected {
    background-color: #313244;
    border-radius: 4px;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #45475a;
}
"""


class MainWindow(QMainWindow):
    """Main application window with a card-based dark-themed layout."""

    def __init__(
        self,
        extractor: Optional[VideoExtractor] = None,
        download_coordinator: Optional[DownloadCoordinator] = None,
        history_manager: Optional[HistoryManager] = None,
        config_manager: Optional[ConfigManager] = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Video Downloader")
        self.resize(720, 480)
        self._url_input: QLineEdit = None  # type: ignore[assignment]
        self._selector_input: QLineEdit = None  # type: ignore[assignment]
        self._extract_button: QPushButton = None  # type: ignore[assignment]
        self._progress_bar: QProgressBar = None  # type: ignore[assignment]
        self._extractor: Optional[VideoExtractor] = extractor
        self._selected_videos: List[VideoInfo] = []
        self._download_coordinator: DownloadCoordinator = (
            download_coordinator
            if download_coordinator is not None
            else DownloadCoordinator(
                M3U8Downloader(FFmpegAdapter()),
                VideoConverter(FFmpegAdapter()),
            )
        )
        self._history_manager: HistoryManager = (
            history_manager if history_manager is not None else HistoryManager()
        )
        self._config_manager: ConfigManager = (
            config_manager if config_manager is not None else ConfigManager()
        )
        self._setup_ui()
        self._setup_menu()
        self._apply_theme()

    def _setup_ui(self) -> None:
        """Build the central card-based layout."""
        central = QWidget()
        self.setCentralWidget(central)

        outer = QVBoxLayout(central)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(12)

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        title = QLabel("Video Downloader")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title)

        url_label = QLabel("Website URL")
        card_layout.addWidget(url_label)
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Enter website URL...")
        self._url_input.setObjectName("url_input")
        card_layout.addWidget(self._url_input)

        selector_label = QLabel("CSS selector")
        card_layout.addWidget(selector_label)
        self._selector_input = QLineEdit()
        self._selector_input.setPlaceholderText("Enter CSS selector...")
        self._selector_input.setObjectName("selector_input")
        card_layout.addWidget(self._selector_input)

        self._extract_button = QPushButton("Extract videos")
        self._extract_button.setObjectName("extract_button")
        self._extract_button.clicked.connect(self._on_extract_clicked)
        card_layout.addWidget(self._extract_button)

        progress_label = QLabel("Progress")
        card_layout.addWidget(progress_label)
        self._progress_bar = QProgressBar()
        self._progress_bar.setObjectName("progress_bar")
        self._progress_bar.setValue(0)
        card_layout.addWidget(self._progress_bar)

        card_layout.addStretch(1)
        outer.addWidget(card)

    def _setup_menu(self) -> None:
        """Build the menu bar with File, Settings, Tracking, Help menus."""
        menubar: QMenuBar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        exit_action = QAction(QIcon.fromTheme("application-exit"), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        settings_menu = menubar.addMenu("&Settings")
        open_settings_action = QAction(QIcon.fromTheme("preferences-system"), "Open settings", self)
        open_settings_action.triggered.connect(self._on_open_settings)
        settings_menu.addAction(open_settings_action)

        tracking_menu = menubar.addMenu("&Tracking")
        open_tracking_action = QAction(QIcon.fromTheme("view-history"), "Open tracking", self)
        open_tracking_action.triggered.connect(self._on_open_tracking)
        tracking_menu.addAction(open_tracking_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction(QIcon.fromTheme("help-about"), "About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _apply_theme(self) -> None:
        """Apply the dark theme stylesheet to the window."""
        self.setStyleSheet(DARK_THEME_QSS)

    def _on_extract_clicked(self) -> None:
        """Handle the extract button: fetch videos and open the download dialog."""
        videos = self.extract_videos()
        if not videos:
            QMessageBox.information(self, "No videos", "No videos found.")
            return
        dialog = DownloadDialog(videos, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._selected_videos = dialog.get_selected_videos()
            if self._selected_videos:
                self.download_selected_videos()

    def extract_videos(self) -> List[VideoInfo]:
        """Read inputs and fetch video links using the configured extractor.

        Returns:
            List of VideoInfo discovered for the current URL and selector.
            Returns an empty list when inputs are missing.
        """
        url = self._url_input.text().strip()
        selector = self._selector_input.text().strip()
        if not url or not selector:
            QMessageBox.warning(
                self,
                "Missing input",
                "Please provide both a website URL and a CSS selector.",
            )
            return []
        extractor = self._extractor
        if extractor is None:
            extractor = VideoExtractor(RequestsAdapter())
        return extractor.extract_video_links(url, selector)

    def get_selected_videos(self) -> List[VideoInfo]:
        """Return the videos selected in the most recent download dialog."""
        return list(self._selected_videos)

    def download_selected_videos(self) -> None:
        """Download the currently selected videos, skipping already-downloaded ones.

        Filters out videos present in history, runs the download coordinator
        over the remaining videos, records successful downloads in history,
        and reports a summary dialog to the user.
        """
        selected = list(self._selected_videos)
        if not selected:
            return
        to_download: List[VideoInfo] = []
        for video in selected:
            if not self._history_manager.is_downloaded(video.url):
                to_download.append(video)
        if not to_download:
            QMessageBox.information(
                self,
                "Already downloaded",
                "All videos already downloaded.",
            )
            return
        max_concurrent = int(self._config_manager.get("concurrent_downloads", 3))
        try:
            results = self._download_coordinator.download_videos(
                to_download,
                max_concurrent=max_concurrent,
                progress_callback=self._on_download_progress,
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Download error",
                f"An error occurred during download: {exc}",
            )
            return
        succeeded = 0
        failed = 0
        for result in results:
            if result.success:
                succeeded += 1
                title = ""
                for video in to_download:
                    if video.url == result.video_url:
                        title = video.title or ""
                        break
                self._history_manager.mark_downloaded(
                    result.video_url,
                    {
                        "title": title,
                        "path": result.output_path,
                        "quality": "default",
                    },
                )
            else:
                failed += 1
        QMessageBox.information(
            self,
            "Download complete",
            f"Downloaded {succeeded}, failed {failed}.",
        )

    def _on_download_progress(self, percentage: float) -> None:
        """Update the progress bar with the current download percentage.

        Args:
            percentage: Overall download progress from 0 to 100.
        """
        self._progress_bar.setValue(int(percentage))

    def _on_open_settings(self) -> None:
        """Placeholder handler for opening the settings dialog."""
        print("Open settings (not implemented yet)")

    def _on_open_tracking(self) -> None:
        """Placeholder handler for opening the tracking dialog."""
        print("Open tracking (not implemented yet)")

    def _on_about(self) -> None:
        """Placeholder handler for the About menu action."""
        print("About (not implemented yet)")
