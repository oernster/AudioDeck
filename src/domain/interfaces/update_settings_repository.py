"""Update settings repository interface."""

from typing import Optional, Protocol


class IUpdateSettingsRepository(Protocol):
    """Interface for persisting the update check's user choices."""

    def get_skipped_version(self) -> Optional[str]:
        """Get the release tag the user chose to skip.

        Returns:
            The exact tag string, or None when nothing is skipped
        """
        ...

    def set_skipped_version(self, version: str) -> None:
        """Persist the release tag the user chose to skip.

        Args:
            version: The exact tag string the prompt offered
        """
        ...
