"""Tests for the Windows role loop, free of COM so they run everywhere (A-2)."""

import pytest

from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    PartialDeviceControlException,
)
from src.infrastructure.windows.endpoint_roles import (
    ROLE_NAMES,
    require_every_role,
    set_every_role,
)

CONSOLE, MULTIMEDIA, COMMUNICATIONS = ROLE_NAMES


class FakePolicyConfig:
    """Refuses the roles it is told to; records the calls it accepts."""

    def __init__(self, refused_roles=()) -> None:
        self.refused = set(refused_roles)
        self.calls = []

    def SetDefaultEndpoint(self, device_id, role):  # noqa: N802
        if role in self.refused:
            raise OSError("E_FAIL")
        self.calls.append((device_id, role))


def test_every_role_is_asked_for_in_order():
    policy = FakePolicyConfig()
    assert set_every_role(policy, "{dev}") == (CONSOLE, MULTIMEDIA, COMMUNICATIONS)
    assert policy.calls == [
        ("{dev}", CONSOLE),
        ("{dev}", MULTIMEDIA),
        ("{dev}", COMMUNICATIONS),
    ]


def test_a_refused_role_does_not_stop_the_others():
    policy = FakePolicyConfig(refused_roles={CONSOLE})
    assert set_every_role(policy, "{dev}") == (MULTIMEDIA, COMMUNICATIONS)


def test_every_role_landing_is_success():
    require_every_role((CONSOLE, MULTIMEDIA, COMMUNICATIONS))


def test_a_missing_role_is_named():
    with pytest.raises(PartialDeviceControlException) as failure:
        require_every_role((CONSOLE, MULTIMEDIA))
    assert failure.value.missing_roles == ("Communications",)


def test_no_role_landing_is_a_plain_refusal():
    with pytest.raises(DeviceControlException) as failure:
        require_every_role(())
    assert not isinstance(failure.value, PartialDeviceControlException)
