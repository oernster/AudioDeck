"""Tests for the actuation presenter."""

from src.presentation.presenters.actuation_presenter import ActuationPresenter
from src.application.dtos.device_dto import DeviceDTO
from src.application.dtos.switch_outcome import (
    SkipReason,
    SkippedDevice,
    SwitchOutcome,
)
from src.domain.value_objects.device_type import DeviceType
from src.domain.value_objects.device_state import DeviceState
from src.domain.exceptions.domain_exceptions import ProfileStorageException

from tests.conftest import (
    FakeGetDevicesUseCase,
    FakeGetProfilesUseCase,
    FakeSwitchUseCase,
    make_profile_dto,
)


def device_dto(device_id="dev-out", state=DeviceState.AVAILABLE):
    return DeviceDTO(device_id, "Speakers", DeviceType.OUTPUT, True, state)


def collect(signal):
    received = []
    signal.connect(received.append)
    return received


def collect_void(signal):
    received = []
    signal.connect(lambda: received.append(True))
    return received


def presenter_with(devices_uc=None, profiles_uc=None, switch_uc=None):
    return ActuationPresenter(
        devices_uc or FakeGetDevicesUseCase(),
        profiles_uc or FakeGetProfilesUseCase(),
        switch_uc or FakeSwitchUseCase(),
    )


def test_get_profiles_success(qtbot):
    dto = make_profile_dto("P")
    presenter = presenter_with(profiles_uc=FakeGetProfilesUseCase(profiles=[dto]))
    assert presenter.get_profiles() == [dto]


def test_get_profiles_error_emits(qtbot):
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(error=ProfileStorageException("boom"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_profiles() == []
    assert errors


def test_get_current_output_success(qtbot):
    presenter = presenter_with(devices_uc=FakeGetDevicesUseCase(default=device_dto()))
    assert presenter.get_current_output_device().id == "dev-out"


def test_get_current_output_silent_on_error(qtbot):
    presenter = presenter_with(
        devices_uc=FakeGetDevicesUseCase(error=RuntimeError("com"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_current_output_device() is None
    assert errors == []


def test_get_current_input_success(qtbot):
    presenter = presenter_with(devices_uc=FakeGetDevicesUseCase(default=device_dto()))
    assert presenter.get_current_input_device().id == "dev-out"


def test_get_current_input_silent_on_error(qtbot):
    presenter = presenter_with(
        devices_uc=FakeGetDevicesUseCase(error=RuntimeError("com"))
    )
    errors = collect(presenter.error_occurred)
    assert presenter.get_current_input_device() is None
    assert errors == []


def test_get_available_device_ids(qtbot):
    available = device_dto("dev-out", DeviceState.AVAILABLE)
    offline = device_dto("dev-bt", DeviceState.DISCONNECTED)
    presenter = presenter_with(
        devices_uc=FakeGetDevicesUseCase(devices=[available, offline])
    )
    assert presenter.get_available_device_ids() == {"dev-out"}


def test_get_available_device_ids_silent_on_error(qtbot):
    presenter = presenter_with(
        devices_uc=FakeGetDevicesUseCase(error=RuntimeError("com"))
    )
    assert presenter.get_available_device_ids() == set()


def test_switch_success_emits_switched(qtbot):
    dto = make_profile_dto("Gaming")
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto), switch_uc=FakeSwitchUseCase()
    )
    switched = collect(presenter.profile_switched)
    notices = collect(presenter.device_unavailable)
    presenter.switch_profile(dto.id)
    assert switched == ["Gaming"]
    assert notices == []


def test_switch_profile_not_found(qtbot):
    presenter = presenter_with(profiles_uc=FakeGetProfilesUseCase(by_id=None))
    errors = collect(presenter.error_occurred)
    presenter.switch_profile("pid")
    assert errors == ["Profile not found"]


def test_switch_nothing_applied_notifies(qtbot):
    dto = make_profile_dto("BT")
    outcome = SwitchOutcome(
        applied=(),
        skipped=(SkippedDevice(DeviceType.OUTPUT, "dev-bt", SkipReason.UNAVAILABLE),),
    )
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto),
        switch_uc=FakeSwitchUseCase(outcome=outcome),
    )
    notices = collect(presenter.device_unavailable)
    switched = collect(presenter.profile_switched)
    presenter.switch_profile(dto.id)
    assert notices and not switched
    assert "Could not switch" in notices[0]


def test_switch_partial_applies_and_notifies(qtbot):
    dto = make_profile_dto("Calls")
    outcome = SwitchOutcome(
        applied=(DeviceType.OUTPUT,),
        skipped=(SkippedDevice(DeviceType.INPUT, "dev-in", SkipReason.UNAVAILABLE),),
    )
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto),
        switch_uc=FakeSwitchUseCase(outcome=outcome),
    )
    switched = collect(presenter.profile_switched)
    notices = collect(presenter.device_unavailable)
    presenter.switch_profile(dto.id)
    assert switched == ["Calls"]
    assert notices and "Switched" in notices[0]


def test_switch_audiodeck_error(qtbot):
    dto = make_profile_dto("P")
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto),
        switch_uc=FakeSwitchUseCase(error=ProfileStorageException("bad")),
    )
    errors = collect(presenter.error_occurred)
    presenter.switch_profile(dto.id)
    assert errors and "bad" in errors[0]


def test_switch_unexpected_error(qtbot):
    dto = make_profile_dto("P")
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto),
        switch_uc=FakeSwitchUseCase(error=RuntimeError("weird")),
    )
    errors = collect(presenter.error_occurred)
    presenter.switch_profile(dto.id)
    assert errors and "Unexpected error" in errors[0]


# --- device-change handling and auto-apply on reconnect ----------------------


def _pending_outcome(device_id="dev-bt"):
    return SwitchOutcome(
        applied=(),
        skipped=(SkippedDevice(DeviceType.OUTPUT, device_id, SkipReason.UNAVAILABLE),),
    )


def _arm_pending(switch_uc, devices_uc, profiles_uc):
    """Switch to a profile whose device is offline, leaving it pending."""
    dto = make_profile_dto("BT")
    profiles_uc._by_id = dto
    presenter = ActuationPresenter(devices_uc, profiles_uc, switch_uc)
    presenter.switch_profile(dto.id)
    return presenter, dto


def test_on_devices_changed_no_pending(qtbot):
    switch = FakeSwitchUseCase()
    presenter = presenter_with(switch_uc=switch)
    changed = collect_void(presenter.current_devices_changed)
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert changed and not applied
    assert switch.executed == []


def test_auto_apply_on_reconnect(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    presenter, dto = _arm_pending(switch, devices_uc, FakeGetProfilesUseCase())

    # Device reconnects and the switch now applies it.
    devices_uc._devices = [device_dto("dev-bt", DeviceState.AVAILABLE)]
    switch.outcome = SwitchOutcome(applied=(DeviceType.OUTPUT,), skipped=())
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert applied and "BT" in applied[0]


def test_no_reapply_while_still_unavailable(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    presenter, dto = _arm_pending(switch, devices_uc, FakeGetProfilesUseCase())

    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert not applied
    assert switch.executed == [dto.id]  # no second switch attempt


def test_reapply_profile_gone_clears_pending(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    profiles_uc = FakeGetProfilesUseCase()
    presenter, dto = _arm_pending(switch, devices_uc, profiles_uc)

    devices_uc._devices = [device_dto("dev-bt", DeviceState.AVAILABLE)]
    profiles_uc._by_id = None  # profile deleted meanwhile
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert not applied
    assert switch.executed == [dto.id]  # did not re-execute


def test_reapply_get_by_id_error_is_silent(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    profiles_uc = FakeGetProfilesUseCase()
    presenter, dto = _arm_pending(switch, devices_uc, profiles_uc)

    devices_uc._devices = [device_dto("dev-bt", DeviceState.AVAILABLE)]
    profiles_uc._by_id = RuntimeError("boom")
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert not applied


def test_reapply_switch_error_is_silent(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    presenter, dto = _arm_pending(switch, devices_uc, FakeGetProfilesUseCase())

    devices_uc._devices = [device_dto("dev-bt", DeviceState.AVAILABLE)]
    switch.error = RuntimeError("boom")
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert not applied


def test_reapply_still_partial_no_auto_applied(qtbot):
    switch = FakeSwitchUseCase(outcome=_pending_outcome())
    devices_uc = FakeGetDevicesUseCase(
        devices=[device_dto("dev-bt", DeviceState.DISCONNECTED)]
    )
    presenter, dto = _arm_pending(switch, devices_uc, FakeGetProfilesUseCase())

    # Device reports available but the switch still skips it (a race); the
    # reapply runs but applies nothing, so no auto-applied notice fires.
    devices_uc._devices = [device_dto("dev-bt", DeviceState.AVAILABLE)]
    applied = collect(presenter.auto_applied)
    presenter.on_devices_changed()
    assert not applied
    assert switch.executed == [dto.id, dto.id]  # re-executed once
