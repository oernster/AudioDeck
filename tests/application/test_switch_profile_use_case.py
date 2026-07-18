"""Tests for SwitchProfileUseCase (partial-apply outcome)."""

from uuid import uuid4

import pytest

from src.application.dtos.switch_outcome import SkipReason
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.exceptions.domain_exceptions import (
    DeviceControlException,
    ProfileNotFoundException,
)
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
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
        make_device("dev-out", "Speakers", DeviceType.OUTPUT, True),
        make_device("dev-in", "Microphone", DeviceType.INPUT, True),
        make_device(
            "dev-bt", "Headset", DeviceType.OUTPUT, False, DeviceState.DISCONNECTED
        ),
    ]


@pytest.fixture
def device_repository(repo_devices):
    return WindowsDeviceRepository(FakeEnumerator(repo_devices))


def use_case(profile_repo, device_repository, controller=None):
    return SwitchProfileUseCase(
        profile_repo, device_repository, controller or FakeDeviceController()
    )


def test_switch_sets_both_devices(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Both", "dev-out", "dev-in")
    controller = FakeDeviceController()
    outcome = use_case(profile_repo, device_repository, controller).execute(profile.id)
    assert outcome.fully_applied
    assert set(outcome.applied) == {DeviceType.OUTPUT, DeviceType.INPUT}
    assert controller.refreshed is True


def test_profile_not_found(profile_repo, device_repository, no_sleep):
    with pytest.raises(ProfileNotFoundException):
        use_case(profile_repo, device_repository).execute(uuid4())


def test_output_missing_is_skipped(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Bad", "missing", None)
    outcome = use_case(profile_repo, device_repository).execute(profile.id)
    assert not outcome.anything_applied
    assert outcome.skipped[0].reason is SkipReason.UNAVAILABLE


def test_disconnected_device_is_skipped(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "BT", "dev-bt", None)
    outcome = use_case(profile_repo, device_repository).execute(profile.id)
    assert not outcome.anything_applied
    assert outcome.skipped[0].reason is SkipReason.UNAVAILABLE


def test_wrong_type_is_skipped(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Wrong", "dev-in", None)
    outcome = use_case(profile_repo, device_repository).execute(profile.id)
    assert outcome.skipped[0].reason is SkipReason.WRONG_TYPE


def test_control_failure_is_skipped(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Ctl", "dev-out", None)
    controller = FakeDeviceController(error=DeviceControlException("nope"))
    outcome = use_case(profile_repo, device_repository, controller).execute(profile.id)
    assert outcome.skipped[0].reason is SkipReason.CONTROL_FAILED


def test_partial_apply(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Partial", "dev-out", "missing")
    outcome = use_case(profile_repo, device_repository).execute(profile.id)
    assert outcome.anything_applied
    assert not outcome.fully_applied
    assert outcome.applied == (DeviceType.OUTPUT,)
    assert outcome.skipped[0].device_type is DeviceType.INPUT


def test_no_devices_configured(profile_repo, device_repository, no_sleep):
    profile = save_profile(profile_repo, "Empty", None, None)
    controller = FakeDeviceController()
    outcome = use_case(profile_repo, device_repository, controller).execute(profile.id)
    assert outcome.applied == ()
    assert outcome.skipped == ()
    assert controller.refreshed is True
