"""Tests for the DeviceType value object."""

from src.domain.value_objects.device_type import DeviceType


def test_values():
    assert DeviceType.INPUT.value == "input"
    assert DeviceType.OUTPUT.value == "output"


def test_display_name():
    assert DeviceType.INPUT.display_name == "Input"
    assert DeviceType.OUTPUT.display_name == "Output"
