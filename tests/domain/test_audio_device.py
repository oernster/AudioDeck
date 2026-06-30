"""Tests for the AudioDevice entity."""

import pytest

from src.domain.entities.audio_device import AudioDevice
from src.domain.value_objects.device_type import DeviceType


def test_valid_device():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, False, True)
    assert device.id == "id"
    assert device.name == "Speakers"


def test_empty_id_raises():
    with pytest.raises(ValueError, match="Device ID cannot be empty"):
        AudioDevice("", "Speakers", DeviceType.OUTPUT, False, True)


def test_empty_name_raises():
    with pytest.raises(ValueError, match="Device name cannot be empty"):
        AudioDevice("id", "", DeviceType.OUTPUT, False, True)


def test_with_default_returns_new_instance():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, False, True)
    updated = device.with_default(True)
    assert updated.is_default is True
    assert device.is_default is False
    assert updated.id == device.id


def test_display_name_default():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, True, True)
    assert device.display_name == "Speakers (Default)"


def test_display_name_disabled():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, False, False)
    assert device.display_name == "Speakers (Disabled)"


def test_display_name_default_and_disabled():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, True, False)
    assert device.display_name == "Speakers (Default, Disabled)"


def test_display_name_plain():
    device = AudioDevice("id", "Speakers", DeviceType.OUTPUT, False, True)
    assert device.display_name == "Speakers"
