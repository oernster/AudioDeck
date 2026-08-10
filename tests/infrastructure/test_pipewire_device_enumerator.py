"""Tests for the pw-dump-backed PipeWire device enumerator."""

import json
import subprocess

from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.pipewire_device_enumerator import (
    PipewireDeviceEnumerator,
)


class FakePwDumpApi:
    """Hand-written fake of the pw-dump command seam."""

    def __init__(self, output: str = "[]", fail: bool = False) -> None:
        self.output = output
        self.fail = fail

    def dump(self):
        if self.fail:
            raise subprocess.SubprocessError("pw-dump failed")
        return self.output


def node(media_class, name, description="A device"):
    """Build one pw-dump node object."""
    return {
        "type": "PipeWire:Interface:Node",
        "info": {
            "props": {
                "media.class": media_class,
                "node.name": name,
                "node.description": description,
            }
        },
    }


def default_metadata(sink=None, source=None):
    """Build the pw-dump metadata object naming the current defaults."""
    entries = []
    if sink is not None:
        entries.append({"key": "default.audio.sink", "value": {"name": sink}})
    if source is not None:
        entries.append({"key": "default.audio.source", "value": {"name": source}})
    return {
        "type": "PipeWire:Interface:Metadata",
        "props": {"metadata.name": "default"},
        "metadata": entries,
    }


def enumerate_from(objects):
    """Enumerate devices from a pw-dump object graph."""
    return PipewireDeviceEnumerator(
        FakePwDumpApi(json.dumps(objects))
    ).get_all_devices()


def test_a_sink_is_an_output_device():
    devices = enumerate_from([node("Audio/Sink", "sink-name", "The Speakers")])
    assert devices[0].id == "sink-name"
    assert devices[0].name == "The Speakers"
    assert devices[0].device_type == DeviceType.OUTPUT
    assert devices[0].state == DeviceState.AVAILABLE


def test_a_source_is_an_input_device():
    devices = enumerate_from([node("Audio/Source", "source-name")])
    assert devices[0].device_type == DeviceType.INPUT


def test_a_source_subtype_is_still_an_input_device():
    devices = enumerate_from([node("Audio/Source/Virtual", "filtered-name")])
    assert devices[0].device_type == DeviceType.INPUT


def test_outputs_are_listed_before_inputs():
    devices = enumerate_from(
        [node("Audio/Source", "source-name"), node("Audio/Sink", "sink-name")]
    )
    assert [d.id for d in devices] == ["sink-name", "source-name"]


def test_a_non_audio_node_is_ignored():
    assert enumerate_from([node("Video/Source", "camera-name")]) == []


def test_a_non_node_object_is_ignored():
    assert enumerate_from([{"type": "PipeWire:Interface:Client"}]) == []


def test_a_node_without_a_name_is_skipped():
    assert enumerate_from([node("Audio/Sink", None)]) == []


def test_a_node_without_a_description_gets_a_positional_name():
    devices = enumerate_from([node("Audio/Sink", "sink-name", None)])
    assert devices[0].name == "Audio Device 1"


def test_the_metadata_default_marks_the_default_device():
    devices = enumerate_from(
        [
            default_metadata(sink="chosen-sink"),
            node("Audio/Sink", "chosen-sink"),
            node("Audio/Sink", "other-sink"),
        ]
    )
    assert [(d.id, d.is_default) for d in devices] == [
        ("chosen-sink", True),
        ("other-sink", False),
    ]


def test_the_default_source_is_read_from_the_same_metadata():
    devices = enumerate_from(
        [
            default_metadata(source="chosen-source"),
            node("Audio/Source", "chosen-source"),
        ]
    )
    assert devices[0].is_default is True


def test_another_metadata_store_is_not_read_for_defaults():
    objects = [default_metadata(sink="chosen-sink"), node("Audio/Sink", "chosen-sink")]
    objects[0]["props"]["metadata.name"] = "settings"
    assert enumerate_from(objects)[0].is_default is False


def test_an_unrelated_metadata_key_is_ignored():
    objects = [default_metadata(sink="chosen-sink"), node("Audio/Sink", "chosen-sink")]
    objects[0]["metadata"].append({"key": "clock.rate", "value": {"name": "48000"}})
    assert enumerate_from(objects)[0].is_default is True


def test_a_metadata_value_that_is_not_an_object_is_ignored():
    objects = [default_metadata(sink="chosen-sink"), node("Audio/Sink", "chosen-sink")]
    objects[0]["metadata"][0]["value"] = "chosen-sink"
    assert enumerate_from(objects)[0].is_default is False


def test_metadata_without_entries_is_survivable():
    objects = [default_metadata(), node("Audio/Sink", "sink-name")]
    objects[0]["metadata"] = None
    assert enumerate_from(objects)[0].is_default is False


def test_a_malformed_object_costs_only_itself():
    devices = enumerate_from(["not an object", node("Audio/Sink", "sink-name")])
    assert [d.id for d in devices] == ["sink-name"]


def test_a_pw_dump_failure_reads_as_no_devices():
    assert PipewireDeviceEnumerator(FakePwDumpApi(fail=True)).get_all_devices() == []


def test_non_json_output_reads_as_no_devices():
    assert PipewireDeviceEnumerator(FakePwDumpApi("not json")).get_all_devices() == []


def test_json_that_is_not_a_list_reads_as_no_devices():
    assert PipewireDeviceEnumerator(FakePwDumpApi("{}")).get_all_devices() == []
