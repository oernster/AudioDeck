"""Auto-apply on reconnect, driven through the real switch use case.

Audit A-5: a reconnect re-applied the whole old profile over a later switch.
Audit A-6: a device gone between enumeration and the set was never retried.
Audit A-7: the notice promised an apply the code cannot always deliver.
"""

import src.domain.exceptions.domain_exceptions as errors
from src.application.use_cases.get_devices_use_case import GetDevicesUseCase
from src.application.use_cases.get_profiles_use_case import GetProfilesUseCase
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.value_objects.device_state import DeviceState
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from src.presentation.presenters.actuation_presenter import ActuationPresenter
from tests.conftest import FakeMachine, save_profile

OUT, IN = DeviceType.OUTPUT, DeviceType.INPUT


def desk_machine() -> FakeMachine:
    """Speakers and a TV; the headset mic is off; the webcam mic is on."""
    machine = FakeMachine()
    machine.add("spk", OUT)
    machine.add("tv", OUT)
    machine.add("hsmic", IN, DeviceState.DISCONNECTED)
    machine.add("cam", IN)
    machine.defaults.update({OUT: "tv", IN: "cam"})
    return machine


def presenter_over(profile_repo, machine, controller=None):
    devices = CachingDeviceRepository(machine)
    switch = SwitchProfileUseCase(profile_repo, devices, controller or machine)
    presenter = ActuationPresenter(
        GetDevicesUseCase(devices), GetProfilesUseCase(profile_repo), switch
    )
    log = []
    presenter.device_unavailable.connect(lambda text: log.append(("notice", text)))
    presenter.auto_applied.connect(lambda text: log.append(("auto", text)))
    presenter.error_occurred.connect(lambda text: log.append(("error", text)))
    return presenter, log


def test_a_later_switch_is_not_overridden_when_the_device_returns(
    qtbot, profile_repo, no_sleep
):
    machine = desk_machine()
    desk = save_profile(profile_repo, "Desk", "spk", "hsmic")
    presenter, log = presenter_over(profile_repo, machine)
    presenter.switch_profile(desk.id)

    machine.defaults[OUT] = "tv"  # a Stream Deck key, in another process
    machine.devices["hsmic"] = (IN, DeviceState.AVAILABLE)
    presenter.on_devices_changed()

    assert machine.defaults == {OUT: "tv", IN: "cam"}
    assert [kind for kind, _ in log] == ["notice"]


def test_only_the_waiting_device_is_applied_when_it_returns(
    qtbot, profile_repo, no_sleep
):
    machine = desk_machine()
    desk = save_profile(profile_repo, "Desk", "spk", "hsmic")
    presenter, log = presenter_over(profile_repo, machine)
    presenter.switch_profile(desk.id)
    calls_before_reconnect = len(machine.set_calls)

    machine.devices["hsmic"] = (IN, DeviceState.AVAILABLE)
    presenter.on_devices_changed()

    assert machine.set_calls[calls_before_reconnect:] == [("hsmic", IN)]
    assert machine.defaults == {OUT: "spk", IN: "hsmic"}
    assert log[-1][0] == "auto"
    assert "Input" in log[-1][1]


class _GoneAtTheSet:
    """The device leaves after the enumeration, just before the set."""

    def __init__(self, machine: FakeMachine) -> None:
        self._machine = machine
        self.gone = True

    def set_default_device(self, device_id, device_type):
        if self.gone:
            raise errors.DeviceNotFoundException(
                f"Device is not currently present: {device_id}"
            )
        self._machine.set_default_device(device_id, device_type)

    def refresh_devices(self):
        pass


def test_a_device_lost_mid_switch_is_applied_when_it_returns(
    qtbot, profile_repo, no_sleep
):
    machine = desk_machine()
    machine.add("hs", OUT)
    controller = _GoneAtTheSet(machine)
    headset = save_profile(profile_repo, "Headset", "hs", None)
    presenter, log = presenter_over(profile_repo, machine, controller)
    presenter.switch_profile(headset.id)

    controller.gone = False
    presenter.on_devices_changed()

    assert "refused" not in log[0][1]
    assert machine.defaults[OUT] == "hs"
    assert log[-1][0] == "auto"


def test_the_waiting_notice_does_not_promise_more_than_the_code_does(
    qtbot, profile_repo, no_sleep
):
    # Identity is the endpoint id alone, so a device that comes back under a
    # new id is never matched. The notice must say so rather than promise.
    machine = desk_machine()
    desk = save_profile(profile_repo, "Desk", "spk", "hsmic")
    presenter, log = presenter_over(profile_repo, machine)
    presenter.switch_profile(desk.id)

    notice = log[0][1]
    assert "will apply when it reconnects." not in notice
    assert "same device" in notice
