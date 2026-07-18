"""A single background thread for running blocking work off the GUI thread.

Device enumeration (COM) and profile switching (which includes settle sleeps)
are slow, so they must never run on the GUI thread. Callables submitted here run
serially on one worker thread; the presenter methods they call emit Qt signals
that are delivered back to the GUI thread by queued connections.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, QThread, Signal, Slot


class _Worker(QObject):
    """Runs submitted callables on the thread it lives on."""

    @Slot(object)
    def _run(self, task: Callable[[], None]) -> None:
        try:
            task()
        except Exception:
            # Background tasks must never crash the worker thread.
            pass


class BackgroundRunner(QObject):
    """Submits callables to a dedicated serial worker thread."""

    _task = Signal(object)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Start the worker thread.

        Args:
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self._thread = QThread()
        self._worker = _Worker()
        self._worker.moveToThread(self._thread)
        self._task.connect(self._worker._run)
        self._thread.start()

    def submit(self, fn: Callable[..., Any], *args: Any) -> None:
        """Run fn(*args) on the worker thread.

        Args:
            fn: The callable to run.
            args: Positional arguments for the callable.
        """
        self._task.emit(lambda: fn(*args))

    def stop(self) -> None:
        """Stop the worker thread and wait for it to finish."""
        self._thread.quit()
        self._thread.wait()
