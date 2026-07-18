"""Domain interfaces (Protocols)."""

from .device_controller import IDeviceController
from .device_repository import IDeviceRepository
from .profile_repository import IProfileRepository

__all__ = ["IDeviceRepository", "IDeviceController", "IProfileRepository"]
