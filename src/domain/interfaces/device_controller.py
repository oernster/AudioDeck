"""Device controller interface."""

from typing import Protocol

from src.domain.value_objects.device_type import DeviceType


class IDeviceController(Protocol):
    """Interface for device control operations."""

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: ID of device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If setting default fails
        """
        ...

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        ...
