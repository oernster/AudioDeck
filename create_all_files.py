"""Script to create all Audio Deck source files."""

import os
from pathlib import Path

# Get the script directory
BASE_DIR = Path(__file__).parent

# Define all files and their content
FILES = {
    # Domain layer - Value Objects
    "src/domain/__init__.py": '"""Domain layer - Business logic and entities."""\n',
    "src/domain/value_objects/__init__.py": '''"""Value objects."""

from .device_type import DeviceType

__all__ = ["DeviceType"]
''',
    "src/domain/value_objects/device_type.py": '''"""Device type value object."""

from enum import Enum


class DeviceType(Enum):
    """Audio device type enumeration."""

    INPUT = "input"
    OUTPUT = "output"

    @property
    def display_name(self) -> str:
        """Get display name for UI.

        Returns:
            Human-readable device type name
        """
        return self.value.capitalize()
''',
    # Domain layer - Entities
    "src/domain/entities/__init__.py": '''"""Domain entities."""

from .audio_device import AudioDevice
from .audio_profile import AudioProfile

__all__ = ["AudioDevice", "AudioProfile"]
''',
    "src/domain/entities/audio_device.py": '''"""Audio device entity."""

from dataclasses import dataclass

from src.domain.value_objects.device_type import DeviceType


@dataclass(frozen=True)
class AudioDevice:
    """Represents an audio device in the system."""

    id: str
    name: str
    device_type: DeviceType
    is_default: bool
    is_enabled: bool

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.id:
            raise ValueError("Device ID cannot be empty")
        if not self.name:
            raise ValueError("Device name cannot be empty")

    def with_default(self, is_default: bool) -> "AudioDevice":
        """Create a new instance with updated default status.

        Args:
            is_default: New default status

        Returns:
            New AudioDevice instance with updated status
        """
        return AudioDevice(
            id=self.id,
            name=self.name,
            device_type=self.device_type,
            is_default=is_default,
            is_enabled=self.is_enabled,
        )

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI.

        Returns:
            Formatted device name with status indicators
        """
        status_parts = []
        if self.is_default:
            status_parts.append("Default")
        if not self.is_enabled:
            status_parts.append("Disabled")

        if status_parts:
            return f"{self.name} ({', '.join(status_parts)})"
        return self.name
''',
    "src/domain/entities/audio_profile.py": '''"""Audio profile entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class AudioProfile:
    """Represents an audio profile configuration."""

    id: UUID
    name: str
    output_device_id: Optional[str] = None
    input_device_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Validate entity after initialization."""
        if not self.name:
            raise ValueError("Profile name cannot be empty")

    def update(
        self,
        name: Optional[str] = None,
        output_device_id: Optional[str] = None,
        input_device_id: Optional[str] = None,
    ) -> None:
        """Update profile fields.

        Args:
            name: Optional new name
            output_device_id: Optional new output device ID
            input_device_id: Optional new input device ID
        """
        if name is not None:
            if not name:
                raise ValueError("Profile name cannot be empty")
            self.name = name

        if output_device_id is not None:
            self.output_device_id = output_device_id

        if input_device_id is not None:
            self.input_device_id = input_device_id

        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert profile to dictionary for serialization.

        Returns:
            Dictionary representation of profile
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "output_device_id": self.output_device_id,
            "input_device_id": self.input_device_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AudioProfile":
        """Create profile from dictionary.

        Args:
            data: Dictionary containing profile data

        Returns:
            AudioProfile instance
        """
        from uuid import UUID

        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            output_device_id=data.get("output_device_id"),
            input_device_id=data.get("input_device_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )
''',
    # Domain layer - Interfaces
    "src/domain/interfaces/__init__.py": '''"""Domain interfaces (Protocols)."""

from .device_repository import IDeviceRepository
from .device_controller import IDeviceController
from .profile_repository import IProfileRepository

__all__ = ["IDeviceRepository", "IDeviceController", "IProfileRepository"]
''',
    "src/domain/interfaces/device_repository.py": '''"""Device repository interface."""

from typing import List, Optional, Protocol

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_type import DeviceType


class IDeviceRepository(Protocol):
    """Interface for device data access."""

    def get_all_devices(self) -> List[AudioDevice]:
        """Get all audio devices.

        Returns:
            List of all audio devices
        """
        ...

    def get_devices_by_type(self, device_type: DeviceType) -> List[AudioDevice]:
        """Get devices filtered by type.

        Args:
            device_type: Type of devices to retrieve

        Returns:
            List of devices of specified type
        """
        ...

    def get_default_device(self, device_type: DeviceType) -> Optional[AudioDevice]:
        """Get the default device for a specific type.

        Args:
            device_type: Type of device

        Returns:
            Default device or None if not found
        """
        ...

    def get_device_by_id(self, device_id: str) -> Optional[AudioDevice]:
        """Get a specific device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device or None if not found
        """
        ...

    def refresh(self) -> None:
        """Refresh the device list from the system."""
        ...
''',
    "src/domain/interfaces/device_controller.py": '''"""Device controller interface."""

from typing import Protocol

from src.domain.value_objects.device_type import DeviceType


class IDeviceController(Protocol):
    """Interface for device control operations."""

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        """Set a device as the default for its type.

        Args:
            device_id: ID of device to set as default
            device_type: Type of device

        Raises:
            DeviceControlException: If setting default fails
        """
        ...

    def refresh_devices(self) -> None:
        """Refresh device list after changes."""
        ...
''',
    "src/domain/interfaces/profile_repository.py": '''"""Profile repository interface."""

from typing import List, Optional, Protocol
from uuid import UUID

from src.domain.entities.audio_profile import AudioProfile


class IProfileRepository(Protocol):
    """Interface for profile persistence."""

    def save(self, profile: AudioProfile) -> None:
        """Save a profile.

        Args:
            profile: Profile to save

        Raises:
            ProfileStorageException: If save fails
        """
        ...

    def get_by_id(self, profile_id: UUID) -> Optional[AudioProfile]:
        """Get a profile by ID.

        Args:
            profile_id: Profile ID

        Returns:
            Profile or None if not found
        """
        ...

    def get_all(self) -> List[AudioProfile]:
        """Get all profiles.

        Returns:
            List of all profiles
        """
        ...

    def delete(self, profile_id: UUID) -> None:
        """Delete a profile.

        Args:
            profile_id: Profile ID to delete

        Raises:
            ProfileStorageException: If delete fails
        """
        ...

    def exists(self, profile_id: UUID) -> bool:
        """Check if a profile exists.

        Args:
            profile_id: Profile ID

        Returns:
            True if profile exists
        """
        ...

    def get_by_name(self, name: str) -> Optional[AudioProfile]:
        """Get a profile by name.

        Args:
            name: Profile name

        Returns:
            Profile or None if not found
        """
        ...
''',
    # Domain layer - Exceptions
    "src/domain/exceptions/__init__.py": '''"""Domain exceptions."""

from .domain_exceptions import (
    AudioDeckException,
    DeviceNotFoundException,
    DeviceControlException,
    ProfileNotFoundException,
    ProfileStorageException,
)

__all__ = [
    "AudioDeckException",
    "DeviceNotFoundException",
    "DeviceControlException",
    "ProfileNotFoundException",
    "ProfileStorageException",
]
''',
    "src/domain/exceptions/domain_exceptions.py": '''"""Domain layer exceptions."""


class AudioDeckException(Exception):
    """Base exception for Audio Deck application."""

    pass


class DeviceNotFoundException(AudioDeckException):
    """Raised when a device is not found."""

    pass


class DeviceControlException(AudioDeckException):
    """Raised when device control operation fails."""

    pass


class ProfileNotFoundException(AudioDeckException):
    """Raised when a profile is not found."""

    pass


class ProfileStorageException(AudioDeckException):
    """Raised when profile storage operation fails."""

    pass
''',
}


def create_files():
    """Create all files."""
    for file_path, content in FILES.items():
        full_path = BASE_DIR / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        print(f"Created: {file_path}")


if __name__ == "__main__":
    create_files()
    print("\nDomain layer files created successfully!")
