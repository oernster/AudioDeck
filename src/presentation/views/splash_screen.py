"""The application splash screen.

A rounded card with the app's purple gradient, the icon, the version and the
author, hand-drawn onto a pixmap rather than assembled from widgets. It lived
in the composition root, where 136 lines of painting sat beside the dependency
wiring and pushed that module into the size rule's danger band.

Author: Oliver Ernster
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QSplashScreen

from src import __version__
from src.presentation.views.resource_paths import APP_ICON_PNG, resource_path


def create_splash_screen() -> QSplashScreen:
    """Create and configure a themed splash screen.

    A rounded card with the app's purple gradient, the icon, the version and the
    author. The version is read from the single source of truth (the VERSION
    file, via __version__).

    Returns:
        Configured splash screen widget
    """
    # Geometry and spacing (named, no magic numbers).
    WIDTH = 440
    HEIGHT = 300
    CORNER_RADIUS = 18
    BORDER_WIDTH = 2
    ICON_SIZE = 112
    ICON_TITLE_GAP = 16
    TITLE_VERSION_GAP = 8
    VERSION_AUTHOR_GAP = 4
    BOTTOM_MARGIN = 22

    # Palette: Audio Deck signature purple, fading to dark.
    color_top = QColor("#4a2c6a")
    color_bottom = QColor("#262430")
    color_border = QColor("#7b5caa")
    color_title = QColor("#ffffff")
    color_version = QColor("#d8ccea")
    color_author = QColor("#b0a4c4")
    color_loading = QColor("#8a7ea3")

    splash_pixmap = QPixmap(WIDTH, HEIGHT)
    splash_pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(splash_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded gradient card.
    inset = BORDER_WIDTH
    card = QPainterPath()
    card.addRoundedRect(
        inset,
        inset,
        WIDTH - 2 * inset,
        HEIGHT - 2 * inset,
        CORNER_RADIUS,
        CORNER_RADIUS,
    )
    gradient = QLinearGradient(0, 0, 0, HEIGHT)
    gradient.setColorAt(0, color_top)
    gradient.setColorAt(1, color_bottom)
    painter.fillPath(card, gradient)
    painter.setPen(QPen(color_border, BORDER_WIDTH))
    painter.drawPath(card)

    # Fonts.
    font_title = QFont()
    font_title.setPointSize(22)
    font_title.setBold(True)
    font_version = QFont()
    font_version.setPointSize(11)
    font_author = QFont()
    font_author.setPointSize(10)
    font_loading = QFont()
    font_loading.setPointSize(9)

    fm_title = QFontMetrics(font_title)
    fm_version = QFontMetrics(font_version)
    fm_author = QFontMetrics(font_author)

    icon_path = resource_path(APP_ICON_PNG)
    has_icon = icon_path.exists()
    icon_block = ICON_SIZE + ICON_TITLE_GAP if has_icon else 0

    block_height = (
        icon_block
        + fm_title.height()
        + TITLE_VERSION_GAP
        + fm_version.height()
        + VERSION_AUTHOR_GAP
        + fm_author.height()
    )
    y = (HEIGHT - block_height) // 2

    if has_icon:
        icon_pixmap = QPixmap(str(icon_path)).scaled(
            ICON_SIZE,
            ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap((WIDTH - icon_pixmap.width()) // 2, y, icon_pixmap)
        y += icon_pixmap.height() + ICON_TITLE_GAP

    def draw_centered(text: str, font: QFont, color: QColor, gap: int) -> None:
        nonlocal y
        painter.setFont(font)
        painter.setPen(color)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)
        painter.drawText((WIDTH - text_width) // 2, y + metrics.ascent(), text)
        y += metrics.height() + gap

    draw_centered("Audio Deck", font_title, color_title, TITLE_VERSION_GAP)
    draw_centered(
        f"Version {__version__}", font_version, color_version, VERSION_AUTHOR_GAP
    )
    draw_centered("by Oliver Ernster", font_author, color_author, 0)

    # Loading line pinned near the bottom edge.
    painter.setFont(font_loading)
    painter.setPen(color_loading)
    fm_loading = QFontMetrics(font_loading)
    loading_text = "Loading..."
    loading_width = fm_loading.horizontalAdvance(loading_text)
    painter.drawText(
        (WIDTH - loading_width) // 2,
        HEIGHT - BOTTOM_MARGIN,
        loading_text,
    )

    painter.end()

    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.setMask(splash_pixmap.mask())
    return splash
