"""Dialog for displaying extracted videos and selecting which to download."""

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


DIALOG_QSS = """
QDialog, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Sans Serif';
    font-size: 13px;
}
QLabel#DialogTitle {
    font-size: 18px;
    font-weight: 600;
    color: #cba6f7;
}
QListWidget {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px;
    color: #cdd6f4;
}
QListWidget::item {
    padding: 6px 4px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #313244;
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
QPushButton#cancel_button {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#cancel_button:hover {
    background-color: #585b70;
}
"""


class DownloadDialog(QDialog):
    """Dialog showing extracted videos with checkboxes for selection."""

    def __init__(self, videos: List, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select videos to download")
        self.resize(520, 420)
        self._videos: List = list(videos)
        self._list_widget: QListWidget = None  # type: ignore[assignment]
        self._setup_ui()
        self.setStyleSheet(DIALOG_QSS)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Select videos to download")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        self._list_widget = QListWidget()
        self._list_widget.setObjectName("video_list")
        for video in self._videos:
            label = video.title or video.url
            item = QListWidgetItem(label)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, video)
            self._list_widget.addItem(item)
        layout.addWidget(self._list_widget, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        select_all = QPushButton("Select all")
        select_all.setObjectName("select_all_button")
        select_all.clicked.connect(self._on_select_all)
        button_row.addWidget(select_all)

        deselect_all = QPushButton("Deselect all")
        deselect_all.setObjectName("deselect_all_button")
        deselect_all.clicked.connect(self._on_deselect_all)
        button_row.addWidget(deselect_all)

        button_row.addStretch(1)

        download = QPushButton("Download selected")
        download.setObjectName("download_button")
        download.clicked.connect(self.accept)
        button_row.addWidget(download)

        cancel = QPushButton("Cancel")
        cancel.setObjectName("cancel_button")
        cancel.clicked.connect(self.reject)
        button_row.addWidget(cancel)

        layout.addLayout(button_row)

    def _on_select_all(self) -> None:
        for i in range(self._list_widget.count()):
            self._list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def _on_deselect_all(self) -> None:
        for i in range(self._list_widget.count()):
            self._list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected_videos(self) -> List:
        selected = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                video = item.data(Qt.ItemDataRole.UserRole)
                if video is not None:
                    selected.append(video)
        return selected
