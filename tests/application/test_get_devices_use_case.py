"""Tests for GetDevicesUseCase."""

from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.windows.windows_device_repository import (
    WindowsDeviceRepository,
)

from tests.conftest import FakeEnumerator, make_device


def test_execute_all_devices(device_repo):
    use_case = GetDevicesUseCase(device_repo)
    result = use_case.execute()
    assert len(result) == 2


def test_execute_filtered_by_type(device_repo):
    use_case = GetDevicesUseCase(device_repo)
    outputs = use_case.execute(device_type=DeviceType.OUTPUT)
    assert len(outputs) == 1
    assert outputs[0].device_type == DeviceType.OUTPUT


def test_execute_with_refresh(devices):
    repo = WindowsDeviceRepository(FakeEnumerator(devices), auto_refresh=False)
    use_case = GetDevicesUseCase(repo)
    assert use_case.execute(refresh=True)  # refresh populates the repo


def test_get_default_device_returns_dto(device_repo):
    use_case = GetDevicesUseCase(device_repo)
    dto = use_case.get_default_device(DeviceType.OUTPUT, refresh=False)
    assert dto is not None
    assert dto.id == "dev-out"


def test_get_default_device_none_when_empty():
    repo = WindowsDeviceRepository(FakeEnumerator([]))
    use_case = GetDevicesUseCase(repo)
    assert use_case.get_default_device(DeviceType.OUTPUT) is None


def test_get_default_device_with_refresh():
    device = make_device("only", "Only", DeviceType.INPUT, False, True)
    repo = WindowsDeviceRepository(FakeEnumerator([device]), auto_refresh=False)
    use_case = GetDevicesUseCase(repo)
    # No default flagged, so the first device is returned after refresh.
    dto = use_case.get_default_device(DeviceType.INPUT, refresh=True)
    assert dto.id == "only"
