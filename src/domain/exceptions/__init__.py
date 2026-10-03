"""Domain exceptions."""

from .domain_exceptions import (
    AudioDeckException,
    DeviceControlException,
    DeviceEnumerationException,
    DeviceNotFoundException,
    PartialDeviceControlException,
    ProfileNotFoundException,
    ProfileStorageException,
    SwitchInProgressException,
)

__all__ = [
    "AudioDeckException",
    "DeviceNotFoundException",
    "DeviceEnumerationException",
    "DeviceControlException",
    "PartialDeviceControlException",
    "ProfileNotFoundException",
    "ProfileStorageException",
    "SwitchInProgressException",
]
