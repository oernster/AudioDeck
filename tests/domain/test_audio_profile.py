"""Tests for the AudioProfile entity."""

from uuid import uuid4

import pytest

from src.domain.entities.audio_profile import AudioProfile


def make(name="Profile", output="out", inp="in"):
    return AudioProfile(
        id=uuid4(), name=name, output_device_id=output, input_device_id=inp
    )


def test_valid_profile():
    profile = make()
    assert profile.name == "Profile"
    assert profile.created_at is not None
    assert profile.updated_at is not None


def test_empty_name_raises():
    with pytest.raises(ValueError, match="Profile name cannot be empty"):
        AudioProfile(id=uuid4(), name="")


def test_update_all_fields():
    profile = make()
    before = profile.updated_at
    profile.update(name="New", output_device_id="o2", input_device_id="i2")
    assert profile.name == "New"
    assert profile.output_device_id == "o2"
    assert profile.input_device_id == "i2"
    assert profile.updated_at >= before


def test_update_name_none_keeps_name():
    profile = make(name="Keep")
    profile.update(name=None, output_device_id="o2")
    assert profile.name == "Keep"
    assert profile.output_device_id == "o2"


def test_update_empty_name_raises():
    profile = make()
    with pytest.raises(ValueError, match="Profile name cannot be empty"):
        profile.update(name="")


def test_to_dict_round_trip():
    profile = make()
    data = profile.to_dict()
    restored = AudioProfile.from_dict(data)
    assert restored.id == profile.id
    assert restored.name == profile.name
    assert restored.output_device_id == profile.output_device_id
    assert restored.input_device_id == profile.input_device_id


def test_from_dict_without_optional_devices():
    profile = make(output=None, inp=None)
    data = profile.to_dict()
    data.pop("output_device_id")
    data.pop("input_device_id")
    restored = AudioProfile.from_dict(data)
    assert restored.output_device_id is None
    assert restored.input_device_id is None
