"""Use case for deleting audio profiles."""

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
