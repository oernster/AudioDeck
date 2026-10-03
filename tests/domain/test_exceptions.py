"""Tests for the domain exception hierarchy."""

import pytest

from src.domain.exceptions.domain_exceptions import (
    AudioDeckException,
    DeviceControlException,
    DeviceEnumerationException,
    DeviceNotFoundException,
    ProfileNotFoundException,
    ProfileStorageException,
    SwitchInProgressException,
)


@pytest.mark.parametrize(
    "exc",
    [
        DeviceControlException,
        DeviceNotFoundException,
        ProfileNotFoundException,
        ProfileStorageException,
        DeviceEnumerationException,
        SwitchInProgressException,
    ],
)
def test_subclasses_of_base(exc):
    assert issubclass(exc, AudioDeckException)
    with pytest.raises(AudioDeckException):
        raise exc("boom")


def test_a_partial_control_failure_names_its_missing_roles():
    from src.domain.exceptions.domain_exceptions import PartialDeviceControlException

    failure = PartialDeviceControlException(("Console", "Communications"))
    assert isinstance(failure, DeviceControlException)
    assert failure.missing_roles == ("Console", "Communications")
    assert "Console, Communications" in str(failure)
