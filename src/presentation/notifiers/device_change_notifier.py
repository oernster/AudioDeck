"""Windows device-change notifier using the WM_DEVICECHANGE message.

This watches the native window message stream for device add/remove/change
events and invokes a callback on the GUI thread. It deliberately avoids a COM
notification-client server (which would need a hand-built callback object) for
robustness; a periodic timer remains as a fallback if no events arrive.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter

# Windows message broadcast when a device is added, removed or changes state.
_WM_DEVICECHANGE = 0x0219
_WINDOWS_MSG_EVENT = b"windows_generic_MSG"


class WindowsDeviceChangeNotifier(QAbstractNativeEventFilter):
    """Invokes a callback when Windows reports a device change."""

    def __init__(self, on_change: Callable[[], None]) -> None:
        """Initialise with the callback to run on a device change.

        Args:
            on_change: Called (on the GUI thread) when a device change occurs.
        """
        super().__init__()
        self._on_change = on_change

    def install(self, app) -> None:
        """Install this filter on the application.

        Args:
            app: The QApplication instance.
        """
        app.installNativeEventFilter(self)

    def nativeEventFilter(self, event_type, message):  # noqa: N802 (Qt override)
        """Handle native events, calling back on WM_DEVICECHANGE."""
        try:
            if event_type == _WINDOWS_MSG_EVENT:
                msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
                if msg.message == _WM_DEVICECHANGE:
                    self._on_change()
        except Exception:
            pass
        return False, 0
