"""The file-locking seam shared by the single-instance guard and the switch lock.

Each platform supplies one implementation: flock on Linux and macOS, msvcrt
byte locking on Windows. The callers hold only this Protocol, so their rules
(fail open, bounded waits) are tested over hand-written fakes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

# Owner read/write only: a lock file may live in a shared directory, so it
# must not be writable by other users.
LOCK_FILE_MODE = 0o600


class LockFileApi(Protocol):
    """The slice of the file-locking API the lock holders need."""

    def try_lock(self, path: Path) -> Optional[int]:
        """Take an exclusive non-blocking lock on the file.

        Returns:
            A handle if the lock was taken, None if another holder has it

        Raises:
            OSError: If the lock cannot be attempted at all (the file cannot
                be created; the lock call fails for any reason other than
                another holder)
        """
        ...

    def unlock(self, handle: int) -> None:
        """Release a handle previously returned by try_lock."""
        ...
