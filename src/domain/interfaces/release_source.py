"""Release source interface."""

from typing import Optional, Protocol

from src.domain.value_objects.release_info import ReleaseInfo


class IReleaseSource(Protocol):
    """Interface for reading the latest published release."""

    def latest_release(self) -> Optional[ReleaseInfo]:
        """Get the latest published release.

        Returns:
            The release, or None when it cannot be read for any reason
        """
        ...
