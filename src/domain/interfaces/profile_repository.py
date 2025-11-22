"""Profile repository interface."""

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
