"""Painted-pixel measurement for emoji glyphs.

Qt sizes text by the font's em box, never by what a glyph actually paints,
and emoji differ widely in how much of that box they fill. A fixed font size
therefore renders different glyphs at visibly different heights. Everything
here measures the real pixels instead, so a font size is derived from the
glyph in hand rather than assumed for glyphs in general. Ported from
ClearBudget's glyph metrics, the house pattern for emoji icon trays.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter

# Side of the scratch canvas a glyph is measured on, as a multiple of its
# font size. Emoji can paint outside their em box, so the canvas is given
# room on every side; a clipped glyph would measure short and be sized up
# to compensate.
_MEASURE_CANVAS_SCALE = 3


def opaque_bounding_rect(image: QImage) -> QRect:
    """Return the QRect bounding box of non-transparent pixels in `image`."""
    image = image.convertToFormat(QImage.Format.Format_ARGB32)
    width, height = image.width(), image.height()

    def row_has_content(y: int) -> bool:
        return any((image.pixel(x, y) >> 24) & 0xFF for x in range(width))

    def col_has_content(x: int) -> bool:
        return any((image.pixel(x, y) >> 24) & 0xFF for y in range(height))

    rows = [y for y in range(height) if row_has_content(y)]
    if not rows:
        return QRect(0, 0, 0, 0)
    cols = [x for x in range(width) if col_has_content(x)]
    return QRect(cols[0], rows[0], cols[-1] - cols[0] + 1, rows[-1] - rows[0] + 1)


def painted_glyph_height(glyph: str, font_px: int) -> int:
    """Return the height in pixels that `glyph` paints at a `font_px` font.

    Rendered to an off-screen ARGB canvas and measured by its opaque pixels,
    which is the only reading that accounts for a colour emoji font, where
    the glyph is a bitmap whose extents owe nothing to the font's metrics.
    """
    font_px = max(1, font_px)
    side = font_px * _MEASURE_CANVAS_SCALE
    canvas = QImage(side, side, QImage.Format.Format_ARGB32)
    canvas.fill(QColor(0, 0, 0, 0))
    painter = QPainter(canvas)
    font = QFont()
    font.setPixelSize(font_px)
    painter.setFont(font)
    painter.drawText(canvas.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
    painter.end()
    return opaque_bounding_rect(canvas).height()


def glyph_font_px_for_height(glyph: str, target_px: int) -> int:
    """Return the font pixel size at which `glyph` paints `target_px` tall.

    The glyph is measured once at the target size, then the font is scaled
    by however far that reading missed. Emoji scale linearly with the font
    size, so one reading is enough and the target doubles as the reference,
    leaving no tuned constant to drift.

    A glyph that paints nothing (a missing font, a blank canvas) falls back
    to the target size.
    """
    target_px = max(1, int(target_px))
    painted = painted_glyph_height(glyph, target_px)
    if painted <= 0:
        return target_px
    return max(1, round(target_px * target_px / painted))
