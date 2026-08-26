"""Read-only viewer for the bundled application licence."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from installer import constants as c


class LicenceDialog(QDialog):
    """Read-only viewer for the application licence."""

    def __init__(self, parent: QWidget) -> None:
        """Build the licence dialog."""
        super().__init__(parent)
        self.setWindowTitle(f"{c.APP_DISPLAY_NAME} License")
        self.setMinimumSize(c.LICENCE_DIALOG_WIDTH, c.LICENCE_DIALOG_HEIGHT)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setLineWrapMode(QTextBrowser.WidgetWidth)
        browser.setPlainText(self._licence_text())
        layout.addWidget(browser)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_row.addWidget(close_button)
        layout.addLayout(close_row)

    @staticmethod
    def _licence_text() -> str:
        """Return the bundled licence text, falling back to a placeholder."""
        try:
            return c.resource_path("LICENSE").read_text(encoding="utf-8")
        except OSError:
            return "GNU Lesser General Public License v3.0 (LGPL-3.0)."
