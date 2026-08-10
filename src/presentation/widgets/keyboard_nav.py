"""One explicit keyboard focus ring for the main window.

Tab and the Right arrow step the ring forward; Shift+Tab and Left step it
back; the ring wraps at both ends and is recomputed live on each move, so
rebuilt pages and disabled controls are handled. The tab strip is one stop
PER TAB (a NavTabBar), a data list is one stop whose items are walked with
Up and Down, a closed combo box drops open on Down instead of silently
changing value and Enter clicks the focused button. Text inputs keep their
horizontal arrows for the caret.

Installed as one application-level event filter, inert while a modal dialog
is up (the modal owns its own focus) or while the window is inactive.
"""

from __future__ import annotations

import enum
from typing import Callable, List, Optional, Tuple, cast

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLayout,
    QLayoutItem,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QToolButton,
    QWidget,
)

from src.presentation.widgets.nav_tab_bar import NavTabBar

_FORWARD = 1
_BACKWARD = -1


class _Kind(enum.Enum):
    """What a ring stop is, which decides its internal keys."""

    STRIP = enum.auto()
    LIST = enum.auto()
    WIDGET = enum.auto()


_Stop = Tuple[_Kind, QWidget]


class KeyboardNavigator(QObject):
    """Drives the explicit focus ring from one application event filter.

    Args:
        window: The main window whose central widget carries the ring.
        active_modal: Returns the active modal widget; a seam for tests.
        window_is_active: Returns whether the window is active; a seam for
            tests, since offscreen activation is unreliable.
    """

    def __init__(
        self,
        window: QMainWindow,
        active_modal: Optional[Callable[[], Optional[QWidget]]] = None,
        window_is_active: Optional[Callable[[], bool]] = None,
    ) -> None:
        super().__init__(window)
        self._window = window
        self._active_modal = active_modal or QApplication.activeModalWidget
        self._window_is_active = window_is_active or window.isActiveWindow
        application = QApplication.instance()
        # The window exists, so the application exists.
        application.installEventFilter(self)  # type: ignore[union-attr]

    # -- Ring collection ---------------------------------------------------

    def _stops(self) -> List[_Stop]:
        """Collect the ring's stops in reading order, live."""
        out: List[_Stop] = []
        central = self._window.centralWidget()
        if central is not None:
            self._walk(central, out)
        return out

    def _walk(self, widget: QWidget, out: List[_Stop]) -> None:
        """Walk one widget, appending its stops in reading order."""
        if not widget.isVisible():
            return
        if isinstance(widget, NavTabBar):
            out.append((_Kind.STRIP, widget))
            return
        if isinstance(widget, QTabWidget):
            self._walk(widget.tabBar(), out)
            corner = widget.cornerWidget(Qt.Corner.TopRightCorner)
            if corner is not None:
                self._walk(corner, out)
            current = widget.currentWidget()
            if current is not None:
                self._walk(current, out)
            return
        if isinstance(widget, QListWidget):
            if widget.isEnabled():
                out.append((_Kind.LIST, widget))
            return
        if isinstance(widget, (QPushButton, QToolButton, QComboBox, QLineEdit)):
            if widget.isEnabled():
                out.append((_Kind.WIDGET, widget))
            return
        self._walk_children(widget, out)

    def _walk_children(self, widget: QWidget, out: List[_Stop]) -> None:
        """Descend a container in layout order, falling back to child order."""
        layout = widget.layout()
        if layout is not None:
            self._walk_layout(layout, out)
            return
        for child in widget.children():
            if isinstance(child, QWidget):
                self._walk(child, out)

    def _walk_layout(self, layout: "QLayout", out: List[_Stop]) -> None:
        """Walk a layout's items in their declared order."""
        for position in range(layout.count()):
            # itemAt never returns None for an index inside count().
            item = cast("QLayoutItem", layout.itemAt(position))
            child_widget = item.widget()
            if child_widget is not None:
                self._walk(child_widget, out)
                continue
            child_layout = item.layout()
            if child_layout is not None:
                self._walk_layout(child_layout, out)

    # -- Key handling ------------------------------------------------------

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        """Drive the ring; every handled key is consumed."""
        if event.type() != QEvent.Type.KeyPress:
            return False
        if self._active_modal() is not None:
            return False
        if not self._window_is_active():
            return False

        key_event = cast(QKeyEvent, event)
        key = key_event.key()
        # The ring belongs to this window, so its own focus widget is the
        # authority (the application-global one is unset while inactive).
        focus = self._window.focusWidget()

        # Text inputs keep their horizontal arrows for the caret.
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right) and isinstance(focus, QLineEdit):
            return False

        shift = bool(key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        if key == Qt.Key.Key_Backtab or (key == Qt.Key.Key_Tab and shift):
            return self._step(_BACKWARD)
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Right):
            return self._step(_FORWARD)
        if key == Qt.Key.Key_Left:
            return self._step(_BACKWARD)

        return self._handle_internal_key(key, focus)

    def _handle_internal_key(self, key: int, focus: Optional[QWidget]) -> bool:
        """Keys that act INSIDE the focused stop rather than on the ring."""
        if isinstance(focus, NavTabBar):
            if key == Qt.Key.Key_Down:
                focus.step_cursor_wrapping(_FORWARD)
                return True
            if key == Qt.Key.Key_Up:
                focus.step_cursor_wrapping(_BACKWARD)
                return True
            return False

        if isinstance(focus, QComboBox) and not focus.view().isVisible():
            # A closed dropdown drops open on Down; Up must not silently
            # change the value either.
            if key == Qt.Key.Key_Down:
                focus.showPopup()
                return True
            if key == Qt.Key.Key_Up:
                return True
            return False

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and isinstance(
            focus, (QPushButton, QToolButton)
        ):
            # Enter equals Space: Qt only wires Return to buttons inside
            # dialogs (autoDefault), so the main window does it here.
            focus.click()
            return True

        return False

    # -- Stepping ----------------------------------------------------------

    def _index_of_focus(
        self, stops: List[_Stop], focus: Optional[QWidget]
    ) -> Optional[int]:
        """Find which stop holds the focus, if any."""
        if focus is None:
            return None
        for position, (_kind, widget) in enumerate(stops):
            if widget is focus or widget.isAncestorOf(focus):
                return position
        return None

    def _step(self, delta: int) -> bool:
        """Move the ring one stop, wrapping; consume the key."""
        stops = self._stops()
        if not stops:
            return False

        current = self._index_of_focus(stops, self._window.focusWidget())
        if current is not None:
            kind, widget = stops[current]
            if kind is _Kind.STRIP and isinstance(widget, NavTabBar):
                if widget.step_cursor(delta):
                    return True
            target_index = (current + delta) % len(stops)
        else:
            target_index = 0 if delta > 0 else len(stops) - 1

        kind, widget = stops[target_index]
        if kind is _Kind.STRIP and isinstance(widget, NavTabBar):
            widget.enter_cursor(delta)
        widget.setFocus(Qt.FocusReason.TabFocusReason)
        return True
