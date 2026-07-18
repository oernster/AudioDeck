"""Tests for the DTOs."""

from datetime import datetime
from uuid import uuid4

from src.application.dtos.device_dto import DeviceDTO
from src.application.dtos.profile_dto import ProfileDTO
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType


def device(is_default=False, state=DeviceState.AVAILABLE):
    return DeviceDTO("id", "Speakers", DeviceType.OUTPUT, is_default, state)


def test_device_display_name_default():
    assert device(is_default=True).display_name == "Speakers (Default)"


def test_device_display_name_disconnected():
    assert device(state=DeviceState.DISCONNECTED).display_name == (
        "Speakers (Disconnected)"
    )


def test_device_display_name_default_and_disconnected():
    assert device(True, DeviceState.DISCONNECTED).display_name == (
        "Speakers (Default, Disconnected)"
    )


def test_device_display_name_plain():
    assert device().display_name == "Speakers"


def test_device_is_available():
    assert device().is_available is True
    assert device(state=DeviceState.DISABLED).is_available is False


def test_device_type_display():
    assert device().type_display == "Output"


def profile(output="o", inp="i"):
    now = datetime(2024, 1, 1)
    return ProfileDTO(uuid4(), "P", output, inp, now, now)


def test_profile_flags_complete():
    p = profile()
    assert p.has_output and p.has_input and p.is_complete


def test_profile_output_only():
    p = profile(output="o", inp=None)
    assert p.has_output and not p.has_input
    assert p.display_name == "P (Output)"


def test_profile_input_only():
    p = profile(output=None, inp="i")
    assert p.display_name == "P (Input)"


def test_profile_empty():
    p = profile(output=None, inp=None)
    assert not p.is_complete
    assert p.display_name == "P (Empty)"


def test_profile_both_display():
    assert profile().display_name == "P (Output + Input)"
