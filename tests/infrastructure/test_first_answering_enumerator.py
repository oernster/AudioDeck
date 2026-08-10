"""Tests for the enumerator that asks each source in turn."""

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.linux.first_answering_enumerator import (
    FirstAnsweringEnumerator,
)


class FakeEnumerator:
    """Hand-written fake of a device enumerator."""

    def __init__(self, devices) -> None:
        self.devices = devices
        self.asked = False

    def get_all_devices(self):
        self.asked = True
        return self.devices


def make_device(identifier: str) -> AudioDevice:
    """Build a device with only the identifier varying."""
    return AudioDevice(
        id=identifier,
        name=identifier,
        device_type=DeviceType.OUTPUT,
        is_default=False,
        state=DeviceState.AVAILABLE,
    )


def test_the_first_source_that_finds_devices_wins():
    first = FakeEnumerator([make_device("from-first")])
    second = FakeEnumerator([make_device("from-second")])

    devices = FirstAnsweringEnumerator((first, second)).get_all_devices()

    assert [d.id for d in devices] == ["from-first"]


def test_a_later_source_is_not_consulted_once_one_answers():
    first = FakeEnumerator([make_device("from-first")])
    second = FakeEnumerator([make_device("from-second")])

    FirstAnsweringEnumerator((first, second)).get_all_devices()

    assert second.asked is False


def test_an_empty_source_hands_over_to_the_next():
    first = FakeEnumerator([])
    second = FakeEnumerator([make_device("from-second")])

    devices = FirstAnsweringEnumerator((first, second)).get_all_devices()

    assert [d.id for d in devices] == ["from-second"]


def test_no_source_finding_anything_reads_as_no_devices():
    assert FirstAnsweringEnumerator((FakeEnumerator([]),)).get_all_devices() == []
