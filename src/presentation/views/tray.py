"""Shared emoji tray recipes: icon buttons, the separator, the theme toggle.

One home for the ClearBudget-style tray sizing so every header icon (the
view switchers, the per-view action icons, the Help button, the theme
toggle) is built by the same rules: the glyph is measured and scaled to
paint at one height, the button is a fixed square of the glyph plus the
ring chrome, the font goes on as a widget-level stylesheet WITH a selector
(a stylesheet rule beats setFont and a bare font-size would cascade to the
tooltip) and the colour rules stay in the app sheet so a theme switch
restyles them for free.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFrame,
    QPushButton,
)

from src.presentation.views import theme
from src.presentation.widgets.glyph_metrics import glyph_font_px_for_height

# Each tray glyph is sized to paint at this height, and its button is a
# fixed square of the glyph plus the ring chrome (without which Qt's
# default push-button minimum makes an icon-sized control 80-odd pixels
# wide).
ICON_GLYPH_HEIGHT_PX = 32
ICON_BTN_CHROME_PX = 8

# The ring border each side of a tray button, matching the app stylesheet.
_RING_BORDER_PX = 2

# The toggle glyph's painted height as a fraction of the tray icons'.
# Deliberately below 1.0: the sun and the moon are solid saturated shapes
# that fill their whole outline, while the other tray glyphs are pictograms
# with internal detail, so equal heights leave the toggle looking the
# heavier. Optical weight, not bounding box, is what the eye compares.
TOGGLE_GLYPH_SCALE = 0.8


def apply_tray_glyph(
    button: QAbstractButton, glyph: str, height_px: int = ICON_GLYPH_HEIGHT_PX
) -> None:
    """Show `glyph` on a tray button, sized to paint at `height_px`.

    The font size is derived from THIS glyph by measuring it, so different
    emoji read as one matched family; the selector scopes the size to the
    button so a tooltip cannot inherit it. The derived size is capped at
    the button's usable square, so a font whose real metrics differ from
    the measured ones can shrink a glyph slightly but never clip it away.
    """
    usable_px = ICON_GLYPH_HEIGHT_PX + ICON_BTN_CHROME_PX - 2 * _RING_BORDER_PX
    glyph_px = min(glyph_font_px_for_height(glyph, height_px), usable_px)
    button.setText(glyph)
    button.setStyleSheet(f"#{button.objectName()} {{ font-size: {glyph_px}px; }}")


def style_tray_button(
    button: QAbstractButton, glyph: str, name: str, object_name: str
) -> None:
    """Restyle any button as a tray icon: glyph only, named by its tooltip."""
    button.setObjectName(object_name)
    button.setToolTip(name)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    apply_tray_glyph(button, glyph)
    side = ICON_GLYPH_HEIGHT_PX + ICON_BTN_CHROME_PX
    button.setFixedSize(side, side)


def make_separator() -> QFrame:
    """Build the themed vertical separator between tray groups."""
    separator = QFrame()
    separator.setObjectName("Separator")
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFrameShadow(QFrame.Shadow.Plain)
    return separator


class ThemeToggleButton(QPushButton):
    """The sun/moon toggle: its glyph shows the mode a press switches TO.

    The glyph changes with the theme and each one paints a different
    fraction of its em box, so `restyle` re-derives the font size from the
    incoming glyph every switch; `apply_theme` finds the button through the
    duck-typed restyle scan.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName(theme.TOGGLE_BUTTON_OBJECT_NAME)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        side = ICON_GLYPH_HEIGHT_PX + ICON_BTN_CHROME_PX
        self.setFixedSize(side, side)
        self.restyle()

    def restyle(self) -> None:
        """Point the glyph and tooltip at the mode a press switches to."""
        instance = QApplication.instance()
        app = instance if isinstance(instance, QApplication) else None
        name = theme.current_theme(app)
        target = max(1, round(ICON_GLYPH_HEIGHT_PX * TOGGLE_GLYPH_SCALE))
        apply_tray_glyph(self, theme.toggle_glyph(name), target)
        self.setToolTip(theme.toggle_tooltip(name))
