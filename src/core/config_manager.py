import json
import os
from typing import Any, Dict, Optional


DEFAULT_CONFIG = {
    "concurrent_downloads": 3,
    "default_quality": "1080p",
    "stream_convert": False,
    "ffmpeg_path": "",
    "output_dir": "./downloads",
}


class ConfigManager:
    """Manages application configuration loading and saving."""

    def __init__(self, config_path: str = "config.json"):
        self._config_path = config_path
        self._config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file.

        If the file does not exist, returns default config.
        Missing keys are filled with defaults.

        Returns:
            Configuration dictionary.
        """
        if os.path.exists(self._config_path):
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self._config = {**DEFAULT_CONFIG, **loaded}
        else:
            self._config = DEFAULT_CONFIG.copy()
        return self._config

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file.

        Args:
            config: Configuration dictionary to save.
        """
        self._config = {**DEFAULT_CONFIG, **config}
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        if not self._config:
            self.load()
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by key.

        Args:
            key: Configuration key.
            value: Value to set.
        """
        if not self._config:
            self.load()
        self._config[key] = value

    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary.

        Returns:
            Full configuration dictionary.
        """
        if not self._config:
            self.load()
        return self._config.copy()
