import tempfile
import time
from unittest.mock import patch

from src.core.error_handler import (
    ErrorHandler,
    check_ffmpeg_available,
    format_user_error,
    retry_on_network_error,
    validate_url,
)
from src.core.ports.mock_ffmpeg_adapter import MockFFmpegAdapter


class TestValidateUrl:
    """Tests for validate_url."""

    def test_validate_url_valid_https(self):
        assert validate_url("https://example.com/page") is True

    def test_validate_url_valid_http(self):
        assert validate_url("http://example.com/page") is True

    def test_validate_url_invalid_no_scheme(self):
        assert validate_url("example.com/page") is False

    def test_validate_url_invalid_empty(self):
        assert validate_url("") is False

    def test_validate_url_invalid_just_domain(self):
        assert validate_url("example") is False


class TestFormatUserError:
    """Tests for format_user_error."""

    def test_format_user_error_connection_error(self):
        msg = format_user_error(ConnectionError("boom"))
        assert msg == "Cannot connect to the server. Check your internet connection."

    def test_format_user_error_timeout(self):
        msg = format_user_error(TimeoutError("slow"))
        assert msg == "The request timed out. Please try again."

    def test_format_user_error_runtime_error(self):
        msg = format_user_error(RuntimeError("FFmpeg command failed: bad input"))
        assert msg.startswith("FFmpeg error:")
        assert "Ensure FFmpeg is installed." in msg

    def test_format_user_error_file_not_found(self):
        msg = format_user_error(FileNotFoundError("missing.ts"))
        assert msg == "File not found: missing.ts"

    def test_format_user_error_permission_error(self):
        msg = format_user_error(PermissionError("denied"))
        assert msg == "Permission denied. Check file/directory permissions."

    def test_format_user_error_os_error(self):
        msg = format_user_error(OSError("no space"))
        assert msg == "Disk may be full. Check available space."

    def test_format_user_error_unknown_exception(self):
        msg = format_user_error(ValueError("wat"))
        assert msg == "wat"


class TestRetryOnNetworkError:
    """Tests for retry_on_network_error."""

    def test_retry_on_network_error_succeeds_after_retry(self):
        calls = {"n": 0}

        @retry_on_network_error(max_retries=3, delay=0)
        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("down")
            return "ok"

        with patch("src.core.error_handler.time.sleep") as sleep_mock:
            result = flaky()
        assert result == "ok"
        assert calls["n"] == 3
        assert sleep_mock.call_count == 2

    def test_retry_on_network_error_fails_after_max_retries(self):
        calls = {"n": 0}

        @retry_on_network_error(max_retries=3, delay=0)
        def always_fails():
            calls["n"] += 1
            raise ConnectionError("down")

        with patch("src.core.error_handler.time.sleep"):
            try:
                always_fails()
                raised = False
            except ConnectionError:
                raised = True
        assert raised is True
        assert calls["n"] == 3

    def test_retry_on_network_error_no_retry_on_success(self):
        calls = {"n": 0}

        @retry_on_network_error(max_retries=3, delay=0)
        def succeeds():
            calls["n"] += 1
            return "ok"

        result = succeeds()
        assert result == "ok"
        assert calls["n"] == 1

    def test_retry_on_network_error_does_not_retry_non_network_error(self):
        calls = {"n": 0}

        @retry_on_network_error(max_retries=3, delay=0)
        def raises_value():
            calls["n"] += 1
            raise ValueError("bad")

        try:
            raises_value()
            raised = False
        except ValueError:
            raised = True
        assert raised is True
        assert calls["n"] == 1


class TestCheckFfmpegAvailable:
    """Tests for check_ffmpeg_available."""

    def test_check_ffmpeg_available_returns_true(self):
        ffmpeg = MockFFmpegAdapter(available=True)
        assert check_ffmpeg_available(ffmpeg) is True

    def test_check_ffmpeg_available_returns_false(self):
        ffmpeg = MockFFmpegAdapter(available=False)
        assert check_ffmpeg_available(ffmpeg) is False


class TestErrorHandlerFacade:
    """Tests for the ErrorHandler facade exposing the same helpers."""

    def test_error_handler_validate_url(self):
        assert ErrorHandler.validate_url("https://example.com") is True

    def test_error_handler_format_user_error(self):
        assert ErrorHandler.format_user_error(TimeoutError()) == (
            "The request timed out. Please try again."
        )
