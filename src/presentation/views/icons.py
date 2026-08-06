"""Emoji icon tokens for button labels.

Zero-dependency icon vocabulary. Every button glyph in the UI comes from
here so the set stays consistent and a glyph is changed in one place.
Emoji are used rather than image assets because they theme themselves and
need no packaging step.

Glyphs are written as escape sequences rather than literal characters for two
reasons: the file survives any editor or terminal encoding, plus the invisible
variation selector becomes visible in source.
"""

# Variation selector 16, requesting the colour emoji presentation rather
# than the monochrome text form some glyphs default to on Windows.
_VS16 = "️"

# Device actions.
ICON_SWITCH = "\U0001f500"  # twisted rightwards arrows
ICON_REFRESH = "\U0001f504"  # anticlockwise arrows

# Profile actions.
ICON_NEW = "➕"  # heavy plus sign
ICON_EDIT = "✏" + _VS16  # pencil
ICON_DELETE = "\U0001f5d1" + _VS16  # wastebasket

# Editor actions.
ICON_SAVE = "\U0001f4be"  # floppy disk
ICON_CANCEL = "✖" + _VS16  # heavy multiplication x


def labelled(icon: str, text: str) -> str:
    """Return a button label combining an icon glyph and its text.

    Args:
        icon: One of the ICON_* constants in this module
        text: The button's visible text

    Returns:
        The icon and text separated by a single space
    """
    return f"{icon} {text}"
