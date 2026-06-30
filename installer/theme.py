"""Qt stylesheets for the Audio Deck installer (dark and light), purple themed.

Buttons carry a transparent 2px border by default so the amber hover and focus
border never reflows the layout (the standard installer hover rule).
"""

from __future__ import annotations

from dataclasses import dataclass

from installer import constants as c


@dataclass(frozen=True)
class Palette:
    """A resolved set of surface and text colours for one theme variant."""

    bg: str
    surface: str
    text: str
    text_muted: str
    disabled_bg: str
    disabled_text: str


DARK = Palette(
    bg=c.DARK_BG,
    surface=c.DARK_SURFACE,
    text=c.DARK_TEXT,
    text_muted=c.DARK_TEXT_MUTED,
    disabled_bg=c.DARK_DISABLED_BG,
    disabled_text=c.DARK_DISABLED_TEXT,
)

LIGHT = Palette(
    bg=c.LIGHT_BG,
    surface=c.LIGHT_SURFACE,
    text=c.LIGHT_TEXT,
    text_muted=c.LIGHT_TEXT_MUTED,
    disabled_bg=c.LIGHT_DISABLED_BG,
    disabled_text=c.LIGHT_DISABLED_TEXT,
)


def stylesheet(dark: bool = True) -> str:
    """Return the installer stylesheet for the chosen variant.

    Args:
        dark: True for the dark palette, False for the light palette.

    Returns:
        A Qt style sheet string.
    """
    p = DARK if dark else LIGHT
    return f"""
        QWidget {{
            background-color: {p.bg};
            color: {p.text};
            font-size: 11pt;
        }}
        QLabel#HeaderTitle {{
            font-size: {c.TITLE_FONT_PT}pt;
            font-weight: bold;
        }}
        QLabel#HeaderVersion {{
            font-size: {c.VERSION_FONT_PT}pt;
            color: {p.text_muted};
        }}
        QLabel#SubTitle {{
            font-size: {c.SUBTITLE_FONT_PT}pt;
            font-weight: bold;
        }}
        QLabel#StatusLine {{
            font-size: {c.STATUS_FONT_PT}pt;
            color: {p.text_muted};
        }}
        QLineEdit, QTextBrowser {{
            background-color: {p.surface};
            border: {c.BORDER_WIDTH}px solid {c.COLOR_PURPLE_BORDER};
            border-radius: {c.BORDER_RADIUS}px;
            padding: 6px;
            color: {p.text};
        }}
        QCheckBox {{
            spacing: 8px;
        }}
        QPushButton {{
            background-color: {c.COLOR_PURPLE_MID};
            color: white;
            border: {c.BORDER_WIDTH}px solid transparent;
            border-radius: {c.BORDER_RADIUS}px;
            padding: {c.BUTTON_PADDING_V}px {c.BUTTON_PADDING_H}px;
            font-weight: bold;
        }}
        QPushButton:enabled:hover {{
            border: {c.BORDER_WIDTH}px solid {c.COLOR_ACCENT_HOVER};
        }}
        QPushButton:enabled:focus {{
            border: {c.BORDER_WIDTH}px solid {c.COLOR_ACCENT_HOVER};
        }}
        QPushButton:enabled:pressed {{
            background-color: {c.COLOR_PURPLE_DEEP};
        }}
        QPushButton:disabled {{
            background-color: {p.disabled_bg};
            color: {p.disabled_text};
        }}
        QPushButton#PrimaryAction {{
            border-radius: {c.BUTTON_RADIUS}px;
            min-width: {c.BUTTON_MIN_WIDTH}px;
        }}
        QPushButton#DangerAction {{
            background-color: {c.COLOR_DANGER};
            border-radius: {c.BUTTON_RADIUS}px;
            min-width: {c.BUTTON_MIN_WIDTH}px;
        }}
        QPushButton#DangerAction:enabled:pressed {{
            background-color: {c.COLOR_DANGER_HOVER};
        }}
        QProgressBar {{
            background-color: {p.surface};
            border: {c.BORDER_WIDTH}px solid {c.COLOR_PURPLE_BORDER};
            border-radius: {c.BORDER_RADIUS}px;
            height: {c.PROGRESS_HEIGHT}px;
            text-align: center;
            color: {p.text};
        }}
        QProgressBar::chunk {{
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {c.COLOR_PURPLE_LIGHT}, stop:1 {c.COLOR_PURPLE_DEEP}
            );
            border-radius: {c.BORDER_RADIUS - 1}px;
        }}
    """
