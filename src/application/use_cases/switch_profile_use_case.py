"""Use case for switching audio profiles."""

import contextlib
import time
from typing import Collection, ContextManager, Dict, List, Optional
from uuid import UUID

from src.application.dtos.switch_outcome import (
    SkippedDevice,
    SkipReason,
    SwitchOutcome,
)
from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    DeviceEnumerationException,
    DeviceNotFoundException,
    PartialDeviceControlException,
    ProfileNotFoundException,
)
from src.domain.interfaces.device_controller import IDeviceController
from src.domain.interfaces.device_repository import IDeviceRepository
from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.interfaces.switch_lock import ISwitchLock
from src.domain.value_objects.device_type import DeviceType

# Settle time after each default-device change, so Windows applies it.
_SETTLE_SECONDS = 0.1
_FINAL_SETTLE_SECONDS = 0.2

# Both slots, in the order a switch applies them.
ALL_SLOTS = (DeviceType.OUTPUT, DeviceType.INPUT)


class SwitchProfileUseCase:
    """Use case for switching to an audio profile."""

    def __init__(
        self,
        profile_repository: IProfileRepository,
        device_repository: IDeviceRepository,
        device_controller: IDeviceController,
        switch_lock: Optional[ISwitchLock] = None,
    ) -> None:
        """Initialize use case with repositories and controller.

        Args:
            profile_repository: Repository for profile persistence
            device_repository: Repository for device data access
            device_controller: Controller for device operations
            switch_lock: The per-user lock both the GUI and the CLI hold for
                the length of a switch; None runs unlocked
        """
        self._profile_repository = profile_repository
        self._device_repository = device_repository
        self._device_controller = device_controller
        self._switch_lock = switch_lock

    def execute(
        self, profile_id: UUID, slots: Collection[DeviceType] = ALL_SLOTS
    ) -> SwitchOutcome:
        """Switch to the specified audio profile.

        Each configured device is applied independently. A device that is
        missing, unavailable, the wrong type or that fails to set is skipped
        and reported, rather than aborting the whole switch. After the settle
        time the defaults are read back, so a call the system accepted
        without acting on is reported rather than called a switch.

        Args:
            profile_id: ID of profile to switch to
            slots: The slots to apply; a reconnect applies only the one that
                was waiting

        Returns:
            A SwitchOutcome listing applied and skipped devices.

        Raises:
            ProfileNotFoundException: If the profile does not exist.
            DeviceEnumerationException: If the devices cannot be read.
            SwitchInProgressException: If another switch holds the lock.
        """
        with self._lock():
            profile = self._profile_repository.get_by_id(profile_id)
            if profile is None:
                raise ProfileNotFoundException(
                    f"Profile with ID {profile_id} not found"
                )

            # Refresh device list to ensure we have current state.
            self._device_repository.refresh()

            targets = {
                device_type: device_id
                for device_type, device_id in (
                    (DeviceType.OUTPUT, profile.output_device_id),
                    (DeviceType.INPUT, profile.input_device_id),
                )
                if device_id is not None and device_type in slots
            }
            applied: List[DeviceType] = []
            skipped: List[SkippedDevice] = []
            for device_type, device_id in targets.items():
                self._apply_slot(device_type, device_id, applied, skipped)

            # Refresh device list after changes.
            self._device_controller.refresh_devices()
            time.sleep(_FINAL_SETTLE_SECONDS)
            self._confirm_applied(targets, applied, skipped)

        return SwitchOutcome(tuple(applied), tuple(skipped))

    def _lock(self) -> ContextManager[None]:
        """Hold the switch lock; hold nothing when none was supplied."""
        if self._switch_lock is None:
            return contextlib.nullcontext()
        return self._switch_lock.hold()

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
        except DeviceNotFoundException:
            # Gone between the enumeration and the set: it waits to come
            # back like any other unavailable device, rather than read as
            # the system refusing it.
            skipped.append(
                SkippedDevice(device_type, device_id, SkipReason.UNAVAILABLE)
            )
            return
        except PartialDeviceControlException as partial:
            skipped.append(
                SkippedDevice(
                    device_type,
                    device_id,
                    SkipReason.PARTIALLY_SET,
                    ", ".join(partial.missing_roles),
                )
            )
        except DeviceControlException:
            skipped.append(
                SkippedDevice(device_type, device_id, SkipReason.CONTROL_FAILED)
            )
            return
        applied.append(device_type)
        time.sleep(_SETTLE_SECONDS)

    def _confirm_applied(
        self,
        targets: Dict[DeviceType, str],
        applied: List[DeviceType],
        skipped: List[SkippedDevice],
    ) -> None:
        """Read the defaults back and demote any slot the system ignored.

        A slot whose default cannot be read (the read fails; no device of
        that flow is marked default) keeps the call's own success: an unknown
        is not evidence of a failure.
        """
        try:
            self._device_repository.refresh()
        except DeviceEnumerationException:
            return
        for device_type in list(applied):
            current = next(
                (
                    device.id
                    for device in self._device_repository.get_devices_by_type(
                        device_type
                    )
                    if device.is_default
                ),
                None,
            )
            if current is None or current == targets[device_type]:
                continue
            applied.remove(device_type)
            skipped[:] = [skip for skip in skipped if skip.device_type != device_type]
            skipped.append(
                SkippedDevice(
                    device_type, targets[device_type], SkipReason.DID_NOT_TAKE
                )
            )
