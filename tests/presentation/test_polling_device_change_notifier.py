"""Tests for the periodic polling device-change notifier."""

from src.presentation.notifiers.polling_device_change_notifier import (
    PollingDeviceChangeNotifier,
)


class FakeSignal:
    """Hand-written stand-in for a Qt signal."""

    def __init__(self) -> None:
        self._callbacks = []

    def connect(self, callback) -> None:
        self._callbacks.append(callback)

    def emit(self) -> None:
        for callback in self._callbacks:
            callback()


class FakeTimer:
    """Hand-written stand-in for QTimer."""

    def __init__(self) -> None:
        self.timeout = FakeSignal()
        self.interval_ms = None
        self.running = False

    def setInterval(self, interval_ms: int) -> None:
        self.interval_ms = interval_ms

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False


def _installed_notifier():
    timer = FakeTimer()
    changes = []
    notifier = PollingDeviceChangeNotifier(
        lambda: changes.append(True), timer_factory=lambda: timer
    )
    notifier.install(app=None)
    return notifier, timer, changes


def test_install_starts_a_repeating_timer():
    _, timer, _ = _installed_notifier()
    assert timer.running is True
    assert timer.interval_ms is not None and timer.interval_ms > 0


def test_each_tick_triggers_the_callback():
    _, timer, changes = _installed_notifier()
    timer.timeout.emit()
    timer.timeout.emit()
    assert changes == [True, True]


def test_stop_halts_the_timer():
    notifier, timer, _ = _installed_notifier()
    notifier.stop()
    assert timer.running is False


def test_stop_without_install_is_a_no_op():
    PollingDeviceChangeNotifier(lambda: None).stop()
