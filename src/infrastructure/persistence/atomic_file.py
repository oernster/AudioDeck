"""Whole-file writes no reader sees half done, with the tolerant read.

A file is written to a temporary file in the same folder, flushed and
fsynced, then moved over the original with os.replace, which is atomic on
every platform Audio Deck runs on. A reader therefore sees the old document
or the new one, never a truncated one. A write that fails part way (a
full disk) leaves the original exactly as it was.

Windows adds one wrinkle, measured rather than assumed: os.replace is refused
with PermissionError while another process holds the target open; a
reader can meet the same refusal at the instant of the replace. Both sides
therefore retry that one error for a short, bounded time, which is how a
Stream Deck read of the profiles and a save in the window coexist.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Callable, TextIO, TypeVar

# A held file is released within milliseconds (a reader parses a small JSON
# document), so a few hundred milliseconds of retries covers it with room to
# spare while still failing promptly if something holds the file for good.
SHARING_ATTEMPTS = 10
SHARING_RETRY_SECONDS = 0.05

_BACKUP_SUFFIX = ".bak"
_TEMPORARY_SUFFIX = ".tmp"

_Result = TypeVar("_Result")


def backup_path(path: Path) -> Path:
    """Return where the last good copy of a file is kept."""
    return path.with_name(path.name + _BACKUP_SUFFIX)


def _retry_while_shared(
    action: Callable[[], _Result], sleep: Callable[[float], object]
) -> _Result:
    """Run an action, retrying a sharing refusal for a bounded time."""
    attempts = 1
    while True:
        try:
            return action()
        except PermissionError:
            if attempts == SHARING_ATTEMPTS:
                raise
            attempts += 1
            sleep(SHARING_RETRY_SECONDS)


def read_tolerantly(path: Path, sleep: Callable[[float], object] = time.sleep) -> str:
    """Read a whole text file, waiting out a replace in progress.

    Args:
        path: The file to read
        sleep: Waits between attempts (injected by tests)

    Returns:
        The file's text
    """
    return _retry_while_shared(lambda: path.read_text(encoding="utf-8"), sleep)


def write_atomically(
    path: Path,
    write: Callable[[TextIO], object],
    sleep: Callable[[float], object] = time.sleep,
) -> None:
    """Replace a file with new content in one atomic step.

    Args:
        path: The file to replace
        write: Writes the whole new content to the handle it is given
        sleep: Waits between replace attempts (injected by tests)

    Raises:
        OSError: If the content cannot be written or moved into place; the
            original file is untouched and no temporary file is left behind
    """
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=_TEMPORARY_SUFFIX
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            write(handle)
            handle.flush()
            os.fsync(handle.fileno())
        _retry_while_shared(lambda: os.replace(temporary_name, path), sleep)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def keep_backup(path: Path, sleep: Callable[[float], object] = time.sleep) -> None:
    """Copy a file's current content to its backup path, atomically.

    Called only with content the caller has just parsed successfully, so the
    backup is always the last good copy. Does nothing when there is no file.

    Args:
        path: The file to back up
        sleep: Waits between attempts (injected by tests)
    """
    if not path.exists():
        return
    content = read_tolerantly(path, sleep)
    write_atomically(backup_path(path), lambda handle: handle.write(content), sleep)
