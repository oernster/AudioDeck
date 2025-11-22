"""Script to create application layer files."""

from pathlib import Path

BASE_DIR = Path(__file__).parent
FILES = {}

# Application layer init
FILES["src/application/__init__.py"] = (
    '"""Application layer - Use cases and business logic."""\n'
)

# DTOs
FILES[
    "src/application/dtos/__init__.py"
] = '''"""Data Transfer Objects for application layer."""

from .device_dto import DeviceDTO
from .profile_dto import ProfileDTO

__all__ = ["DeviceDTO", "ProfileDTO"]
'''

FILES[
    "src/application/dtos/device_dto.py"
] = '''"""Device Data Transfer Object."""

from dataclasses import dataclass

from src.domain.value_objects.device_type import DeviceType


@dataclass(frozen=True)
class DeviceDTO:
    """DTO for transferring device data between layers."""

    id: str
    name: str
    device_type: DeviceType
    is_default: bool
    is_enabled: bool

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        status_parts = []
        if self.is_default:
            status_parts.append("Default")
        if not self.is_enabled:
            status_parts.append("Disabled")

        if status_parts:
            return f"{self.name} ({', '.join(status_parts)})"
        return self.name

    @property
    def type_display(self) -> str:
        """Get device type display name."""
        return self.device_type.display_name
'''

FILES[
    "src/application/dtos/profile_dto.py"
] = '''"""Profile Data Transfer Object."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class ProfileDTO:
    """DTO for transferring profile data between layers."""

    id: UUID
    name: str
    output_device_id: Optional[str]
    input_device_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @property
    def has_output(self) -> bool:
        """Check if profile has output device configured."""
        return self.output_device_id is not None

    @property
    def has_input(self) -> bool:
        """Check if profile has input device configured."""
        return self.input_device_id is not None

    @property
    def is_complete(self) -> bool:
        """Check if profile has both input and output configured."""
        return self.has_output and self.has_input

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        parts = []
        if self.has_output:
            parts.append("Output")
        if self.has_input:
            parts.append("Input")

        if parts:
            return f"{self.name} ({' + '.join(parts)})"
        return f"{self.name} (Empty)"
'''

# Use cases init
FILES[
    "src/application/use_cases/__init__.py"
] = '''"""Application use cases."""

from .get_devices_use_case import GetDevicesUseCase
from .create_profile_use_case import CreateProfileUseCase
from .update_profile_use_case import UpdateProfileUseCase
from .delete_profile_use_case import DeleteProfileUseCase
from .get_profiles_use_case import GetProfilesUseCase
from .switch_profile_use_case import SwitchProfileUseCase

__all__ = [
    "GetDevicesUseCase",
    "CreateProfileUseCase",
    "UpdateProfileUseCase",
    "DeleteProfileUseCase",
    "GetProfilesUseCase",
    "SwitchProfileUseCase",
]
'''

FILES[
    "src/application/use_cases/get_devices_use_case.py"
] = '''"""Use case for retrieving audio devices."""

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

    def get_default_device(self, device_type: DeviceType) -> Optional[DeviceDTO]:
        """Get the default device for a specific type.

        Args:
            device_type: Type of device to get default for

        Returns:
            Default device DTO or None if not found
        """
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
'''

FILES[
    "src/application/use_cases/create_profile_use_case.py"
] = '''"""Use case for creating audio profiles."""

from typing import Optional
from uuid import uuid4

from src.domain.entities.audio_profile import AudioProfile
from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.exceptions.domain_exceptions import ProfileStorageException
from src.application.dtos.profile_dto import ProfileDTO


class CreateProfileUseCase:
    """Use case for creating new audio profiles."""

    def __init__(self, profile_repository: IProfileRepository) -> None:
        """Initialize use case with profile repository.

        Args:
            profile_repository: Repository for profile persistence
        """
        self._profile_repository = profile_repository

    def execute(
        self,
        name: str,
        output_device_id: Optional[str] = None,
        input_device_id: Optional[str] = None,
    ) -> ProfileDTO:
        """Create a new audio profile.

        Args:
            name: Profile name
            output_device_id: Optional output device ID
            input_device_id: Optional input device ID

        Returns:
            Created profile DTO

        Raises:
            ProfileStorageException: If profile with same name exists or save fails
        """
        # Check if profile with same name already exists
        existing = self._profile_repository.get_by_name(name)
        if existing is not None:
            raise ProfileStorageException(f"Profile with name '{name}' already exists")

        # Create new profile entity
        profile = AudioProfile(
            id=uuid4(),
            name=name,
            output_device_id=output_device_id,
            input_device_id=input_device_id,
        )

        # Save profile
        self._profile_repository.save(profile)

        # Convert to DTO and return
        return ProfileDTO(
            id=profile.id,
            name=profile.name,
            output_device_id=profile.output_device_id,
            input_device_id=profile.input_device_id,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
'''

FILES[
    "src/application/use_cases/update_profile_use_case.py"
] = '''"""Use case for updating audio profiles."""

from typing import Optional
from uuid import UUID

from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.exceptions.domain_exceptions import (
    ProfileNotFoundException,
    ProfileStorageException,
)
from src.application.dtos.profile_dto import ProfileDTO


class UpdateProfileUseCase:
    """Use case for updating existing audio profiles."""

    def __init__(self, profile_repository: IProfileRepository) -> None:
        """Initialize use case with profile repository.

        Args:
            profile_repository: Repository for profile persistence
        """
        self._profile_repository = profile_repository

    def execute(
        self,
        profile_id: UUID,
        name: Optional[str] = None,
        output_device_id: Optional[str] = None,
        input_device_id: Optional[str] = None,
    ) -> ProfileDTO:
        """Update an existing audio profile.

        Args:
            profile_id: ID of profile to update
            name: Optional new name
            output_device_id: Optional new output device ID
            input_device_id: Optional new input device ID

        Returns:
            Updated profile DTO

        Raises:
            ProfileNotFoundException: If profile doesn't exist
            ProfileStorageException: If name conflicts with another profile
        """
        # Get existing profile
        profile = self._profile_repository.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundException(f"Profile with ID {profile_id} not found")

        # Check for name conflicts if name is being changed
        if name is not None and name != profile.name:
            existing = self._profile_repository.get_by_name(name)
            if existing is not None and existing.id != profile_id:
                raise ProfileStorageException(
                    f"Profile with name '{name}' already exists"
                )

        # Update profile
        profile.update(
            name=name,
            output_device_id=output_device_id,
            input_device_id=input_device_id,
        )

        # Save updated profile
        self._profile_repository.save(profile)

        # Convert to DTO and return
        return ProfileDTO(
            id=profile.id,
            name=profile.name,
            output_device_id=profile.output_device_id,
            input_device_id=profile.input_device_id,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
'''

FILES[
    "src/application/use_cases/delete_profile_use_case.py"
] = '''"""Use case for deleting audio profiles."""

from uuid import UUID

from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.exceptions.domain_exceptions import ProfileNotFoundException


class DeleteProfileUseCase:
    """Use case for deleting audio profiles."""

    def __init__(self, profile_repository: IProfileRepository) -> None:
        """Initialize use case with profile repository.

        Args:
            profile_repository: Repository for profile persistence
        """
        self._profile_repository = profile_repository

    def execute(self, profile_id: UUID) -> None:
        """Delete an audio profile.

        Args:
            profile_id: ID of profile to delete

        Raises:
            ProfileNotFoundException: If profile doesn't exist
        """
        # Check if profile exists
        if not self._profile_repository.exists(profile_id):
            raise ProfileNotFoundException(f"Profile with ID {profile_id} not found")

        # Delete profile
        self._profile_repository.delete(profile_id)
'''

FILES[
    "src/application/use_cases/get_profiles_use_case.py"
] = '''"""Use case for retrieving audio profiles."""

from typing import List, Optional
from uuid import UUID

from src.domain.interfaces.profile_repository import IProfileRepository
from src.domain.exceptions.domain_exceptions import ProfileNotFoundException
from src.application.dtos.profile_dto import ProfileDTO


class GetProfilesUseCase:
    """Use case for retrieving audio profiles."""

    def __init__(self, profile_repository: IProfileRepository) -> None:
        """Initialize use case with profile repository.

        Args:
            profile_repository: Repository for profile persistence
        """
        self._profile_repository = profile_repository

    def execute(self) -> List[ProfileDTO]:
        """Get all audio profiles.

        Returns:
            List of profile DTOs
        """
        profiles = self._profile_repository.get_all()

        # Convert domain entities to DTOs
        return [
            ProfileDTO(
                id=profile.id,
                name=profile.name,
                output_device_id=profile.output_device_id,
                input_device_id=profile.input_device_id,
                created_at=profile.created_at,
                updated_at=profile.updated_at,
            )
            for profile in profiles
        ]

    def get_by_id(self, profile_id: UUID) -> ProfileDTO:
        """Get a specific profile by ID.

        Args:
            profile_id: ID of profile to retrieve

        Returns:
            Profile DTO

        Raises:
            ProfileNotFoundException: If profile doesn't exist
        """
        profile = self._profile_repository.get_by_id(profile_id)
        if profile is None:
            raise ProfileNotFoundException(f"Profile with ID {profile_id} not found")

        return ProfileDTO(
            id=profile.id,
            name=profile.name,
            output_device_id=profile.output_device_id,
            input_device_id=profile.input_device_id,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def get_by_name(self, name: str) -> Optional[ProfileDTO]:
        """Get a specific profile by name.

        Args:
            name: Name of profile to retrieve

        Returns:
            Profile DTO or None if not found
        """
        profile = self._profile_repository.get_by_name(name)
        if profile is None:
            return None

        return ProfileDTO(
            id=profile.id,
            name=profile.name,
            output_device_id=profile.output_device_id,
            input_device_id=profile.input_device_id,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
'''

FILES[
    "src/application/use_cases/switch_profile_use_case.py"
] = '''"""Use case for switching audio profiles."""

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

        # Refresh device list after changes
        self._device_controller.refresh_devices()
'''

print("Creating application layer files...")
for file_path, content in FILES.items():
    full_path = BASE_DIR / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    print(f"Created: {file_path}")

print("\nApplication layer files created successfully!")
