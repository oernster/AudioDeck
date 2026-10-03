"""A switch reports what the machine actually did (audit A-2, A-3, A-6, A-8).

The machine is a hand-written fake that is both the enumerator and the
controller, so whatever a switch changes is what the next enumeration sees.
"""

import pytest

import src.domain.exceptions.domain_exceptions as errors
from src.application.dtos.switch_outcome import SkipReason
from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from tests.conftest import (
    FakeDeviceController,
    FakeEnumerator,
    FakeMachine,
    make_device,
    save_profile,
)

OUT, IN = DeviceType.OUTPUT, DeviceType.INPUT


def speakers_and_headset() -> FakeMachine:
    machine = FakeMachine()
    machine.add("spk", OUT)
    machine.add("hs", OUT)
    machine.add("mic", IN)
    machine.defaults[OUT] = "spk"
    return machine


def switch_over(profile_repo, machine, controller=None):
    return SwitchProfileUseCase(
        profile_repo, CachingDeviceRepository(machine), controller or machine
    )


def reasons(outcome):
    return [(skip.device_type, skip.reason) for skip in outcome.skipped]


def test_a_switch_the_system_ignores_is_not_reported_as_applied(profile_repo, no_sleep):
    machine = speakers_and_headset()
    machine.ignore_sets = True
    profile = save_profile(profile_repo, "Headset", "hs", None)

    outcome = switch_over(profile_repo, machine).execute(profile.id)

    assert outcome.applied == ()
    assert reasons(outcome) == [(OUT, SkipReason.DID_NOT_TAKE)]


def test_a_switch_that_lands_is_confirmed(profile_repo, no_sleep):
    machine = speakers_and_headset()
    profile = save_profile(profile_repo, "Headset", "hs", "mic")

    outcome = switch_over(profile_repo, machine).execute(profile.id)

    assert set(outcome.applied) == {OUT, IN}
    assert outcome.fully_applied


def test_a_default_that_cannot_be_read_back_is_not_called_a_mismatch(
    profile_repo, no_sleep
):
    # No device is marked default, so the read-back cannot tell either way;
    # the call's own success stands rather than a guessed failure.
    devices = [make_device("hs", "Headset", OUT, is_default=False)]
    repository = CachingDeviceRepository(FakeEnumerator(devices))
    profile = save_profile(profile_repo, "Headset", "hs", None)

    outcome = SwitchProfileUseCase(
        profile_repo, repository, FakeDeviceController()
    ).execute(profile.id)

    assert outcome.applied == (OUT,)


class _ReadsOnceThenFails:
    """Answers the switch's first enumeration, then cannot read devices."""

    def __init__(self, machine: FakeMachine) -> None:
        self._machine = machine
        self.reads = 0

    def get_all_devices(self):
        self.reads += 1
        if self.reads > 1:
            raise errors.DeviceEnumerationException("Could not read the audio devices")
        return self._machine.get_all_devices()


def test_a_read_back_that_fails_keeps_what_the_system_accepted(profile_repo, no_sleep):
    machine = speakers_and_headset()
    enumerator = _ReadsOnceThenFails(machine)
    repository = CachingDeviceRepository(enumerator, auto_refresh=False)
    profile = save_profile(profile_repo, "Headset", "hs", None)

    outcome = SwitchProfileUseCase(profile_repo, repository, machine).execute(
        profile.id
    )

    assert outcome.applied == (OUT,)
    assert enumerator.reads == 2


def test_a_device_gone_by_the_time_of_the_set_waits_for_reconnection(
    profile_repo, no_sleep
):
    machine = speakers_and_headset()
    controller = FakeDeviceController(
        error=errors.DeviceNotFoundException("not present")
    )
    profile = save_profile(profile_repo, "Headset", "hs", None)

    outcome = switch_over(profile_repo, machine, controller).execute(profile.id)

    assert reasons(outcome) == [(OUT, SkipReason.UNAVAILABLE)]


class _MissesCommunications:
    """Sets the default, then reports the Communications role refused."""

    def __init__(self, machine: FakeMachine) -> None:
        self._machine = machine

    def set_default_device(self, device_id, device_type):
        self._machine.set_default_device(device_id, device_type)
        raise errors.PartialDeviceControlException(("Communications",))

    def refresh_devices(self):
        pass


def test_a_device_set_for_only_some_roles_names_the_roles_it_missed(
    profile_repo, no_sleep
):
    machine = speakers_and_headset()
    profile = save_profile(profile_repo, "Headset", "hs", None)

    outcome = switch_over(
        profile_repo, machine, _MissesCommunications(machine)
    ).execute(profile.id)

    assert outcome.applied == (OUT,)
    assert not outcome.fully_applied
    assert reasons(outcome) == [(OUT, SkipReason.PARTIALLY_SET)]
    assert outcome.skipped[0].detail == "Communications"


def test_devices_that_cannot_be_read_stop_the_switch_with_that_reason(
    profile_repo, no_sleep
):
    failure = errors.DeviceEnumerationException("Could not read the audio devices: RPC")
    repository = CachingDeviceRepository(
        FakeEnumerator(error=failure), auto_refresh=False
    )
    profile = save_profile(profile_repo, "Desk", "spk", "mic")

    with pytest.raises(errors.DeviceEnumerationException, match="Could not read"):
        SwitchProfileUseCase(profile_repo, repository, FakeDeviceController()).execute(
            profile.id
        )


def test_a_switch_can_be_limited_to_one_slot(profile_repo, no_sleep):
    machine = speakers_and_headset()
    profile = save_profile(profile_repo, "Desk", "hs", "mic")

    outcome = switch_over(profile_repo, machine).execute(profile.id, slots=(IN,))

    assert machine.set_calls == [("mic", IN)]
    assert outcome.applied == (IN,)
