"""Main window for the video downloader GUI."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenuBar,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Video Downloader")
        self.resize(720, 480)
        self._url_input: QLineEdit = None  # type: ignore[assignment]
        self._selector_input: QLineEdit = None  # type: ignore[assignment]
        self._extract_button: QPushButton = None  # type: ignore[assignment]
        self._progress_bar: QProgressBar = None  # type: ignore[assignment]
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
        """Placeholder handler for the extract button."""
        print("Extract clicked (not wired yet)")

    def _on_open_settings(self) -> None:
        """Placeholder handler for opening the settings dialog."""
        print("Open settings (not implemented yet)")

    def _on_open_tracking(self) -> None:
        """Placeholder handler for opening the tracking dialog."""
        print("Open tracking (not implemented yet)")

    def _on_about(self) -> None:
        """Placeholder handler for the About menu action."""
        print("About (not implemented yet)")
