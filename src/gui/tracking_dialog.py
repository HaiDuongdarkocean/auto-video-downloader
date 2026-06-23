"""Dialog for managing watch lists and schedules."""

from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.tracking.episode_tracker import EpisodeTracker
from src.core.tracking.scheduler_manager import SchedulerManager
from src.core.tracking.watch_list_manager import WatchListEntry, WatchListManager


TRACKING_DIALOG_QSS = """
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
QCheckBox {
    color: #cdd6f4;
    background: transparent;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #45475a;
    background-color: #181825;
}
QCheckBox::indicator:checked {
    background-color: #cba6f7;
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
QPushButton#close_button {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#close_button:hover {
    background-color: #585b70;
}
"""


class TrackingDialog(QDialog):
    """Dialog for managing tracked series, schedules, and update checks."""

    def __init__(
        self,
        watch_list_manager: WatchListManager,
        scheduler_manager: SchedulerManager,
        episode_tracker: Optional[EpisodeTracker] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tracking")
        self.resize(560, 480)
        self._watch_list_manager = watch_list_manager
        self._scheduler_manager = scheduler_manager
        self._episode_tracker = episode_tracker
        self._series_list: QListWidget = None  # type: ignore[assignment]
        self._schedule_input: QLineEdit = None  # type: ignore[assignment]
        self._auto_download_checkbox: QCheckBox = None  # type: ignore[assignment]
        self._notify_checkbox: QCheckBox = None  # type: ignore[assignment]
        self._setup_ui()
        self.setStyleSheet(TRACKING_DIALOG_QSS)
        self._load_series()

    def _setup_ui(self) -> None:
        """Build the dialog layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Tracking")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        self._series_list = QListWidget()
        self._series_list.setObjectName("series_list")
        self._series_list.itemSelectionChanged.connect(self._on_series_selected)
        layout.addWidget(self._series_list, 1)

        list_button_row = QHBoxLayout()
        list_button_row.setSpacing(8)

        add_button = QPushButton("Add")
        add_button.setObjectName("add_button")
        add_button.clicked.connect(self._on_add)
        list_button_row.addWidget(add_button)

        remove_button = QPushButton("Remove")
        remove_button.setObjectName("remove_button")
        remove_button.clicked.connect(self._on_remove)
        list_button_row.addWidget(remove_button)

        list_button_row.addStretch(1)
        layout.addLayout(list_button_row)

        schedule_label = QLabel("Schedule (cron)")
        layout.addWidget(schedule_label)
        self._schedule_input = QLineEdit()
        self._schedule_input.setObjectName("schedule_input")
        self._schedule_input.setPlaceholderText("e.g. 0 * * * *")
        layout.addWidget(self._schedule_input)

        self._auto_download_checkbox = QCheckBox("Auto-download new episodes")
        self._auto_download_checkbox.setObjectName("auto_download_checkbox")
        layout.addWidget(self._auto_download_checkbox)

        self._notify_checkbox = QCheckBox("Notify on new episodes")
        self._notify_checkbox.setObjectName("notify_checkbox")
        layout.addWidget(self._notify_checkbox)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        check_updates_button = QPushButton("Check for updates")
        check_updates_button.setObjectName("check_updates_button")
        check_updates_button.clicked.connect(self._on_check_updates)
        action_row.addWidget(check_updates_button)

        save_button = QPushButton("Save")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self._on_save)
        action_row.addWidget(save_button)

        action_row.addStretch(1)

        close_button = QPushButton("Close")
        close_button.setObjectName("close_button")
        close_button.clicked.connect(self.reject)
        action_row.addWidget(close_button)

        layout.addLayout(action_row)

    def _load_series(self) -> None:
        """Refresh the series list from the watch list manager."""
        self._series_list.clear()
        entries: List[WatchListEntry] = self._watch_list_manager.get_all_watch_lists()
        for entry in entries:
            label = entry.url or entry.watch_id
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, entry.watch_id)
            self._series_list.addItem(item)

    def _selected_watch_id(self) -> Optional[str]:
        """Return the watch_id of the currently selected series, or None."""
        item = self._series_list.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def _on_add(self) -> None:
        """Prompt for URL, selector, and schedule, then add a watch list entry."""
        url, ok = QInputDialog.getText(self, "Add watch list", "Series URL:")
        if not ok or not url.strip():
            return
        selector, ok = QInputDialog.getText(self, "Add watch list", "CSS selector:")
        if not ok:
            return
        schedule, ok = QInputDialog.getText(self, "Add watch list", "Schedule (cron):")
        if not ok:
            return
        self._watch_list_manager.add_watch_list(
            url=url.strip(),
            selector=selector.strip(),
            schedule=schedule.strip(),
        )
        self._load_series()

    def _on_remove(self) -> None:
        """Remove the currently selected series from the watch list."""
        watch_id = self._selected_watch_id()
        if watch_id is None:
            return
        self._watch_list_manager.remove_watch_list(watch_id)
        try:
            self._scheduler_manager.remove_job(watch_id)
        except Exception:
            pass
        self._load_series()

    def _on_save(self) -> None:
        """Persist schedule and toggle changes for the selected series."""
        watch_id = self._selected_watch_id()
        if watch_id is None:
            return
        self._watch_list_manager.update_watch_list(
            watch_id,
            schedule=self._schedule_input.text().strip(),
            auto_download=self._auto_download_checkbox.isChecked(),
            notify=self._notify_checkbox.isChecked(),
        )
        self._load_series()

    def _on_check_updates(self) -> None:
        """Check the selected series for new episodes and show the result."""
        watch_id = self._selected_watch_id()
        if watch_id is None:
            return
        if self._episode_tracker is None:
            QMessageBox.information(
                self, "Check for updates", "No episode tracker configured."
            )
            return
        entry = self._watch_list_manager.get_watch_list(watch_id)
        if entry is None:
            return
        videos = self._episode_tracker.check_for_updates(entry)
        if not videos:
            QMessageBox.information(self, "Check for updates", "No new episodes found.")
        else:
            lines = [f"{v.title or v.url}" for v in videos]
            QMessageBox.information(
                self,
                "Check for updates",
                f"Found {len(videos)} new episode(s):\n" + "\n".join(lines),
            )

    def _on_series_selected(self) -> None:
        """Populate the inputs from the currently selected series."""
        watch_id = self._selected_watch_id()
        if watch_id is None:
            return
        entry = self._watch_list_manager.get_watch_list(watch_id)
        if entry is None:
            return
        self._schedule_input.setText(entry.schedule)
        self._auto_download_checkbox.setChecked(entry.auto_download)
        self._notify_checkbox.setChecked(entry.notify)

    def get_series_count(self) -> int:
        """Return the number of series currently displayed in the list."""
        return self._series_list.count()
