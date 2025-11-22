"""Domain exceptions."""

from .domain_exceptions import (
    AudioDeckException,
    DeviceNotFoundException,
    DeviceControlException,
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
