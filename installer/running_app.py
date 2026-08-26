"""Detect and end a running copy of the application before touching its files.

Windows holds a running executable with an image mapping that denies write
sharing, so extracting the payload over it fails immediately with a bare
``PermissionError`` naming a path. The progress bar stops at its first step and
the user is told nothing they can act on, which is how this presented: an
install that appeared to hang.

The setup program therefore asks first, offers to close the app and only then
deploys.

Two decisions worth keeping. The terminate names the IMAGE only and never
passes ``/t``: that flag ends everything Windows considers descended from the
target, decided from a recorded parent process id; on a machine where the
app is repeatedly killed and restarted the setup program itself can be recorded
as a descendant. It then terminates itself, with no traceback and no crash
report, because a terminate is not a crash. The app starts no children that
need ending, so ``/t`` buys nothing and costs the installer its life. ``/f``
stays, because the app intercepts a window close to minimise to its tray icon
and would otherwise keep its files locked.

Every command runs through an injected callable, so the tests drive real code
against a hand-written fake rather than patching the subprocess module.
"""

from __future__ import annotations

import subprocess
import time
from typing import Callable, Optional, Sequence

from installer import constants as c

# Runs a command and returns its completed process. Injected for testing.
CommandRunner = Callable[[Sequence[str]], "subprocess.CompletedProcess[str]"]

_CREATE_NO_WINDOW = 0x08000000

# tasklist prints this header line when it has nothing to report, so a match
# is confirmed by finding the image name rather than by counting output lines.
_TASKLIST_NO_MATCH = "no tasks"


def _run(command: Sequence[str]) -> "subprocess.CompletedProcess[str]":
    """Run a command with no console window and capture its output."""
    return subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        creationflags=_CREATE_NO_WINDOW,
        check=False,
    )


def is_running(
    exe_name: str = c.APP_EXE_NAME,
    run: Optional[CommandRunner] = None,
) -> bool:
    """Report whether a process with this image name is running.

    Args:
        exe_name: The executable's image name, for example ``AudioDeck.exe``.
        run: Command runner, injected by the tests.

    Returns:
        True when at least one such process is running. A tasklist that cannot
        be run at all returns False: the deploy then fails on the locked file
        as it did before, which is no worse than the state this replaces.
    """
    runner = run or _run
    try:
        result = runner(
            ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/NH", "/FO", "CSV"]
        )
    except OSError:
        return False
    output = (result.stdout or "").strip().lower()
    if not output or _TASKLIST_NO_MATCH in output:
        return False
    return exe_name.lower() in output


def close(
    exe_name: str = c.APP_EXE_NAME,
    run: Optional[CommandRunner] = None,
) -> bool:
    """End every process with this image name.

    Never passes ``/t``: see the module docstring for what that costs.

    Args:
        exe_name: The executable's image name.
        run: Command runner, injected by the tests.

    Returns:
        True when the terminate command itself succeeded. The caller still
        confirms with :func:`wait_until_closed`, because a zero exit says the
        request was accepted rather than that the process has gone.
    """
    runner = run or _run
    try:
        result = runner(["taskkill", "/f", "/im", exe_name])
    except OSError:
        return False
    return result.returncode == 0


def wait_until_closed(
    exe_name: str = c.APP_EXE_NAME,
    run: Optional[CommandRunner] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Poll until the process has gone, else until the bounded wait runs out.

    Args:
        exe_name: The executable's image name.
        run: Command runner, injected by the tests.
        sleep: Sleep function, injected by the tests.

    Returns:
        True when the process is gone, False when it outlasted the wait.
    """
    for attempt in range(c.CLOSE_POLL_COUNT):
        if not is_running(exe_name, run):
            return True
        if attempt < c.CLOSE_POLL_COUNT - 1:
            sleep(c.CLOSE_POLL_DELAY_SECONDS)
    return not is_running(exe_name, run)


def close_and_confirm(
    exe_name: str = c.APP_EXE_NAME,
    run: Optional[CommandRunner] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """End the app and confirm it has actually gone.

    Args:
        exe_name: The executable's image name.
        run: Command runner, injected by the tests.
        sleep: Sleep function, injected by the tests.

    Returns:
        True when nothing with that image name is left running.
    """
    close(exe_name, run)
    return wait_until_closed(exe_name, run, sleep)
