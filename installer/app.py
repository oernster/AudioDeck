"""Entry point for the Audio Deck setup executable.

Shows the state-driven installer window. When invoked with ``--uninstall`` (the
command registered in Add or Remove Programs) it preselects the uninstall flow.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `from installer import ...` when run as a script in development.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from installer import constants as c  # noqa: E402
from installer.state import Operation  # noqa: E402
from installer.theme import stylesheet  # noqa: E402
from installer.ui import InstallerWindow  # noqa: E402


def main() -> int:
    """Run the installer.

    Returns:
        Process exit code.
    """
    preselect = Operation.UNINSTALL if c.UNINSTALL_FLAG in sys.argv else None

    app = QApplication(sys.argv)
    app.setApplicationName(f"{c.APP_DISPLAY_NAME} Setup")
    app.setStyleSheet(stylesheet(dark=True))

    window = InstallerWindow(preselect=preselect)
    window.show()
    window.raise_()
    window.activateWindow()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
