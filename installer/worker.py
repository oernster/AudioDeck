"""Background worker that runs one piece of installer work off the UI thread.

The worker is given the work rather than an operation to look up, so the window
decides what pressing a go-ahead means and this decides only where that runs.
Progress arrives as a signal, so the window is repainted by its own thread
rather than from the one doing the work.

Author: Oliver Ernster
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QThread, Signal

# Reports progress as (percent, message).
ProgressCallback = Callable[[int, str], None]
# One piece of work, returning the installed executable where there is one.
Work = Callable[[ProgressCallback], Optional[Path]]


class InstallerWorker(QThread):
    """Runs one piece of work and reports how it went with signals."""

    progress = Signal(int, str)  # percent, message
    finished_ok = Signal(object)  # installed exe path or None
    failed = Signal(str)  # error message

    def __init__(self, work: Work) -> None:
        """Initialise the worker.

        Args:
            work: The work to run, taking a progress callback.
        """
        super().__init__()
        self._work = work

    def run(self) -> None:
        """Execute the work, reporting either its result or its failure."""
        try:
            self.finished_ok.emit(self._work(self._emit_progress))
        except Exception as error:  # surface any failure to the UI
            self.failed.emit(str(error))

    def _emit_progress(self, percent: int, message: str) -> None:
        """Forward a progress update as a signal."""
        self.progress.emit(percent, message)
