"""Identity, paths, sizes and theme colours for the Audio Deck installer.

All installer identity lives here as module-level constants, never as inline
literals, so the build scripts and the runtime UI share one source.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Identity.
APP_NAME = "AudioDeck"
APP_DISPLAY_NAME = "Audio Deck"
APP_TAGLINE = "Audio device switcher for Windows"
APP_PUBLISHER = "Oliver Ernster"
APP_EXE_NAME = "AudioDeck.exe"
INSTALLER_EXE_NAME = "AudioDeckSetup.exe"
START_MENU_FOLDER = "Audio Deck"

# Windows registry: per-user uninstall entry.
UNINSTALL_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\AudioDeck"

# Payload (bundled inside the setup exe).
PAYLOAD_DIR_NAME = "payload"
PAYLOAD_ZIP_NAME = "payload.zip"
MANIFEST_NAME = "manifest.json"
ICON_FILE_NAME = "audiodeck.ico"
# Where the generated icon set lives in the repo. The masters it is derived
# from sit in assets/ beside it and are never shipped.
ICONS_DIR_NAME = "icons"

# Layout inside the install directory.
UNINSTALL_SUBDIR = "_uninstall"

# CLI flag that puts the setup exe into uninstall mode.
UNINSTALL_FLAG = "--uninstall"

# Window copy.
SUBTITLE_TEXT = f"Welcome to the {APP_DISPLAY_NAME} installer"

# Theme. Every colour is sampled from the application's own artwork rather than
# picked by eye, so the setup program and the app it installs read as one thing:
# the accent is the icon's bright blue, the ring is its green and the danger
# colour is the red of the prohibition bar the delete and cancel icons wear.
#
# The RING MODEL is the house one and is deliberately not the application's: no
# ring at rest, a green ring while an enabled control is hovered or focused, a
# permanent danger ring while a control is disabled. Green reads as "you can use
# this"; the accent is never a ring, because it carries identity rather than
# state.

# Dark appearance.
DARK_WINDOW = "#0b1622"
DARK_SURFACE = "#132335"
DARK_SURFACE_ALT = "#1b2f46"
DARK_BORDER = "#24405e"
DARK_TEXT = "#eaf2fa"
DARK_TEXT_MUTED = "#9fb3c8"
DARK_ACCENT = "#00b0f8"
DARK_SELECTION = "#123a52"
DARK_RING = "#00d84a"
DARK_DANGER = "#ff6b6f"
DARK_DANGER_SOFT = "#3a1418"
DARK_DISABLED_SURFACE = "#16202b"
DARK_DISABLED_TEXT = "#63788c"

# Light appearance. The accent and the ring are darkened rather than reused: a
# bright cyan and a bright green both fail against white, so each theme names
# its own value and the contrast holds by construction.
LIGHT_WINDOW = "#eef6fb"
LIGHT_SURFACE = "#ffffff"
LIGHT_SURFACE_ALT = "#dcecf7"
LIGHT_BORDER = "#b6d4e6"
LIGHT_TEXT = "#0d2233"
LIGHT_TEXT_MUTED = "#4d6a80"
LIGHT_ACCENT = "#0077b0"
LIGHT_SELECTION = "#cfe9f8"
LIGHT_RING = "#00802a"
LIGHT_DANGER = "#c00000"
LIGHT_DANGER_SOFT = "#fbe0e1"
LIGHT_DISABLED_SURFACE = "#dfe7ed"
LIGHT_DISABLED_TEXT = "#8aa0b0"

# Sizes (named, no magic numbers in the UI). The house geometry and type
# scale, in pixels throughout: a point size renders differently per display DPI
# setting, so a window laid out in points and one laid out in pixels drift apart
# on the same machine.
WINDOW_MIN_WIDTH = 850
WINDOW_MIN_HEIGHT = 620

# The mark is drawn at a size that can be read across the room, which is the
# single strongest signal that the right installer is open.
MARK_PX = 126
CHECK_PX = 24
TRACK_PX = 9
RING_PX = 2

HEADER_SPACING = 13
HEADER_PAD_PX = 15
CONTENT_MARGIN_H = 26
CONTENT_MARGIN_TOP = 22
CONTENT_MARGIN_BOTTOM = 18
CONTENT_SPACING = 16
ACTION_SPACING = 18
OPTION_GAP_PX = 10

BASE_FONT_PX = 18
TITLE_FONT_PX = 32
SUB_FONT_PX = 18
HEADING_FONT_PX = 28
INFO_FONT_PX = 16
STATUS_FONT_PX = 16
LICENCE_FONT_PX = 13

BUTTON_MIN_WIDTH = 150
LICENCE_DIALOG_WIDTH = 680
LICENCE_DIALOG_HEIGHT = 520

# Bytes per kilobyte, for the registry EstimatedSize (a DWORD in KB).
BYTES_PER_KB = 1024

# Retry loop for self-delete / locked-file handling.
FILE_RETRY_COUNT = 20
FILE_RETRY_DELAY_SECONDS = 0.15

# Bounded poll waiting for a terminated app to actually disappear. A terminate
# returning success means the request was accepted, not that the process has
# gone, so the wait is confirmed rather than assumed. Three seconds in total,
# which is far longer than a forced terminate needs and short enough that a
# refusal is reported promptly rather than looking like another hang.
CLOSE_POLL_COUNT = 30
CLOSE_POLL_DELAY_SECONDS = 0.1


def install_dir() -> Path:
    """Return the per-user install directory.

    Returns:
        ``%LOCALAPPDATA%\\Programs\\AudioDeck``.
    """
    local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home()))
    return Path(local_app_data) / "Programs" / APP_NAME


def resource_path(relative: str) -> Path:
    """Resolve a bundled resource path for dev and PyInstaller runs.

    Args:
        relative: Path relative to the bundle root.

    Returns:
        Absolute path to the resource.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = str(Path(__file__).resolve().parent.parent)
    return Path(base) / relative
