"""Domain exceptions."""

from .domain_exceptions import (
    AudioDeckException,
    DeviceControlException,
    DeviceNotFoundException,
    ProfileNotFoundException,
    ProfileStorageException,
)

__all__ = [
    "AudioDeckException",
    "DeviceNotFoundException",
    "DeviceControlException",
    "ProfileNotFoundException",
    "ProfileStorageException",
]
