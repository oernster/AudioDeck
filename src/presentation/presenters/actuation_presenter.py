"""Presenter for actuation view."""

from typing import Dict, List, Optional, Set
from uuid import UUID

from PySide6.QtCore import QObject, Signal

from src.application.dtos.device_dto import DeviceDTO
from src.application.dtos.profile_dto import ProfileDTO
from src.application.dtos.switch_outcome import SkipReason, SwitchOutcome
from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.exceptions.domain_exceptions import AudioDeckException
from src.domain.value_objects.device_type import DeviceType
from src.presentation.presenters.switch_messages import skip_message


class ActuationPresenter(QObject):
    """Presenter for actuation view."""

    # Signals
    error_occurred = Signal(str)
    device_unavailable = Signal(str)  # friendly notice, not an error
    profile_switched = Signal(str)  # profile name
    # Computed off the GUI thread: (output DTO|None, input DTO|None, available ids)
    status_ready = Signal(object, object, object)
    auto_applied = Signal(str)  # a pending device was applied on reconnect

    def __init__(
        self,
        get_devices_use_case: GetDevicesUseCase,
        get_profiles_use_case: GetProfilesUseCase,
        switch_profile_use_case: SwitchProfileUseCase,
    ) -> None:
        """Initialize presenter with use cases.

        Args:
            get_devices_use_case: Use case for getting devices
            get_profiles_use_case: Use case for getting profiles
            switch_profile_use_case: Use case for switching profiles
        """
        super().__init__()
        self._get_devices_use_case = get_devices_use_case
        self._get_profiles_use_case = get_profiles_use_case
        self._switch_profile_use_case = switch_profile_use_case
        # The last profile the user switched to; the device each slot was
        # set to; the slots still waiting for their device to reconnect.
        self._active_profile_id: Optional[UUID] = None
        self._applied: Dict[DeviceType, str] = {}
        self._pending: Dict[DeviceType, str] = {}

    def get_profiles(self) -> List[ProfileDTO]:
        """Get all profiles.

        Returns:
            List of profile DTOs
        """
        try:
            return self._get_profiles_use_case.execute()
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
            return []

    def get_current_output_device(self) -> Optional[DeviceDTO]:
        """Get current default output device.

        Returns:
            Current output device DTO or None
        """
        # Status read used by periodic polling: never raise a dialog, just
        # show "None" if the device cannot be read this moment.
        try:
            return self._get_devices_use_case.get_default_device(DeviceType.OUTPUT)
        except Exception:
            return None

    def get_current_input_device(self) -> Optional[DeviceDTO]:
        """Get current default input device.

        Returns:
            Current input device DTO or None
        """
        # Status read used by periodic polling: never raise a dialog.
        try:
            return self._get_devices_use_case.get_default_device(DeviceType.INPUT)
        except Exception:
            return None

    def get_available_device_ids(self) -> Set[str]:
        """Return the IDs of devices that are currently available.

        Used to badge profiles whose configured devices are offline. Silent on
        error, since it is called during periodic and incidental refreshes.

        Returns:
            Set of available device IDs (empty if devices cannot be read).
        """
        try:
            devices = self._get_devices_use_case.execute(refresh=True)
            return {device.id for device in devices if device.is_available}
        except Exception:
            return set()

    def switch_profile(self, profile_id: UUID) -> None:
        """Switch to a profile.

        Applies whichever configured devices are available now and reports any
        that were skipped (for example a disconnected Bluetooth headset).

        Args:
            profile_id: Profile ID to switch to
        """
        try:
            profile = self._get_profiles_use_case.get_by_id(profile_id)
            if profile is None:
                self.error_occurred.emit("Profile not found")
                return

            outcome = self._switch_profile_use_case.execute(profile_id)

            if outcome.anything_applied:
                self.profile_switched.emit(profile.name)
            if outcome.skipped:
                self.device_unavailable.emit(skip_message(profile.name, outcome))

            self._active_profile_id = profile_id
            self._applied = {}
            self._pending = {}
            self._record(profile, outcome)
            self.refresh_status()
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error switching profile: {e}")

    def refresh_status(self) -> None:
        """Read the current defaults and availability, then publish them.

        Runs on a background thread; emits status_ready with plain data so the
        GUI thread only renders (it never touches the audio API itself).
        """
        output = self.get_current_output_device()
        input_device = self.get_current_input_device()
        available = self.get_available_device_ids()
        self.status_ready.emit(output, input_device, available)

    def on_devices_changed(self) -> None:
        """React to a device add, remove or state change.

        Called (on a background thread) by the periodic timer and the native
        device-change notifier. Refreshes the current-default display, then
        applies a device a profile was waiting for if it has reconnected.
        """
        self.refresh_status()
        self._reapply_pending_if_ready()

    def _record(self, profile: ProfileDTO, outcome: SwitchOutcome) -> None:
        """Note what a switch applied and which slots now wait to reconnect."""
        configured = {
            device_type: device_id
            for device_type, device_id in (
                (DeviceType.OUTPUT, profile.output_device_id),
                (DeviceType.INPUT, profile.input_device_id),
            )
            if device_id is not None
        }
        self._applied.update(
            {
                device_type: configured[device_type]
                for device_type in outcome.applied
                if device_type in configured
            }
        )
        for skipped in outcome.skipped:
            if skipped.reason == SkipReason.UNAVAILABLE:
                self._pending[skipped.device_type] = skipped.device_id

    def _defaults_moved(self) -> bool:
        """Say whether a default this presenter set has since been changed.

        Another switch (a Stream Deck key, the system's own settings) has
        then taken over; re-applying the old profile's device would undo
        it. A default that cannot be read is not evidence of a move.
        """
        for device_type, device_id in self._applied.items():
            try:
                current = self._get_devices_use_case.get_default_device(
                    device_type, refresh=False
                )
            except Exception:
                continue
            if current is not None and current.is_default and current.id != device_id:
                return True
        return False

    def _reapply_pending_if_ready(self) -> None:
        """Apply a waiting slot whose device is available again.

        Only the waiting slot is applied, never the whole profile. It happens only
        while the defaults are still the ones this presenter set: once
        something else has switched, the wait is over.
        """
        if not self._pending or self._active_profile_id is None:
            return
        available = self.get_available_device_ids()
        if self._defaults_moved():
            self._pending = {}
            return
        ready = tuple(
            device_type
            for device_type, device_id in self._pending.items()
            if device_id in available
        )
        if not ready:
            return

        try:
            profile = self._get_profiles_use_case.get_by_id(self._active_profile_id)
        except Exception:
            # Silent by design: this runs off a device-change event the user did
            # not trigger, so a dialog here would appear out of nowhere. The
            # pending slots are left intact, so the next event tries again.
            return
        if profile is None:
            self._pending = {}
            return

        try:
            outcome = self._switch_profile_use_case.execute(
                self._active_profile_id, slots=ready
            )
        except Exception:
            # Same reasoning as above: unprompted work, so it fails quietly and
            # leaves the pending slots for the next device-change event. A
            # switch the user asked for is handled by switch_profile, which
            # does report.
            return

        for device_type in ready:
            self._pending.pop(device_type, None)
        self._record(profile, outcome)
        if outcome.anything_applied:
            names = " and ".join(
                device_type.display_name for device_type in outcome.applied
            )
            self.auto_applied.emit(
                f"Applied the {names} device of '{profile.name}' now that it "
                "has reconnected."
            )
