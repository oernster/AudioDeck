"""Tests for the WM_DEVICECHANGE native event filter.

A real ctypes MSG is built and its address passed in, exactly as Qt would,
so the pointer cast in the filter is genuinely exercised.
"""

import ctypes
from ctypes import wintypes

from src.presentation.notifiers.device_change_notifier import (
    _WINDOWS_MSG_EVENT,
    _WM_DEVICECHANGE,
    WindowsDeviceChangeNotifier,
)

# An unrelated Windows message, used to prove the filter is selective.
WM_PAINT = 0x000F


class FakeApp:
    """Records native event filter installation."""

    def __init__(self):
        self.installed = []

    def installNativeEventFilter(self, filter_):  # noqa: N802 (Qt naming)
        self.installed.append(filter_)


class CallRecorder:
    """Counts how many times it was called."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1


def _message_at(message_id):
    """Build a real MSG and return it with its address.

    The MSG is returned alongside the address so the caller keeps a reference;
    letting it be collected would leave the address dangling.
    """
    msg = wintypes.MSG()
    msg.message = message_id
    return msg, ctypes.addressof(msg)


def test_install_registers_the_filter():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    app = FakeApp()
    notifier.install(app)
    assert app.installed == [notifier]


def test_device_change_invokes_the_callback():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    _msg, address = _message_at(_WM_DEVICECHANGE)
    notifier.nativeEventFilter(_WINDOWS_MSG_EVENT, address)
    assert recorder.calls == 1


def test_other_windows_messages_are_ignored():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    _msg, address = _message_at(WM_PAINT)
    notifier.nativeEventFilter(_WINDOWS_MSG_EVENT, address)
    assert recorder.calls == 0


def test_other_event_types_are_ignored():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    _msg, address = _message_at(_WM_DEVICECHANGE)
    notifier.nativeEventFilter(b"xcb_generic_event_t", address)
    assert recorder.calls == 0


def test_a_bad_message_pointer_is_swallowed():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    # None cannot be cast to a pointer; the filter must not propagate that.
    notifier.nativeEventFilter(_WINDOWS_MSG_EVENT, None)
    assert recorder.calls == 0


def test_a_failing_callback_is_swallowed():
    def boom():
        raise RuntimeError("callback exploded")

    notifier = WindowsDeviceChangeNotifier(boom)
    _msg, address = _message_at(_WM_DEVICECHANGE)
    assert notifier.nativeEventFilter(_WINDOWS_MSG_EVENT, address) == (False, 0)


def test_filter_never_consumes_the_event():
    recorder = CallRecorder()
    notifier = WindowsDeviceChangeNotifier(recorder)
    _msg, address = _message_at(_WM_DEVICECHANGE)
    assert notifier.nativeEventFilter(_WINDOWS_MSG_EVENT, address) == (False, 0)
