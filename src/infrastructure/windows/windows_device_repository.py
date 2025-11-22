"""Windows device repository implementation."""

from typing import List, Optional

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.windows.device_enumerator import WindowsDeviceEnumerator


class WindowsDeviceRepository:
    """Repository for Windows audio devices."""

    def __init__(
        self, enumerator: WindowsDeviceEnumerator, auto_refresh: bool = True
    ) -> None:
        """Initialize repository.

        Args:
            enumerator: Device enumerator instance
            auto_refresh: Whether to automatically refresh on initialization
        """
        self._enumerator = enumerator
        self._devices: List[AudioDevice] = []
        if auto_refresh:
            self.refresh()

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices.

        Returns:
            List of all audio devices
        """
        return self._devices.copy()

    def get_devices_by_type(self, device_type: DeviceType) -> List[AudioDevice]:
        """Get devices filtered by type.

        Args:
            device_type: Type of devices to retrieve

        Returns:
            List of devices of specified type
        """
        return [d for d in self._devices if d.device_type == device_type]

    def get_default_device(self, device_type: DeviceType) -> Optional[AudioDevice]:
        """Get the default device for a specific type.

        Args:
            device_type: Type of device

        Returns:
            Default device or None if not found
        """
        devices = self.get_devices_by_type(device_type)
        for device in devices:
            if device.is_default:
                return device
        # Return first device if no default found
        return devices[0] if devices else None

    def get_device_by_id(self, device_id: str) -> Optional[AudioDevice]:
        """Get a specific device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device or None if not found
        """
        for device in self._devices:
            if device.id == device_id:
                return device
        return None

    def refresh(self) -> None:
        """Refresh the device list from the system."""
        self._devices = self._enumerator.get_all_devices()
