"""Single-instance enforcement for the GUI, using a Windows named mutex.

A named mutex is the authoritative lock: creating one that already exists
is a single atomic Win32 call, so two processes racing to start cannot both
believe they are first. The window activation below is best effort on top
of that, so a second launch raises the running window rather than appearing
to do nothing.

This guards the GUI only. The headless CLI path (--profile, --list) must
stay freely runnable, because that is how a Stream Deck button drives the
application; those invocations switch a profile then exit.
"""

from __future__ import annotations

import ctypes
from typing import Optional, Protocol

# Win32: CreateMutexW sets this as the last error when the named mutex
# already exists, which means another instance owns it.
ERROR_ALREADY_EXISTS = 183

# Win32 ShowWindow command: restore a minimized window to its former size.
SW_RESTORE = 9

# A handle value of zero is the Win32 convention for failure.
_NULL_HANDLE = 0


class MutexApi(Protocol):
    """The slice of the Win32 mutex API this module needs."""

    def create_mutex(self, name: str) -> int:
        """Create or open the named mutex, returning a handle (0 on failure)."""
        ...

    def last_error(self) -> int:
        """Return the calling thread's last Win32 error code."""
        ...

    def close_handle(self, handle: int) -> None:
        """Release a handle previously returned by create_mutex."""
        ...


class WindowApi(Protocol):
    """The slice of the Win32 window API this module needs."""

    def find_window(self, title: str) -> int:
        """Return the handle of a top-level window by title (0 if absent)."""
        ...

    def is_minimized(self, handle: int) -> bool:
        """Return True if the window is currently minimized."""
        ...

    def restore(self, handle: int) -> None:
        """Restore a minimized window to its former size."""
        ...

    def bring_to_front(self, handle: int) -> bool:
        """Give the window foreground focus, returning True on success."""
        ...


class Win32MutexApi:  # pragma: no cover
    """Real Win32 mutex calls, kept behind MutexApi so the logic is testable."""

    def create_mutex(self, name: str) -> int:
        """Create or open the named mutex via kernel32."""
        return int(ctypes.windll.kernel32.CreateMutexW(None, False, name))

    def last_error(self) -> int:
        """Return the calling thread's last Win32 error code."""
        return int(ctypes.windll.kernel32.GetLastError())

    def close_handle(self, handle: int) -> None:
        """Close a kernel handle."""
        ctypes.windll.kernel32.CloseHandle(handle)


class Win32WindowApi:  # pragma: no cover
    """Real Win32 window calls, kept behind WindowApi so the logic is testable."""

    def find_window(self, title: str) -> int:
        """Find a top-level window by its exact title."""
        return int(ctypes.windll.user32.FindWindowW(None, title))

    def is_minimized(self, handle: int) -> bool:
        """Return True if the window is minimized."""
        return bool(ctypes.windll.user32.IsIconic(handle))

    def restore(self, handle: int) -> None:
        """Restore a minimized window."""
        ctypes.windll.user32.ShowWindow(handle, SW_RESTORE)

    def bring_to_front(self, handle: int) -> bool:
        """Bring the window to the foreground."""
        return bool(ctypes.windll.user32.SetForegroundWindow(handle))


class SingleInstanceGuard:
    """Holds a named mutex for as long as this process owns the GUI.

    The handle is deliberately kept open for the lifetime of the process:
    Windows releases the name only when the last handle to it closes, so
    releasing early would let a second instance start.
    """

    def __init__(self, name: str, mutex_api: MutexApi) -> None:
        """Initialize the guard.

        Args:
            name: The mutex name, including its namespace prefix
            mutex_api: The Win32 mutex calls to use
        """
        self._name = name
        self._mutex_api = mutex_api
        self._handle: Optional[int] = None

    def acquire(self) -> bool:
        """Try to become the single running instance.

        Fails open: if Windows refuses to create the mutex at all, the
        application still starts. A guard that cannot be established must
        never be the reason the application will not run.

        Returns:
            True if this process may proceed, False if another instance owns
            the mutex
        """
        handle = self._mutex_api.create_mutex(self._name)

        if handle == _NULL_HANDLE:
            return True

        if self._mutex_api.last_error() == ERROR_ALREADY_EXISTS:
            self._mutex_api.close_handle(handle)
            return False

        self._handle = handle
        return True

    def release(self) -> None:
        """Close the mutex handle, allowing a later instance to start.

        Windows would do this on process exit anyway; calling it explicitly
        keeps the ownership window tied to the application's lifetime rather
        than to interpreter teardown.
        """
        if self._handle is not None:
            self._mutex_api.close_handle(self._handle)
            self._handle = None


def activate_existing_window(title: str, window_api: WindowApi) -> bool:
    """Raise the already-running instance's window.

    Args:
        title: The exact window title to look for
        window_api: The Win32 window calls to use

    Returns:
        True if a window was found and brought to the foreground
    """
    handle = window_api.find_window(title)

    if handle == _NULL_HANDLE:
        return False

    if window_api.is_minimized(handle):
        window_api.restore(handle)

    return window_api.bring_to_front(handle)
