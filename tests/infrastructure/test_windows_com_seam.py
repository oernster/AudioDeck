"""The Windows controller and enumerator over a faked COM seam (A-2, A-8).

Nothing here creates a real COM object: CoCreateInstance and pycaw's
AudioUtilities are replaced with hand-written fakes, so no default device is
changed and no endpoint is opened. The modules import comtypes and pycaw,
which exist on Windows only.
"""

import sys

import pytest

import src.domain.exceptions.domain_exceptions as errors
from src.domain.value_objects.device_type import DeviceType

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="COM is Windows")

# Core Audio's ERole numbering: eConsole, eMultimedia, eCommunications.
CONSOLE, MULTIMEDIA, COMMUNICATIONS = 0, 1, 2


class FakePolicyConfig:
    """Stand-in for IPolicyConfig, refusing the roles it is told to."""

    def __init__(self, refused_roles) -> None:
        self.refused = set(refused_roles)
        self.landed = []

    def SetDefaultEndpoint(self, device_id, role):
        if role in self.refused:
            raise OSError(f"E_FAIL for role {role}")
        self.landed.append(role)


def controller_over(monkeypatch, policy):
    import comtypes

    from src.infrastructure.windows.windows_device_controller import (
        WindowsDeviceController,
    )

    monkeypatch.setattr(comtypes, "CoCreateInstance", lambda *_args: policy)
    return WindowsDeviceController()


def test_every_role_landing_is_full_success(monkeypatch):
    policy = FakePolicyConfig(refused_roles=())
    controller_over(monkeypatch, policy).set_default_device("{dev}", DeviceType.OUTPUT)
    assert policy.landed == [CONSOLE, MULTIMEDIA, COMMUNICATIONS]


def test_a_refused_communications_role_is_reported_by_name(monkeypatch):
    policy = FakePolicyConfig(refused_roles={COMMUNICATIONS})
    controller = controller_over(monkeypatch, policy)

    with pytest.raises(errors.DeviceControlException) as failure:
        controller.set_default_device("{dev}", DeviceType.OUTPUT)

    assert isinstance(failure.value, errors.PartialDeviceControlException)
    assert failure.value.missing_roles == ("Communications",)


def test_two_refused_roles_are_both_named(monkeypatch):
    policy = FakePolicyConfig(refused_roles={CONSOLE, COMMUNICATIONS})
    controller = controller_over(monkeypatch, policy)

    with pytest.raises(errors.DeviceControlException) as failure:
        controller.set_default_device("{dev}", DeviceType.OUTPUT)

    assert failure.value.missing_roles == ("Console", "Communications")


def test_every_role_refused_is_a_plain_refusal(monkeypatch):
    policy = FakePolicyConfig(refused_roles={CONSOLE, MULTIMEDIA, COMMUNICATIONS})
    controller = controller_over(monkeypatch, policy)

    with pytest.raises(errors.DeviceControlException) as failure:
        controller.set_default_device("{dev}", DeviceType.OUTPUT)

    assert not isinstance(failure.value, errors.PartialDeviceControlException)


class _EndpointServiceDown:
    """pycaw's AudioUtilities when the audio service cannot be reached."""

    @staticmethod
    def GetDeviceEnumerator():
        raise OSError("RPC_E_DISCONNECTED")

    @staticmethod
    def GetAllDevices():
        raise OSError("RPC_E_DISCONNECTED")


def test_an_enumeration_that_reads_nothing_raises(monkeypatch):
    from src.infrastructure.windows import device_enumerator as module

    monkeypatch.setattr(module, "AudioUtilities", _EndpointServiceDown)

    with pytest.raises(errors.AudioDeckException, match="Could not read"):
        module.WindowsDeviceEnumerator().get_all_devices()
