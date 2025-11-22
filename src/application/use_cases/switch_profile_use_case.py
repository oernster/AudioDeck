"""Use case for switching audio profiles."""

import time
from uuid import UUID

from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.interfaces.device_repository import IDeviceRepository
from src.domain.interfaces.device_controller import IDeviceController
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import (
    ProfileNotFoundException,
    DeviceNotFoundException,
    DeviceControlException,
)


class SwitchProfileUseCase:
    """Use case for switching to an audio profile."""

    def __init__(
        self,
        profile_repository: IProfileRepository,
        device_repository: IDeviceRepository,
        device_controller: IDeviceController,
    ) -> None:
        """Initialize use case with repositories and controller.

        Args:
            profile_repository: Repository for profile persistence
            device_repository: Repository for device data access
            device_controller: Controller for device operations
        """
        self._profile_repository = profile_repository
        self._device_repository = device_repository
        self._device_controller = device_controller

    def execute(self, profile_id: UUID) -> None:
        """Switch to the specified audio profile.

        This will set the default input and/or output devices
        according to the profile configuration.

        Args:
            profile_id: ID of profile to switch to

        Raises:
            ProfileNotFoundException: If profile doesn't exist
            DeviceNotFoundException: If configured device doesn't exist
            DeviceControlException: If device switching fails
        """
        # Get profile
        profile = self._profile_repository.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundException(f"Profile with ID {profile_id} not found")

        # Refresh device list to ensure we have current state
        self._device_repository.refresh()

        # Switch output device if configured
        if profile.output_device_id is not None:
            output_device = self._device_repository.get_device_by_id(
                profile.output_device_id
            )
            if output_device is None:
                raise DeviceNotFoundException(
                    f"Output device {profile.output_device_id} not found"
                )

            if output_device.device_type != DeviceType.OUTPUT:
                raise DeviceControlException(
                    f"Device {profile.output_device_id} is not an output device"
                )

            self._device_controller.set_default_device(
                profile.output_device_id, DeviceType.OUTPUT
            )

            # Give Windows a moment to process the change
            time.sleep(0.1)

        # Switch input device if configured
        if profile.input_device_id is not None:
            input_device = self._device_repository.get_device_by_id(
                profile.input_device_id
            )
            if input_device is None:
                raise DeviceNotFoundException(
                    f"Input device {profile.input_device_id} not found"
                )

            if input_device.device_type != DeviceType.INPUT:
                raise DeviceControlException(
                    f"Device {profile.input_device_id} is not an input device"
                )

            self._device_controller.set_default_device(
                profile.input_device_id, DeviceType.INPUT
            )

            # Give Windows a moment to process the change
            time.sleep(0.1)

        # Refresh device list after changes
        self._device_controller.refresh_devices()

        # Additional delay to ensure Windows has fully processed both changes
        time.sleep(0.2)
