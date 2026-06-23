import sys

import pytest

from src.utils.notification_helper import (
    show_desktop_notification,
    show_in_app_notification,
    NotificationManager,
)
import src.utils.notification_helper as nh_mod


@pytest.fixture
def stub_messagebox(monkeypatch):
    """Prevent the real blocking Win32 MessageBoxW from being shown."""
    monkeypatch.setattr(nh_mod, "_win_message_box", lambda title, message: True)


class TestShowDesktopNotification:
    """Tests for show_desktop_notification."""

    def test_show_desktop_notification_returns_bool(self, stub_messagebox):
        result = show_desktop_notification("Title", "Message")
        assert isinstance(result, bool)

    def test_show_desktop_notification_does_not_raise(self, stub_messagebox):
        show_desktop_notification("Title", "Message")


class TestShowInAppNotification:
    """Tests for show_in_app_notification."""

    def test_show_in_app_notification_with_callback(self):
        received = []

        def callback(message: str) -> None:
            received.append(message)

        show_in_app_notification("hello", callback=callback)
        assert received == ["hello"]

    def test_show_in_app_notification_without_callback_prints(self, capsys):
        show_in_app_notification("printed message")
        captured = capsys.readouterr()
        assert "printed message" in captured.out


class TestNotificationManager:
    """Tests for NotificationManager."""

    def test_notification_manager_register_and_notify(self, stub_messagebox):
        manager = NotificationManager()
        received = []

        def callback(message: str) -> None:
            received.append(message)

        manager.register_in_app_handler(callback)
        manager.notify("Title", "Body", desktop=False, in_app=True)
        assert received == ["Body"]

    def test_notification_manager_notify_desktop_only(self, stub_messagebox):
        manager = NotificationManager()
        called = []

        def callback(message: str) -> None:
            called.append(message)

        manager.register_in_app_handler(callback)
        manager.notify("Title", "Body", desktop=True, in_app=False)
        assert called == []

    def test_notification_manager_notify_neither(self, stub_messagebox):
        manager = NotificationManager()
        called = []

        def callback(message: str) -> None:
            called.append(message)

        manager.register_in_app_handler(callback)
        manager.notify("Title", "Body", desktop=False, in_app=False)
        assert called == []

    def test_notification_manager_default_flags_show_both(self, stub_messagebox):
        manager = NotificationManager()
        received = []

        def callback(message: str) -> None:
            received.append(message)

        manager.register_in_app_handler(callback)
        manager.notify("Title", "Body")
        assert received == ["Body"]
