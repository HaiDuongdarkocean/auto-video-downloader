"""Error handling utilities for the video downloader application.

Provides retry decorators, URL validation, user-friendly error formatting,
and a safe FFmpeg availability check so callers can present actionable
messages instead of raw technical exceptions.
"""

import functools
import time
from typing import Callable, Optional, TypeVar

from src.core.ports.ffmpeg_port import FFmpegPort
from src.utils.logger import get_logger

F = TypeVar("F", bound=Callable)

_logger = get_logger("error_handler")


def retry_on_network_error(
    func: Optional[Callable] = None, *, max_retries: int = 3, delay: float = 1.0
) -> Callable:
    """Retry a callable on ConnectionError/TimeoutError with fixed backoff.

    Can be used as a bare decorator (``@retry_on_network_error``) or with
    arguments (``@retry_on_network_error(max_retries=5, delay=0.5)``).

    Args:
        func: The function to wrap when used as a bare decorator.
        max_retries: Maximum number of attempts (including the first).
        delay: Seconds to wait between retries.

    Returns:
        A wrapper that retries on network errors and re-raises non-network
        errors immediately.
    """

    def _wrap(target: Callable) -> Callable:
        @functools.wraps(target)
        def wrapper(*args, **kwargs):
            last_exc: Optional[Exception] = None
            for attempt in range(1, max_retries + 1):
                try:
                    return target(*args, **kwargs)
                except (ConnectionError, TimeoutError) as exc:
                    last_exc = exc
                    _logger.warning(
                        "Network error on attempt %d/%d for %s: %s",
                        attempt,
                        max_retries,
                        target.__name__,
                        exc,
                    )
                    if attempt < max_retries:
                        time.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper

    if func is not None and callable(func):
        return _wrap(func)
    return _wrap


def validate_url(url: str) -> bool:
    """Validate that a string is a plausible http(s) URL.

    Args:
        url: The string to validate.

    Returns:
        True when the URL starts with http:// or https:// and contains a
        domain component (a dot in the netloc), False otherwise.
    """
    if not isinstance(url, str) or not url:
        return False
    lowered = url.lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        return False
    scheme_end = lowered.find("://") + 3
    rest = url[scheme_end:]
    if not rest:
        return False
    netloc = rest.split("/", 1)[0]
    if not netloc:
        return False
    return "." in netloc or "localhost" in netloc


def format_user_error(error: Exception) -> str:
    """Convert a technical exception into a user-friendly message.

    Args:
        error: The exception to format.

    Returns:
        A human-readable message suitable for display in the GUI.
    """
    if isinstance(error, ConnectionError):
        return "Cannot connect to the server. Check your internet connection."
    if isinstance(error, TimeoutError):
        return "The request timed out. Please try again."
    if isinstance(error, RuntimeError):
        message = str(error)
        if "ffmpeg" in message.lower():
            return f"FFmpeg error: {message}. Ensure FFmpeg is installed."
        return str(error)
    if isinstance(error, FileNotFoundError):
        return f"File not found: {error}"
    if isinstance(error, PermissionError):
        return "Permission denied. Check file/directory permissions."
    if isinstance(error, OSError):
        return "Disk may be full. Check available space."
    return str(error)


def check_ffmpeg_available(ffmpeg_port: FFmpegPort) -> bool:
    """Return whether FFmpeg is available, never raising.

    Args:
        ffmpeg_port: An FFmpegPort implementation with check_available().

    Returns:
        True when FFmpeg is available, False on any error.
    """
    try:
        return bool(ffmpeg_port.check_available())
    except Exception as exc:
        _logger.error("FFmpeg availability check failed: %s", exc)
        return False


class ErrorHandler:
    """Static utility surface for error handling helpers.

    Exposes the module functions as class methods so callers can use either
    the module-level functions or this facade.
    """

    retry_on_network_error = staticmethod(retry_on_network_error)
    validate_url = staticmethod(validate_url)
    format_user_error = staticmethod(format_user_error)
    check_ffmpeg_available = staticmethod(check_ffmpeg_available)
