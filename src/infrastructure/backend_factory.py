"""Selects the platform's audio backend and single-instance guard.

The composition roots pass sys.platform in and receive fully built
infrastructure out, so all platform dispatch lives here and nowhere else.
Platform modules are imported inside their branch: pycaw and comtypes do
not exist off Windows, so a module-level import would break the other
platforms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from src.domain.exceptions.domain_exceptions import UnsupportedPlatformException
from src.domain.interfaces.device_controller import IDeviceController
from src.domain.interfaces.device_enumerator import IDeviceEnumerator

# The Windows mutex name. The "Local\" namespace scopes it to the current
# logon session, matching the per-user profiles store: two different Windows
# users may each run their own copy.
_WINDOWS_MUTEX_NAME = "Local\\OliverErnster.AudioDeck.SingleInstance"


@dataclass(frozen=True)
class DeviceBackend:
    """The platform pair the device use cases are wired with."""

    enumerator: IDeviceEnumerator
    controller: IDeviceController


@dataclass(frozen=True)
class SingleInstance:
    """The platform single-instance guard plus its activation step.

    activate raises the already-running instance's window by title where
    the platform supports that; elsewhere it is a no-op returning False.
    """

    guard: "InstanceGuard"
    activate: Callable[[str], bool]


class InstanceGuard(Protocol):
    """Structural type for the guards."""

    def acquire(self) -> bool:
        """Try to become the single running instance."""
        ...

    def release(self) -> None:
        """Give the instance lock up."""
        ...


def create_device_backend(platform: str) -> DeviceBackend:
    """Build the audio enumerator and controller for a platform.

    Args:
        platform: The sys.platform string

    Returns:
        The platform's DeviceBackend

    Raises:
        UnsupportedPlatformException: If no backend exists for the platform
    """
    if platform == "win32":
        from src.infrastructure.windows.device_enumerator import (
            WindowsDeviceEnumerator,
        )
        from src.infrastructure.windows.windows_device_controller import (
            WindowsDeviceController,
        )

        return DeviceBackend(WindowsDeviceEnumerator(), WindowsDeviceController())

    if platform.startswith("linux"):
        from src.infrastructure.linux.linux_device_controller import (
            LinuxDeviceController,
        )
        from src.infrastructure.linux.linux_device_enumerator import (
            LinuxDeviceEnumerator,
        )
        from src.infrastructure.linux.pactl_api import SubprocessPactlApi

        pactl = SubprocessPactlApi()
        return DeviceBackend(LinuxDeviceEnumerator(pactl), LinuxDeviceController(pactl))

    if platform == "darwin":
        from src.infrastructure.macos.coreaudio_api import CtypesCoreAudioApi
        from src.infrastructure.macos.macos_device_controller import (
            MacosDeviceController,
        )
        from src.infrastructure.macos.macos_device_enumerator import (
            MacosDeviceEnumerator,
        )

        core_audio = CtypesCoreAudioApi()
        return DeviceBackend(
            MacosDeviceEnumerator(core_audio), MacosDeviceController(core_audio)
        )

    raise UnsupportedPlatformException(f"No audio backend for platform: {platform}")


def create_single_instance(platform: str) -> SingleInstance:
    """Build the single-instance guard for a platform.

    Args:
        platform: The sys.platform string

    Returns:
        The platform's SingleInstance
    """
    if platform == "win32":
        from src.infrastructure.windows.single_instance import (
            SingleInstanceGuard,
            Win32MutexApi,
            Win32WindowApi,
            activate_existing_window,
        )

        window_api = Win32WindowApi()
        return SingleInstance(
            guard=SingleInstanceGuard(_WINDOWS_MUTEX_NAME, Win32MutexApi()),
            activate=lambda title: activate_existing_window(title, window_api),
        )

    from src.infrastructure.posix.single_instance import (
        FcntlLockFileApi,
        PosixSingleInstanceGuard,
        default_lock_path,
    )

    # Neither Wayland nor macOS lets one process reliably raise another
    # application's window, so activation is a no-op there.
    return SingleInstance(
        guard=PosixSingleInstanceGuard(default_lock_path(), FcntlLockFileApi()),
        activate=lambda title: False,
    )
