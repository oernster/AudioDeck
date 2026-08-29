"""Locating bundled resources in development and in a frozen build.

The window and every Help dialog needs the same answer to "where is this file",
while the answer differs between running from source and running from the
PyInstaller bundle. It lives here rather than on the window so the dialogs can
use it without reaching back into their parent.

Author: Oliver Ernster
"""

import sys
from pathlib import Path

# Everything the application draws comes out of the icon generator into this
# one directory. The masters it is generated FROM sit in assets/ beside it and
# are never read at runtime: they are multi-megabyte source artwork, so the
# build stages this directory alone.
ICONS_DIR = "assets/icons"

# The application icon, used at 64 pixels by the dialogs and as the window icon.
APP_ICON_PNG = f"{ICONS_DIR}/audiodeck_icon_256.png"

# The same icon as a multi-frame Windows .ico, which is what a window, a
# taskbar button and a shortcut want: Windows picks the frame it needs rather
# than rescaling one size badly.
APP_ICON_ICO = f"{ICONS_DIR}/audiodeck.ico"


def resource_path(relative_path: str) -> Path:
    """Return the absolute path to a bundled resource.

    Args:
        relative_path: Path to the resource, relative to the project root.

    Returns:
        The absolute path, resolved for a frozen build or for source.
    """
    # PyInstaller creates a temp folder and stores its path in _MEIPASS, which
    # only exists in a frozen build, so it is read defensively.
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir is not None:
        return Path(bundle_dir) / relative_path

    # Running in development mode.
    return Path(__file__).parent.parent.parent.parent / relative_path


def button_icon_path(name: str) -> Path:
    """Return the artwork for one button, named by what that button DOES.

    The name is the action ("switch", "delete-profile"), never the picture,
    because the caller is a button and knows its own job rather than its
    artwork. That is also what lets a picture be redrawn without touching any
    calling code.
    """
    return resource_path(f"{ICONS_DIR}/{name}.png")
