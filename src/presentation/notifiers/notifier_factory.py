"""Selects the device-change notifier for the running platform."""

from __future__ import annotations

from typing import Any, Callable

from src.presentation.notifiers.device_change_notifier import (
    WindowsDeviceChangeNotifier,
)
from src.presentation.notifiers.linux_device_change_notifier import (
    LinuxDeviceChangeNotifier,
)
from src.presentation.notifiers.polling_device_change_notifier import (
    PollingDeviceChangeNotifier,
)


def create_device_change_notifier(platform: str, on_change: Callable[[], None]) -> Any:
    """Build the notifier matching a sys.platform value.

    Args:
        platform: The sys.platform string
        on_change: Called (on the GUI thread) when a device change occurs

    Returns:
        A notifier exposing install(app)
    """
    if platform == "win32":
        return WindowsDeviceChangeNotifier(on_change)
    if platform.startswith("linux"):
        return LinuxDeviceChangeNotifier(on_change)
    # macOS and anything unrecognised: the polling fallback works anywhere.
    return PollingDeviceChangeNotifier(on_change)
