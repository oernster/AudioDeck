"""The Help tray icon and its menu.

Extracted from MainWindow so the window module stays clear of the size
danger band; the button is one self-contained recipe in the ClearBudget
tray style (measured glyph, fixed square, three-state ring restated because
an object-name rule would otherwise swallow the app-wide one).
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QToolButton

from src.presentation.widgets.glyph_metrics import glyph_font_px_for_height
from src.presentation.widgets.keyboard_nav import RING_GREEN

# Matches the view icons' tray sizing in main_window.
_GLYPH_HEIGHT_PX = 32
_BTN_CHROME_PX = 8
_HOVER_FILL = "#313244"


def build_help_button(
    on_documentation: Callable[[], None],
    on_dev_documentation: Callable[[], None],
    on_license: Callable[[], None],
    on_check_updates: Callable[[], None],
    on_about: Callable[[], None],
) -> QToolButton:
    """Build the Help icon with its menu wired to the given actions."""
    help_button = QToolButton()
    help_button.setObjectName("HelpButton")
    help_button.setText("ℹ️")
    help_button.setToolTip("Help")
    help_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    help_button.setCursor(Qt.CursorShape.PointingHandCursor)
    glyph_px = glyph_font_px_for_height("ℹ️", _GLYPH_HEIGHT_PX)
    side = _GLYPH_HEIGHT_PX + _BTN_CHROME_PX
    help_button.setFixedSize(side, side)
    help_button.setStyleSheet(f"""
        QToolButton#HelpButton {{
            background-color: transparent;
            border: 2px solid transparent;
            border-radius: 4px;
            font-size: {glyph_px}px;
            padding: 0px;
        }}
        QToolButton#HelpButton:enabled:hover,
        QToolButton#HelpButton:enabled:focus {{
            background-color: {_HOVER_FILL};
            border: 2px solid {RING_GREEN};
        }}
        QToolButton#HelpButton::menu-indicator {{
            image: none;
        }}
    """)
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
