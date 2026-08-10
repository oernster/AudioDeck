"""Tests for the painted-pixel glyph measurement."""

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage

from src.presentation.widgets.glyph_metrics import (
    glyph_font_px_for_height,
    opaque_bounding_rect,
    painted_glyph_height,
)

_CANVAS_SIDE = 20
_BOX_ORIGIN = 5
_BOX_SIDE = 8
_TARGET_PX = 32


def _canvas() -> QImage:
    image = QImage(_CANVAS_SIDE, _CANVAS_SIDE, QImage.Format.Format_ARGB32)
    image.fill(QColor(0, 0, 0, 0))
    return image


def test_bounding_rect_of_an_empty_image_is_null(qtbot):
    assert opaque_bounding_rect(_canvas()) == QRect(0, 0, 0, 0)


def test_bounding_rect_finds_the_painted_box(qtbot):
    image = _canvas()
    for x in range(_BOX_ORIGIN, _BOX_ORIGIN + _BOX_SIDE):
        for y in range(_BOX_ORIGIN, _BOX_ORIGIN + _BOX_SIDE):
            image.setPixel(x, y, 0xFF000000)
    assert opaque_bounding_rect(image) == QRect(
        _BOX_ORIGIN, _BOX_ORIGIN, _BOX_SIDE, _BOX_SIDE
    )


def test_a_real_glyph_paints_a_measurable_height(qtbot):
    assert painted_glyph_height("X", _TARGET_PX) > 0


def test_a_blank_glyph_falls_back_to_the_target(qtbot):
    assert glyph_font_px_for_height("", _TARGET_PX) == _TARGET_PX


def test_the_derived_font_size_is_positive_and_finite(qtbot):
    derived = glyph_font_px_for_height("X", _TARGET_PX)
    assert 0 < derived < _TARGET_PX * 4
