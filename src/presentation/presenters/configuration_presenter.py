"""Presenter for configuration view."""

from typing import List, Optional
from uuid import UUID

from PySide6.QtCore import QObject, Signal

from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.create_profile_use_case import CreateProfileUseCase
from src.application.use_cases.update_profile_use_case import UpdateProfileUseCase
from src.application.use_cases.delete_profile_use_case import DeleteProfileUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.dtos.device_dto import DeviceDTO
from src.application.dtos.profile_dto import ProfileDTO
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import AudioDeckException


class ConfigurationPresenter(QObject):
    """Presenter for configuration view."""

    # Signals
    error_occurred = Signal(str)
    profile_saved = Signal(str)  # profile name

    def __init__(
        self,
        get_devices_use_case: GetDevicesUseCase,
        create_profile_use_case: CreateProfileUseCase,
        update_profile_use_case: UpdateProfileUseCase,
        delete_profile_use_case: DeleteProfileUseCase,
        get_profiles_use_case: GetProfilesUseCase,
    ) -> None:
        """Initialize presenter with use cases.

        Args:
            get_devices_use_case: Use case for getting devices
            create_profile_use_case: Use case for creating profiles
            update_profile_use_case: Use case for updating profiles
            delete_profile_use_case: Use case for deleting profiles
            get_profiles_use_case: Use case for getting profiles
        """
        super().__init__()
        self._get_devices_use_case = get_devices_use_case
        self._create_profile_use_case = create_profile_use_case
        self._update_profile_use_case = update_profile_use_case
        self._delete_profile_use_case = delete_profile_use_case
        self._get_profiles_use_case = get_profiles_use_case

    def get_output_devices(self, refresh: bool = False) -> List[DeviceDTO]:
        """Get output devices.

        Args:
            refresh: Whether to refresh device list

        Returns:
            List of output device DTOs
        """
        try:
            return self._get_devices_use_case.execute(
                device_type=DeviceType.OUTPUT, refresh=refresh
            )
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
            return []

    def get_input_devices(self, refresh: bool = False) -> List[DeviceDTO]:
        """Get input devices.

        Args:
            refresh: Whether to refresh device list

        Returns:
            List of input device DTOs
        """
        try:
            return self._get_devices_use_case.execute(
                device_type=DeviceType.INPUT, refresh=refresh
            )
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
            return []

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

    def get_profile_by_id(self, profile_id: UUID) -> Optional[ProfileDTO]:
        """Get profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile DTO or None if not found
        """
        try:
            return self._get_profiles_use_case.get_by_id(profile_id)
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
            return None

    def create_profile(
        self,
        name: str,
        output_device_id: Optional[str],
        input_device_id: Optional[str],
    ) -> None:
        """Create a new profile.

        Args:
            name: Profile name
            output_device_id: Optional output device ID
            input_device_id: Optional input device ID
        """
        try:
            profile = self._create_profile_use_case.execute(
                name=name,
                output_device_id=output_device_id,
                input_device_id=input_device_id,
            )
            self.profile_saved.emit(profile.name)
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))

    def update_profile(
        self,
        profile_id: UUID,
        name: str,
        output_device_id: Optional[str],
        input_device_id: Optional[str],
    ) -> None:
        """Update an existing profile.

        Args:
            profile_id: Profile ID
            name: Profile name
            output_device_id: Optional output device ID
            input_device_id: Optional input device ID
        """
        try:
            profile = self._update_profile_use_case.execute(
                profile_id=profile_id,
                name=name,
                output_device_id=output_device_id,
                input_device_id=input_device_id,
            )
            self.profile_saved.emit(profile.name)
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))

    def delete_profile(self, profile_id: UUID) -> None:
        """Delete a profile.

        Args:
            profile_id: Profile ID
        """
        try:
            self._delete_profile_use_case.execute(profile_id)
        except AudioDeckException as e:
            self.error_occurred.emit(str(e))
