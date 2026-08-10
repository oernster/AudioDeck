"""Tests for the pactl-backed Linux device controller."""

import subprocess

import pytest

from src.domain.exceptions.domain_exceptions import DeviceControlException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.linux_device_controller import LinuxDeviceController


class FakePactlApi:
    """Hand-written fake of the pactl command seam."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple] = []

    def run(self, *args):
        self.calls.append(args)
        if self.fail:
            raise subprocess.SubprocessError("pactl failed")
        return ""


def test_an_output_device_becomes_the_default_sink():
    api = FakePactlApi()
    LinuxDeviceController(api).set_default_device("sink-name", DeviceType.OUTPUT)
    assert api.calls == [("set-default-sink", "sink-name")]


def test_an_input_device_becomes_the_default_source():
    api = FakePactlApi()
    LinuxDeviceController(api).set_default_device("source-name", DeviceType.INPUT)
    assert api.calls == [("set-default-source", "source-name")]


def test_a_pactl_failure_raises_a_device_control_exception():
    controller = LinuxDeviceController(FakePactlApi(fail=True))
    with pytest.raises(DeviceControlException):
        controller.set_default_device("sink-name", DeviceType.OUTPUT)


def test_refresh_devices_is_a_no_op():
    api = FakePactlApi()
    LinuxDeviceController(api).refresh_devices()
    assert api.calls == []
