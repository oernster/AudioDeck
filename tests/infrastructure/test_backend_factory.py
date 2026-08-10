"""Tests for the platform backend factory."""

import pytest

from src.domain.exceptions.domain_exceptions import UnsupportedPlatformException
from src.infrastructure.backend_factory import (
    create_device_backend,
    create_single_instance,
)
from src.infrastructure.linux.linux_device_controller import LinuxDeviceController
from src.infrastructure.linux.linux_device_enumerator import LinuxDeviceEnumerator
from src.infrastructure.macos.macos_device_controller import MacosDeviceController
from src.infrastructure.macos.macos_device_enumerator import MacosDeviceEnumerator
from src.infrastructure.posix.single_instance import PosixSingleInstanceGuard
from src.infrastructure.windows.device_enumerator import WindowsDeviceEnumerator
from src.infrastructure.windows.single_instance import SingleInstanceGuard
from src.infrastructure.windows.windows_device_controller import (
    WindowsDeviceController,
)

# A title no real window carries, so the Windows activation path exercises
# its not-found branch without touching any actual window.
_ABSENT_WINDOW_TITLE = "AudioDeck test window that does not exist"


def test_win32_gets_the_windows_backend():
    backend = create_device_backend("win32")
    assert isinstance(backend.enumerator, WindowsDeviceEnumerator)
    assert isinstance(backend.controller, WindowsDeviceController)


def test_linux_gets_the_pactl_backend():
    backend = create_device_backend("linux")
    assert isinstance(backend.enumerator, LinuxDeviceEnumerator)
    assert isinstance(backend.controller, LinuxDeviceController)


def test_darwin_gets_the_coreaudio_backend():
    backend = create_device_backend("darwin")
    assert isinstance(backend.enumerator, MacosDeviceEnumerator)
    assert isinstance(backend.controller, MacosDeviceController)


def test_an_unknown_platform_raises():
    with pytest.raises(UnsupportedPlatformException):
        create_device_backend("plan9")


def test_win32_single_instance_uses_the_named_mutex_guard():
    single = create_single_instance("win32")
    assert isinstance(single.guard, SingleInstanceGuard)


def test_win32_activation_reports_false_for_an_absent_window():
    single = create_single_instance("win32")
    assert single.activate(_ABSENT_WINDOW_TITLE) is False


def test_posix_single_instance_uses_the_lock_file_guard():
    single = create_single_instance("linux")
    assert isinstance(single.guard, PosixSingleInstanceGuard)


def test_posix_activation_is_a_no_op():
    single = create_single_instance("darwin")
    assert single.activate(_ABSENT_WINDOW_TITLE) is False
