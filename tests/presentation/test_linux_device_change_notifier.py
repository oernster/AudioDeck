"""Tests for the pactl-subscribe Linux device-change notifier."""

from src.presentation.notifiers.linux_device_change_notifier import (
    LinuxDeviceChangeNotifier,
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


class FakeProcess:
    """Hand-written stand-in for QProcess."""

    def __init__(self) -> None:
        self.readyReadStandardOutput = FakeSignal()
        self.started_with = None
        self.killed = False
        self.pending_output = b""

    def start(self, program, arguments) -> None:
        self.started_with = (program, tuple(arguments))

    def kill(self) -> None:
        self.killed = True

    def readAllStandardOutput(self) -> bytes:
        output, self.pending_output = self.pending_output, b""
        return output


class FakeApp:
    """Hand-written stand-in for QApplication."""

    def __init__(self) -> None:
        self.aboutToQuit = FakeSignal()


def _installed_notifier():
    process = FakeProcess()
    changes = []
    notifier = LinuxDeviceChangeNotifier(
        lambda: changes.append(True), process_factory=lambda: process
    )
    notifier.install(FakeApp())
    return notifier, process, changes


def test_install_starts_pactl_subscribe():
    _, process, _ = _installed_notifier()
    assert process.started_with == ("pactl", ("subscribe",))


def test_a_sink_event_triggers_the_callback():
    _, process, changes = _installed_notifier()
    process.pending_output = b"Event 'new' on sink #2\n"
    process.readyReadStandardOutput.emit()
    assert changes == [True]


def test_a_source_event_triggers_the_callback():
    _, process, changes = _installed_notifier()
    process.pending_output = b"Event 'remove' on source #5\n"
    process.readyReadStandardOutput.emit()
    assert changes == [True]


def test_a_server_event_triggers_the_callback():
    _, process, changes = _installed_notifier()
    process.pending_output = b"Event 'change' on server #0\n"
    process.readyReadStandardOutput.emit()
    assert changes == [True]


def test_an_unrelated_event_does_not_trigger_the_callback():
    _, process, changes = _installed_notifier()
    process.pending_output = b"Event 'change' on client #31\n"
    process.readyReadStandardOutput.emit()
    assert changes == []


def test_stop_kills_the_process():
    notifier, process, _ = _installed_notifier()
    notifier.stop()
    assert process.killed is True


def test_quitting_the_app_stops_the_process():
    process = FakeProcess()
    app = FakeApp()
    notifier = LinuxDeviceChangeNotifier(lambda: None, lambda: process)
    notifier.install(app)
    app.aboutToQuit.emit()
    assert process.killed is True


def test_output_after_stop_is_ignored():
    notifier, process, changes = _installed_notifier()
    notifier.stop()
    process.pending_output = b"Event 'new' on sink #2\n"
    process.readyReadStandardOutput.emit()
    assert changes == []


def test_stop_without_install_is_a_no_op():
    LinuxDeviceChangeNotifier(lambda: None).stop()
