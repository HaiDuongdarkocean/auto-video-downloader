import json
import os
import tempfile

import pytest

from src.core.config_manager import ConfigManager, DEFAULT_CONFIG


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_load_existing_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"concurrent_downloads": 5, "default_quality": "720p"}, f)
            f.flush()
            path = f.name

        try:
            manager = ConfigManager(path)
            config = manager.load()
            assert config["concurrent_downloads"] == 5
            assert config["default_quality"] == "720p"
            assert config["stream_convert"] == DEFAULT_CONFIG["stream_convert"]
            assert config["ffmpeg_path"] == DEFAULT_CONFIG["ffmpeg_path"]
            assert config["output_dir"] == DEFAULT_CONFIG["output_dir"]
        finally:
            os.unlink(path)

    def test_load_missing_config_returns_defaults(self):
        manager = ConfigManager("nonexistent_config.json")
        config = manager.load()
        assert config == DEFAULT_CONFIG

    def test_save_config(self):
        path = os.path.join(tempfile.gettempdir(), "test_save_config.json")
        manager = ConfigManager(path)
        manager.save({"concurrent_downloads": 10, "default_quality": "480p"})

        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            assert saved["concurrent_downloads"] == 10
            assert saved["default_quality"] == "480p"
            assert saved["stream_convert"] == DEFAULT_CONFIG["stream_convert"]
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_get_value(self):
        manager = ConfigManager("nonexistent_config.json")
        manager.load()
        assert manager.get("concurrent_downloads") == 3
        assert manager.get("default_quality") == "1080p"
        assert manager.get("nonexistent_key", "fallback") == "fallback"

    def test_set_value(self):
        manager = ConfigManager("nonexistent_config.json")
        manager.load()
        manager.set("concurrent_downloads", 7)
        assert manager.get("concurrent_downloads") == 7

    def test_get_all(self):
        manager = ConfigManager("nonexistent_config.json")
        manager.load()
        config = manager.get_all()
        assert config == DEFAULT_CONFIG
        config["concurrent_downloads"] = 999
        assert manager.get("concurrent_downloads") == 3
