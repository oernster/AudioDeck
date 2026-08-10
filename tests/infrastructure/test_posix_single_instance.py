"""Tests for the POSIX lock-file single-instance guard."""

from pathlib import Path
from typing import Optional

import pytest

from src.infrastructure.posix.single_instance import (
    PosixSingleInstanceGuard,
    default_lock_path,
)

_LOCK_PATH = Path("/tmp/audiodeck-test.lock")
_HANDLE = 7


class FakeLockFileApi:
    """Hand-written fake of the file-locking calls."""

    def __init__(
        self, handle: Optional[int] = _HANDLE, raise_os_error: bool = False
    ) -> None:
        self.handle = handle
        self.raise_os_error = raise_os_error
        self.locked_paths: list[Path] = []
        self.unlocked_handles: list[int] = []

    def try_lock(self, path: Path) -> Optional[int]:
        if self.raise_os_error:
            raise OSError("cannot create lock file")
        self.locked_paths.append(path)
        return self.handle

    def unlock(self, handle: int) -> None:
        self.unlocked_handles.append(handle)


def test_acquire_succeeds_when_lock_is_free():
    api = FakeLockFileApi()
    guard = PosixSingleInstanceGuard(_LOCK_PATH, api)
    assert guard.acquire() is True
    assert api.locked_paths == [_LOCK_PATH]


def test_acquire_fails_when_another_instance_holds_the_lock():
    guard = PosixSingleInstanceGuard(_LOCK_PATH, FakeLockFileApi(handle=None))
    assert guard.acquire() is False


def test_acquire_fails_open_when_the_lock_file_cannot_be_created():
    guard = PosixSingleInstanceGuard(_LOCK_PATH, FakeLockFileApi(raise_os_error=True))
    assert guard.acquire() is True


def test_release_unlocks_the_held_handle():
    api = FakeLockFileApi()
    guard = PosixSingleInstanceGuard(_LOCK_PATH, api)
    guard.acquire()
    guard.release()
    assert api.unlocked_handles == [_HANDLE]


def test_release_without_a_held_handle_is_a_no_op():
    api = FakeLockFileApi(handle=None)
    guard = PosixSingleInstanceGuard(_LOCK_PATH, api)
    guard.acquire()
    guard.release()
    assert api.unlocked_handles == []


def test_default_lock_path_prefers_the_xdg_runtime_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    assert default_lock_path() == tmp_path / "audiodeck.gui.lock"


def test_default_lock_path_falls_back_to_a_per_user_temp_name(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    path = default_lock_path()
    assert path.name.startswith("audiodeck-")
    assert path.name.endswith(".gui.lock")
