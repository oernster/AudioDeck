"""Tests for the enumerator that asks each source in turn."""

import pytest

from src.domain.entities.audio_device import AudioDevice
from src.domain.exceptions.domain_exceptions import DeviceEnumerationException
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


class FailingEnumerator:
    """A source whose command cannot be run."""

    def get_all_devices(self):
        raise DeviceEnumerationException("Could not read the audio devices")


def test_a_source_that_cannot_be_read_hands_over_to_the_next():
    second = FakeEnumerator([make_device("from-second")])
    devices = FirstAnsweringEnumerator((FailingEnumerator(), second)).get_all_devices()
    assert [d.id for d in devices] == ["from-second"]


def test_a_failed_source_and_an_empty_one_read_as_no_devices():
    sources = (FailingEnumerator(), FakeEnumerator([]))
    assert FirstAnsweringEnumerator(sources).get_all_devices() == []


def test_every_source_failing_is_a_failure_to_read():
    # Audit A-8: unreadable must never look like "every device is gone".
    sources = (FailingEnumerator(), FailingEnumerator())
    with pytest.raises(DeviceEnumerationException, match="Could not read"):
        FirstAnsweringEnumerator(sources).get_all_devices()


def test_no_sources_at_all_read_as_no_devices():
    assert FirstAnsweringEnumerator(()).get_all_devices() == []
