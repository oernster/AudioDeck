"""Shared tray recipes: icon buttons, the separator, the theme toggle.

One home for the tray sizing so every header control (the view switchers, the
per-view action icons, the donate button, the theme toggle, Help) is built by
the same rules: the artwork is drawn at ONE height, the button is that picture
plus the ring chrome; the colour rules stay in the app sheet so a theme
switch restyles them for free.

Every tray button draws a PICTURE. It drew an emoji once, chosen because emoji
theme themselves and need no packaging step; they were replaced because at a
readable size their detail is coarse and a set assembled from whatever the font
happened to provide could not be drawn in one visual language.

Matched on HEIGHT, sized on WIDTH. A shared height is what puts a row of
differently shaped pictures on one baseline, which is the edge the eye actually
checks along a row; forcing a shared WIDTH instead squeezes the wide ones, while
fitting each picture into a square by its LONGER side makes the wide ones
SHORTER than their neighbours, which is the failure this rule exists to avoid.
So each button is exactly as wide as its own artwork and exactly as tall as
every other button.

Author: Oliver Ernster
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QFrame,
    QPushButton,
    QWidget,
)

from src.presentation.views import theme
from src.presentation.views.resource_paths import button_icon_path

# Every tray icon is drawn at this height. The generator renders each master at
# four times this so the artwork stays crisp on a display above 100% scale and
# Qt only ever scales DOWN, which is the direction that looks good.
ICON_HEIGHT_PX = 72

# The ring chrome around a tray button: 2px padding plus 2px border each side.
# Added to the artwork's own box so the ring never sits hard against the
# picture and a hover cannot reflow the row.
ICON_BTN_CHROME_PX = 8


def apply_tray_icon(
    button: QAbstractButton, icon_name: str, height_px: int = ICON_HEIGHT_PX
) -> None:
    """Draw `icon_name`'s artwork on a tray button at `height_px`.

    The button is fixed to the artwork's own width and the shared height, since
    Qt's default push-button minimum would otherwise make an icon-sized control
    80-odd pixels wide.

    A picture that fails to load leaves the button present, sized and
    tooltipped rather than taking the window down; that a name resolves at all
    is held by a structural test, so a missing file fails the suite instead of
    shipping.
    """
    pixmap = QPixmap(str(button_icon_path(icon_name)))
    width_px = height_px
    if not pixmap.isNull():
        pixmap = pixmap.scaledToHeight(
            height_px, Qt.TransformationMode.SmoothTransformation
        )
        button.setIcon(QIcon(pixmap))
        button.setIconSize(pixmap.size())
        width_px = pixmap.width()
    # The face is the picture, so any inherited label would sit beside it.
    button.setText("")
    button.setFixedSize(width_px + ICON_BTN_CHROME_PX, height_px + ICON_BTN_CHROME_PX)


def style_tray_button(
    button: QAbstractButton, icon_name: str, name: str, object_name: str
) -> None:
    """Restyle any button as a tray icon: artwork only, named by its tooltip."""
    button.setObjectName(object_name)
    button.setToolTip(name)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    apply_tray_icon(button, icon_name)


def style_form_icon_button(
    button: QAbstractButton, icon_name: str, name: str, companion: QWidget
) -> None:
    """Restyle a button that sits INSIDE a form row rather than in the header.

    Its height comes from the control it sits beside rather than from the tray,
    so the row keeps a single line height. The header's own icon height is
    around three times a combo box, so reusing it here would stretch every form
    row the button appeared in.

    `companion` is polished before it is measured: a freshly built widget still
    carries the fallback font until Qt polishes it, so measuring too early
    gives the wrong height by a few pixels.
    """
    companion.ensurePolished()
    button.setObjectName("FormIconButton")
    button.setToolTip(name)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    apply_tray_icon(button, icon_name, companion.sizeHint().height())


def make_separator() -> QFrame:
    """Build the themed vertical separator between tray groups."""
    separator = QFrame()
    separator.setObjectName("Separator")
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setFrameShadow(QFrame.Shadow.Plain)
    # A separator is chrome, never a stop on the keyboard ring.
    separator.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    return separator


class ThemeToggleButton(QPushButton):
    """The sun/moon toggle: its artwork shows the mode a press switches TO.

    The picture changes with the theme, so `restyle` re-reads it every switch;
    `apply_theme` finds the button through the duck-typed restyle scan.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName(theme.TOGGLE_BUTTON_OBJECT_NAME)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restyle()

    def restyle(self) -> None:
        """Point the artwork and tooltip at the mode a press switches to."""
        instance = QApplication.instance()
        app = instance if isinstance(instance, QApplication) else None
        name = theme.current_theme(app)
        apply_tray_icon(self, theme.toggle_icon_name(name))
        self.setToolTip(theme.toggle_tooltip(name))
