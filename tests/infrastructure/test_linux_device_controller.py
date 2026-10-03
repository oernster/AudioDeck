"""Tests for the pactl-backed Linux device controller."""

import subprocess

import pytest

from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    DeviceEnumerationException,
    DeviceNotFoundException,
)
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.linux_device_controller import LinuxDeviceController
from tests.conftest import make_device


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


class FakeDeviceList:
    """Hand-written fake of the enumerator the controller checks against."""

    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.devices = [
            make_device("sink-name", "Speakers", DeviceType.OUTPUT),
            make_device("source-name", "Microphone", DeviceType.INPUT),
        ]

    def get_all_devices(self):
        if self.error is not None:
            raise self.error
        return list(self.devices)


def make_controller(
    pactl_fails: bool = False,
    metadata_fails: bool = False,
    device_list: FakeDeviceList | None = None,
):
    """Build a controller over the fakes and return it with them."""
    pactl = FakePactlApi(fail=pactl_fails)
    metadata = FakePwMetadataApi(fail=metadata_fails)
    devices = device_list or FakeDeviceList()
    return LinuxDeviceController(pactl, metadata, devices), pactl, metadata


def test_a_missing_sink_is_never_written_into_the_metadata():
    # pw-metadata accepts any name, so writing one with no node behind it
    # would report a switch that changed nothing (audit A-3).
    controller, _, metadata = make_controller(pactl_fails=True)
    with pytest.raises(DeviceNotFoundException, match="alsa_output.gone"):
        controller.set_default_device("alsa_output.gone", DeviceType.OUTPUT)
    assert metadata.calls == []


def test_a_name_listed_for_the_other_flow_does_not_count():
    controller, _, metadata = make_controller(pactl_fails=True)
    with pytest.raises(DeviceNotFoundException):
        controller.set_default_device("source-name", DeviceType.OUTPUT)
    assert metadata.calls == []


def test_devices_that_cannot_be_read_refuse_the_metadata_write():
    unreadable = FakeDeviceList(error=DeviceEnumerationException("no pactl"))
    controller, _, metadata = make_controller(pactl_fails=True, device_list=unreadable)
    with pytest.raises(DeviceControlException, match="pactl failed"):
        controller.set_default_device("sink-name", DeviceType.OUTPUT)
    assert metadata.calls == []


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
