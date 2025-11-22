"""Use case for retrieving audio devices."""

from typing import List, Optional

from src.domain.interfaces.device_repository import IDeviceRepository
from src.domain.value_objects.device_type import DeviceType
from src.application.dtos.device_dto import DeviceDTO


class GetDevicesUseCase:
    """Use case for retrieving audio devices."""

    def __init__(self, device_repository: IDeviceRepository) -> None:
        """Initialize use case with device repository.

        Args:
            device_repository: Repository for device data access
        """
        self._device_repository = device_repository

    def execute(
        self, device_type: Optional[DeviceType] = None, refresh: bool = False
    ) -> List[DeviceDTO]:
        """Get audio devices, optionally filtered by type.

        Args:
            device_type: Optional device type to filter by
            refresh: Whether to refresh device list before retrieving

        Returns:
            List of device DTOs
        """
        if refresh:
            self._device_repository.refresh()

        if device_type is None:
            devices = self._device_repository.get_all_devices()
        else:
            devices = self._device_repository.get_devices_by_type(device_type)

        # Convert domain entities to DTOs
        return [
            DeviceDTO(
                id=device.id,
                name=device.name,
                device_type=device.device_type,
                is_default=device.is_default,
                is_enabled=device.is_enabled,
            )
            for device in devices
        ]

    def get_default_device(
        self, device_type: DeviceType, refresh: bool = True
    ) -> Optional[DeviceDTO]:
        """Get the default device for a specific type.

        Args:
            device_type: Type of device to get default for
            refresh: Whether to refresh device list before retrieving (default: True)

        Returns:
            Default device DTO or None if not found
        """
        if refresh:
            self._device_repository.refresh()

        device = self._device_repository.get_default_device(device_type)
        if device is None:
            return None

        return DeviceDTO(
            id=device.id,
            name=device.name,
            device_type=device.device_type,
            is_default=device.is_default,
            is_enabled=device.is_enabled,
        )
