"""The row of picture buttons across the top of the window.

Held apart from the window because it is one concern with one shape: every
control in it is a fixed-size picture button built by the same tray recipe;
its assembled WIDTH is what the window's minimum size has to respect.

That last part is the reason this module carries the window's size constants
rather than the window doing so. The header's width is decided by the artwork
height, so the two are coupled: raise the icon height and the header grows,
while a window minimum written as a literal quietly stops being big enough and
clips the controls at the right-hand end. Keeping the floor next to the code
that measures the header is what stops them drifting apart.

Author: Oliver Ernster
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QHBoxLayout, QPushButton

from src.presentation.views import tray
from src.presentation.views.icons import ICON_DONATE

# What the donate button says it will do. The picture is a beer and a coffee,
# which tells nobody that pressing it leaves the application, so the tooltip
# has to.
DONATE_TOOLTIP = "Buy the author a drink (opens your browser)"

# The window never opens smaller than this. The WIDTH is a FLOOR rather than
# the answer: see the module docstring for why the header decides the rest.
WINDOW_MIN_WIDTH_FLOOR_PX = 600
WINDOW_MIN_HEIGHT_PX = 500

# The margins around the header row. No bottom margin: the views below carry
# their own, so a second one here would double the gap.
HEADER_MARGINS = (8, 8, 8, 0)


def make_view_button(icon_name: str, name: str) -> QPushButton:
    """Build one view-switching icon in the tray style."""
    button = QPushButton()
    tray.style_tray_button(button, icon_name, name, "ViewButton")
    return button


def adopt_tray_actions(
    header: QHBoxLayout, actions: tuple[tuple[QPushButton, str, str], ...]
) -> tuple[QPushButton, ...]:
    """Restyle one view's action buttons as tray icons and add them."""
    buttons = []
    for button, icon_name, name in actions:
        tray.style_tray_button(button, icon_name, name, "TrayAction")
        header.addWidget(button)
        buttons.append(button)
    return tuple(buttons)


def make_donate_button(on_click: Callable[[], None]) -> QPushButton:
    """Build the donate button.

    It belongs to no view and to none of the application's own controls, which
    is why the window puts it in the right-hand cluster rather than among the
    action icons: it sits where nothing else is reached by accident.
    """
    button = QPushButton()
    tray.style_tray_button(button, ICON_DONATE, DONATE_TOOLTIP, "DonateButton")
    button.clicked.connect(on_click)
    return button


def minimum_window_size(header: QHBoxLayout) -> tuple[int, int]:
    """Return the smallest the window may be, given this header.

    Measured rather than guessed, so retuning the icon height carries the
    window minimum with it instead of leaving a literal behind that is one
    icon size out of date.
    """
    return (
        max(WINDOW_MIN_WIDTH_FLOOR_PX, header.sizeHint().width()),
        WINDOW_MIN_HEIGHT_PX,
    )
