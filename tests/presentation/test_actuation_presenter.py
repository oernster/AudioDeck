"""Tests for the actuation presenter."""

from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.application.dtos.device_dto import DeviceDTO
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import (
    DeviceNotFoundException,
    ProfileStorageException,
)

from tests.conftest import (
    FakeGetDevicesUseCase,
    FakeGetProfilesUseCase,
    FakeSwitchUseCase,
    make_profile_dto,
)


def device_dto():
    return DeviceDTO("dev-out", "Speakers", DeviceType.OUTPUT, True, True)


def collect(signal):
    received = []
    signal.connect(received.append)
    return received


def test_get_profiles_success(qtbot):
    dto = make_profile_dto("P")
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(profiles=[dto]),
        FakeSwitchUseCase(),
    )
    assert presenter.get_profiles() == [dto]


def test_get_profiles_error_emits(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(error=ProfileStorageException("boom")),
        FakeSwitchUseCase(),
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_profiles() == []
    assert errors


def test_get_current_output_success(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(default=device_dto()),
        FakeGetProfilesUseCase(),
        FakeSwitchUseCase(),
    )
    assert presenter.get_current_output_device().id == "dev-out"


def test_get_current_output_silent_on_error(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(error=RuntimeError("com")),
        FakeGetProfilesUseCase(),
        FakeSwitchUseCase(),
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_current_output_device() is None
    assert errors == []  # polling must not raise a dialog


def test_get_current_input_success(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(default=device_dto()),
        FakeGetProfilesUseCase(),
        FakeSwitchUseCase(),
    )
    assert presenter.get_current_input_device().id == "dev-out"


def test_get_current_input_silent_on_error(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(error=RuntimeError("com")),
        FakeGetProfilesUseCase(),
        FakeSwitchUseCase(),
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_current_input_device() is None
    assert errors == []


def test_switch_success_emits_switched(qtbot):
    dto = make_profile_dto("Gaming")
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(by_id=dto),
        FakeSwitchUseCase(),
    )
    switched = collect(presenter.profile_switched)
    presenter.switch_profile(dto.id)
    assert switched == ["Gaming"]


def test_switch_profile_not_found(qtbot):
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(by_id=None),
        FakeSwitchUseCase(),
    )
    errors = collect(presenter.error_occurred)
    presenter.switch_profile("pid")
    assert errors == ["Profile not found"]


def test_switch_device_unavailable(qtbot):
    dto = make_profile_dto("BT")
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(by_id=dto),
        FakeSwitchUseCase(error=DeviceNotFoundException("gone")),
    )
    notices = collect(presenter.device_unavailable)
    errors = collect(presenter.error_occurred)
    presenter.switch_profile(dto.id)
    assert notices and not errors


def test_switch_audiodeck_error(qtbot):
    dto = make_profile_dto("P")
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(by_id=dto),
        FakeSwitchUseCase(error=ProfileStorageException("bad")),
    )
    errors = collect(presenter.error_occurred)
    presenter.switch_profile(dto.id)
    assert errors and "bad" in errors[0]


def test_switch_unexpected_error(qtbot):
    dto = make_profile_dto("P")
    presenter = ActuationPresenter(
        FakeGetDevicesUseCase(),
        FakeGetProfilesUseCase(by_id=dto),
        FakeSwitchUseCase(error=RuntimeError("weird")),
    )
    errors = collect(presenter.error_occurred)
    presenter.switch_profile(dto.id)
    assert errors and "Unexpected error" in errors[0]
