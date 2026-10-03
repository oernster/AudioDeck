"""Presenter wording for a partly set device; waits that survive unknowns."""

from src.application.dtos.switch_outcome import (
    SkippedDevice,
    SkipReason,
    SwitchOutcome,
)
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from tests.conftest import (
    FakeGetDevicesUseCase,
    FakeGetProfilesUseCase,
    FakeSwitchUseCase,
    make_profile_dto,
)
from tests.presentation.test_actuation_presenter import (
    collect,
    device_dto,
    presenter_with,
)


class _DefaultsUnreadable(FakeGetDevicesUseCase):
    """Lists devices but cannot read the current defaults."""

    def get_default_device(self, device_type, refresh=True):
        raise RuntimeError("default unreadable")


def test_unreadable_defaults_do_not_cancel_the_wait(qtbot):
    # Unknown is not evidence that another switch moved the defaults.
    dto = make_profile_dto("Desk", output_device_id="spk", input_device_id="mic")
    outcome = SwitchOutcome(
        applied=(DeviceType.OUTPUT,),
        skipped=(SkippedDevice(DeviceType.INPUT, "mic", SkipReason.UNAVAILABLE),),
    )
    switch = FakeSwitchUseCase(outcome=outcome)
    devices_uc = _DefaultsUnreadable(devices=[])
    presenter = ActuationPresenter(
        devices_uc, FakeGetProfilesUseCase(by_id=dto), switch
    )
    presenter.switch_profile(dto.id)

    devices_uc._devices = [device_dto("mic", DeviceState.AVAILABLE)]
    presenter.on_devices_changed()

    assert switch.slots[-1] == (DeviceType.INPUT,)


def test_a_partly_set_device_is_named_with_its_missing_roles(qtbot):
    dto = make_profile_dto("Calls")
    outcome = SwitchOutcome(
        applied=(DeviceType.OUTPUT,),
        skipped=(
            SkippedDevice(
                DeviceType.OUTPUT, "dev-out", SkipReason.PARTIALLY_SET, "Console"
            ),
        ),
    )
    presenter = presenter_with(
        profiles_uc=FakeGetProfilesUseCase(by_id=dto),
        switch_uc=FakeSwitchUseCase(outcome=outcome),
    )
    notices = collect(presenter.device_unavailable)
    presenter.switch_profile(dto.id)
    assert "not made the default for Console" in notices[0]
