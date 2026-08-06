"""Locating bundled resources in development and in a frozen build.

The window and every Help dialog needs the same answer to "where is this file",
and the answer differs between running from source and running from the
PyInstaller bundle. It lives here rather than on the window so the dialogs can
use it without reaching back into their parent.

Author: Oliver Ernster
"""

import sys
from pathlib import Path

# The application icon, used at 64 pixels by the dialogs and as the window icon.
APP_ICON_PNG = "assets/audiodeck_icon_256.png"


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
