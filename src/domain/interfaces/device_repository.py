"""Device repository interface."""

from typing import List, Optional, Protocol

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_type import DeviceType


class IDeviceRepository(Protocol):
    """Interface for device data access."""

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices.

        Returns:
            List of all audio devices
        """
        ...

    def get_devices_by_type(self, device_type: DeviceType) -> List[AudioDevice]:
        """Get devices filtered by type.

        Args:
            device_type: Type of devices to retrieve

        Returns:
            List of devices of specified type
        """
        ...

    def get_default_device(self, device_type: DeviceType) -> Optional[AudioDevice]:
        """Get the default device for a specific type.

        Args:
            device_type: Type of device

        Returns:
            Default device or None if not found
        """
        ...

    def get_device_by_id(self, device_id: str) -> Optional[AudioDevice]:
        """Get a specific device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device or None if not found
        """
        ...

    def refresh(self) -> None:
        """Refresh the device list from the system."""
        ...
