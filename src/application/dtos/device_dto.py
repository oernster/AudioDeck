"""Device Data Transfer Object."""

from dataclasses import dataclass

from src.domain.value_objects.device_type import DeviceType
from src.domain.value_objects.device_state import DeviceState


@dataclass(frozen=True)
class DeviceDTO:
    """DTO for transferring device data between layers."""

    id: str
    name: str
    device_type: DeviceType
    is_default: bool
    state: DeviceState

    @property
    def is_available(self) -> bool:
        """Whether the device can be used right now."""
        return self.state.is_available

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        status_parts = []
        if self.is_default:
            status_parts.append("Default")
        if not self.state.is_available:
            status_parts.append(self.state.label)

        if status_parts:
            return f"{self.name} ({', '.join(status_parts)})"
        return self.name

    @property
    def type_display(self) -> str:
        """Get device type display name."""
        return self.device_type.display_name
