"""Tests for the device repository logic (over a fake enumerator)."""

from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.caching_device_repository import (
    CachingDeviceRepository,
)
from tests.conftest import FakeEnumerator, make_device


def test_auto_refresh_populates(devices):
    repo = CachingDeviceRepository(FakeEnumerator(devices))
    assert len(repo.get_all_devices()) == 2


def test_no_auto_refresh_is_empty(devices):
    repo = CachingDeviceRepository(FakeEnumerator(devices), auto_refresh=False)
    assert repo.get_all_devices() == []


def test_get_all_returns_copy(devices):
    repo = CachingDeviceRepository(FakeEnumerator(devices))
    result = repo.get_all_devices()
    result.clear()
    assert len(repo.get_all_devices()) == 2


def test_get_devices_by_type(devices):
    repo = CachingDeviceRepository(FakeEnumerator(devices))
    assert len(repo.get_devices_by_type(DeviceType.OUTPUT)) == 1


def test_get_default_returns_flagged_default():
    items = [
        make_device("a", "A", DeviceType.OUTPUT, False),
        make_device("b", "B", DeviceType.OUTPUT, True),
    ]
    repo = CachingDeviceRepository(FakeEnumerator(items))
    assert repo.get_default_device(DeviceType.OUTPUT).id == "b"


def test_get_default_falls_back_to_first():
    items = [
        make_device("a", "A", DeviceType.OUTPUT, False),
        make_device("b", "B", DeviceType.OUTPUT, False),
    ]
    repo = CachingDeviceRepository(FakeEnumerator(items))
    assert repo.get_default_device(DeviceType.OUTPUT).id == "a"


def test_get_default_none_when_empty():
    repo = CachingDeviceRepository(FakeEnumerator([]))
    assert repo.get_default_device(DeviceType.OUTPUT) is None


def test_get_device_by_id_found_and_missing(devices):
    repo = CachingDeviceRepository(FakeEnumerator(devices))
    assert repo.get_device_by_id("dev-out").id == "dev-out"
    assert repo.get_device_by_id("nope") is None


def test_refresh_reloads():
    enumerator = FakeEnumerator([make_device("a", "A")])
    repo = CachingDeviceRepository(enumerator, auto_refresh=False)
    repo.refresh()
    assert len(repo.get_all_devices()) == 1
