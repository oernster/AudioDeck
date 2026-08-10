"""Tests for the pactl-backed Linux device enumerator."""

import json
import subprocess

from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.linux_device_enumerator import LinuxDeviceEnumerator

_SINKS = [
    {"name": "alsa_output.usb-dac", "description": "USB DAC"},
    {"name": "alsa_output.hdmi", "description": "HDMI Audio"},
]
_SOURCES = [
    {"name": "alsa_input.usb-mic", "description": "USB Microphone"},
    {
        "name": "alsa_output.usb-dac.monitor",
        "description": "Monitor of USB DAC",
        "monitor_of_sink_name": "alsa_output.usb-dac",
    },
]


class FakePactlApi:
    """Hand-written fake of the pactl command seam."""

    def __init__(self, responses=None, failing_commands=()) -> None:
        self.responses = responses or {}
        self.failing_commands = failing_commands
        self.calls: list[tuple] = []

    def run(self, *args):
        self.calls.append(args)
        if args[0] in self.failing_commands or args[-1] in self.failing_commands:
            raise subprocess.SubprocessError("pactl failed")
        return self.responses[args]


def _api(
    sinks=_SINKS,
    sources=_SOURCES,
    default_sink="alsa_output.usb-dac",
    default_source="alsa_input.usb-mic",
    failing_commands=(),
):
    return FakePactlApi(
        responses={
            ("-f", "json", "list", "sinks"): json.dumps(sinks),
            ("-f", "json", "list", "sources"): json.dumps(sources),
            ("get-default-sink",): f"{default_sink}\n",
            ("get-default-source",): f"{default_source}\n",
        },
        failing_commands=failing_commands,
    )


def test_sinks_map_to_output_devices_with_descriptions():
    devices = LinuxDeviceEnumerator(_api()).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert [d.id for d in outputs] == ["alsa_output.usb-dac", "alsa_output.hdmi"]
    assert [d.name for d in outputs] == ["USB DAC", "HDMI Audio"]


def test_the_default_sink_and_source_are_marked():
    devices = LinuxDeviceEnumerator(_api()).get_all_devices()
    defaults = [d.id for d in devices if d.is_default]
    assert defaults == ["alsa_output.usb-dac", "alsa_input.usb-mic"]


def test_monitor_sources_are_excluded():
    devices = LinuxDeviceEnumerator(_api()).get_all_devices()
    inputs = [d for d in devices if d.device_type == DeviceType.INPUT]
    assert [d.id for d in inputs] == ["alsa_input.usb-mic"]


def test_a_monitor_source_is_recognised_by_name_suffix_alone():
    sources = [{"name": "something.monitor", "description": "Monitor"}]
    devices = LinuxDeviceEnumerator(_api(sources=sources)).get_all_devices()
    assert [d for d in devices if d.device_type == DeviceType.INPUT] == []


def test_a_missing_description_falls_back_to_a_positional_name():
    sinks = [{"name": "bare_sink"}]
    devices = LinuxDeviceEnumerator(_api(sinks=sinks)).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert outputs[0].name == "Audio Device 1"


def test_an_item_with_no_name_is_skipped():
    sinks = [{"description": "Nameless"}, {"name": "ok", "description": "OK"}]
    devices = LinuxDeviceEnumerator(_api(sinks=sinks)).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert [d.id for d in outputs] == ["ok"]


def test_a_malformed_item_is_skipped_without_losing_the_rest():
    api = _api()
    api.responses[("-f", "json", "list", "sinks")] = json.dumps(
        ["not-a-dict", {"name": "ok", "description": "OK"}]
    )
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert [d.id for d in outputs] == ["ok"]


def test_non_list_json_degrades_to_no_devices():
    api = _api()
    api.responses[("-f", "json", "list", "sinks")] = json.dumps({"error": "odd"})
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    assert [d for d in devices if d.device_type == DeviceType.OUTPUT] == []


def test_non_json_output_degrades_to_no_devices():
    api = _api()
    api.responses[("-f", "json", "list", "sinks")] = "not json"
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    assert [d for d in devices if d.device_type == DeviceType.OUTPUT] == []


def test_a_failing_list_command_degrades_to_no_devices():
    api = _api(failing_commands=("sinks",))
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    assert [d for d in devices if d.device_type == DeviceType.OUTPUT] == []


def test_a_failing_default_lookup_marks_no_default():
    api = _api(failing_commands=("get-default-sink",))
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert all(not d.is_default for d in outputs)


def test_an_empty_default_answer_marks_no_default():
    api = _api(default_sink="")
    devices = LinuxDeviceEnumerator(api).get_all_devices()
    outputs = [d for d in devices if d.device_type == DeviceType.OUTPUT]
    assert all(not d.is_default for d in outputs)
