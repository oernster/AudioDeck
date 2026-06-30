"""Background worker that runs an installer operation off the UI thread."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from installer import ops
from installer.state import Operation


class InstallerWorker(QThread):
    """Runs one operation and reports progress with signals."""

    progress = Signal(int, str)  # percent, message
    finished_ok = Signal(object)  # installed exe path or None
    failed = Signal(str)  # error message

    def __init__(
        self,
        operation: Operation,
        create_desktop: bool = False,
        create_start_menu: bool = False,
    ) -> None:
        """Initialise the worker.

        Args:
            operation: The operation to run.
            create_desktop: Whether to create or restore a Desktop shortcut.
            create_start_menu: Whether to create or restore a Start Menu shortcut.
        """
        super().__init__()
        self._operation = operation
        self._create_desktop = create_desktop
        self._create_start_menu = create_start_menu

    def run(self) -> None:
        """Execute the requested operation."""
        try:
            result: Optional[Path] = ops.run(
                self._operation,
                self._create_desktop,
                self._create_start_menu,
                self._emit_progress,
            )
            self.finished_ok.emit(result)
        except Exception as error:  # surface any failure to the UI
            self.failed.emit(str(error))

    def _emit_progress(self, percent: int, message: str) -> None:
        """Forward a progress update as a signal."""
        self.progress.emit(percent, message)
