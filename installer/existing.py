"""What is already on this machine, read once before anything is drawn.

Setup used to open every box ticked whatever was actually there, so a user who
had deliberately declined a desktop shortcut was offered one again as though
they had asked for it; a reinstall then silently put it back. The boxes now say
what is true; the reading is taken once and passed around, so no two screens
can disagree about it.

Author: Oliver Ernster
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from installer import constants as c
from installer import registry, shortcuts


@dataclass(frozen=True)
class Existing:
    """What the machine already holds, at the moment setup started."""

    version: str
    location: Path
    desktop: bool
    start_menu: bool

    @property
    def installed(self) -> bool:
        """Whether there is an install to talk about at all."""
        return bool(self.version)

    @property
    def executable(self) -> Path:
        """The installed application, wherever the Apps list says it is."""
        return self.location / c.APP_EXE_NAME


def look() -> Existing:
    """Read the registry and the shortcut folders as they stand.

    Returns:
        One reading of the machine, for every screen to share.
    """
    recorded = registry.read_registered()
    location = Path(recorded.get("InstallLocation", str(c.install_dir())))
    return Existing(
        version=recorded.get("DisplayVersion", ""),
        location=location,
        desktop=shortcuts.desktop_shortcut_path().exists(),
        start_menu=shortcuts.start_menu_shortcut_path().exists(),
    )
