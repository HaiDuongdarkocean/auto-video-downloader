import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import MagicMock

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
)

from src.core.ports.mock_scheduler_adapter import MockSchedulerAdapter
from src.core.tracking.scheduler_manager import SchedulerManager
from src.core.tracking.watch_list_manager import WatchListManager
from src.core.video_extractor import VideoInfo
from src.gui.tracking_dialog import TrackingDialog


def _make_manager(tmp_path) -> WatchListManager:
    return WatchListManager(str(tmp_path / "watch_list.json"))


def _make_scheduler() -> SchedulerManager:
    return SchedulerManager(MockSchedulerAdapter())


class TestTrackingDialog:
    """Tests for the TrackingDialog watch list management UI."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def test_dialog_displays_existing_series(self, tmp_path):
        manager = _make_manager(tmp_path)
        manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        manager.add_watch_list("https://b.com", ".ep", "0 * * * *")
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            assert series_list is not None
            assert series_list.count() == 2
        finally:
            dialog.close()

    def test_add_button_creates_new_entry(self, tmp_path, monkeypatch):
        manager = _make_manager(tmp_path)
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            assert series_list.count() == 0

            responses = iter(
                [
                    ("https://c.com", True),
                    (".ep", True),
                    ("0 * * * *", True),
                ]
            )
            monkeypatch.setattr(
                "src.gui.tracking_dialog.QInputDialog.getText",
                lambda *a, **k: next(responses),
            )
            add_button = dialog.findChild(QPushButton, "add_button")
            add_button.click()
            assert series_list.count() == 1
            assert dialog.get_series_count() == 1
            assert manager.get_all_watch_lists()[0].url == "https://c.com"
        finally:
            dialog.close()

    def test_remove_button_removes_selected(self, tmp_path):
        manager = _make_manager(tmp_path)
        manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        manager.add_watch_list("https://b.com", ".ep", "0 * * * *")
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            series_list.setCurrentRow(0)
            remove_button = dialog.findChild(QPushButton, "remove_button")
            remove_button.click()
            assert series_list.count() == 1
            assert len(manager.get_all_watch_lists()) == 1
        finally:
            dialog.close()

    def test_selecting_series_populates_inputs(self, tmp_path):
        manager = _make_manager(tmp_path)
        wid = manager.add_watch_list(
            "https://a.com", ".ep", "0 * * * *", auto_download=True, notify=False
        )
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            for i in range(series_list.count()):
                if series_list.item(i).data(0x100) == wid:
                    series_list.setCurrentRow(i)
                    break
            schedule_input = dialog.findChild(QLineEdit, "schedule_input")
            auto_dl = dialog.findChild(QCheckBox, "auto_download_checkbox")
            notify = dialog.findChild(QCheckBox, "notify_checkbox")
            assert schedule_input.text() == "0 * * * *"
            assert auto_dl.isChecked() is True
            assert notify.isChecked() is False
        finally:
            dialog.close()

    def test_save_button_updates_entry(self, tmp_path):
        manager = _make_manager(tmp_path)
        wid = manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            series_list.setCurrentRow(0)
            schedule_input = dialog.findChild(QLineEdit, "schedule_input")
            schedule_input.setText("*/5 * * * *")
            save_button = dialog.findChild(QPushButton, "save_button")
            save_button.click()
            entry = manager.get_watch_list(wid)
            assert entry.schedule == "*/5 * * * *"
        finally:
            dialog.close()

    def test_check_updates_with_no_tracker_does_not_crash(self, tmp_path, monkeypatch):
        manager = _make_manager(tmp_path)
        manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        dialog = TrackingDialog(manager, _make_scheduler(), episode_tracker=None)
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            series_list.setCurrentRow(0)
            info_mock = MagicMock()
            monkeypatch.setattr(QMessageBox, "information", info_mock)
            check_button = dialog.findChild(QPushButton, "check_updates_button")
            check_button.click()
            assert info_mock.called
        finally:
            dialog.close()

    def test_check_updates_with_tracker_shows_results(self, tmp_path, monkeypatch):
        manager = _make_manager(tmp_path)
        manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        tracker = MagicMock()
        tracker.check_for_updates.return_value = [
            VideoInfo(url="https://a.com/1", title="Ep 1"),
            VideoInfo(url="https://a.com/2", title="Ep 2"),
        ]
        dialog = TrackingDialog(manager, _make_scheduler(), episode_tracker=tracker)
        try:
            series_list = dialog.findChild(QListWidget, "series_list")
            series_list.setCurrentRow(0)
            captured = {}
            info_mock = MagicMock()
            info_mock.side_effect = lambda *a, **k: captured.setdefault("text", a)
            monkeypatch.setattr(QMessageBox, "information", info_mock)
            check_button = dialog.findChild(QPushButton, "check_updates_button")
            check_button.click()
            assert tracker.check_for_updates.called
            assert info_mock.called
        finally:
            dialog.close()

    def test_close_button_rejects_dialog(self, tmp_path):
        manager = _make_manager(tmp_path)
        dialog = TrackingDialog(manager, _make_scheduler())
        close_button = dialog.findChild(QPushButton, "close_button")
        close_button.click()
        assert dialog.result() == QDialog.DialogCode.Rejected

    def test_get_series_count(self, tmp_path):
        manager = _make_manager(tmp_path)
        manager.add_watch_list("https://a.com", ".ep", "0 * * * *")
        manager.add_watch_list("https://b.com", ".ep", "0 * * * *")
        dialog = TrackingDialog(manager, _make_scheduler())
        try:
            assert dialog.get_series_count() == 2
        finally:
            dialog.close()
