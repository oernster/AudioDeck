"""Presenter for actuation view."""

from typing import List, Optional
from uuid import UUID

from PySide6.QtCore import QObject, Signal

from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.application.dtos.device_dto import DeviceDTO
from src.application.dtos.profile_dto import ProfileDTO
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import (
    AudioDeckException,
    DeviceNotFoundException,
)


class ActuationPresenter(QObject):
    """Presenter for actuation view."""

    # Signals
    error_occurred = Signal(str)
    device_unavailable = Signal(str)  # friendly notice, not an error
    profile_switched = Signal(str)  # profile name

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

    def switch_profile(self, profile_id: UUID) -> None:
        """Switch to a profile.

        Args:
            profile_id: Profile ID to switch to
        """
        try:
            # Get profile name for success message
            profile = self._get_profiles_use_case.get_by_id(profile_id)
            if profile is None:
                self.error_occurred.emit("Profile not found")
                return

            # Switch profile
            self._switch_profile_use_case.execute(profile_id)
            self.profile_switched.emit(profile.name)
        except DeviceNotFoundException:
            # A configured device is not currently available (for example a
            # Bluetooth headset that is off). This is a normal condition, not
            # a crash, so surface a friendly notice.
            self.device_unavailable.emit(
                f"A device in '{profile.name}' is not currently available. "
                "Connect the device, or edit the profile in the Configuration "
                "tab."
            )
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error switching profile: {e}")
