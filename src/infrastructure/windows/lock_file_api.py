"""Windows file locking for the switch lock, over msvcrt byte locks.

Measured on Windows 11: a byte another descriptor holds refuses LK_NBLCK with
PermissionError, errno EACCES; once released it can be taken. The lock file
itself is never read or written, so one locked byte past its end is enough.
"""

from __future__ import annotations

import errno
import os
from pathlib import Path
from typing import Optional

from src.infrastructure.lock_file_api import LOCK_FILE_MODE

# One byte at offset zero is the whole lock.
_LOCKED_BYTES = 1


def lock_is_held(error: OSError) -> bool:
    """Say whether a failed non-blocking msvcrt lock means another holder.

    Args:
        error: The error msvcrt.locking raised

    Returns:
        True only for EACCES, the refusal a held byte produces
    """
    return error.errno == errno.EACCES


class MsvcrtLockFileApi:  # pragma: no cover
    """Real msvcrt calls, behind LockFileApi so the callers are testable.

    Windows only: msvcrt does not exist elsewhere, so the import is deferred
    to the calls.
    """

    def try_lock(self, path: Path) -> Optional[int]:
        """Open the lock file and take its first byte without blocking."""
        import msvcrt

        descriptor = os.open(path, os.O_RDWR | os.O_CREAT, LOCK_FILE_MODE)
        try:
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, _LOCKED_BYTES)
        except OSError as error:
            os.close(descriptor)
            if lock_is_held(error):
                return None
            raise
        return descriptor

    def unlock(self, handle: int) -> None:
        """Release the byte and close the descriptor."""
        import msvcrt

        try:
            msvcrt.locking(handle, msvcrt.LK_UNLCK, _LOCKED_BYTES)
        finally:
            os.close(handle)
