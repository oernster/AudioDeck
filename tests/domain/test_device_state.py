"""Tests for the DeviceState value object."""

from src.domain.value_objects.device_state import DeviceState


def test_is_available_only_for_available():
    assert DeviceState.AVAILABLE.is_available is True
    assert DeviceState.DISCONNECTED.is_available is False
    assert DeviceState.DISABLED.is_available is False
    assert DeviceState.NOT_PRESENT.is_available is False


def test_labels():
    assert DeviceState.AVAILABLE.label == "Available"
    assert DeviceState.DISCONNECTED.label == "Disconnected"
    assert DeviceState.DISABLED.label == "Disabled"
    assert DeviceState.NOT_PRESENT.label == "Not present"
