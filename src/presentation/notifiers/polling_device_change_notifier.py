"""Periodic device refresh for platforms without a usable event stream.

macOS has no equivalent of WM_DEVICECHANGE or `pactl subscribe` short of a
CoreAudio property listener, whose C callback lifetime rules are a crash
risk from Python. A slow periodic refresh is the honest trade: the device
list is seconds stale at worst and nothing can dangle.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QTimer

# How often the device list is re-read. Slow enough to be free, fast enough
# that a plugged-in headset appears before the user goes looking for it.
_POLL_INTERVAL_MS = 3000


class PollingDeviceChangeNotifier:
    """Invokes a callback on a fixed interval."""

    def __init__(
        self,
        on_change: Callable[[], None],
        timer_factory: Callable[[], Any] = QTimer,
    ) -> None:
        """Initialise with the callback to run on each tick.

        Args:
            on_change: Called (on the GUI thread) periodically.
            timer_factory: Builds the timer; a seam for tests.
        """
        self._on_change = on_change
        self._timer_factory = timer_factory
        self._timer: Any = None

    def install(self, app: Any) -> None:
        """Start the periodic refresh.

        Args:
            app: The QApplication instance (unused; kept for the shared
                notifier install signature).
        """
        timer = self._timer_factory()
        timer.setInterval(_POLL_INTERVAL_MS)
        timer.timeout.connect(self._on_change)
        self._timer = timer
        timer.start()

    def stop(self) -> None:
        """Stop the periodic refresh, if it is running."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
