"""Use case for retrieving audio profiles."""

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
