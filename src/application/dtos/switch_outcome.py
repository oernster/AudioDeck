"""Result of a profile switch (supports partial application)."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.domain.value_objects.device_type import DeviceType


class SkipReason(Enum):
    """Why a device in a profile was not applied during a switch."""

    UNAVAILABLE = "unavailable"
    WRONG_TYPE = "wrong_type"
    CONTROL_FAILED = "control_failed"

    @property
    def label(self) -> str:
        """Human-readable reason."""
        return {
            SkipReason.UNAVAILABLE: "not available",
            SkipReason.WRONG_TYPE: "wrong device type",
            SkipReason.CONTROL_FAILED: "could not be set",
        }[self]


@dataclass(frozen=True)
class SkippedDevice:
    """A device that was not applied, with the reason."""

    device_type: DeviceType
    device_id: str
    reason: SkipReason


@dataclass(frozen=True)
class SwitchOutcome:
    """Which devices were applied and which were skipped during a switch."""

    applied: Tuple[DeviceType, ...]
    skipped: Tuple[SkippedDevice, ...]

    @property
    def fully_applied(self) -> bool:
        """True when nothing was skipped."""
        return not self.skipped

    @property
    def anything_applied(self) -> bool:
        """True when at least one device was applied."""
        return bool(self.applied)
