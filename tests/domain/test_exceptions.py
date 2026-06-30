"""Tests for the domain exception hierarchy."""

import pytest

from src.domain.exceptions.domain_exceptions import (
    AudioDeckException,
    DeviceControlException,
    DeviceNotFoundException,
    ProfileNotFoundException,
    ProfileStorageException,
)


@pytest.mark.parametrize(
    "exc",
    [
        DeviceControlException,
        DeviceNotFoundException,
        ProfileNotFoundException,
        ProfileStorageException,
    ],
)
def test_subclasses_of_base(exc):
    assert issubclass(exc, AudioDeckException)
    with pytest.raises(AudioDeckException):
        raise exc("boom")
