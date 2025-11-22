"""Use case for updating audio profiles."""

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
