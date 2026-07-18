"""Tests for the AudioDevice entity."""

import pytest

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType


def make(is_default=False, state=DeviceState.AVAILABLE):
    return AudioDevice("id", "Speakers", DeviceType.OUTPUT, is_default, state)


def test_valid_device():
    device = make()
    assert device.id == "id"
    assert device.is_available is True


def test_empty_id_raises():
    with pytest.raises(ValueError, match="Device ID cannot be empty"):
        AudioDevice("", "Speakers", DeviceType.OUTPUT, False, DeviceState.AVAILABLE)


def test_empty_name_raises():
    with pytest.raises(ValueError, match="Device name cannot be empty"):
        AudioDevice("id", "", DeviceType.OUTPUT, False, DeviceState.AVAILABLE)


def test_is_available_false_when_disconnected():
    assert make(state=DeviceState.DISCONNECTED).is_available is False


def test_with_default_preserves_state():
    device = make(is_default=False, state=DeviceState.DISCONNECTED)
    updated = device.with_default(True)
    assert updated.is_default is True
    assert updated.state is DeviceState.DISCONNECTED
    assert device.is_default is False


def test_display_name_default():
    assert make(is_default=True).display_name == "Speakers (Default)"


def test_display_name_disconnected():
    assert make(state=DeviceState.DISCONNECTED).display_name == (
        "Speakers (Disconnected)"
    )


def test_display_name_default_and_disconnected():
    device = make(is_default=True, state=DeviceState.DISCONNECTED)
    assert device.display_name == "Speakers (Default, Disconnected)"


def test_display_name_plain():
    assert make().display_name == "Speakers"
