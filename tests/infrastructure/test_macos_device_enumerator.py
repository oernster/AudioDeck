"""Tests for the CoreAudio-backed macOS device enumerator."""

from typing import Dict, List, Optional

from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.macos.macos_device_enumerator import MacosDeviceEnumerator

_SPEAKERS = 10
_MICROPHONE = 20
_HEADSET = 30


class FakeCoreAudioApi:
    """Hand-written fake of the CoreAudio seam."""

    def __init__(
        self,
        device_ids: Optional[List[int]] = None,
        uids: Optional[Dict[int, str]] = None,
        names: Optional[Dict[int, str]] = None,
        outputs: Optional[List[int]] = None,
        inputs: Optional[List[int]] = None,
        default_output: Optional[int] = None,
        default_input: Optional[int] = None,
        raising_ids: Optional[List[int]] = None,
    ) -> None:
        self.device_ids = device_ids or [_SPEAKERS, _MICROPHONE, _HEADSET]
        self.uids = uids or {
            _SPEAKERS: "uid-speakers",
            _MICROPHONE: "uid-microphone",
            _HEADSET: "uid-headset",
        }
        self.names = names or {
            _SPEAKERS: "Built-in Speakers",
            _MICROPHONE: "USB Microphone",
            _HEADSET: "USB Headset",
        }
        self.outputs = outputs if outputs is not None else [_SPEAKERS, _HEADSET]
        self.inputs = inputs if inputs is not None else [_MICROPHONE, _HEADSET]
        self.default_output = default_output
        self.default_input = default_input
        self.raising_ids = raising_ids or []

    def all_device_ids(self) -> List[int]:
        return self.device_ids

    def device_uid(self, device_id: int) -> Optional[str]:
        return self.uids.get(device_id)

    def device_name(self, device_id: int) -> Optional[str]:
        return self.names.get(device_id)

    def has_output_streams(self, device_id: int) -> bool:
        if device_id in self.raising_ids:
            raise RuntimeError("stream check failed")
        return device_id in self.outputs

    def has_input_streams(self, device_id: int) -> bool:
        return device_id in self.inputs

    def default_device_id(self, input_device: bool) -> Optional[int]:
        return self.default_input if input_device else self.default_output

    def set_default_device(self, device_id: int, input_device: bool) -> bool:
        raise AssertionError("the enumerator must never set a default")


def test_devices_split_by_stream_direction():
    devices = MacosDeviceEnumerator(FakeCoreAudioApi()).get_all_devices()
    outputs = [d.id for d in devices if d.device_type == DeviceType.OUTPUT]
    inputs = [d.id for d in devices if d.device_type == DeviceType.INPUT]
    assert outputs == ["uid-speakers", "uid-headset"]
    assert inputs == ["uid-microphone", "uid-headset"]


def test_a_duplex_device_appears_once_per_direction():
    devices = MacosDeviceEnumerator(FakeCoreAudioApi()).get_all_devices()
    headset_entries = [d for d in devices if d.id == "uid-headset"]
    assert {d.device_type for d in headset_entries} == {
        DeviceType.OUTPUT,
        DeviceType.INPUT,
    }


def test_the_default_devices_are_marked_per_direction():
    api = FakeCoreAudioApi(default_output=_SPEAKERS, default_input=_HEADSET)
    devices = MacosDeviceEnumerator(api).get_all_devices()
    defaults = {(d.device_type, d.id) for d in devices if d.is_default}
    assert defaults == {
        (DeviceType.OUTPUT, "uid-speakers"),
        (DeviceType.INPUT, "uid-headset"),
    }


def test_a_device_with_no_readable_uid_is_skipped():
    # The headset is duplex, so the missing UID must skip it from both the
    # output list and the input list.
    api = FakeCoreAudioApi()
    del api.uids[_HEADSET]
    devices = MacosDeviceEnumerator(api).get_all_devices()
    assert "uid-headset" not in [d.id for d in devices]
    assert "uid-speakers" in [d.id for d in devices]
    assert "uid-microphone" in [d.id for d in devices]


def test_a_missing_name_falls_back_to_a_positional_name():
    api = FakeCoreAudioApi()
    del api.names[_SPEAKERS]
    devices = MacosDeviceEnumerator(api).get_all_devices()
    speakers = next(d for d in devices if d.id == "uid-speakers")
    assert speakers.name == "Audio Device 1"


def test_a_device_that_raises_is_skipped_without_losing_the_rest():
    api = FakeCoreAudioApi(raising_ids=[_SPEAKERS])
    devices = MacosDeviceEnumerator(api).get_all_devices()
    assert "uid-speakers" not in [d.id for d in devices]
    assert "uid-headset" in [d.id for d in devices]


def test_no_devices_yields_an_empty_list():
    api = FakeCoreAudioApi(device_ids=[], outputs=[], inputs=[])
    assert MacosDeviceEnumerator(api).get_all_devices() == []
