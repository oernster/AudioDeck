"""Audio device entity."""

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
