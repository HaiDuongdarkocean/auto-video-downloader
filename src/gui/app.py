"""Application factory and entry point for the video downloader GUI."""

import sys
from typing import Tuple

from PyQt6.QtWidgets import QApplication

from src.gui.main_window import DARK_THEME_QSS, MainWindow


def create_app() -> Tuple[QApplication, MainWindow]:
    """Create and show the QApplication and MainWindow.

    Returns:
        A tuple of (application, main_window).
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)
    window = MainWindow()
    window.show()
    return app, window


def main() -> None:
    """Run the GUI application event loop."""
    app, window = create_app()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
