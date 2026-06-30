"""Tests for SwitchProfileUseCase."""

from uuid import uuid4

import pytest

from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    DeviceNotFoundException,
    ProfileNotFoundException,
)
from src.infrastructure.windows.windows_device_repository import (
    WindowsDeviceRepository,
)

from tests.conftest import (
    FakeDeviceController,
    FakeEnumerator,
    make_device,
    save_profile,
)


@pytest.fixture
def repo_devices():
    return [
        make_device("dev-out", "Speakers", DeviceType.OUTPUT, True, True),
        make_device("dev-in", "Microphone", DeviceType.INPUT, True, True),
    ]


@pytest.fixture
def device_repository(repo_devices):
    return WindowsDeviceRepository(FakeEnumerator(repo_devices))


def test_switch_sets_both_devices(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Both", "dev-out", "dev-in")
    controller = FakeDeviceController()
    use_case = SwitchProfileUseCase(profile_repo, device_repository, controller)
    use_case.execute(profile.id)
    assert ("dev-out", DeviceType.OUTPUT) in controller.calls
    assert ("dev-in", DeviceType.INPUT) in controller.calls
    assert controller.refreshed is True


def test_switch_profile_not_found(profile_repo, device_repository, no_sleep):
    use_case = SwitchProfileUseCase(
        profile_repo, device_repository, FakeDeviceController()
    )
    with pytest.raises(ProfileNotFoundException):
        use_case.execute(uuid4())


def test_switch_output_missing(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Bad", "missing", None)
    use_case = SwitchProfileUseCase(
        profile_repo, device_repository, FakeDeviceController()
    )
    with pytest.raises(DeviceNotFoundException):
        use_case.execute(profile.id)


def test_switch_output_wrong_type(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Wrong", "dev-in", None)
    use_case = SwitchProfileUseCase(
        profile_repo, device_repository, FakeDeviceController()
    )
    with pytest.raises(DeviceControlException):
        use_case.execute(profile.id)


def test_switch_input_missing(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "BadIn", None, "missing")
    use_case = SwitchProfileUseCase(
        profile_repo, device_repository, FakeDeviceController()
    )
    with pytest.raises(DeviceNotFoundException):
        use_case.execute(profile.id)


def test_switch_input_wrong_type(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "WrongIn", None, "dev-out")
    use_case = SwitchProfileUseCase(
        profile_repo, device_repository, FakeDeviceController()
    )
    with pytest.raises(DeviceControlException):
        use_case.execute(profile.id)


def test_switch_no_devices_configured(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Empty", None, None)
    controller = FakeDeviceController()
    use_case = SwitchProfileUseCase(profile_repo, device_repository, controller)
    use_case.execute(profile.id)
    assert controller.calls == []
    assert controller.refreshed is True
