"""Domain layer exceptions."""


class AudioDeckException(Exception):
    """Base exception for Audio Deck application."""

    pass


class DeviceNotFoundException(AudioDeckException):
    """Raised when a device is not found."""

    pass


class DeviceControlException(AudioDeckException):
    """Raised when device control operation fails."""

    pass


class ProfileNotFoundException(AudioDeckException):
    """Raised when a profile is not found."""

    pass


class ProfileStorageException(AudioDeckException):
    """Raised when profile storage operation fails."""

    pass
