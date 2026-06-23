"""Dialog for configuring application settings."""

from typing import Dict

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


SETTINGS_DIALOG_QSS = """
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
QLabel {
    color: #cdd6f4;
    background: transparent;
}
QSpinBox, QComboBox {
    background-color: #181825;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
}
QSpinBox:focus, QComboBox:focus {
    border: 1px solid #cba6f7;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #181825;
    border: 1px solid #45475a;
    selection-background-color: #313244;
    color: #cdd6f4;
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
QPushButton#cancel_button {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#cancel_button:hover {
    background-color: #585b70;
}
QPushButton#ffmpeg_browse_button, QPushButton#output_browse_button {
    background-color: #45475a;
    color: #cdd6f4;
}
QPushButton#ffmpeg_browse_button:hover, QPushButton#output_browse_button:hover {
    background-color: #585b70;
}
"""


QUALITY_OPTIONS = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    def __init__(self, config_manager, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(480, 420)
        self._config_manager = config_manager
        self._concurrent_spinbox: QSpinBox = None  # type: ignore[assignment]
        self._quality_combo: QComboBox = None  # type: ignore[assignment]
        self._stream_convert_checkbox: QCheckBox = None  # type: ignore[assignment]
        self._ffmpeg_path_input: QLineEdit = None  # type: ignore[assignment]
        self._output_dir_input: QLineEdit = None  # type: ignore[assignment]
        self._setup_ui()
        self._load_current_config()
        self.setStyleSheet(SETTINGS_DIALOG_QSS)

    def _setup_ui(self) -> None:
        """Build the settings form layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        concurrent_label = QLabel("Concurrent downloads")
        layout.addWidget(concurrent_label)
        self._concurrent_spinbox = QSpinBox()
        self._concurrent_spinbox.setObjectName("concurrent_spinbox")
        self._concurrent_spinbox.setRange(1, 10)
        layout.addWidget(self._concurrent_spinbox)

        quality_label = QLabel("Default quality")
        layout.addWidget(quality_label)
        self._quality_combo = QComboBox()
        self._quality_combo.setObjectName("quality_combo")
        self._quality_combo.addItems(QUALITY_OPTIONS)
        layout.addWidget(self._quality_combo)

        self._stream_convert_checkbox = QCheckBox("Convert stream after download")
        self._stream_convert_checkbox.setObjectName("stream_convert_checkbox")
        layout.addWidget(self._stream_convert_checkbox)

        ffmpeg_label = QLabel("FFmpeg path")
        layout.addWidget(ffmpeg_label)
        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.setSpacing(8)
        self._ffmpeg_path_input = QLineEdit()
        self._ffmpeg_path_input.setObjectName("ffmpeg_path_input")
        self._ffmpeg_path_input.setPlaceholderText("ffmpeg")
        ffmpeg_row.addWidget(self._ffmpeg_path_input, 1)
        ffmpeg_browse = QPushButton("Browse")
        ffmpeg_browse.setObjectName("ffmpeg_browse_button")
        ffmpeg_browse.clicked.connect(self._on_browse_ffmpeg)
        ffmpeg_row.addWidget(ffmpeg_browse)
        layout.addLayout(ffmpeg_row)

        output_label = QLabel("Output directory")
        layout.addWidget(output_label)
        output_row = QHBoxLayout()
        output_row.setSpacing(8)
        self._output_dir_input = QLineEdit()
        self._output_dir_input.setObjectName("output_dir_input")
        self._output_dir_input.setPlaceholderText("./downloads")
        output_row.addWidget(self._output_dir_input, 1)
        output_browse = QPushButton("Browse")
        output_browse.setObjectName("output_browse_button")
        output_browse.clicked.connect(self._on_browse_output_dir)
        output_row.addWidget(output_browse)
        layout.addLayout(output_row)

        layout.addStretch(1)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        button_row.addStretch(1)
        save_button = QPushButton("Save")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self._on_save)
        button_row.addWidget(save_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self._on_cancel)
        button_row.addWidget(cancel_button)
        layout.addLayout(button_row)

    def _load_current_config(self) -> None:
        """Read current values from the config manager and populate fields."""
        self._concurrent_spinbox.setValue(int(self._config_manager.get("concurrent_downloads", 3)))
        quality = str(self._config_manager.get("default_quality", "1080p"))
        index = self._quality_combo.findText(quality)
        if index >= 0:
            self._quality_combo.setCurrentIndex(index)
        self._stream_convert_checkbox.setChecked(bool(self._config_manager.get("stream_convert", False)))
        self._ffmpeg_path_input.setText(str(self._config_manager.get("ffmpeg_path", "")))
        self._output_dir_input.setText(str(self._config_manager.get("output_dir", "./downloads")))

    def _on_save(self) -> None:
        """Validate, persist settings via the config manager, and accept the dialog."""
        if not self._validate_ffmpeg_path():
            return
        self._config_manager.save(self.get_config())
        self.accept()

    def _on_cancel(self) -> None:
        """Reject the dialog without saving."""
        self.reject()

    def _on_browse_ffmpeg(self) -> None:
        """Open a file dialog to pick the FFmpeg executable path."""
        path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg executable")
        if path:
            self._ffmpeg_path_input.setText(path)

    def _on_browse_output_dir(self) -> None:
        """Open a directory dialog to pick the output directory."""
        path = QFileDialog.getExistingDirectory(self, "Select output directory")
        if path:
            self._output_dir_input.setText(path)

    def _validate_ffmpeg_path(self) -> bool:
        """Validate the FFmpeg path field.

        Returns:
            True when the path is non-empty or set to the default "ffmpeg".
            Shows a warning and returns False otherwise.
        """
        path = self._ffmpeg_path_input.text().strip()
        if not path:
            QMessageBox.warning(
                self,
                "Invalid FFmpeg path",
                "Please provide an FFmpeg path or leave it as the default \"ffmpeg\".",
            )
            return False
        return True

    def get_config(self) -> Dict:
        """Return the current field values as a configuration dictionary.

        Returns:
            Dictionary mapping config keys to current widget values.
        """
        return {
            "concurrent_downloads": self._concurrent_spinbox.value(),
            "default_quality": self._quality_combo.currentText(),
            "stream_convert": self._stream_convert_checkbox.isChecked(),
            "ffmpeg_path": self._ffmpeg_path_input.text(),
            "output_dir": self._output_dir_input.text(),
        }
