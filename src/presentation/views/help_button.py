"""The Help tray icon and its menu.

Extracted from MainWindow so the window module stays clear of the size
danger band; the button wears the shared tray recipe and its colour rules
live in the theme's app stylesheet, so a theme switch restyles it for free.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QToolButton

from src.presentation.views.tray import style_tray_button


def build_help_button(
    on_documentation: Callable[[], None],
    on_dev_documentation: Callable[[], None],
    on_license: Callable[[], None],
    on_check_updates: Callable[[], None],
    on_about: Callable[[], None],
) -> QToolButton:
    """Build the Help icon with its menu wired to the given actions."""
    help_button = QToolButton()
    help_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    style_tray_button(help_button, "ℹ️", "Help", "HelpButton")
    help_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

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

    help_button.setMenu(help_menu)
    return help_button
