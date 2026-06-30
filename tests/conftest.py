"""Shared fixtures and hand-written test doubles.

No mock libraries are used. Where a real implementation is safe (the JSON
profile repository on a tmp path, the device repository over a fake enumerator)
it is used directly; the Windows COM boundary is replaced with small explicit
fakes so tests never touch real hardware or change system audio.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4

import pytest

from src.domain.entities.audio_device import AudioDevice
from src.domain.entities.audio_profile import AudioProfile
from src.domain.value_objects.device_type import DeviceType
from src.application.dtos.profile_dto import ProfileDTO
from src.infrastructure.persistence.json_profile_repository import (
    JsonProfileRepository,
)
from src.infrastructure.windows.windows_device_repository import (
    WindowsDeviceRepository,
)

# --- Hand-written test doubles ------------------------------------------------


class FakeEnumerator:
    """Stand-in for the COM device enumerator."""

    def __init__(self, devices: Optional[List[AudioDevice]] = None, error=None):
        self._devices = list(devices or [])
        self._error = error

    def get_all_devices(self) -> List[AudioDevice]:
        if self._error is not None:
            raise self._error
        return list(self._devices)


class FakeDeviceController:
    """Records set-default calls; optionally raises a configured error."""

    def __init__(self, error=None):
        self.calls = []
        self.refreshed = False
        self._error = error

    def set_default_device(self, device_id: str, device_type: DeviceType) -> None:
        if self._error is not None:
            raise self._error
        self.calls.append((device_id, device_type))

    def refresh_devices(self) -> None:
        self.refreshed = True


class FakeGetDevicesUseCase:
    """Stub for GetDevicesUseCase used by presenter tests."""

    def __init__(self, default=None, devices=None, error=None):
        self._default = default
        self._devices = devices or []
        self._error = error

    def get_default_device(self, device_type, refresh=True):
        if self._error is not None:
            raise self._error
        return self._default

    def execute(self, device_type=None, refresh=False):
        if self._error is not None:
            raise self._error
        return list(self._devices)


class FakeGetProfilesUseCase:
    """Stub for GetProfilesUseCase used by presenter tests."""

    def __init__(self, profiles=None, by_id=None, error=None):
        self._profiles = profiles or []
        self._by_id = by_id
        self._error = error

    def execute(self):
        if self._error is not None:
            raise self._error
        return list(self._profiles)

    def get_by_id(self, profile_id):
        if isinstance(self._by_id, Exception):
            raise self._by_id
        return self._by_id


class FakeSwitchUseCase:
    """Stub for SwitchProfileUseCase used by presenter and CLI tests."""

    def __init__(self, error=None):
        self.error = error
        self.executed = []

    def execute(self, profile_id):
        if self.error is not None:
            raise self.error
        self.executed.append(profile_id)


class FakeMutateProfileUseCase:
    """Stub for create/update use cases returning a DTO or raising."""

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, *args, **kwargs):
        if self.error is not None:
            raise self.error
        self.calls.append((args, kwargs))
        return self.result


class FakeDeleteProfileUseCase:
    """Stub for DeleteProfileUseCase."""

    def __init__(self, error=None):
        self.error = error
        self.deleted = []

    def execute(self, profile_id):
        if self.error is not None:
            raise self.error
        self.deleted.append(profile_id)


# --- Factories ----------------------------------------------------------------


def make_device(
    device_id="dev-out",
    name="Speakers",
    device_type=DeviceType.OUTPUT,
    is_default=False,
    is_enabled=True,
) -> AudioDevice:
    """Build an AudioDevice for tests."""
    return AudioDevice(device_id, name, device_type, is_default, is_enabled)


def make_profile_dto(
    name="Profile",
    output_device_id: Optional[str] = "dev-out",
    input_device_id: Optional[str] = "dev-in",
) -> ProfileDTO:
    """Build a ProfileDTO for tests."""
    from datetime import datetime

    now = datetime(2024, 1, 1, 0, 0, 0)
    return ProfileDTO(
        id=uuid4(),
        name=name,
        output_device_id=output_device_id,
        input_device_id=input_device_id,
        created_at=now,
        updated_at=now,
    )


def save_profile(
    repository: JsonProfileRepository,
    name="Profile",
    output_device_id: Optional[str] = "dev-out",
    input_device_id: Optional[str] = "dev-in",
) -> AudioProfile:
    """Create and persist an AudioProfile, returning it."""
    profile = AudioProfile(
        id=uuid4(),
        name=name,
        output_device_id=output_device_id,
        input_device_id=input_device_id,
    )
    repository.save(profile)
    return profile


# --- Fixtures -----------------------------------------------------------------


@pytest.fixture
def output_device() -> AudioDevice:
    return make_device("dev-out", "Speakers", DeviceType.OUTPUT, True, True)


@pytest.fixture
def input_device() -> AudioDevice:
    return make_device("dev-in", "Microphone", DeviceType.INPUT, True, True)


@pytest.fixture
def devices(output_device, input_device) -> List[AudioDevice]:
    return [output_device, input_device]


@pytest.fixture
def profile_repo(tmp_path) -> JsonProfileRepository:
    return JsonProfileRepository(tmp_path / "profiles.json")


@pytest.fixture
def device_repo(devices) -> WindowsDeviceRepository:
    return WindowsDeviceRepository(FakeEnumerator(devices))


@pytest.fixture
def no_sleep(monkeypatch):
    """Replace the switch use case's sleeps so tests run fast."""
    import src.application.use_cases.switch_profile_use_case as module

    monkeypatch.setattr(module.time, "sleep", lambda *_: None)
