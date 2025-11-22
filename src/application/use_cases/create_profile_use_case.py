"""Use case for creating audio profiles."""

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
