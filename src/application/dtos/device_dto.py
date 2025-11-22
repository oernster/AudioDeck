"""Device Data Transfer Object."""

from dataclasses import dataclass

from src.domain.value_objects.device_type import DeviceType


@dataclass(frozen=True)
class DeviceDTO:
    """DTO for transferring device data between layers."""

    id: str
    name: str
    device_type: DeviceType
    is_default: bool
    is_enabled: bool

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        status_parts = []
        if self.is_default:
            status_parts.append("Default")
        if not self.is_enabled:
            status_parts.append("Disabled")

        if status_parts:
            return f"{self.name} ({', '.join(status_parts)})"
        return self.name

    @property
    def type_display(self) -> str:
        """Get device type display name."""
        return self.device_type.display_name
