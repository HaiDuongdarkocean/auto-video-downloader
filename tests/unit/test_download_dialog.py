import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QListWidget, QPushButton

from src.core.video_extractor import VideoInfo
from src.gui.download_dialog import DownloadDialog


def _videos():
    return [
        VideoInfo(url="https://example.com/v1", title="Episode 1"),
        VideoInfo(url="https://example.com/v2", title="Episode 2"),
        VideoInfo(url="https://example.com/v3", title="Episode 3"),
    ]


class TestDownloadDialog:
    """Tests for the DownloadDialog selection UI."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def test_dialog_displays_all_videos(self):
        dialog = DownloadDialog(_videos())
        try:
            list_widget = dialog.findChild(QListWidget, "video_list")
            assert list_widget is not None
            assert list_widget.count() == 3
        finally:
            dialog.close()

    def test_select_all_checks_all_items(self):
        dialog = DownloadDialog(_videos())
        try:
            list_widget = dialog.findChild(QListWidget, "video_list")
            select_all = dialog.findChild(QPushButton, "select_all_button")
            select_all.click()
            for i in range(list_widget.count()):
                assert list_widget.item(i).checkState() == Qt.CheckState.Checked
        finally:
            dialog.close()

    def test_deselect_all_unchecks_all_items(self):
        dialog = DownloadDialog(_videos())
        try:
            list_widget = dialog.findChild(QListWidget, "video_list")
            select_all = dialog.findChild(QPushButton, "select_all_button")
            deselect_all = dialog.findChild(QPushButton, "deselect_all_button")
            select_all.click()
            deselect_all.click()
            for i in range(list_widget.count()):
                assert list_widget.item(i).checkState() == Qt.CheckState.Unchecked
        finally:
            dialog.close()

    def test_get_selected_videos_returns_checked(self):
        dialog = DownloadDialog(_videos())
        try:
            list_widget = dialog.findChild(QListWidget, "video_list")
            list_widget.item(0).setCheckState(Qt.CheckState.Checked)
            list_widget.item(1).setCheckState(Qt.CheckState.Checked)
            selected = dialog.get_selected_videos()
            assert len(selected) == 2
            assert selected[0].title == "Episode 1"
            assert selected[1].title == "Episode 2"
        finally:
            dialog.close()

    def test_get_selected_videos_empty_when_none_checked(self):
        dialog = DownloadDialog(_videos())
        try:
            assert dialog.get_selected_videos() == []
        finally:
            dialog.close()

    def test_download_button_accepts_dialog(self):
        dialog = DownloadDialog(_videos())
        download_button = dialog.findChild(QPushButton, "download_button")
        download_button.click()
        assert dialog.result() == QDialog.DialogCode.Accepted

    def test_cancel_button_rejects_dialog(self):
        dialog = DownloadDialog(_videos())
        cancel_button = dialog.findChild(QPushButton, "cancel_button")
        cancel_button.click()
        assert dialog.result() == QDialog.DialogCode.Rejected
