"""Switching the setup program between the two appearances.

The toggle shows the appearance it would switch TO, which is why the artwork is
chosen from the ARRIVING mode rather than the current one. That is the same
convention the application's own toggle follows; it is the reason the sun
appears while you are in the dark: pressing it brings the light.

The artwork is the application's own, taken from the generated icon set the
setup program already carries, so the two toggles cannot end up wearing
different pictures for the same idea.

Author: Oliver Ernster
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QPushButton

from installer import constants as c
from installer.theme import stylesheet

# The artwork for each arriving appearance, named as the icon set names it.
LIGHT_MODE_ICON = "light-mode"
DARK_MODE_ICON = "dark-mode"


def toggle_icon_name(dark: bool) -> str:
    """The artwork for the appearance the toggle would switch to."""
    return LIGHT_MODE_ICON if dark else DARK_MODE_ICON


def toggle_icon_path(dark: bool) -> Path:
    """Where that artwork lives inside the bundle."""
    return c.resource_path(f"assets/{c.ICONS_DIR_NAME}/{toggle_icon_name(dark)}.png")


def toggle_tooltip(dark: bool) -> str:
    """What the toggle says it will do, naming the mode it moves to."""
    return "Switch to light mode" if dark else "Switch to dark mode"


def apply(dark: bool, button: QPushButton) -> None:
    """Repaint the whole setup program, then re-face its toggle.

    Both halves belong together: a repaint that left the toggle showing the
    mode just departed would invite the reader to press it again.
    """
    path = toggle_icon_path(dark)
    if path.is_file():
        button.setIcon(QIcon(str(path)))
    button.setToolTip(toggle_tooltip(dark))
    application = QApplication.instance()
    if application is not None:
        application.setStyleSheet(stylesheet(dark))
