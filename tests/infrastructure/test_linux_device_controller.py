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


class FakePwMetadataApi:
    """Hand-written fake of the pw-metadata command seam."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple] = []

    def set_property(self, key, value):
        self.calls.append((key, value))
        if self.fail:
            raise OSError("pw-metadata is not installed")


def make_controller(pactl_fails: bool = False, metadata_fails: bool = False):
    """Build a controller over both fakes and return it with them."""
    pactl = FakePactlApi(fail=pactl_fails)
    metadata = FakePwMetadataApi(fail=metadata_fails)
    return LinuxDeviceController(pactl, metadata), pactl, metadata


def test_an_output_device_becomes_the_default_sink():
    controller, pactl, metadata = make_controller()
    controller.set_default_device("sink-name", DeviceType.OUTPUT)
    assert pactl.calls == [("set-default-sink", "sink-name")]
    assert metadata.calls == []


def test_an_input_device_becomes_the_default_source():
    controller, pactl, metadata = make_controller()
    controller.set_default_device("source-name", DeviceType.INPUT)
    assert pactl.calls == [("set-default-source", "source-name")]
    assert metadata.calls == []


def test_a_refused_pactl_falls_back_to_the_pipewire_output_metadata():
    controller, _, metadata = make_controller(pactl_fails=True)
    controller.set_default_device("sink-name", DeviceType.OUTPUT)
    assert metadata.calls == [
        ("default.configured.audio.sink", '{"name": "sink-name"}')
    ]


def test_a_refused_pactl_falls_back_to_the_pipewire_input_metadata():
    controller, _, metadata = make_controller(pactl_fails=True)
    controller.set_default_device("source-name", DeviceType.INPUT)
    assert metadata.calls == [
        ("default.configured.audio.source", '{"name": "source-name"}')
    ]


def test_both_routes_failing_raises_a_device_control_exception():
    controller, _, _ = make_controller(pactl_fails=True, metadata_fails=True)
    with pytest.raises(DeviceControlException) as failure:
        controller.set_default_device("sink-name", DeviceType.OUTPUT)
    # The pactl error is the one worth showing: a PulseAudio-only machine has
    # no pw-metadata at all.
    assert "pactl failed" in str(failure.value)


def test_refresh_devices_is_a_no_op():
    controller, pactl, metadata = make_controller()
    controller.refresh_devices()
    assert pactl.calls == []
    assert metadata.calls == []
