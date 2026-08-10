"""Use case for switching audio profiles."""

import time
from typing import List
from uuid import UUID

from src.application.dtos.switch_outcome import (
    SkippedDevice,
    SkipReason,
    SwitchOutcome,
)
from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    ProfileNotFoundException,
)
from src.domain.interfaces.device_controller import IDeviceController
from src.domain.interfaces.device_repository import IDeviceRepository
from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.value_objects.device_type import DeviceType

# Settle time after each default-device change, so Windows applies it.
_SETTLE_SECONDS = 0.1
_FINAL_SETTLE_SECONDS = 0.2


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

    def execute(self, profile_id: UUID) -> SwitchOutcome:
        """Switch to the specified audio profile.

        Each configured device is applied independently. A device that is
        missing, unavailable, the wrong type or that fails to set is skipped
        and reported, rather than aborting the whole switch.

        Args:
            profile_id: ID of profile to switch to

        Returns:
            A SwitchOutcome listing applied and skipped devices.

        Raises:
            ProfileNotFoundException: If the profile does not exist.
        """
        profile = self._profile_repository.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundException(f"Profile with ID {profile_id} not found")

        # Refresh device list to ensure we have current state.
        self._device_repository.refresh()

        applied: List[DeviceType] = []
        skipped: List[SkippedDevice] = []

        slots = (
            (DeviceType.OUTPUT, profile.output_device_id),
            (DeviceType.INPUT, profile.input_device_id),
        )
        for device_type, device_id in slots:
            if device_id is None:
                continue
            self._apply_slot(device_type, device_id, applied, skipped)

        # Refresh device list after changes.
        self._device_controller.refresh_devices()
        time.sleep(_FINAL_SETTLE_SECONDS)

        return SwitchOutcome(tuple(applied), tuple(skipped))

    def _apply_slot(
        self,
        device_type: DeviceType,
        device_id: str,
        applied: List[DeviceType],
        skipped: List[SkippedDevice],
    ) -> None:
        """Apply a single device slot, recording the outcome."""
        # Match on id AND direction: one hardware device can appear as both an
        # output and an input under the same id (a duplex headset does on
        # macOS), so an id-only lookup can land on the wrong direction.
        device = next(
            (
                candidate
                for candidate in self._device_repository.get_devices_by_type(
                    device_type
                )
                if candidate.id == device_id
            ),
            None,
        )
        if device is None:
            reason = (
                SkipReason.WRONG_TYPE
                if self._device_repository.get_device_by_id(device_id) is not None
                else SkipReason.UNAVAILABLE
            )
            skipped.append(SkippedDevice(device_type, device_id, reason))
            return
        if not device.is_available:
            skipped.append(
                SkippedDevice(device_type, device_id, SkipReason.UNAVAILABLE)
            )
            return
        try:
            self._device_controller.set_default_device(device_id, device_type)
            applied.append(device_type)
            time.sleep(_SETTLE_SECONDS)
        except DeviceControlException:
            skipped.append(
                SkippedDevice(device_type, device_id, SkipReason.CONTROL_FAILED)
            )
