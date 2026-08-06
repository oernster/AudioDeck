"""Desktop and Start Menu shortcut creation for Audio Deck.

Shortcuts are created with a short PowerShell WScript.Shell script so the
installer needs no extra Python dependency.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from installer import constants as c

_CREATE_NO_WINDOW = 0x08000000


def desktop_dir() -> Path:
    """Return the current user's Desktop directory."""
    return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"


def start_menu_dir() -> Path:
    """Return the current user's Start Menu Programs directory for the app."""
    appdata = os.environ.get("APPDATA", str(Path.home()))
    return (
        Path(appdata)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / c.START_MENU_FOLDER
    )


def desktop_shortcut_path() -> Path:
    """Return the Desktop shortcut path."""
    return desktop_dir() / f"{c.APP_DISPLAY_NAME}.lnk"


def start_menu_shortcut_path() -> Path:
    """Return the Start Menu shortcut path."""
    return start_menu_dir() / f"{c.APP_DISPLAY_NAME}.lnk"


def create_shortcut(
    shortcut_path: Path,
    target: Path,
    icon: Path,
    working_dir: Path,
) -> None:
    """Create a Windows shortcut (.lnk).

    Args:
        shortcut_path: Where to write the .lnk file.
        target: The executable the shortcut points at.
        icon: Icon file for the shortcut.
        working_dir: Working directory for the shortcut.
    """
    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{shortcut_path}'); "
        f"$s.TargetPath = '{target}'; "
        f"$s.WorkingDirectory = '{working_dir}'; "
        f"$s.IconLocation = '{icon}'; "
        f"$s.Description = '{c.APP_DISPLAY_NAME}'; "
        "$s.Save()"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        creationflags=_CREATE_NO_WINDOW,
    )


def remove_shortcut(shortcut_path: Path) -> None:
    """Delete a shortcut if present, then prune an empty Start Menu folder.

    Args:
        shortcut_path: The .lnk path to remove.
    """
    try:
        shortcut_path.unlink()
    except FileNotFoundError:
        pass
    parent = shortcut_path.parent
    if parent == start_menu_dir() and parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
