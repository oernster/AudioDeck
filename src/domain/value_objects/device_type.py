"""Device type value object."""

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
