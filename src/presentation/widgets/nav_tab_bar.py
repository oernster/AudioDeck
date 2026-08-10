"""A tab bar where every tab is its own ring stop.

Qt ties a QTabBar's focus to its CURRENT tab, so a plainly focused bar can
only ring the tab the user is already on, a dead stop. This bar carries a
cursor of its own, painted as the green ring around the cursor tab, and
commits a page switch only on Enter or Space, so walking the strip never
changes the page under the user.

Tab and Shift+Tab (and the horizontal arrows) walk the tabs BOUNDED: when
the strip runs out in that direction the walk reports it, which is the outer
ring's cue to move on. Up and Down walk the same tabs wrapping, as a
convenience.
"""

from __future__ import annotations

from typing import Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFocusEvent, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import QTabBar

from src.presentation.widgets.ring_walk import next_candidate, next_candidate_bounded

# The green ring token, matching the application stylesheet's.
RING_GREEN = "#a6e3a1"
_RING_WIDTH_PX = 2
_RING_RADIUS_PX = 5

_COMMIT_KEYS = (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space)


class NavTabBar(QTabBar):
    """Tab bar with an independent keyboard cursor, one ring stop per tab."""

    def __init__(self) -> None:
        """Initialize with no cursor and strong focus."""
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._cursor: Optional[int] = None
        self._show_ring = False

    def _skip_indices(self) -> Set[int]:
        """Indices the cursor never lands on: disabled or hidden tabs."""
        return {
            index
            for index in range(self.count())
            if not (self.isTabEnabled(index) and self.isTabVisible(index))
        }

    def cursor_index(self) -> Optional[int]:
        """Return the cursor's current tab index, None when outside."""
        return self._cursor

    def enter_cursor(self, delta: int) -> None:
        """Place the cursor at the edge the ring arrives from.

        Args:
            delta: +1 entering forward (leftmost tab), -1 backward (rightmost)
        """
        start = -1 if delta > 0 else self.count()
        self._cursor = next_candidate_bounded(
            self.count(), start, delta, self._skip_indices()
        )
        self.update()

    def step_cursor(self, delta: int) -> bool:
        """Step the cursor one tab without wrapping.

        Returns:
            True if the cursor moved; False when the strip has run out in
            that direction, the outer ring's cue to move on.
        """
        if self._cursor is None:
            return False
        stepped = next_candidate_bounded(
            self.count(), self._cursor, delta, self._skip_indices()
        )
        if stepped is None:
            self._cursor = None
            self.update()
            return False
        self._cursor = stepped
        self.update()
        return True

    def step_cursor_wrapping(self, delta: int) -> None:
        """Step the cursor one tab, wrapping (the Up/Down convenience)."""
        start = self._cursor if self._cursor is not None else -1
        self._cursor = next_candidate(
            self.count(), start, delta, self._skip_indices()
        )
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Commit the cursor tab on Enter or Space; swallow the arrows.

        The navigator drives all cursor movement; the bar itself must not
        let Qt's own left/right tab-switching run, or walking the strip
        would change the page under the user.
        """
        if event.key() in _COMMIT_KEYS and self._cursor is not None:
            self.setCurrentIndex(self._cursor)
            event.accept()
            return
        event.accept()

    def focusInEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        """Show the ring; seed the cursor if the ring has not placed it."""
        super().focusInEvent(event)
        self._show_ring = True
        if self._cursor is None:
            self._cursor = self.currentIndex() if self.count() else None
        self.update()

    def focusOutEvent(self, event: QFocusEvent) -> None:  # noqa: N802
        """Hide the ring and drop the cursor."""
        super().focusOutEvent(event)
        self._show_ring = False
        self._cursor = None
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        """Paint the tabs, then the green ring around the cursor tab."""
        super().paintEvent(event)
        if not self._show_ring or self._cursor is None:
            return
        rect = self.tabRect(self._cursor)
        if rect.isNull():
            return
        painter = QPainter(self)
        pen = QPen(QColor(RING_GREEN))
        pen.setWidth(_RING_WIDTH_PX)
        painter.setPen(pen)
        inset = _RING_WIDTH_PX // 2 + 1
        painter.drawRoundedRect(
            rect.adjusted(inset, inset, -inset, -inset),
            _RING_RADIUS_PX,
            _RING_RADIUS_PX,
        )
        painter.end()
