"""The setup program's look: the house shell over Audio Deck's own palette.

The geometry and the type scale are the house ones, taken from the reference
setup program rather than invented here. Only the colours are Audio Deck's;
those are sampled from the application's own artwork so the installer and the
app it installs read as one thing.

The ring model is the house one and it is deliberately NOT the application's:
no ring at rest, a green ring while an enabled control is hovered or focused and
a permanent danger ring while a control is disabled. The accent is never a ring,
because it carries identity rather than state. So this is a stylesheet in its
own right rather than a layer over the application's, which carries a different
model and would otherwise fight it.
"""

from __future__ import annotations

from dataclasses import dataclass

from installer import constants as c


@dataclass(frozen=True)
class Palette:
    """Every colour one appearance needs, named by role rather than by hue."""

    window: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    selection: str
    ring: str
    danger: str
    danger_soft: str
    disabled_surface: str
    disabled_text: str


DARK = Palette(
    window=c.DARK_WINDOW,
    surface=c.DARK_SURFACE,
    surface_alt=c.DARK_SURFACE_ALT,
    border=c.DARK_BORDER,
    text=c.DARK_TEXT,
    text_muted=c.DARK_TEXT_MUTED,
    accent=c.DARK_ACCENT,
    selection=c.DARK_SELECTION,
    ring=c.DARK_RING,
    danger=c.DARK_DANGER,
    danger_soft=c.DARK_DANGER_SOFT,
    disabled_surface=c.DARK_DISABLED_SURFACE,
    disabled_text=c.DARK_DISABLED_TEXT,
)

LIGHT = Palette(
    window=c.LIGHT_WINDOW,
    surface=c.LIGHT_SURFACE,
    surface_alt=c.LIGHT_SURFACE_ALT,
    border=c.LIGHT_BORDER,
    text=c.LIGHT_TEXT,
    text_muted=c.LIGHT_TEXT_MUTED,
    accent=c.LIGHT_ACCENT,
    selection=c.LIGHT_SELECTION,
    ring=c.LIGHT_RING,
    danger=c.LIGHT_DANGER,
    danger_soft=c.LIGHT_DANGER_SOFT,
    disabled_surface=c.LIGHT_DISABLED_SURFACE,
    disabled_text=c.LIGHT_DISABLED_TEXT,
)

# The glow behind the window. A derivation of the accent rather than a second
# colour value, so it can never drift away from the accent it is a glow of.
GLOW_ALPHA = 0.11
GLOW_CENTRE = -0.08
GLOW_RADIUS = 0.9
GLOW_EDGE = 0.7
HEX_PAIRS = ((1, 3), (3, 5), (5, 7))


def tinted(colour: str, alpha: float) -> str:
    """One palette colour at a given transparency."""
    red, green, blue = (int(colour[start:end], 16) for start, end in HEX_PAIRS)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def palette_for(dark: bool) -> Palette:
    """The palette for one appearance."""
    return DARK if dark else LIGHT


def stylesheet(dark: bool = True) -> str:
    """Return the whole setup program stylesheet for one appearance."""
    colour = palette_for(dark)
    glow = tinted(colour.accent, GLOW_ALPHA)
    return f"""
    QWidget {{
        background: {colour.window};
        color: {colour.text};
        font-family: 'Segoe UI';
        font-size: {c.BASE_FONT_PX}px;
    }}
    /* The glow belongs to the window, so everything drawn over it says so
       rather than painting the flat colour back on top of it. */
    QWidget#Shell {{
        background: qradialgradient(
            cx: 0.5, cy: {GLOW_CENTRE}, radius: {GLOW_RADIUS},
            fx: 0.5, fy: {GLOW_CENTRE},
            stop: 0 {glow}, stop: {GLOW_EDGE} {colour.window}
        );
    }}
    QWidget#Pane, QWidget#Body, QLabel, QCheckBox {{
        background: transparent;
    }}
    QLabel#HeaderTitle {{
        font-size: {c.TITLE_FONT_PX}px;
        font-weight: 700;
    }}
    QLabel#HeaderSub {{
        font-size: {c.SUB_FONT_PX}px;
        color: {colour.text_muted};
    }}
    QLabel#Heading {{
        font-size: {c.HEADING_FONT_PX}px;
        font-weight: 700;
    }}
    QLabel#Lead {{
        color: {colour.text_muted};
    }}
    QLabel#Status {{
        font-size: {c.STATUS_FONT_PX}px;
        color: {colour.text_muted};
    }}
    QLabel#InfoBox {{
        background: {colour.surface};
        border: 1px solid {colour.border};
        border-radius: 9px;
        padding: 13px 16px;
        font-size: {c.INFO_FONT_PX}px;
        color: {colour.text_muted};
    }}
    QFrame#Rule {{
        background: {colour.border};
        border: none;
    }}
    QLineEdit {{
        background: {colour.surface};
        border: 1px solid {colour.border};
        border-radius: 9px;
        padding: 10px 12px;
        color: {colour.text};
    }}
    QLineEdit:enabled:hover, QLineEdit:enabled:focus {{
        border: {c.RING_PX}px solid {colour.ring};
    }}
    QLineEdit:disabled {{
        background: {colour.disabled_surface};
        border: {c.RING_PX}px solid {colour.danger};
        color: {colour.disabled_text};
    }}
    QCheckBox {{
        spacing: {c.OPTION_GAP_PX}px;
        border: {c.RING_PX}px solid transparent;
        border-radius: 8px;
        padding: 5px 7px;
    }}
    QCheckBox:enabled:hover, QCheckBox:enabled:focus {{
        border-color: {colour.ring};
    }}
    QCheckBox:disabled {{
        border-color: {colour.danger};
        color: {colour.disabled_text};
    }}
    QCheckBox::indicator {{
        width: {c.CHECK_PX}px;
        height: {c.CHECK_PX}px;
        border: 1px solid {colour.border};
        border-radius: 5px;
        background: {colour.surface};
    }}
    QCheckBox::indicator:checked {{
        background: {colour.accent};
        border-color: {colour.accent};
    }}
    QCheckBox::indicator:disabled {{
        background: {colour.disabled_surface};
    }}
    QPushButton {{
        background: {colour.surface_alt};
        color: {colour.text};
        border: {c.RING_PX}px solid transparent;
        border-radius: 9px;
        padding: 11px 22px;
        font-weight: 600;
    }}
    QPushButton:enabled:hover, QPushButton:enabled:focus {{
        border-color: {colour.ring};
    }}
    QPushButton:disabled {{
        background: {colour.disabled_surface};
        border-color: {colour.danger};
        color: {colour.disabled_text};
    }}
    /* The two named actions keep their own fill, so each still needs its own
       ring rule: an object-name rule setting `border` beats the generic one by
       id specificity and would otherwise leave them with no ring at all. */
    QPushButton#PrimaryAction {{
        background: {colour.selection};
        color: {colour.accent};
        min-width: {c.BUTTON_MIN_WIDTH}px;
    }}
    QPushButton#PrimaryAction:enabled:hover, QPushButton#PrimaryAction:enabled:focus {{
        border-color: {colour.ring};
    }}
    QPushButton#PrimaryAction:disabled {{
        background: {colour.disabled_surface};
        border-color: {colour.danger};
        color: {colour.disabled_text};
    }}
    QPushButton#DangerAction {{
        background: {colour.danger_soft};
        color: {colour.danger};
        min-width: {c.BUTTON_MIN_WIDTH}px;
    }}
    QPushButton#DangerAction:enabled:hover, QPushButton#DangerAction:enabled:focus {{
        border-color: {colour.ring};
    }}
    QPushButton#DangerAction:disabled {{
        background: {colour.disabled_surface};
        border-color: {colour.danger};
        color: {colour.disabled_text};
    }}
    QProgressBar {{
        background: {colour.surface_alt};
        border: 1px solid {colour.border};
        border-radius: 5px;
        min-height: {c.TRACK_PX}px;
        max-height: {c.TRACK_PX}px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {colour.accent};
        border-radius: 4px;
    }}
    QTextBrowser {{
        background: {colour.surface};
        border: 1px solid {colour.border};
        border-radius: 9px;
        color: {colour.text};
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: {c.LICENCE_FONT_PX}px;
    }}
    QDialog {{
        background: {colour.window};
    }}
    """
