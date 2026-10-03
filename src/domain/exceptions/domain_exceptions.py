"""Domain layer exceptions."""

from typing import Tuple


class AudioDeckException(Exception):
    """Base exception for Audio Deck application."""

    pass


class DeviceNotFoundException(AudioDeckException):
    """Raised when a device is not found.

    A controller raises it when the device left between the enumeration and
    the set, so the switch can treat it as unavailable and wait for it to
    come back rather than report a refusal.
    """

    pass


class DeviceEnumerationException(AudioDeckException):
    """Raised when the system's devices cannot be read at all.

    Distinct from an empty answer: a machine whose devices could not be read
    must never look like one whose devices are all disconnected.
    """

    pass


class DeviceControlException(AudioDeckException):
    """Raised when device control operation fails."""

    pass


class PartialDeviceControlException(DeviceControlException):
    """Raised when a device became the default for only some of its roles.

    Windows keeps a separate default per role; the device is the default for
    every role except those named in missing_roles.
    """

    def __init__(self, missing_roles: Tuple[str, ...]) -> None:
        """Initialize with the roles that did not take the device.

        Args:
            missing_roles: Display names of the roles still on the old device
        """
        super().__init__(f"Not set for: {', '.join(missing_roles)}")
        self.missing_roles = missing_roles


class ProfileNotFoundException(AudioDeckException):
    """Raised when a profile is not found."""

    pass


class ProfileStorageException(AudioDeckException):
    """Raised when profile storage operation fails."""

    pass


class SwitchInProgressException(AudioDeckException):
    """Raised when another switch still holds the lock after a bounded wait."""

    pass


class UnsupportedPlatformException(AudioDeckException):
    """Raised when no audio backend exists for the running platform."""

    pass
