"""Tests for the SwitchOutcome result object."""

from src.application.dtos.switch_outcome import (
    SkipReason,
    SkippedDevice,
    SwitchOutcome,
)
from src.domain.value_objects.device_type import DeviceType


def test_fully_applied_when_nothing_skipped():
    outcome = SwitchOutcome(applied=(DeviceType.OUTPUT,), skipped=())
    assert outcome.fully_applied is True
    assert outcome.anything_applied is True


def test_partial_when_some_skipped():
    skipped = SkippedDevice(DeviceType.INPUT, "dev-in", SkipReason.UNAVAILABLE)
    outcome = SwitchOutcome(applied=(DeviceType.OUTPUT,), skipped=(skipped,))
    assert outcome.fully_applied is False
    assert outcome.anything_applied is True


def test_nothing_applied():
    skipped = SkippedDevice(DeviceType.OUTPUT, "dev-out", SkipReason.UNAVAILABLE)
    outcome = SwitchOutcome(applied=(), skipped=(skipped,))
    assert outcome.anything_applied is False


def test_skip_reason_labels():
    assert SkipReason.UNAVAILABLE.label == "not available"
    assert SkipReason.WRONG_TYPE.label == "wrong device type"
    assert SkipReason.CONTROL_FAILED.label == "could not be set"
