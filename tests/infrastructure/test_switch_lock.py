"""The per-user lock around a switch, shared by the GUI and the CLI (audit A-9).

Two switches at once used to interleave, leaving a mix of both profiles while
each reported full success. The timing rules are driven over a hand-written
lock fake and a fake clock; the exclusion itself over the platform's real
file lock on a temporary path (no audio device is involved).
"""

import sys
import threading
from pathlib import Path
from typing import List, Optional

import pytest

from src.application.use_cases.switch_profile_use_case import SwitchProfileUseCase
from src.domain.exceptions.domain_exceptions import SwitchInProgressException
from src.domain.value_objects.device_type import DeviceType
from src.infrastructure.backend_factory import create_lock_file_api, create_switch_lock
from src.infrastructure.caching_device_repository import CachingDeviceRepository
from src.infrastructure.switch_lock import (
    SWITCH_LOCK_FILE_NAME,
    SWITCH_LOCK_POLL_SECONDS,
    SWITCH_LOCK_WAIT_SECONDS,
    FileSwitchLock,
)
from tests.conftest import FakeMachine, save_profile

_HANDLE = 3
# Generous ceiling for one thread to reach a point another is waiting on.
_THREAD_TIMEOUT_SECONDS = 10


class FakeLockFileApi:
    """Held for a number of attempts, then free; or unable to lock at all."""

    def __init__(self, held_attempts: int = 0, broken: bool = False) -> None:
        self.held_attempts = held_attempts
        self.broken = broken
        self.attempts = 0
        self.unlocked: List[int] = []

    def try_lock(self, path: Path) -> Optional[int]:
        self.attempts += 1
        if self.broken:
            raise OSError("cannot create the lock file")
        if self.attempts <= self.held_attempts:
            return None
        return _HANDLE

    def unlock(self, handle: int) -> None:
        self.unlocked.append(handle)


class FakeClock:
    """Time moves only when the lock sleeps."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def lock_over(api, tmp_path, clock=None):
    clock = clock or FakeClock()
    return FileSwitchLock(tmp_path / "switch.lock", api, sleep=clock.sleep, clock=clock)


def test_a_lock_held_briefly_is_waited_for(tmp_path):
    api = FakeLockFileApi(held_attempts=2)
    ran = []
    with lock_over(api, tmp_path).hold():
        ran.append(True)
    assert ran == [True]
    assert api.unlocked == [_HANDLE]


def test_a_lock_held_past_the_wait_reports_a_switch_in_progress(tmp_path):
    api = FakeLockFileApi(held_attempts=sys.maxsize)
    clock = FakeClock()
    with pytest.raises(SwitchInProgressException, match="Another switch"):
        with lock_over(api, tmp_path, clock).hold():
            pytest.fail("the switch ran without the lock")
    assert clock.now >= SWITCH_LOCK_WAIT_SECONDS
    assert api.attempts <= SWITCH_LOCK_WAIT_SECONDS / SWITCH_LOCK_POLL_SECONDS + 2


def test_a_lock_file_that_cannot_be_made_does_not_block_the_switch(tmp_path):
    # Fails open, as the single-instance guard does: a lock that cannot be
    # established must never be the reason a Stream Deck key does nothing.
    api = FakeLockFileApi(broken=True)
    ran = []
    with lock_over(api, tmp_path).hold():
        ran.append(True)
    assert ran == [True]
    assert api.unlocked == []


def test_the_lock_is_released_when_the_switch_fails(tmp_path):
    api = FakeLockFileApi()
    with pytest.raises(RuntimeError):
        with lock_over(api, tmp_path).hold():
            raise RuntimeError("switch failed")
    assert api.unlocked == [_HANDLE]


def test_the_platform_lock_excludes_a_second_holder(tmp_path):
    api = create_lock_file_api(sys.platform)
    path = tmp_path / "switch.lock"
    first = api.try_lock(path)
    assert first is not None
    assert api.try_lock(path) is None
    api.unlock(first)
    again = api.try_lock(path)
    assert again is not None
    api.unlock(again)


def test_two_switches_at_once_run_one_after_the_other(profile_repo, tmp_path, no_sleep):
    machine = FakeMachine()
    for device_id, device_type in (
        ("s1", DeviceType.OUTPUT),
        ("s2", DeviceType.OUTPUT),
        ("m1", DeviceType.INPUT),
        ("m2", DeviceType.INPUT),
    ):
        machine.add(device_id, device_type)
    first = save_profile(profile_repo, "P1", "s1", "m1")
    second = save_profile(profile_repo, "P2", "s2", "m2")
    lock_path = tmp_path / SWITCH_LOCK_FILE_NAME
    first_inside, release_first, second_waiting = (threading.Event() for _ in "abc")

    class HoldsTheFirstSet:
        def set_default_device(self, device_id, device_type):
            if device_id == "s1":
                first_inside.set()
                release_first.wait(_THREAD_TIMEOUT_SECONDS)
            machine.set_default_device(device_id, device_type)

        def refresh_devices(self):
            pass

    def second_sleeps(seconds):
        second_waiting.set()
        threading.Event().wait(seconds)

    def switch(profile, controller, lock):
        use_case = SwitchProfileUseCase(
            profile_repo, CachingDeviceRepository(machine), controller, lock
        )
        outcomes[profile.name] = use_case.execute(profile.id)

    outcomes = {}
    platform_api = create_lock_file_api(sys.platform)
    first_lock = create_switch_lock(sys.platform, tmp_path)
    second_lock = FileSwitchLock(lock_path, platform_api, sleep=second_sleeps)
    threads = [
        threading.Thread(target=switch, args=(first, HoldsTheFirstSet(), first_lock)),
        threading.Thread(target=switch, args=(second, machine, second_lock)),
    ]
    threads[0].start()
    assert first_inside.wait(_THREAD_TIMEOUT_SECONDS)
    threads[1].start()
    assert second_waiting.wait(_THREAD_TIMEOUT_SECONDS)
    release_first.set()
    for thread in threads:
        thread.join(_THREAD_TIMEOUT_SECONDS)

    assert machine.set_calls == [
        ("s1", DeviceType.OUTPUT),
        ("m1", DeviceType.INPUT),
        ("s2", DeviceType.OUTPUT),
        ("m2", DeviceType.INPUT),
    ]
    assert all(outcome.fully_applied for outcome in outcomes.values())
