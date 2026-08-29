"""A picture button is reached by Tab, never left ringed by the mouse.

Measured, not guessed: pressing the donate button left a green rectangle round
it for the rest of the session. The ring rules were innocent (a tray button
paints nothing at rest and 636 ring pixels when focused, in both themes) and so
was the artwork, which carries four green-dominant pixels in 61,000. The cause
was the focus policy: Qt gives a push button STRONG focus, so the click that
opened the browser focused it; nothing in the window ever took the focus back.

The ring says where the KEYBOARD is, so the mouse must not set it. Every header
and form picture button therefore takes TAB focus only, which leaves the
keyboard ring exactly as it was: the navigator collects its stops by what is
enabled and visible, never by focus policy.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from src.presentation.views import theme, tray
from src.presentation.views.header_band import make_donate_button, make_view_button
from src.presentation.views.help_button import build_help_button
from src.presentation.views.icons import ICON_DONATE

THEMES = ("dark", "light")


def _noop() -> None:
    """A handler that does nothing, for a button under test."""


def _picture_buttons() -> tuple[QPushButton, ...]:
    """One of every picture button the application builds."""
    action = QPushButton()
    tray.style_tray_button(action, ICON_DONATE, "action", "TrayAction")
    form = QPushButton()
    tray.style_form_icon_button(form, ICON_DONATE, "form", QLineEdit())
    return (
        make_donate_button(_noop),
        make_view_button(ICON_DONATE, "view"),
        build_help_button(_noop, _noop, _noop, _noop, _noop),
        tray.ThemeToggleButton(),
        action,
        form,
    )


def test_every_picture_button_takes_tab_focus_only(qapp) -> None:
    """Qt's own default is StrongFocus, which is what left the ring behind."""
    for button in _picture_buttons():
        assert button.focusPolicy() == Qt.FocusPolicy.TabFocus, (
            f"{button.objectName()} takes focus from the mouse, so a click "
            "leaves it wearing the ring"
        )


@pytest.mark.parametrize("name", THEMES)
def test_a_click_fires_the_action_and_leaves_no_ring(qapp, name: str) -> None:
    """The whole defect, end to end: press it; nothing is left ringed."""
    tokens = theme.tokens_for(name)
    qapp.setStyleSheet(theme.build_stylesheet(tokens))
    host = QWidget()
    row = QHBoxLayout(host)
    sink = QWidget()
    sink.setFixedSize(0, 0)
    sink.setFocusPolicy(Qt.FocusPolicy.TabFocus)
    row.addWidget(sink)
    presses: list[int] = []
    donate = make_donate_button(lambda: presses.append(1))
    row.addWidget(donate)
    host.show()
    sink.setFocus()
    qapp.processEvents()

    # A REAL mouse press, not `click()`: a programmatic click never takes
    # focus, so it would pass against the very default this test exists for.
    QTest.mouseClick(donate, Qt.MouseButton.LeftButton)
    qapp.processEvents()

    assert presses == [1]
    assert qapp.focusWidget() is not donate
    assert _ring_pixels(donate, tokens["ring"]) == 0

    donate.setFocus(Qt.FocusReason.TabFocusReason)
    qapp.processEvents()

    assert _ring_pixels(donate, tokens["ring"]) > 0, (
        "the keyboard ring must still show; else the fix has taken the "
        "focus indicator away with the click focus"
    )


def _ring_pixels(button: QPushButton, ring: str) -> int:
    """How many pixels of the ring colour the button actually paints."""
    wanted = QColor(ring).name()
    image = button.grab().toImage()
    return sum(
        1
        for y in range(image.height())
        for x in range(image.width())
        if QColor(image.pixel(x, y)).name() == wanted
    )
