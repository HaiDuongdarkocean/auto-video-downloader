import sys
from typing import Callable, Optional


def _win_message_box(title: str, message: str) -> bool:
    """Show a Win32 MessageBoxW dialog. Returns True on success.

    Isolated so tests can patch this module-level reference instead of
    invoking the real blocking Win32 dialog.
    """
    import ctypes

    MB_OK = 0x00000000
    MB_ICONINFORMATION = 0x00000040
    ctypes.windll.user32.MessageBoxW(0, message, title, MB_OK | MB_ICONINFORMATION)
    return True


def show_desktop_notification(title: str, message: str) -> bool:
    """Show a desktop notification on Windows; no-op on other platforms.

    Uses the stdlib ctypes binding to the Win32 MessageBoxW API. Returns True
    when a notification was shown, False when the platform is unsupported or
    the call failed. Never raises.
    """
    try:
        if sys.platform != "win32":
            print(f"[notification] {title}: {message}")
            return False
        return _win_message_box(title, message)
    except Exception:
        return False


def show_in_app_notification(
    message: str, callback: Optional[Callable[[str], None]] = None
) -> None:
    """Show an in-app notification via a registered GUI callback.

    When a callback is provided it is invoked with the message (the GUI is
    expected to render a toast/banner). Otherwise the message is printed to
    stdout as a fallback.
    """
    if callback is not None:
        callback(message)
    else:
        print(message)


class NotificationManager:
    """Coordinates desktop and in-app notifications.

    The GUI registers an in-app handler via register_in_app_handler so that
    callers (e.g. episode_tracker) can call notify(...) without knowing about
    the UI layer.
    """

    def __init__(self) -> None:
        self._in_app_callback: Optional[Callable[[str], None]] = None

    def register_in_app_handler(self, callback: Callable[[str], None]) -> None:
        """Register the callback used to display in-app notifications."""
        self._in_app_callback = callback

    def notify(
        self, title: str, message: str, desktop: bool = True, in_app: bool = True
    ) -> None:
        """Show a desktop and/or in-app notification based on the flags."""
        if desktop:
            show_desktop_notification(title, message)
        if in_app:
            show_in_app_notification(message, callback=self._in_app_callback)
