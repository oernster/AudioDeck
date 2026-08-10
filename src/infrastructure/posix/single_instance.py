"""Single-instance enforcement for the GUI on POSIX platforms.

An exclusively flocked lock file is the authoritative lock: the kernel drops
the lock when the owning process exits, so a crash never leaves a stale
guard behind. Unlike Windows, neither Wayland nor macOS lets one process
reliably raise another application's window, so a second GUI launch simply
exits; the activation step is a no-op on these platforms.

This guards the GUI only. The headless CLI path (--profile, --list) must
stay freely runnable, because that is how a Stream Deck button drives the
application; those invocations switch a profile then exit.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Protocol

# Owner read/write only: the lock file lives in a shared directory when
# XDG_RUNTIME_DIR is unset, so it must not be writable by other users.
_LOCK_FILE_MODE = 0o600


def default_lock_path() -> Path:
    """Return the per-user lock file path.

    XDG_RUNTIME_DIR is the per-user runtime directory on Linux; when it is
    absent (macOS, unusual Linux setups) the temp directory is used with the
    user id in the file name, because that directory may be shared.

    Returns:
        Path to the lock file for the current user
    """
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return Path(runtime_dir) / "audiodeck.gui.lock"
    user_id = getattr(os, "getuid", lambda: "user")()
    return Path(tempfile.gettempdir()) / f"audiodeck-{user_id}.gui.lock"


class LockFileApi(Protocol):
    """The slice of the file-locking API this module needs."""

    def try_lock(self, path: Path) -> Optional[int]:
        """Take an exclusive non-blocking lock on the file.

        Returns:
            A handle if the lock was taken, None if another process holds it

        Raises:
            OSError: If the lock file cannot be created at all
        """
        ...

    def unlock(self, handle: int) -> None:
        """Release a handle previously returned by try_lock."""
        ...


class FcntlLockFileApi:  # pragma: no cover
    """Real flock calls, kept behind LockFileApi so the logic is testable.

    POSIX only: the fcntl module does not exist on Windows, so the import
    is deferred to the calls.
    """

    def try_lock(self, path: Path) -> Optional[int]:
        """Open the lock file and take an exclusive non-blocking flock."""
        import fcntl

        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, _LOCK_FILE_MODE)
        try:
            # mypy on Windows sees an empty fcntl stub; the module is real
            # wherever this class actually runs.
            fcntl.flock(  # type: ignore[attr-defined]
                descriptor,
                fcntl.LOCK_EX | fcntl.LOCK_NB,  # type: ignore[attr-defined]
            )
        except OSError:
            os.close(descriptor)
            return None
        return descriptor

    def unlock(self, handle: int) -> None:
        """Close the descriptor, which drops the flock with it."""
        os.close(handle)


class PosixSingleInstanceGuard:
    """Holds a file lock for as long as this process owns the GUI.

    The descriptor is deliberately kept open for the lifetime of the
    process: the kernel releases the lock only when it closes, so releasing
    early would let a second instance start.
    """

    def __init__(self, lock_path: Path, lock_api: LockFileApi) -> None:
        """Initialize the guard.

        Args:
            lock_path: The lock file location
            lock_api: The file-locking calls to use
        """
        self._lock_path = lock_path
        self._lock_api = lock_api
        self._handle: Optional[int] = None

    def acquire(self) -> bool:
        """Try to become the single running instance.

        Fails open: if the lock file cannot be created at all, the
        application still starts. A guard that cannot be established must
        never be the reason the application will not run.

        Returns:
            True if this process may proceed, False if another instance
            holds the lock
        """
        try:
            handle = self._lock_api.try_lock(self._lock_path)
        except OSError:
            return True

        if handle is None:
            return False

        self._handle = handle
        return True

    def release(self) -> None:
        """Drop the lock, allowing a later instance to start.

        The kernel would do this on process exit anyway; calling it
        explicitly keeps the ownership window tied to the application's
        lifetime rather than to interpreter teardown.
        """
        if self._handle is not None:
            self._lock_api.unlock(self._handle)
            self._handle = None
