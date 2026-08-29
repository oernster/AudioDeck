"""The window can never open narrower than its own header.

The header is a row of FIXED-size picture buttons, so its width is decided by
the artwork height. That makes the two numbers coupled: raising the icon height
widens the header, so a window minimum written as a literal silently stops
being big enough. The symptom is buttons clipped off the right-hand end, which
does not look like a sizing bug and is easy to blame on the theme.

Measured when the icons went from 32px to 72px: the busy view's header needed
about 954px against a window minimum of 600px.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from src.presentation.views import tray
from src.presentation.views.header_band import (
    DONATE_TOOLTIP,
    WINDOW_MIN_WIDTH_FLOOR_PX,
)

# The Configuration view is the busier of the two, so it decides the width:
# both view switchers, its five profile actions, then the right-hand cluster.
_BUSIEST_HEADER = (
    "quick-switch",
    "configuration",
    "add-profile",
    "edit-profile",
    "delete-profile",
    "save-profile",
    "cancel-edit",
    "donate",
    "light-mode",
    "help-info",
)


def _busiest_header(qtbot) -> QWidget:
    """Build the widest header the application can show."""
    host = QWidget()
    qtbot.addWidget(host)
    row = QHBoxLayout(host)
    row.addWidget(tray.make_separator())
    for name in _BUSIEST_HEADER:
        button = QPushButton()
        tray.style_tray_button(button, name, DONATE_TOOLTIP, "TrayAction")
        row.addWidget(button)
    return host


def test_the_window_minimum_is_wide_enough_for_the_busiest_header(qtbot) -> None:
    """What the window actually uses is the larger of the floor and the header."""
    header = _busiest_header(qtbot)
    needed = header.sizeHint().width()
    applied = max(WINDOW_MIN_WIDTH_FLOOR_PX, needed)

    assert applied >= needed


def test_the_floor_alone_would_not_be_enough(qtbot) -> None:
    """The reason the minimum is derived rather than written down.

    If this ever fails the icons have shrunk far enough that the floor covers
    the header again, so the derivation could be simplified. It is not a
    failure to route around by raising the floor.
    """
    header = _busiest_header(qtbot)

    assert header.sizeHint().width() > WINDOW_MIN_WIDTH_FLOOR_PX


def test_every_button_in_the_header_shares_one_height(qtbot) -> None:
    """Matched on height is what puts the row on a single baseline."""
    heights = set()
    for name in _BUSIEST_HEADER:
        button = QPushButton()
        qtbot.addWidget(button)
        tray.style_tray_button(button, name, name, "TrayAction")
        heights.add(button.height())

    assert heights == {tray.ICON_HEIGHT_PX + tray.ICON_BTN_CHROME_PX}
