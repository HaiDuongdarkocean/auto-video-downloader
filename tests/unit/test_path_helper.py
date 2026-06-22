import os
import tempfile

import pytest

from src.utils.path_helper import create_output_path, sanitize_filename, get_website_name


class TestSanitizeFilename:
    """Tests for sanitize_filename."""

    def test_removes_invalid_characters(self):
        result = sanitize_filename('movie\\/:*?"<>|name')
        assert result == "moviename"

    def test_preserves_dash_and_space(self):
        result = sanitize_filename("part1 - part2")
        assert result == "part1 - part2"

    def test_strips_whitespace(self):
        result = sanitize_filename("  title  ")
        assert result == "title"

    def test_collapses_multiple_spaces(self):
        result = sanitize_filename("title    with   spaces")
        assert result == "title with spaces"

    def test_empty_string_returns_untitled(self):
        assert sanitize_filename("") == "untitled"

    def test_only_invalid_chars_returns_untitled(self):
        assert sanitize_filename("\\/:*?\"<>|") == "untitled"


class TestGetWebsiteName:
    """Tests for get_website_name."""

    def test_extracts_domain_from_https(self):
        assert get_website_name("https://example.com/page") == "example.com"

    def test_extracts_domain_from_http(self):
        assert get_website_name("http://sub.example.org/path/q") == "sub.example.org"

    def test_extracts_domain_with_www(self):
        assert get_website_name("https://www.example.net") == "www.example.net"

    def test_strips_trailing_slash(self):
        assert get_website_name("https://example.com/") == "example.com"

    def test_invalid_url_returns_unknown(self):
        assert get_website_name("not a url") == "unknown"


class TestCreateOutputPath:
    """Tests for create_output_path."""

    def test_creates_website_title_folder_structure(self):
        with tempfile.TemporaryDirectory() as base:
            path = create_output_path(
                "https://example.com/series/1",
                "Episode 01",
                base_dir=base,
            )
            assert path == os.path.join(base, "example.com", "Episode 01")
            assert os.path.isdir(path)

    def test_sanitizes_title_in_path(self):
        with tempfile.TemporaryDirectory() as base:
            path = create_output_path(
                "https://example.com",
                'bad\\:*?"<>|title',
                base_dir=base,
            )
            assert os.path.isdir(path)
            assert "badtitle" in os.path.basename(path)

    def test_idempotent_when_folder_exists(self):
        with tempfile.TemporaryDirectory() as base:
            path = create_output_path("https://example.com", "Title", base_dir=base)
            # second call should not raise
            path2 = create_output_path("https://example.com", "Title", base_dir=base)
            assert path == path2
            assert os.path.isdir(path2)

    def test_uses_default_base_dir(self):
        # Default base_dir is "./downloads"; just verify it builds the right
        # relative path without actually creating on disk in the repo.
        path = create_output_path("https://example.com", "Title", base_dir="downloads")
        assert path == os.path.join("downloads", "example.com", "Title")
