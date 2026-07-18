"""Presenter for actuation view."""

from typing import List, Optional, Set
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
        # The last profile the user switched to, and any of its devices that
        # were unavailable, so they can be auto-applied when they reconnect.
        self._active_profile_id: Optional[UUID] = None
        self._pending_device_ids: Set[str] = set()

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
                self.device_unavailable.emit(self._skip_message(profile, outcome))

            self._remember_pending(profile_id, outcome)
            self.refresh_status()
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error switching profile: {e}")

    def refresh_status(self) -> None:
        """Read the current defaults and availability, and publish them.

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
        device-change notifier. Refreshes the current-default display and, if a
        device a profile was waiting for has reconnected, applies it
        automatically.
        """
        self.refresh_status()
        self._reapply_pending_if_ready()

    def _remember_pending(self, profile_id: UUID, outcome: SwitchOutcome) -> None:
        """Record the active profile and any devices awaiting reconnection."""
        self._active_profile_id = profile_id
        self._pending_device_ids = {
            skipped.device_id
            for skipped in outcome.skipped
            if skipped.reason == SkipReason.UNAVAILABLE
        }

    def _reapply_pending_if_ready(self) -> None:
        """Re-apply the active profile if a pending device is now available."""
        if not self._pending_device_ids or self._active_profile_id is None:
            return
        if not (self._pending_device_ids & self.get_available_device_ids()):
            return

        try:
            profile = self._get_profiles_use_case.get_by_id(self._active_profile_id)
        except Exception:
            return
        if profile is None:
            self._pending_device_ids = set()
            return

        try:
            outcome = self._switch_profile_use_case.execute(self._active_profile_id)
        except Exception:
            return

        if outcome.anything_applied:
            self.auto_applied.emit(
                f"Applied '{profile.name}' now that a device has reconnected."
            )
        self._pending_device_ids = {
            skipped.device_id
            for skipped in outcome.skipped
            if skipped.reason == SkipReason.UNAVAILABLE
        }

    @staticmethod
    def _skip_message(profile: ProfileDTO, outcome: SwitchOutcome) -> str:
        """Build a friendly notice describing skipped devices."""
        directions = ", ".join(
            skipped.device_type.display_name for skipped in outcome.skipped
        )
        if outcome.anything_applied:
            return (
                f"Switched '{profile.name}', but the {directions} device is not "
                "available right now. It will need to be connected."
            )
        return (
            f"Could not switch '{profile.name}': the {directions} device is not "
            "available. Connect it, or edit the profile in the Configuration tab."
        )
