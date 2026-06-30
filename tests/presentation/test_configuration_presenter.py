"""Tests for the configuration presenter."""

from src.presentation.presenters.configuration_presenter import (
    ConfigurationPresenter,
)
from src.application.dtos.device_dto import DeviceDTO
from src.domain.value_objects.device_type import DeviceType
from src.domain.exceptions.domain_exceptions import (
    ProfileNotFoundException,
    ProfileStorageException,
)

from tests.conftest import (
    FakeDeleteProfileUseCase,
    FakeGetDevicesUseCase,
    FakeGetProfilesUseCase,
    FakeMutateProfileUseCase,
    make_profile_dto,
)


def device_dto():
    return DeviceDTO("d", "Dev", DeviceType.OUTPUT, False, True)


def collect(signal):
    received = []
    signal.connect(received.append)
    return received


def build(
    devices_uc=None, create_uc=None, update_uc=None, delete_uc=None, profiles_uc=None
):
    return ConfigurationPresenter(
        devices_uc or FakeGetDevicesUseCase(),
        create_uc or FakeMutateProfileUseCase(),
        update_uc or FakeMutateProfileUseCase(),
        delete_uc or FakeDeleteProfileUseCase(),
        profiles_uc or FakeGetProfilesUseCase(),
    )


def test_get_output_devices_success(qtbot):
    presenter = build(devices_uc=FakeGetDevicesUseCase(devices=[device_dto()]))
    assert len(presenter.get_output_devices()) == 1


def test_get_output_devices_audiodeck_error(qtbot):
    presenter = build(
        devices_uc=FakeGetDevicesUseCase(error=ProfileStorageException("x"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_output_devices() == []
    assert errors


def test_get_output_devices_generic_error_silent(qtbot):
    presenter = build(devices_uc=FakeGetDevicesUseCase(error=RuntimeError("com")))
    errors = collect(presenter.error_occurred)
    assert presenter.get_output_devices() == []
    assert errors == []


def test_get_input_devices_success(qtbot):
    presenter = build(devices_uc=FakeGetDevicesUseCase(devices=[device_dto()]))
    assert len(presenter.get_input_devices()) == 1


def test_get_input_devices_audiodeck_error(qtbot):
    presenter = build(
        devices_uc=FakeGetDevicesUseCase(error=ProfileStorageException("x"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_input_devices() == []
    assert errors


def test_get_input_devices_generic_error_silent(qtbot):
    presenter = build(devices_uc=FakeGetDevicesUseCase(error=RuntimeError("com")))
    errors = collect(presenter.error_occurred)
    assert presenter.get_input_devices() == []
    assert errors == []


def test_get_profiles_success(qtbot):
    dto = make_profile_dto("P")
    presenter = build(profiles_uc=FakeGetProfilesUseCase(profiles=[dto]))
    assert presenter.get_profiles() == [dto]


def test_get_profiles_error(qtbot):
    presenter = build(
        profiles_uc=FakeGetProfilesUseCase(error=ProfileStorageException("x"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_profiles() == []
    assert errors


def test_get_profile_by_id_success(qtbot):
    dto = make_profile_dto("P")
    presenter = build(profiles_uc=FakeGetProfilesUseCase(by_id=dto))
    assert presenter.get_profile_by_id(dto.id) == dto


def test_get_profile_by_id_error(qtbot):
    presenter = build(
        profiles_uc=FakeGetProfilesUseCase(by_id=ProfileNotFoundException("nope"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_profile_by_id("pid") is None
    assert errors


def test_create_profile_success(qtbot):
    dto = make_profile_dto("New")
    presenter = build(create_uc=FakeMutateProfileUseCase(result=dto))
    saved = collect(presenter.profile_saved)
    presenter.create_profile("New", "o", "i")
    assert saved == ["New"]


def test_create_profile_error(qtbot):
    presenter = build(
        create_uc=FakeMutateProfileUseCase(error=ProfileStorageException("dup"))
    )
    errors = collect(presenter.error_occurred)
    presenter.create_profile("New", "o", "i")
    assert errors


def test_update_profile_success(qtbot):
    dto = make_profile_dto("Upd")
    presenter = build(update_uc=FakeMutateProfileUseCase(result=dto))
    saved = collect(presenter.profile_saved)
    presenter.update_profile(dto.id, "Upd", "o", "i")
    assert saved == ["Upd"]


def test_update_profile_error(qtbot):
    presenter = build(
        update_uc=FakeMutateProfileUseCase(error=ProfileNotFoundException("gone"))
    )
    errors = collect(presenter.error_occurred)
    presenter.update_profile("pid", "X", "o", "i")
    assert errors


def test_delete_profile_success(qtbot):
    delete_uc = FakeDeleteProfileUseCase()
    presenter = build(delete_uc=delete_uc)
    presenter.delete_profile("pid")
    assert delete_uc.deleted == ["pid"]


def test_delete_profile_error(qtbot):
    presenter = build(
        delete_uc=FakeDeleteProfileUseCase(error=ProfileNotFoundException("gone"))
    )
    errors = collect(presenter.error_occurred)
    presenter.delete_profile("pid")
    assert errors
