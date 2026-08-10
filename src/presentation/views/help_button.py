"""The Help tray icon and its menu.

Extracted from MainWindow so the window module stays clear of the size
danger band; the button wears the shared tray recipe and its colour rules
live in the theme's app stylesheet, so a theme switch restyles it for free.

A plain QPushButton popping the menu itself, NOT a QToolButton with
setMenu: a QToolButton reserves menu-indicator space inside its fixed
square and ELIDES its text when the remainder cannot hold the glyph, which
turned the measured ℹ️ into a literal "…" on the real Windows font. A push
button reserves nothing and never elides.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QPushButton

from src.presentation.views.tray import style_tray_button


def build_help_button(
    on_documentation: Callable[[], None],
    on_dev_documentation: Callable[[], None],
    on_license: Callable[[], None],
    on_check_updates: Callable[[], None],
    on_about: Callable[[], None],
) -> QPushButton:
    """Build the Help icon with its menu wired to the given actions."""
    help_button = QPushButton()
    style_tray_button(help_button, "ℹ️", "Help", "HelpButton")

    help_menu = QMenu(help_button)
    entries = (
        ("View Documentation", on_documentation),
        ("Development Documentation", on_dev_documentation),
        ("View License (LGPL-3.0)", on_license),
        None,
        ("Check for Updates", on_check_updates),
        None,
        ("About Audio Deck", on_about),
    )
    for entry in entries:
        if entry is None:
            help_menu.addSeparator()
            continue
        title, handler = entry
        action = QAction(title, help_button)
        action.triggered.connect(handler)
        help_menu.addAction(action)

    def show_menu() -> None:
        help_menu.popup(help_button.mapToGlobal(QPoint(0, help_button.height())))

    help_button.clicked.connect(show_menu)
    return help_button
