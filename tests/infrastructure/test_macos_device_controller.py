"""Tests for the CoreAudio-backed macOS device controller."""

from typing import List, Optional

import pytest

from src.domain.exceptions.domain_exceptions import DeviceControlException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.macos.macos_device_controller import MacosDeviceController

_SPEAKERS = 10
_MICROPHONE = 20


class FakeCoreAudioApi:
    """Hand-written fake of the CoreAudio seam."""

    def __init__(self, set_succeeds: bool = True) -> None:
        self.uids = {_SPEAKERS: "uid-speakers", _MICROPHONE: "uid-microphone"}
        self.set_succeeds = set_succeeds
        self.set_calls: List[tuple] = []

    def all_device_ids(self) -> List[int]:
        return list(self.uids)

    def device_uid(self, device_id: int) -> Optional[str]:
        return self.uids.get(device_id)

    def device_name(self, device_id: int) -> Optional[str]:
        return None

    def has_output_streams(self, device_id: int) -> bool:
        return True

    def has_input_streams(self, device_id: int) -> bool:
        return True

    def default_device_id(self, input_device: bool) -> Optional[int]:
        return None

    def set_default_device(self, device_id: int, input_device: bool) -> bool:
        self.set_calls.append((device_id, input_device))
        return self.set_succeeds


def test_an_output_uid_resolves_and_becomes_the_default_output():
    api = FakeCoreAudioApi()
    MacosDeviceController(api).set_default_device("uid-speakers", DeviceType.OUTPUT)
    assert api.set_calls == [(_SPEAKERS, False)]


def test_an_input_uid_resolves_and_becomes_the_default_input():
    api = FakeCoreAudioApi()
    MacosDeviceController(api).set_default_device("uid-microphone", DeviceType.INPUT)
    assert api.set_calls == [(_MICROPHONE, True)]


def test_an_absent_device_raises_a_device_control_exception():
    controller = MacosDeviceController(FakeCoreAudioApi())
    with pytest.raises(DeviceControlException):
        controller.set_default_device("uid-gone", DeviceType.OUTPUT)


def test_a_refused_set_raises_a_device_control_exception():
    controller = MacosDeviceController(FakeCoreAudioApi(set_succeeds=False))
    with pytest.raises(DeviceControlException):
        controller.set_default_device("uid-speakers", DeviceType.OUTPUT)


def test_refresh_devices_is_a_no_op():
    api = FakeCoreAudioApi()
    MacosDeviceController(api).refresh_devices()
    assert api.set_calls == []
