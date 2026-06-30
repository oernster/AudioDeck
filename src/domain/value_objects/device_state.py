"""Device availability state value object."""

from enum import Enum


class DeviceState(Enum):
    """Availability of an audio endpoint as reported by Windows."""

    AVAILABLE = "available"
    DISCONNECTED = "disconnected"
    DISABLED = "disabled"
    NOT_PRESENT = "not_present"

    @property
    def is_available(self) -> bool:
        """Return True only when the device can be used right now."""
        return self is DeviceState.AVAILABLE

    @property
    def label(self) -> str:
        """Return a human-readable label for the state."""
        return {
            DeviceState.AVAILABLE: "Available",
            DeviceState.DISCONNECTED: "Disconnected",
            DeviceState.DISABLED: "Disabled",
            DeviceState.NOT_PRESENT: "Not present",
        }[self]
