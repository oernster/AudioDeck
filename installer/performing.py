"""Doing the work, then saying honestly how it went.

Split from the window's shell because the two answer different questions: over
there is what setup looks like on each route, here is what pressing the
go-ahead actually does. Every path through this module ends in one of two
places, a verdict on screen or the application running, so setup can never
finish by quietly doing nothing.

Nothing here reaches for a control it was not given by the window it is mixed
into; the window owns the state and this owns the sequence.

Author: Oliver Ernster
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QTimer

from installer import constants as c
from installer import ops, running_app, screens, wording
from installer.footer import PRIMARY, Action
from installer.worker import InstallerWorker, ProgressCallback

TICK = "✓"
ALERT = "⚠"

# Delay before the window closes itself after launching the application. Any
# value posts the close onto a later turn of the event loop, which is the point;
# a short one also leaves the "Starting..." line readable.
CLOSE_ON_NEXT_TURN_MS = 400

# Upper bound on joining the worker thread while the window closes. The worker
# has finished its work by then and only has to unwind, so this is a guard
# against hanging the close rather than a real wait. A QThread destroyed while
# still running takes the process with it, so the join is never unbounded and
# never skipped.
WORKER_JOIN_TIMEOUT_MS = 5000

# What a finished piece of work does next, given whatever it produced.
Finish = Callable[[Optional[Path]], None]


class Performing:
    """The work half of the setup window, mixed into it."""

    # ------------------------------------------------------------- reporting

    def _working(self, title: str) -> None:
        """Show the progress screen, with no actions offered while it runs."""
        self._progress_title.setText(title)
        self._progress.setValue(0)
        self._progress_status.setText("Starting...")
        self._show_screen(screens.SCREEN_PROGRESS, ())

    def _verdict(self, mark: str, title: str, lead: str) -> None:
        """Show how it ended, with nothing left to do but close."""
        self._verdict_mark.setText(mark)
        self._verdict_title.setText(title)
        self._verdict_lead.setText(lead)
        self._show_screen(
            screens.SCREEN_VERDICT, (Action("Close", self.close, PRIMARY),)
        )

    def _on_progress(self, percent: int, message: str) -> None:
        """Move the bar and say which step is running."""
        self._progress.setValue(percent)
        self._progress_status.setText(message)

    def _on_failed(self, message: str) -> None:
        """Report a step that raised, naming where its trail is written."""
        self.log.write(f"FAILED: {message}")
        self._verdict(
            ALERT,
            wording.FAILED_HEADING,
            f"{message} A step by step log is at {self.log.path}.",
        )

    # --------------------------------------------------------------- guarding

    def _guarded(
        self,
        title: str,
        work: Callable[[ProgressCallback], Optional[Path]],
        finish: Finish,
    ) -> None:
        """Run the work once nothing is holding the application's files open.

        Extracting over a locked executable raises partway through, leaving a
        half written install, so this is asked BEFORE any file is touched
        rather than discovered halfway.

        Args:
            title: What the progress screen is titled while this runs.
            work: The work itself, taking a progress callback.
            finish: What to do with whatever the work produced.
        """
        if not running_app.is_running():
            self._start(title, work, finish)
            return
        self.log.write("the application is running")
        self._running_heading.setText(wording.RUNNING_HEADING)
        self._running_lead.setText(wording.RUNNING_LEAD)
        self._show_screen(
            screens.SCREEN_RUNNING,
            (
                Action("Cancel", self._show_current),
                Action(
                    "Close it and continue",
                    lambda: self._close_then(title, work, finish),
                    PRIMARY,
                ),
            ),
        )

    def _close_then(
        self,
        title: str,
        work: Callable[[ProgressCallback], Optional[Path]],
        finish: Finish,
    ) -> None:
        """Close the running application, then carry on with what was asked."""
        self._working(f"Closing {c.APP_DISPLAY_NAME}")
        self._on_progress(0, "Waiting for it to close...")
        if not running_app.close_and_confirm():
            self.log.write("the application would not close")
            self._verdict(
                ALERT, wording.STILL_RUNNING_HEADING, wording.STILL_RUNNING_LEAD
            )
            return
        self.log.write("the application was closed")
        self._start(title, work, finish)

    # ------------------------------------------------------------------ work

    def _start(
        self,
        title: str,
        work: Callable[[ProgressCallback], Optional[Path]],
        finish: Finish,
    ) -> None:
        """Show the progress screen and run the work on the worker thread."""
        self._working(title)
        self._finish = finish
        self._worker = InstallerWorker(work)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _write_files(self, reinstalling: bool = False) -> None:
        """Install, update, go back or reinstall, whichever this run is for."""
        self.log.write(f"writing files, reinstalling: {reinstalling}")
        self._guarded(
            wording.working_title(self.route, reinstalling),
            functools.partial(
                ops.deploy,
                self._desktop.isChecked(),
                self._start_menu.isChecked(),
            ),
            functools.partial(self._installed, reinstalling=reinstalling),
        )

    def _repair(self) -> None:
        """Put the files back, leaving every other choice as it stands."""
        self.log.write("repairing")
        self._guarded(
            f"Repairing {c.APP_DISPLAY_NAME}",
            functools.partial(
                ops.repair,
                self._desktop.isChecked(),
                self._start_menu.isChecked(),
            ),
            self._repaired,
        )

    def _remove(self) -> None:
        """Remove the application, then say what was and was not taken."""
        self.log.write("removing")
        self._guarded(f"Removing {c.APP_DISPLAY_NAME}", ops.uninstall, self._removed)

    # ---------------------------------------------------------------- finish

    def _on_finished(self, result: object) -> None:
        """Hand whatever the work produced to the finish it was started with."""
        self._finish(result if isinstance(result, Path) else None)

    def _installed(
        self, executable: Optional[Path], reinstalling: bool = False
    ) -> None:
        """Report a finished install, then start the application if asked."""
        self.log.write(f"installed {executable}")
        if reinstalling:
            title, lead = wording.REINSTALLED_HEADING, wording.REINSTALLED_LEAD
        else:
            title = f"{c.APP_DISPLAY_NAME} {self.version} is installed"
            lead = wording.installed_lead(
                str(executable.parent) if executable else str(c.install_dir())
            )
        self._launch_or_rest(executable, title, lead)

    def _repaired(self, executable: Optional[Path]) -> None:
        """Report a finished repair."""
        self.log.write("repaired")
        self._launch_or_rest(
            executable, wording.REPAIRED_HEADING, wording.REPAIRED_LEAD
        )

    def _removed(self, _: Optional[Path]) -> None:
        """Report a finished removal; there is nothing left to start."""
        self.log.write("removed")
        self._verdict(TICK, wording.REMOVED_HEADING, wording.REMOVED_LEAD)

    def _launch_or_rest(
        self, executable: Optional[Path], title: str, lead: str
    ) -> None:
        """Show the verdict, then start the application when that was asked.

        The close is posted onto a later turn of the event loop rather than
        called from inside this slot: application shutdown inside a signal
        emission is the state that hung the o7Debrief setup program twice on
        launch-on-finish.
        """
        if executable is None or not self._launch.isChecked():
            self._verdict(TICK, title, lead)
            return
        ops.launch(executable)
        self._verdict(TICK, title, f"{lead} {wording.LAUNCHING_LEAD}")
        QTimer.singleShot(CLOSE_ON_NEXT_TURN_MS, self.close)
