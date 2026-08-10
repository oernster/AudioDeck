"""Gentle auto-scroll for read-through surfaces.

Long help content (the licence, the documentation viewers) holds still for
a moment when the surface opens, then reads itself down slowly, holds at
the end, rewinds fast and repeats. Any manual reading input suspends the
cycle briefly and it resumes from wherever the reader left it; it is never
switched off. While a modal dialog sits above the surface the cycle is
frozen in place, consuming neither time nor input, and resumes exactly
where it was when the modal closes.

The pace constants are the application's, never per-dialog overrides: if
one surface needs a different pace, the pace is wrong everywhere.
"""

from __future__ import annotations

import enum
from typing import Callable, Optional

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QWidget

# One standard pace for every surface in the application.
TICK_MS = 40
START_HOLD_MS = 5000
DESCENT_TICKS_PER_STEP = 2
DESCENT_STEP_PX = 1
BOTTOM_HOLD_MS = 5000
REWIND_STEP_PX = 15
TOP_HOLD_MS = 2000
MANUAL_RESUME_MS = 2500

# Event types that count as the reader taking hold of the surface.
_MANUAL_EVENT_TYPES = (
    QEvent.Type.Wheel,
    QEvent.Type.MouseButtonPress,
    QEvent.Type.KeyPress,
)


class _Phase(enum.Enum):
    """Where the cycle currently is."""

    DOWN = enum.auto()
    PAUSE_BOTTOM = enum.auto()
    UP = enum.auto()
    PAUSE_TOP = enum.auto()
    MANUAL = enum.auto()


class AutoScroller(QObject):
    """Reads a scrollable surface down slowly, forever, unless the user is.

    Args:
        area: The scroll surface to drive; also becomes the Qt parent, so
            the surface owns the scroller's lifetime.
        active_modal: Returns the application's active modal widget; a seam
            so tests can freeze the surface without mocking Qt.
    """

    def __init__(
        self,
        area: QAbstractScrollArea,
        active_modal: Optional[Callable[[], Optional[QWidget]]] = None,
    ) -> None:
        super().__init__(area)
        self._area = area
        self._bar = area.verticalScrollBar()
        self._active_modal = active_modal or QApplication.activeModalWidget

        # The cycle opens holding still: PAUSE_TOP seeded with the start
        # hold, which only counts down once content actually overflows.
        self._phase = _Phase.PAUSE_TOP
        self._wait_ms = START_HOLD_MS
        self._in_start_hold = True
        self._descent_countdown = DESCENT_TICKS_PER_STEP

        area.installEventFilter(self)
        area.viewport().installEventFilter(self)
        self._bar.sliderPressed.connect(self._suspend)
        self._bar.sliderReleased.connect(self._suspend)
        self._bar.sliderMoved.connect(self._suspend)
        # The surface exists, so the application exists; the instance cannot
        # be None here.
        QApplication.instance().focusChanged.connect(  # type: ignore[union-attr]
            self._on_focus_changed
        )

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_MS)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        """Suspend on wheel, click or key on the surface or its viewport."""
        if event.type() in _MANUAL_EVENT_TYPES:
            self._suspend()
        return False

    def _on_focus_changed(self, old: Optional[QWidget], new: Optional[QWidget]) -> None:
        """Suspend when keyboard focus enters the surface or any child."""
        if new is None:
            return
        if new is self._area or self._area.isAncestorOf(new):
            self._suspend()

    def _is_frozen(self) -> bool:
        """Return True while an unrelated modal sits above the surface."""
        modal = self._active_modal()
        if modal is None:
            return False
        return not (modal is self._area.window() or modal.isAncestorOf(self._area))

    def _suspend(self) -> None:
        """Record the reader taking hold; the cycle resumes after stillness.

        A frozen surface has no reader by definition, so nothing reaching it
        counts; and the surface's own opening focus is not a reader, so the
        start hold survives the dialog appearing.
        """
        if self._is_frozen():
            return
        if self._in_start_hold:
            return
        self._phase = _Phase.MANUAL
        self._wait_ms = MANUAL_RESUME_MS

    def _tick(self) -> None:
        """Advance the cycle by one 40ms tick."""
        if self._is_frozen():
            return
        if self._bar.maximum() == 0:
            return
        if self._wait_ms > 0:
            self._wait_ms -= TICK_MS
            if self._wait_ms <= 0:
                self._begin_next_leg()
            return
        # Only DOWN and UP ever run with no wait pending.
        if self._phase is _Phase.DOWN:
            self._step_down()
            return
        self._step_up()

    def _begin_next_leg(self) -> None:
        """Choose the direction after any wait runs out."""
        # The start hold ends the moment its wait is spent, not on the first
        # movement, so a reader arriving between the two is not missed.
        self._in_start_hold = False
        at_bottom = self._bar.value() >= self._bar.maximum()
        if self._phase is _Phase.PAUSE_BOTTOM:
            self._phase = _Phase.UP
        elif self._phase is _Phase.MANUAL and at_bottom:
            # The only way on from the bottom is back up.
            self._phase = _Phase.UP
        else:
            self._phase = _Phase.DOWN
        self._descent_countdown = DESCENT_TICKS_PER_STEP

    def _step_down(self) -> None:
        """The reading pass: one pixel every second tick."""
        self._descent_countdown -= 1
        if self._descent_countdown > 0:
            return
        self._descent_countdown = DESCENT_TICKS_PER_STEP
        self._bar.setValue(self._bar.value() + DESCENT_STEP_PX)
        if self._bar.value() >= self._bar.maximum():
            self._phase = _Phase.PAUSE_BOTTOM
            self._wait_ms = BOTTOM_HOLD_MS

    def _step_up(self) -> None:
        """The rewind: a reposition, not a reading pass, so it travels fast."""
        self._bar.setValue(max(self._bar.value() - REWIND_STEP_PX, 0))
        if self._bar.value() <= 0:
            self._phase = _Phase.PAUSE_TOP
            self._wait_ms = TOP_HOLD_MS
