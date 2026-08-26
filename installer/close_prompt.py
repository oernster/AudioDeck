"""Ask the user to close a running application before its files are replaced.

Windows holds a running executable with an image mapping that denies write
sharing, so deploying over it fails on the first file with a bare permission
error naming a path, while the progress bar stops at its first step. Asking
first turns that into a choice the user can act on.

Kept apart from the installer window because it is one self-contained
exchange with the user, complete with its own outcomes, rather than part of
building or driving that window.
"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from installer import constants as c
from installer import running_app

# Reports progress to the caller's status line.
StatusReporter = Callable[[str], None]


def clear_running_app(
    parent: QWidget,
    report: StatusReporter,
    is_running: Optional[Callable[[], bool]] = None,
    close_and_confirm: Optional[Callable[[], bool]] = None,
) -> bool:
    """Make sure the application is not running, offering to close it.

    Args:
        parent: Widget owning the message boxes.
        report: Writes a line to the window's status text.
        is_running: Running check, injected by the tests.
        close_and_confirm: Terminate and verify, injected by the tests.

    Returns:
        True when the operation may proceed, False when the user declined or
        the application would not close.
    """
    running = is_running or running_app.is_running
    close = close_and_confirm or running_app.close_and_confirm

    if not running():
        return True

    reply = QMessageBox.question(
        parent,
        f"{c.APP_DISPLAY_NAME} is running",
        f"{c.APP_DISPLAY_NAME} is open; its files cannot be replaced "
        "while it is.\n\nClose it now and continue?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes,
    )
    if reply != QMessageBox.Yes:
        report(f"Close {c.APP_DISPLAY_NAME} first, then try again.")
        return False

    report(f"Closing {c.APP_DISPLAY_NAME}...")
    # The confirm below blocks this thread while it polls, so paint the
    # message first: a frozen window showing the old text is what the user
    # read as a hang in the first place.
    app = QApplication.instance()
    if app is not None:
        app.processEvents()

    if close():
        return True

    QMessageBox.warning(
        parent,
        f"{c.APP_DISPLAY_NAME} is still running",
        f"{c.APP_DISPLAY_NAME} could not be closed. Close it yourself, "
        "including its tray icon, then run this installer again.",
    )
    report(f"{c.APP_DISPLAY_NAME} could not be closed.")
    return False
