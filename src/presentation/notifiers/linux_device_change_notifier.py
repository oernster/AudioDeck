"""Linux device-change notifier over `pactl subscribe`.

`pactl subscribe` prints one line per sound-server event for as long as it
runs, so a long-lived child process watched with QProcess delivers device
changes on the GUI thread with no polling and no extra threads. If pactl is
missing or the stream dies the notifier goes quiet rather than failing; the
user can still refresh by switching profiles.
"""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QProcess

# Event lines look like "Event 'new' on sink #2". Sink and source events are
# device arrivals, removals and state changes; server events carry default
# device switches.
_DEVICE_EVENT_MARKERS = (" on sink", " on source", " on server")


class LinuxDeviceChangeNotifier:
    """Invokes a callback when the PulseAudio server reports a change."""

    def __init__(
        self,
        on_change: Callable[[], None],
        process_factory: Callable[[], Any] = QProcess,
    ) -> None:
        """Initialise with the callback to run on a device change.

        Args:
            on_change: Called (on the GUI thread) when a device change occurs.
            process_factory: Builds the subscribe process; a seam for tests.
        """
        self._on_change = on_change
        self._process_factory = process_factory
        self._process: Any = None

    def install(self, app: Any) -> None:
        """Start the subscribe process and watch its output.

        Args:
            app: The QApplication instance.
        """
        process = self._process_factory()
        process.readyReadStandardOutput.connect(self._handle_output)
        app.aboutToQuit.connect(self.stop)
        self._process = process
        process.start("pactl", ["subscribe"])

    def stop(self) -> None:
        """Kill the subscribe process, if it is running."""
        if self._process is not None:
            self._process.kill()
            self._process = None

    def _handle_output(self) -> None:
        """Read pending event lines, calling back when any names a device."""
        if self._process is None:
            return
        text = bytes(self._process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        if any(
            marker in line
            for line in text.splitlines()
            for marker in _DEVICE_EVENT_MARKERS
        ):
            self._on_change()
