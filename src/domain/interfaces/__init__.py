"""Domain interfaces (Protocols)."""

from .device_repository import IDeviceRepository
from .device_controller import IDeviceController
from .profile_repository import IProfileRepository

__all__ = ["IDeviceRepository", "IDeviceController", "IProfileRepository"]
