"""The Windows default-endpoint roles and the loop that sets each of them.

Windows keeps a separate default device per role, so one switch is three
calls, any of which can be refused on its own. This module holds that loop
and its verdict, free of COM, so it is measured by the coverage gate while
the controller that creates the real COM object stays out of it.
"""

from __future__ import annotations

from typing import Protocol, Tuple

from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    PartialDeviceControlException,
)

# Core Audio's ERole values (eConsole, eMultimedia, eCommunications) with the
# names a user is shown when one of them is refused.
ROLE_NAMES = {
    0: "Console",
    1: "Multimedia",
    2: "Communications",
}


class EndpointPolicy(Protocol):
    """The one IPolicyConfig method the role loop needs."""

    def SetDefaultEndpoint(self, device_id: str, role: int) -> object:  # noqa: N802
        """Make the device the default for one role, raising if refused."""
        ...


def set_every_role(policy: EndpointPolicy, device_id: str) -> Tuple[int, ...]:
    """Ask for the device as the default in every role, one at a time.

    A refused role does not stop the others: a device that lands for some
    roles is still the better outcome; the caller is told exactly which.

    Args:
        policy: The policy-config object
        device_id: Endpoint ID of the device

    Returns:
        The roles that took the device, in role order
    """
    landed = []
    for role in ROLE_NAMES:
        try:
            policy.SetDefaultEndpoint(device_id, role)
        except Exception:
            continue
        landed.append(role)
    return tuple(landed)


def require_every_role(landed: Tuple[int, ...]) -> None:
    """Turn the roles that landed into success, a partial result or a refusal.

    Args:
        landed: The roles that took the device

    Raises:
        DeviceControlException: If no role took the device
        PartialDeviceControlException: If some roles kept the old device
    """
    if not landed:
        raise DeviceControlException("Failed to set device as default for any role")
    missing = tuple(name for role, name in ROLE_NAMES.items() if role not in landed)
    if missing:
        raise PartialDeviceControlException(missing)
