"""The window's wording for a switch that did not fully apply.

One sentence per reason, each naming the devices it concerns, so the user
learns what actually happened rather than a single catch-all.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from src.application.dtos.switch_outcome import (
    SkippedDevice,
    SkipReason,
    SwitchOutcome,
)


def _names(skipped: List[SkippedDevice]) -> str:
    return ", ".join(skip.device_type.display_name for skip in skipped)


def _partly_set(skipped: List[SkippedDevice]) -> str:
    return "; ".join(
        f"the {skip.device_type.display_name} device was not made the default "
        f"for {skip.detail}"
        for skip in skipped
    )


# Identity is the device's id alone, so a device the system brings back under
# a new id (another USB port, a re-paired headset) is never matched: the
# waiting notice says so rather than promise an apply that cannot happen.
_PHRASES: Dict[SkipReason, Callable[[List[SkippedDevice]], str]] = {
    SkipReason.UNAVAILABLE: lambda skipped: (
        f"the {_names(skipped)} device is not available right now; it will "
        "apply when it reconnects, as long as the system still knows it as "
        "the same device"
    ),
    SkipReason.CONTROL_FAILED: lambda skipped: (
        f"the system refused to set the {_names(skipped)} device"
    ),
    SkipReason.WRONG_TYPE: lambda skipped: (
        f"the {_names(skipped)} device in this profile is not that kind of "
        "device; edit the profile in the Configuration tab"
    ),
    SkipReason.PARTIALLY_SET: _partly_set,
    SkipReason.DID_NOT_TAKE: lambda skipped: (
        f"the system accepted the {_names(skipped)} device but kept the old default"
    ),
}


def skip_message(profile_name: str, outcome: SwitchOutcome) -> str:
    """Build a friendly notice naming each skipped device's real reason.

    Args:
        profile_name: The profile that was switched to
        outcome: The switch's outcome, with at least one skipped device

    Returns:
        One sentence for the notice
    """
    problems = []
    for reason, phrase in _PHRASES.items():
        skipped = [skip for skip in outcome.skipped if skip.reason is reason]
        if skipped:
            problems.append(phrase(skipped))
    detail = "; ".join(problems)
    if outcome.anything_applied:
        return f"Switched '{profile_name}'; {detail}."
    return f"Could not switch '{profile_name}': {detail}."
