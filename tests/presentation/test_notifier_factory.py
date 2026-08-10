"""Tests for the device-change notifier platform selection."""

from src.presentation.notifiers.device_change_notifier import (
    WindowsDeviceChangeNotifier,
)
from src.presentation.notifiers.linux_device_change_notifier import (
    LinuxDeviceChangeNotifier,
)
from src.presentation.notifiers.notifier_factory import (
    create_device_change_notifier,
)
from src.presentation.notifiers.polling_device_change_notifier import (
    PollingDeviceChangeNotifier,
)


def _on_change() -> None:
    pass


def test_win32_gets_the_native_event_notifier(qapp):
    notifier = create_device_change_notifier("win32", _on_change)
    assert isinstance(notifier, WindowsDeviceChangeNotifier)


def test_linux_gets_the_pactl_subscribe_notifier():
    notifier = create_device_change_notifier("linux", _on_change)
    assert isinstance(notifier, LinuxDeviceChangeNotifier)


def test_darwin_gets_the_polling_notifier():
    notifier = create_device_change_notifier("darwin", _on_change)
    assert isinstance(notifier, PollingDeviceChangeNotifier)


def test_an_unknown_platform_gets_the_polling_notifier():
    notifier = create_device_change_notifier("plan9", _on_change)
    assert isinstance(notifier, PollingDeviceChangeNotifier)
