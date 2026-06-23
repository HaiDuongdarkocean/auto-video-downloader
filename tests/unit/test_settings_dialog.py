import os
import tempfile
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from src.core.config_manager import ConfigManager
from src.gui.settings_dialog import SettingsDialog


class TestSettingsDialog:
    """Tests for the SettingsDialog configuration UI."""

    @classmethod
    def setup_class(cls) -> None:
        app = QApplication.instance()
        if app is None:
            cls._app = QApplication([])
        else:
            cls._app = app

    def _make_config_manager(self) -> ConfigManager:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        path = tmp.name
        tmp.close()
        os.unlink(path)
        manager = ConfigManager(path)
        manager.load()
        return manager

    def test_dialog_loads_current_config(self):
        manager = self._make_config_manager()
        manager.save({
            "concurrent_downloads": 5,
            "default_quality": "720p",
            "stream_convert": False,
            "ffmpeg_path": "",
            "output_dir": "./downloads",
        })
        dialog = SettingsDialog(manager)
        try:
            spinbox = dialog.findChild(QSpinBox, "concurrent_spinbox")
            combo = dialog.findChild(QComboBox, "quality_combo")
            assert spinbox.value() == 5
            assert combo.currentText() == "720p"
        finally:
            dialog.close()

    def test_dialog_loads_default_config(self):
        manager = self._make_config_manager()
        dialog = SettingsDialog(manager)
        try:
            spinbox = dialog.findChild(QSpinBox, "concurrent_spinbox")
            combo = dialog.findChild(QComboBox, "quality_combo")
            checkbox = dialog.findChild(QCheckBox, "stream_convert_checkbox")
            assert spinbox.value() == 3
            assert combo.currentText() == "1080p"
            assert checkbox.isChecked() is False
        finally:
            dialog.close()

    def test_get_config_returns_field_values(self):
        manager = self._make_config_manager()
        dialog = SettingsDialog(manager)
        try:
            spinbox = dialog.findChild(QSpinBox, "concurrent_spinbox")
            combo = dialog.findChild(QComboBox, "quality_combo")
            spinbox.setValue(7)
            combo.setCurrentText("480p")
            config = dialog.get_config()
            assert config["concurrent_downloads"] == 7
            assert config["default_quality"] == "480p"
        finally:
            dialog.close()

    def test_save_button_saves_config(self):
        manager = self._make_config_manager()
        dialog = SettingsDialog(manager)
        try:
            spinbox = dialog.findChild(QSpinBox, "concurrent_spinbox")
            combo = dialog.findChild(QComboBox, "quality_combo")
            ffmpeg_input = dialog.findChild(QLineEdit, "ffmpeg_path_input")
            spinbox.setValue(8)
            combo.setCurrentText("360p")
            ffmpeg_input.setText("ffmpeg")
            save_button = dialog.findChild(QPushButton, "save_button")
            save_button.click()
            assert dialog.result() == QDialog.DialogCode.Accepted
        finally:
            dialog.close()
        new_manager = ConfigManager(manager._config_path)
        new_manager.load()
        assert new_manager.get("concurrent_downloads") == 8
        assert new_manager.get("default_quality") == "360p"

    def test_cancel_button_rejects_without_saving(self):
        manager = self._make_config_manager()
        original = manager.get_all()
        dialog = SettingsDialog(manager)
        try:
            spinbox = dialog.findChild(QSpinBox, "concurrent_spinbox")
            spinbox.setValue(10)
            cancel_button = dialog.findChild(QPushButton, "cancel_button")
            cancel_button.click()
            assert dialog.result() == QDialog.DialogCode.Rejected
        finally:
            dialog.close()
        new_manager = ConfigManager(manager._config_path)
        new_manager.load()
        assert new_manager.get("concurrent_downloads") == original["concurrent_downloads"]

    def test_stream_convert_checkbox_loads(self):
        manager = self._make_config_manager()
        manager.save({
            "concurrent_downloads": 3,
            "default_quality": "1080p",
            "stream_convert": True,
            "ffmpeg_path": "",
            "output_dir": "./downloads",
        })
        dialog = SettingsDialog(manager)
        try:
            checkbox = dialog.findChild(QCheckBox, "stream_convert_checkbox")
            assert checkbox.isChecked() is True
        finally:
            dialog.close()

    def test_ffmpeg_path_input_loads(self):
        manager = self._make_config_manager()
        manager.save({
            "concurrent_downloads": 3,
            "default_quality": "1080p",
            "stream_convert": False,
            "ffmpeg_path": "/usr/bin/ffmpeg",
            "output_dir": "./downloads",
        })
        dialog = SettingsDialog(manager)
        try:
            ffmpeg_input = dialog.findChild(QLineEdit, "ffmpeg_path_input")
            assert ffmpeg_input.text() == "/usr/bin/ffmpeg"
        finally:
            dialog.close()

    def test_output_dir_input_loads(self):
        manager = self._make_config_manager()
        manager.save({
            "concurrent_downloads": 3,
            "default_quality": "1080p",
            "stream_convert": False,
            "ffmpeg_path": "",
            "output_dir": "/tmp/vids",
        })
        dialog = SettingsDialog(manager)
        try:
            output_input = dialog.findChild(QLineEdit, "output_dir_input")
            assert output_input.text() == "/tmp/vids"
        finally:
            dialog.close()

    def test_validate_ffmpeg_path_empty_returns_false(self):
        manager = self._make_config_manager()
        dialog = SettingsDialog(manager)
        try:
            ffmpeg_input = dialog.findChild(QLineEdit, "ffmpeg_path_input")
            ffmpeg_input.setText("")
            with patch("src.gui.settings_dialog.QMessageBox.warning"):
                assert dialog._validate_ffmpeg_path() is False
        finally:
            dialog.close()

    def test_validate_ffmpeg_path_valid_returns_true(self):
        manager = self._make_config_manager()
        dialog = SettingsDialog(manager)
        try:
            ffmpeg_input = dialog.findChild(QLineEdit, "ffmpeg_path_input")
            ffmpeg_input.setText("ffmpeg")
            assert dialog._validate_ffmpeg_path() is True
        finally:
            dialog.close()
