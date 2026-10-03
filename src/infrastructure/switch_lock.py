"""The per-user lock held for the length of a switch, by the GUI and the CLI.

Two switches at once (two Stream Deck keys pressed together; a key pressed
while the window switches) would otherwise interleave their calls and leave a
mix of both profiles, each reporting full success. The lock is a file beside
the profiles, so every process run by the same user meets the same one.

A switch that finds the lock taken waits for a bounded time, which covers
any real switch with room to spare, then gives up with a message saying so.
A lock file that cannot be created at all does not stop the switch: like the
single-instance guard, the lock fails open rather than become the reason a
key does nothing.
"""

from __future__ import annotations

import contextlib
import time
from pathlib import Path
from typing import Callable, Iterator, Optional

from src.domain.exceptions.domain_exceptions import SwitchInProgressException
from src.infrastructure.lock_file_api import LockFileApi

SWITCH_LOCK_FILE_NAME = "switch.lock"

# A switch settles for well under a second, so ten seconds only runs out when
# another switch is stuck; polling every 50 ms keeps the hand-over prompt.
SWITCH_LOCK_WAIT_SECONDS = 10.0
SWITCH_LOCK_POLL_SECONDS = 0.05

_BUSY_MESSAGE = (
    "Another switch is still running and did not finish within "
    f"{SWITCH_LOCK_WAIT_SECONDS:g} seconds. Try the profile again in a moment."
)


class FileSwitchLock:
    """Holds an exclusive lock file for the length of one switch."""

    def __init__(
        self,
        path: Path,
        lock_api: LockFileApi,
        sleep: Callable[[float], object] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Initialize the lock.

        Args:
            path: The lock file
            lock_api: The platform's file-locking calls
            sleep: Waits between attempts (injected by tests)
            clock: Reads the time for the bounded wait (injected by tests)
        """
        self._path = path
        self._lock_api = lock_api
        self._sleep = sleep
        self._clock = clock

    @contextlib.contextmanager
    def hold(self) -> Iterator[None]:
        """Hold the lock for the body of a with statement.

        Raises:
            SwitchInProgressException: If another switch keeps the lock past
                the bounded wait
        """
        handle = self._acquire()
        try:
            yield
        finally:
            if handle is not None:
                self._lock_api.unlock(handle)

    def _acquire(self) -> Optional[int]:
        """Take the lock, waiting a bounded time; None when it fails open."""
        deadline = self._clock() + SWITCH_LOCK_WAIT_SECONDS
        while True:
            try:
                handle = self._lock_api.try_lock(self._path)
            except OSError:
                return None
            if handle is not None:
                return handle
            if self._clock() >= deadline:
                raise SwitchInProgressException(_BUSY_MESSAGE)
            self._sleep(SWITCH_LOCK_POLL_SECONDS)
