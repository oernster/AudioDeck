"""The dialogs behind the Help button: documentation, licences and about.

These were methods on MainWindow, which put the dialog bodies inside the
class that owns the views and the device notifier. They are plain functions
taking the parent widget, because none of them needs anything from the
window except somewhere to sit.

Author: Oliver Ernster
"""

import math
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.presentation.views.resource_paths import APP_ICON_PNG, resource_path
from src.presentation.widgets.auto_scroller import AutoScroller

# The licence text arrives hard-wrapped, so the dialog is sized to the text
# rather than to a guessed minimum. The cap comes from the screen, not a
# constant: at the app's 13.5pt base font a 78-column licence line is
# around 1400px wide, so any fixed cap either truncates the text on a
# desktop monitor or overflows a small one. The margin keeps the dialog
# clear of the screen edges when the text wants more than the screen has.
LICENCE_HEIGHT_PX = 600
LICENCE_SCREEN_MARGIN_PX = 80

# Icon size used by every dialog that shows the app icon.
ICON_PX = 64

# Body font for the markdown viewer: 1.3x the base size rather than 1.5x.
VIEWER_FONT_CSS = "font-size: 11.7pt;"

ABOUT_HTML = f"""
<h2>Audio Deck</h2>
<p><b>A local-first audio device switcher for Windows, Linux and macOS,
with Stream Deck integration on Windows.</b></p>
<p><b>Version:</b> {__version__}</p>
<p><b>Author:</b> Oliver Ernster</p>
<p>Audio Deck is free software, distributed under two licences: the
backend under GPL-3.0 and the user interface under LGPL-3.0. See the Help
menu for both licences.</p>
<hr>
<h3>Open source credits</h3>
<ul>
<li><b>PySide6</b> (Qt for Python) - LGPL-3.0 (the user interface).</li>
<li><b>Python</b> - PSF License.</li>
<li><b>pycaw</b> - MIT (the Windows Core Audio seam).</li>
<li><b>comtypes</b> - MIT (COM bindings under pycaw).</li>
<li><b>PyInstaller</b> - GPL-2.0 with exception (packaging).</li>
<li><b>Pillow</b> - HPND (the icon build).</li>
<li><b>pytest, pytest-qt, pytest-cov, black, ruff, mypy</b> - MIT and
similar (the development tools).</li>
</ul>
<p>Built on the Python and Qt ecosystems, with thanks to their
communities.</p>
"""


def _scaled_app_icon() -> QPixmap | None:
    """Return the app icon scaled for a dialog, else None when it is missing."""
    icon_path = resource_path(APP_ICON_PNG)
    if not icon_path.exists():
        return None
    return QPixmap(str(icon_path)).scaled(
        ICON_PX,
        ICON_PX,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _make_icon_label() -> QLabel | None:
    """Return a label carrying the app icon, else None when it is missing."""
    pixmap = _scaled_app_icon()
    if pixmap is None:
        return None
    icon_label = QLabel()
    icon_label.setPixmap(pixmap)
    return icon_label


def _add_close_button(dialog: QDialog, layout: QVBoxLayout) -> None:
    """Add the Close button every one of these dialogs ends with."""
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)
    layout.addWidget(close_button)


def _read_bundled_text(
    parent: QWidget, path: Path, subject: str, missing_title: str
) -> str | None:
    """Return a bundled text file's contents, reporting failure to the user.

    Returns None when the file is absent or unreadable, having already shown
    the message, so the caller simply stops.
    """
    if not path.exists():
        QMessageBox.warning(
            parent,
            missing_title,
            f"{subject} file not found. Please check the installation.",
        )
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as error:
        # Falls back to showing nothing: the file exists but cannot be read,
        # which is a broken installation rather than something recoverable.
        QMessageBox.critical(parent, "Error", f"Failed to read {subject}: {error}")
        return None


def show_documentation(parent: QWidget) -> None:
    """Show the in-app user guide, headed by the app icon on the left."""
    content = _read_bundled_text(
        parent,
        resource_path("DOCUMENTATION.md"),
        "DOCUMENTATION.md",
        "Documentation Not Found",
    )
    if content is None:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle("Audio Deck Documentation")
    dialog.setMinimumSize(760, 600)

    layout = QVBoxLayout(dialog)

    icon_label = _make_icon_label()
    if icon_label is not None:
        header_layout = QHBoxLayout()
        header_layout.addWidget(icon_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

    text_browser = QTextBrowser()
    text_browser.setOpenExternalLinks(True)
    text_browser.setStyleSheet(VIEWER_FONT_CSS)
    text_browser.setMarkdown(content)
    layout.addWidget(text_browser)
    AutoScroller(text_browser)

    _add_close_button(dialog, layout)

    dialog.exec()


def _fit_dialog_width_to_text(
    dialog: QDialog, browser: QTextBrowser, layout: QVBoxLayout
) -> None:
    """Size a dialog to its pre-wrapped plain text instead of a guessed width.

    Must run after the text is set, and the browser must be POLISHED first:
    the app stylesheet's font only lands on the widget at polish time, so an
    unpolished document measures its ideal width in the default font and
    undersizes the dialog by the difference. The chrome is the scrollbar,
    the frame and the layout margins; the height stays a constant.
    """
    browser.ensurePolished()
    browser.document().setDefaultFont(browser.font())
    chrome = (
        browser.verticalScrollBar().sizeHint().width()
        + 2 * browser.frameWidth()
        + layout.contentsMargins().left()
        + layout.contentsMargins().right()
    )
    cap = dialog.screen().availableGeometry().width() - LICENCE_SCREEN_MARGIN_PX
    width = min(math.ceil(browser.document().idealWidth()) + chrome, cap)
    dialog.setMinimumSize(width, LICENCE_HEIGHT_PX)
    dialog.resize(width, LICENCE_HEIGHT_PX)


def _show_licence_file(parent: QWidget, file_name: str, title: str) -> None:
    """Show one licence text in a dialog sized to fit it."""
    licence_content = _read_bundled_text(
        parent, resource_path(file_name), file_name, "Licence Not Found"
    )
    if licence_content is None:
        return

    dialog = QDialog(parent)
    dialog.setWindowTitle(title)

    layout = QVBoxLayout(dialog)

    text_browser = QTextBrowser()
    text_browser.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)
    text_browser.setPlainText(licence_content)
    layout.addWidget(text_browser)
    _fit_dialog_width_to_text(dialog, text_browser, layout)
    AutoScroller(text_browser)

    _add_close_button(dialog, layout)

    dialog.exec()


def show_ui_license(parent: QWidget) -> None:
    """Show the user-interface licence (LGPL-3.0), aligning with Qt's."""
    _show_licence_file(parent, "LICENSE-LGPL-3.0.txt", "UI Licence - GNU LGPL v3.0")


def show_backend_license(parent: QWidget) -> None:
    """Show the backend licence (GPL-3.0)."""
    _show_licence_file(parent, "LICENSE-GPL-3.0.txt", "Backend Licence - GNU GPL v3.0")


def show_about(parent: QWidget) -> None:
    """Show the About dialog: icon, identity, licences and credits."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("About Audio Deck")
    dialog.setMinimumSize(540, 520)

    layout = QVBoxLayout(dialog)

    icon_label = _make_icon_label()
    if icon_label is not None:
        icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(icon_label)

    # A browser rather than a label so the body can auto-scroll when the
    # dialog is sized smaller than the content; attaching the scroller to a
    # body that fits is free, since it only acts on overflow.
    text_browser = QTextBrowser()
    text_browser.setOpenExternalLinks(True)
    text_browser.setHtml(ABOUT_HTML)
    layout.addWidget(text_browser)
    AutoScroller(text_browser)

    _add_close_button(dialog, layout)

    dialog.exec()
