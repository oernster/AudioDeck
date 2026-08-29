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

# Theme: Audio Deck signature purple, shared by dark and light variants.
COLOR_PURPLE_LIGHT = "#8b6ead"
COLOR_PURPLE_MID = "#7b5caa"
COLOR_PURPLE_DEEP = "#4a2c6a"
COLOR_PURPLE_BORDER = "#5a3d7f"
COLOR_ACCENT_HOVER = "#f59e0b"
COLOR_DANGER = "#7a1f25"
COLOR_DANGER_HOVER = "#6a1b21"

# Dark theme surfaces and text.
DARK_BG = "#2a2a2a"
DARK_SURFACE = "#353535"
DARK_TEXT = "#f0f0f0"
DARK_TEXT_MUTED = "#b8b8b8"
DARK_DISABLED_BG = "#555555"
DARK_DISABLED_TEXT = "#999999"

# Light theme surfaces and text.
LIGHT_BG = "#f4f1f8"
LIGHT_SURFACE = "#ffffff"
LIGHT_TEXT = "#2a2233"
LIGHT_TEXT_MUTED = "#6b6478"
LIGHT_DISABLED_BG = "#cfc8d8"
LIGHT_DISABLED_TEXT = "#8d8699"

# Sizes (named, no magic numbers in the UI).
WINDOW_MIN_WIDTH = 750
WINDOW_MIN_HEIGHT = 520
ICON_BADGE_PX = 64
HEADER_SPACING = 14
TITLE_FONT_PT = 22
SUBTITLE_FONT_PT = 14
STATUS_FONT_PT = 10
VERSION_FONT_PT = 11
CONTENT_MARGIN_H = 36
CONTENT_MARGIN_TOP = 24
CONTENT_MARGIN_BOTTOM = 20
CONTENT_SPACING = 16
ACTION_SPACING = 18
BORDER_WIDTH = 2
BORDER_RADIUS = 6
BUTTON_RADIUS = 22
BUTTON_PADDING_V = 10
BUTTON_PADDING_H = 24
BUTTON_MIN_WIDTH = 150
PROGRESS_HEIGHT = 18
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
