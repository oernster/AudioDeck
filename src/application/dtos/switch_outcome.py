"""Result of a profile switch (supports partial application)."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from src.domain.value_objects.device_type import DeviceType


class SkipReason(Enum):
    """Why a device in a profile was not fully applied during a switch."""

    UNAVAILABLE = "unavailable"
    WRONG_TYPE = "wrong_type"
    CONTROL_FAILED = "control_failed"
    # The device became the default for some roles only (Windows keeps one
    # default per role). The slot also counts as applied.
    PARTIALLY_SET = "partially_set"
    # The system accepted the call but the default read back afterwards is
    # still another device.
    DID_NOT_TAKE = "did_not_take"

    @property
    def label(self) -> str:
        """Human-readable reason."""
        return {
            SkipReason.UNAVAILABLE: "not available",
            SkipReason.WRONG_TYPE: "wrong device type",
            SkipReason.CONTROL_FAILED: "could not be set",
            SkipReason.PARTIALLY_SET: "not set for every role",
            SkipReason.DID_NOT_TAKE: "accepted; the old default stayed",
        }[self]


@dataclass(frozen=True)
class SkippedDevice:
    """A device that was not (fully) applied, with the reason.

    detail carries what the reason alone cannot say: for PARTIALLY_SET, the
    roles that kept the old device.
    """

    device_type: DeviceType
    device_id: str
    reason: SkipReason
    detail: str = ""

    @property
    def description(self) -> str:
        """The reason, followed by its detail when there is one."""
        if self.detail:
            return f"{self.reason.label}: missing {self.detail}"
        return self.reason.label


@dataclass(frozen=True)
class SwitchOutcome:
    """Which devices were applied and which were skipped during a switch.

    A device set for only some roles appears in both: it is applied; the
    roles it missed are reported as a PARTIALLY_SET entry in skipped.
    """

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
